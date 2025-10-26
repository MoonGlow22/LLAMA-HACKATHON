from typing import Optional
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import os
import re
import json
from fastapi import APIRouter
from pydantic import BaseModel
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
def bolumlere_ayir(text):
        # Tüm ana başlıkları (## ...) bul
        basliklar = re.findall(r"^##\s+.*", text, re.MULTILINE)
        bolumler = {}
        
        for i, baslik in enumerate(basliklar):
            baslik_adi = baslik.replace("##", "").strip()
            start = text.find(baslik)
            end = text.find(basliklar[i + 1], start + 1) if i + 1 < len(basliklar) else len(text)
            bolumler[baslik_adi] = text[start:end].strip()
        
        return bolumler
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
def mainagent(query: str):
    # CSV dosyasını oku
    df = pd.read_csv("backend/users.csv")

    """
    Determines whether a GitHub link is a repository or a profile,
    then runs the appropriate analyzer.
    """

    # Güvenli token kullanımı (gerçek ortamda environment variable'dan alınmalı)
    

    # Ollama LLM başlat
    #ollama_llm = OllamaLLM(model="llama3.1:8b", base_url="http://localhost:11434")

    # Prompt oluştur
    """prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a helpful assistant that identifies whether a GitHub link belongs to a repository or a profile."
        ),
        (
            "user",
            "Is this link a repository or profile: {query}? "
            "If it's a repo, return only 'repo'. If it's a profile, return only 'profile'."
        )
    ])"""

    # Chain oluştur
    """chain = prompt | ollama_llm

    # LLM'i çağır
    result = chain.invoke({"query": query})

    # Bazı modeller sonucu dict olarak döner
    if isinstance(result, dict):
        path = result.get("text", "").strip().lower()
    else:
        path = str(result).strip().lower()

    print(f"🔎 Model output: {path}")

    # -------------------------------
    # PROFİL veya REPO tespiti
    # -------------------------------
    if "profile" in path:"""
        # -------------------------------
        # 👤 PROFİL ANALİZİ
        # -------------------------------
        

        # Analyzer import et
    from ollama_chat4 import GitHubProfileAnalyzer

    analyzer = GitHubProfileAnalyzer(
        github_token=GITHUB_TOKEN,
    )

    # Kullanıcı adını URL'den ayıkla
    username = query.split("github.com/")[1].split("/")[0]
    print(f"👤 Analyzing GitHub profile: {username}")

    # Rapor oluştur
    report, hws, jsoned = analyzer.generate_full_report(username)
    jsoned=json.loads(jsoned)
    print(jsoned)
    report_sections = bolumlere_ayir(report)
    print("📄 Rapor bölümleri:", report_sections.keys())
    yeni_satir = pd.DataFrame(
        [[
            username,
            jsoned[0]["course_name"],
            jsoned[1]["course_name"],
            jsoned[0]["link"],
            jsoned[1]["link"]
        ]],
        columns=df.columns
    )
    
    # DataFrame'leri birleştir
    df_yeni = pd.concat([df, yeni_satir], ignore_index=True)

    # CSV'ye tekrar yaz
    df_yeni.to_csv(
        "backend/users.csv",
        index=False
    )

    return report_sections
        

        

def minagent2(query: str):
    

    from ollamachat3 import GitHubRepoAnalyzer

    analyzer = GitHubRepoAnalyzer(
        github_token=GITHUB_TOKEN,
        model_name="llama3.1:8b",
        chroma_path="./chroma_db"
    )

    # Kullanıcı adı ve repo ismini ayır
    parts = query.split("github.com/")[1].split("/")
    username, repo_name = parts[0], parts[1]

    print(f"📦 Analyzing repository: {username}/{repo_name}")

    # Analiz işlemleri
    metrics = analyzer.analyze_repo_comprehensive(
        username,
        repo_name,
        use_llm_scoring=False
    )
    ai_report = analyzer.generate_ai_deep_analysis(metrics)
    #pdf_path = analyzer.print_analysis_report(metrics, ai_report)
    reco = analyzer.analyze_requirements_modernization(username, repo_name)
    print(ai_report)
    return ai_report,reco
    

# -------------------------------
# 🧪 Test kodu
# -------------------------------
if __name__ == "__main__":
    query = "github.com/AltanReisoglu"
    out = mainagent(query)
    print(out)
