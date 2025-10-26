import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence
from operator import add as add_messages

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import PyPDF2
import io

# ---------------------------------------------------------------------
# PDF İşleme Fonksiyonları (YENİ)
# ---------------------------------------------------------------------
def extract_text_from_pdf(pdf_file):
    """PDF'den metin çıkar"""
    text_chunks = []
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    for page_num, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text.strip():
            text_chunks.append({
                'text': text,
                'page': page_num + 1
            })
    
    return text_chunks

def chunk_text(text, chunk_size=500, overlap=50):
    """Metni parçalara böl"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

def add_pdf_to_vectorstore(pdf_file, filename: str, vectorstore, chunk_size=500, overlap=50):
    """PDF'i Chroma veritabanına ekle"""
    pages = extract_text_from_pdf(pdf_file)
    
    all_texts = []
    all_metadatas = []
    
    for page_data in pages:
        chunks = chunk_text(page_data['text'], chunk_size, overlap)
        
        for chunk_idx, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_metadatas.append({
                'source': filename,
                'page': page_data['page'],
                'chunk': chunk_idx
            })
    
    if all_texts:
        vectorstore.add_texts(texts=all_texts, metadatas=all_metadatas)
        return len(all_texts)
    
    return 0

# ---------------------------------------------------------------------
# Ortam değişkenleri ve model yükleme
# ---------------------------------------------------------------------
load_dotenv()

DB_PATH = "chroma_db"
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

try:
    llm = Ollama(model=MODEL_NAME, temperature=0.7)
    print(f"✅ Ollama modeli '{MODEL_NAME}' başarıyla yüklendi.")
except Exception as e:
    print(f"⚠ Ollama bağlantı hatası: {e}")
    print("💡 'ollama serve' komutunun çalıştığından emin ol.")
    llm = None

# ---------------------------------------------------------------------
# Chroma vektör veritabanı setup
# ---------------------------------------------------------------------
def init_vectorstore():
    """Chroma veritabanını başlatır veya mevcut olanı yükler."""
    embeddings = FastEmbedEmbeddings()
    vectorstore = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings
    )
    return vectorstore

vectorstore = init_vectorstore()

# ---------------------------------------------------------------------
# RAG retriever aracı
# ---------------------------------------------------------------------
@tool
def retriever_tool(query: str):
    """Chroma'dan en benzer belgeleri getirir."""
    try:
        results = vectorstore.similarity_search(query, k=3)
        if not results:
            return "Veritabanında ilgili bilgi bulunamadı."
        text = "\n\n".join([
            f"📄 Kaynak: {doc.metadata.get('source', 'Bilinmiyor')} - Sayfa: {doc.metadata.get('page', 'N/A')}\n{doc.page_content}" 
            for doc in results
        ])
        return text
    except Exception as e:
        return f"RAG arama hatası: {e}"

tools = [retriever_tool]
tools_dict = {t.name: t for t in tools}

# ---------------------------------------------------------------------
# Agent graph (LangGraph) setup
# ---------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

def build_system_prompt():
    return (
        "Sen bir üniveriste öğrencisi ve yeni mezunlar için kariyer danışmanı ve CV analiz uzmanısın. "
        "Kullanıcının sorusunu yanıtlamak için gerekirse Chroma vektör veritabanından **retriever_tool** bilgi çekebilirsin. "
        "Yanıtlarında Nazik ve komik olmaya çalış, ancak bilgiyi net ve anlaşılır şekilde sun. Önemli olan sana soru soran kişinin ihtiyaçlarını karşılamak ve ona yardımcı olmaktır. "
    )

def should_continue(state: AgentState):
    result = state["messages"][-1]
    return hasattr(result, "tool_calls") and len(result.tool_calls) > 0

def call_llm(state: AgentState) -> AgentState:
    messages = [SystemMessage(content=build_system_prompt())] + list(state["messages"])
    message = llm.invoke(messages)
    return {"messages": [message]}

def take_action(state: AgentState) -> AgentState:
    tool_calls = state["messages"][-1].tool_calls
    results = []
    for t in tool_calls:
        if t["name"] not in tools_dict:
            result = "Hatalı araç adı"
        else:
            result = tools_dict[t["name"]].invoke(t["args"].get("query", ""))
        results.append(ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result)))
    return {"messages": results}

graph = StateGraph(AgentState)
graph.add_node("llm", call_llm)
graph.add_node("retriever_agent", take_action)
graph.add_conditional_edges("llm", should_continue, {True: "retriever_agent", False: END})
graph.add_edge("retriever_agent", "llm")
graph.set_entry_point("llm")

memory = MemorySaver()
rag_agent = graph.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "123"}}

# ---------------------------------------------------------------------
# FastAPI arayüzü
# ---------------------------------------------------------------------
app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    history: list[str] | None = None


def get_response_model(query, history=None):
    user_msg = HumanMessage(content=query)
    result = rag_agent.invoke({"messages": [user_msg]}, config)
    as1 = result['messages'][-1]
    if hasattr(as1, "content"):
        return as1.content

    return as1


if __name__ == "__main__":
    
    sonuc=get_response_model("Python programlama hakkında ne biliyorsun?")
    print(sonuc)
# ---------------------------------------------------------------------
# Başlatma
