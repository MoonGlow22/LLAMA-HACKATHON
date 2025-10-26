import chromadb
from chromadb.config import Settings
import ollama
from pathlib import Path
import PyPDF2

class PDFRAGSystem:
    def __init__(self, collection_name="pdf_documents", persist_directory="./chroma_db"):
        """
        PDF RAG sistemi için ChromaDB ve Ollama embedding kullanımı
        
        Args:
            collection_name: ChromaDB koleksiyon adı
            persist_directory: Veritabanı kayıt dizini
        """
        # ChromaDB client oluştur
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Collection oluştur veya mevcut olanı al
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
    def extract_text_from_pdf(self, pdf_path):
        """PDF'den metin çıkar"""
        text_chunks = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_chunks.append({
                        'text': text,
                        'page': page_num + 1,
                        'source': Path(pdf_path).name
                    })
        
        return text_chunks
    
    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Metni parçalara böl"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
            
        return chunks
    
    def get_ollama_embedding(self, text, model="nomic-embed-text"):
        """Ollama kullanarak embedding oluştur"""
        try:
            response = ollama.embeddings(model=model, prompt=text)
            return response['embedding']
        except Exception as e:
            print(f"Embedding hatası: {e}")
            return None
    
    def add_pdf_to_chroma(self, pdf_path, chunk_size=500, overlap=50):
        """PDF'i ChromaDB'ye ekle"""
        print(f"PDF işleniyor: {pdf_path}")
        
        # PDF'den metin çıkar
        pages = self.extract_text_from_pdf(pdf_path)
        
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        doc_id = 0
        
        for page_data in pages:
            # Metni parçalara böl
            chunks = self.chunk_text(page_data['text'], chunk_size, overlap)
            
            for chunk_idx, chunk in enumerate(chunks):
                # Embedding oluştur
                embedding = self.get_ollama_embedding(chunk)
                
                if embedding:
                    documents.append(chunk)
                    embeddings.append(embedding)
                    metadatas.append({
                        'source': page_data['source'],
                        'page': page_data['page'],
                        'chunk': chunk_idx
                    })
                    ids.append(f"doc_{doc_id}")
                    doc_id += 1
                    
                    print(f"İşlendi: Sayfa {page_data['page']}, Parça {chunk_idx}")
        
        # ChromaDB'ye ekle
        if documents:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            print(f"\n✓ Toplam {len(documents)} parça ChromaDB'ye eklendi!")
        
        return len(documents)
    
    def query(self, query_text, n_results=5):
        """Sorgu yap ve benzer dokümanları getir"""
        # Sorgu için embedding oluştur
        query_embedding = self.get_ollama_embedding(query_text)
        
        if not query_embedding:
            return None
        
        # ChromaDB'de ara
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return results


# KULLANIM ÖRNEĞİ
if __name__ == "__main__":
    # RAG sistemi oluştur
    rag = PDFRAGSystem(
        collection_name="my_pdf_collection",
        persist_directory="./chroma_db"
    )
    
    # PDF'i ekle
    pdf_path = "chat_stage/src.pdf"  # PDF dosya yolunuzu buraya yazın
    rag.add_pdf_to_chroma(pdf_path, chunk_size=500, overlap=50)
    
    # Sorgu örneği
    print("\n--- SORGU YAPILIYOR ---")
    query = "Bu belgede ne anlatılıyor?"
    results = rag.query(query, n_results=3)
    
    if results:
        print(f"\nSorgu: {query}\n")
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"Sonuç {i+1}:")
            print(f"Kaynak: {metadata['source']}, Sayfa: {metadata['page']}")
            print(f"İçerik: {doc[:200]}...")
            print("-" * 80)