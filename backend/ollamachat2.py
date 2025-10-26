from typing import Dict, List, Optional
import requests
import json
from langchain_ollama.llms import OllamaLLM

import os
from datetime import datetime
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

import time
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.tools import tool

class GitHubProfileAnalyzer:
    """GitHub profil analizi yapan AI agent - ChromaDB ile kurs önerileri"""
    
    def __init__(self, github_token: Optional[str] = None, model_name: str = "llama3.1:8b", 
                 chroma_path: str = "./chroma_db"):
        """
        Args:
            github_token: GitHub API token (opsiyonel, rate limit için önerilir)
            model_name: Ollama model adı (llama3.2, llama2, mistral vb.)
            chroma_path: ChromaDB veritabanı yolu
        """
        self.github_token = github_token
        self.headers = {"Authorization": f"token {github_token}"} if github_token else {}
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Ollama LLM'i başlat
        try:
            self.llm = OllamaLLM(model=model_name, temperature=0.7)
            print(f"✅ Ollama modeli '{model_name}' başarıyla yüklendi")
        except Exception as e:
            print(f"⚠️ Ollama bağlantı hatası: {e}")
            print("💡 Ollama'nın çalıştığından emin olun: 'ollama serve'")
            self.llm = None
        
        # ChromaDB ve embedding fonksiyonu başlat
        try:
            self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
                model_name="nomic-embed-text",  # Ollama'da bulunan model
                url="http://localhost:11434/api/embeddings"
            )
            
            self.chroma_client =  chromadb.PersistentClient(path="./chroma_db")
            
            # programming_courses koleksiyonunu al veya oluştur
            try:
                self.courses_collection = self.chroma_client.get_collection(
                    name="courses",
                    embedding_function=self.embedding_fn
                )
                
                print(f"✅ ChromaDB 'courses' koleksiyonu yüklendi")
            except:
                self.courses_collection = self.chroma_client.create_collection(
                    name="programming_courses",
                    embedding_function=self.embedding_fn
                )
                print(f"✅ ChromaDB 'programming_courses' koleksiyonu oluşturuldu")
                
        except Exception as e:
            print(f"⚠️ ChromaDB bağlantı hatası: {e}")
            print("💡 ChromaDB'nin doğru yüklendiğinden emin olun")
            self.courses_collection = None
        
    def _make_request(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[requests.Response]:
        """Retry mantığı ile güvenli istek"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                
                # Rate limit kontrolü
                if response.status_code == 403:
                    rate_limit = response.headers.get('X-RateLimit-Remaining', 'Bilinmiyor')
                    if rate_limit == '0':
                        reset_time = response.headers.get('X-RateLimit-Reset', 'Bilinmiyor')
                        print(f"⚠️ Rate limit aşıldı. Reset zamanı: {reset_time}")
                        print("💡 GitHub token kullanarak rate limit'i artırabilirsiniz")
                    return None
                
                if response.status_code == 200:
                    return response
                    
                print(f"⚠️ HTTP {response.status_code} hatası, deneme {attempt + 1}/{max_retries}")
                
            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout hatası, deneme {attempt + 1}/{max_retries}")
            except requests.exceptions.ConnectionError as e:
                print(f"🔌 Bağlantı hatası, deneme {attempt + 1}/{max_retries}: {str(e)[:100]}")
            except Exception as e:
                print(f"❌ Beklenmeyen hata: {str(e)[:100]}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"⏳ {wait_time} saniye bekleniyor...")
                time.sleep(wait_time)
        
        return None
    
    def get_user_profile(self, username: str) -> Optional[Dict]:
        """GitHub kullanıcı profilini çek"""
        url = f"{self.base_url}/users/{username}"
        response = self._make_request(url)
        
        if response is None or response.status_code != 200:
            print(f"❌ Kullanıcı profili alınamadı: {username}")
            return None
        
        return response.json()
    
    def get_user_repos(self, username: str, max_repos: int = 50) -> List[Dict]:
        """Kullanıcının repolarını çek"""
        url = f"{self.base_url}/users/{username}/repos"
        params = {"per_page": min(max_repos, 100), "sort": "updated"}
        response = self._make_request(url, params)
        
        if response is None:
            print("⚠️ Repolar alınamadı, boş liste döndürülüyor")
            return []
        
        return response.json()
    
    def get_repo_languages(self, username: str, repo_name: str) -> Dict:
        """Repo dillerini çek"""
        url = f"{self.base_url}/repos/{username}/{repo_name}/languages"
        response = self._make_request(url)
        
        if response is None:
            return {}
        
        return response.json()
    
    def analyze_profile_data(self, username: str) -> Optional[Dict]:
        """Profil verilerini topla ve analiz et"""
        print(f"\n {username} kullanıcısının profili analiz ediliyor...")
        
        # Profil bilgilerini çek
        profile = self.get_user_profile(username)
        if profile is None:
            return None
        
        print(f"✅ Profil bilgileri alındı")
        
        repos = self.get_user_repos(username, max_repos=30)
        print(f"✅ {len(repos)} repo bilgisi alındı")
        
        # İstatistikleri hesapla
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repos)
        total_forks = sum(repo.get('forks_count', 0) for repo in repos)
        
        # Dilleri topla (rate limit için sınırlı sayıda)
        all_languages = {}
        print(f"📝 Dil analizi yapılıyor (ilk 10 repo)...")
        
        for i, repo in enumerate(repos[:10]):
            if not repo.get('fork', False):
                langs = self.get_repo_languages(username, repo['name'])
                for lang, bytes_count in langs.items():
                    all_languages[lang] = all_languages.get(lang, 0) + bytes_count
                time.sleep(0.5)  # Rate limit için
        
        # En çok kullanılan diller
        sorted_languages = sorted(all_languages.items(), key=lambda x: x[1], reverse=True)
        top_languages = [lang for lang, _ in sorted_languages[:10]]
        
        # Aktif repo sayısı (son 6 ayda güncellenmiş)
        try:
            six_months_ago = datetime.now().timestamp() - (6 * 30 * 24 * 60 * 60)
            active_repos = []
            for r in repos:
                try:
                    updated = datetime.strptime(r['updated_at'], '%Y-%m-%dT%H:%M:%SZ').timestamp()
                    if updated > six_months_ago:
                        active_repos.append(r)
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Aktivite hesaplaması sırasında hata: {e}")
            active_repos = []
        
        analysis_data = {
            'username': username,
            'name': profile.get('name') or 'N/A',
            'bio': profile.get('bio') or 'Biyografi yok',
            'location': profile.get('location') or 'Belirtilmemiş',
            'company': profile.get('company') or 'Belirtilmemiş',
            'public_repos': profile.get('public_repos', 0),
            'followers': profile.get('followers', 0),
            'following': profile.get('following', 0),
            'account_created': profile.get('created_at', 'N/A'),
            'total_stars': total_stars,
            'total_forks': total_forks,
            'top_languages': top_languages if top_languages else ['Veri yok'],
            'active_repos_count': len(active_repos),
            'top_repos': sorted(repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)[:5]
        }
        
        print(f"✅ Analiz tamamlandı\n")
        return analysis_data
    
    def calculate_score(self, data: Dict) -> Dict:
        """Profil skoru hesapla"""
        score_breakdown = {
            'repo_count': min((data['public_repos'] / 50) * 20, 20),
            'followers': min((data['followers'] / 100) * 15, 15),
            'stars': min((data['total_stars'] / 200) * 25, 25),
            'activity': min((data['active_repos_count'] / 10) * 15, 15),
            'language_diversity': min(len(data['top_languages']) * 2.5, 15),
            'forks': min((data['total_forks'] / 50) * 10, 10)
        }
        
        total_score = sum(score_breakdown.values())
        
        return {
            'total_score': round(total_score, 1),
            'max_score': 100,
            'breakdown': score_breakdown,
            'rating': self._get_rating(total_score)
        }
    
    def _get_rating(self, score: float) -> str:
        """Skor bazlı değerlendirme"""
        if score >= 80:
            return "⭐⭐⭐⭐⭐ Mükemmel"
        elif score >= 60:
            return "⭐⭐⭐⭐ Çok İyi"
        elif score >= 40:
            return "⭐⭐⭐ İyi"
        elif score >= 20:
            return "⭐⭐ Orta"
        else:
            return "⭐ Başlangıç"
    
    def retrieve_courses_from_chromadb(self, languages: List[str], level: str, n_results: int = 5) -> List[Dict]:
        """ChromaDB'den kullanıcı profiline uygun kursları retrieve et"""
        if self.courses_collection is None:
            print("⚠️ ChromaDB koleksiyonu mevcut değil")
            return []
        
        print(f"🔍 ChromaDB'den kurs aranıyor - Diller: {languages[:3]}")
        
        # Her dil için ayrı ayrı sorgu yap
        all_courses = []
        seen_course_names = set()  # Duplikasyon önlemek için
        
        for lang in languages[:5]:  # İlk 5 dili kullan
            try:
                result = self.courses_collection.query(
                    query_texts=[f"{lang} programming"],
                    n_results=n_results
                )
                
                # Sonuçları işle
                if result and result['documents'] and result['documents'][0]:
                    for i in range(len(result['documents'][0])):
                        course_name = result['metadatas'][0][i].get('course_name', '')
                        
                        # Duplikasyonu önle
                        if course_name and course_name not in seen_course_names:
                            course_info = {
                                'content': result['documents'][0][i],
                                'metadata': result['metadatas'][0][i],
                                'distance': result['distances'][0][i],
                                'similarity': 1 - result['distances'][0][i],
                                'language_match': lang  # Hangi dil için bulundu
                            }
                            all_courses.append(course_info)
                            seen_course_names.add(course_name)
                            
            except Exception as e:
                print(f"⚠️ {lang} için sorgu hatası: {e}")
                continue
        
        # Benzerlik skoruna göre sırala
        all_courses.sort(key=lambda x: x['similarity'], reverse=True)
        
        # En iyi n_results kadarını al
        top_courses = all_courses[:n_results * 2]  # Biraz fazla al, LLM seçsin
        
        if top_courses:
            print(f"✅ {len(top_courses)} benzersiz kurs bulundu")
            print(f"   En yüksek benzerlik: {top_courses[0]['similarity']:.2f}")
            print(f"   Bulunan diller: {set(c['language_match'] for c in top_courses)}")
        else:
            print("⚠️ Hiç kurs bulunamadı")
        
        return top_courses
            
        
    
    def generate_ai_analysis(self, data: Dict, score_data: Dict) -> str:
        """LLM ile detaylı analiz oluştur"""
        
        
        template = """Profesyonel bir GitHub profil yardımcısısın. Görevin, aşağıda sağlanan profil verilerini analiz etmek ve aşağıdaki yapıya bağlı kalarak Türkçe geri bildirim vermektir:

1. Güçlü Yönleri belirt.
2. Geliştirilebilecek Alanlardan bahset.
3. Pratik Öneriler sun.
4. Kariyer Tavsiyesi ver.

Profil Verileri:
{profile_data}

Puan Verileri:
{score_data}

İçten, motive edici ve yapıcı bir ton kullan. Yazarken kısa ve öz ol.
"""
        
        try:
            prompt = ChatPromptTemplate.from_template(template)
            chain = prompt | self.llm
            
            profile_summary = f"""Kullanıcı: {data['username']}, İsim: {data['name']}, Repo: {data['public_repos']}, Takipçi: {data['followers']}, Yıldız: {data['total_stars']}, Diller: {', '.join(data['top_languages'][:5])}"""
            
            score_summary = f"""Skor: {score_data['total_score']}/100, Seviye: {score_data['rating']}"""
            
            print("🤖 AI analizi oluşturuluyor...\n")
            ai_analysis = chain.invoke({"profile_data": profile_summary, "score_data": score_summary})
            
            return ai_analysis
            
        except Exception as e:
            print(f"⚠️ AI analizi oluşturulamadı: {e}")
            
    
    
    
    def generate_course_recommendations(self, data: Dict) -> str:
        """ChromaDB'den retrieve edilen kurslarla öneriler oluştur"""
        
        
        
        print("DATALARFA")
        print(data['top_languages'])
        # Seviye belirleme
        level = "Beginner" if data['public_repos'] < 10 else "Intermediate" if data['public_repos'] < 30 else "Advanced"
        
        # ChromaDB'den kurs retrieve et
        retrieved_courses = self.retrieve_courses_from_chromadb(
            languages=data['top_languages'][:5],
            level=level,
            n_results=1
        )
        
        # Retrieve edilen kursları formatlı string'e çevir
        courses_context = "\n\n".join([
            f"Kurs {i+1}:\n{course['content']}\n(Benzerlik skoru: {1 - course['distance']:.2f})"
            for i, course in enumerate(retrieved_courses[:5])
        ])
        
        template = """Sen profesyonel bir kariyer danışmanı ve kurs tavsiye motorusun.

Aşağıda ChromaDB'den retrieve edilmiş, kullanıcının profiliyle ilgili kurslar var:

{courses_context}

Kullanıcının mevcut durumu:
- Diller: {languages}
- Seviye: {level}
- Repo sayısı: {repo_count}

Bu retrieve edilmiş kursları kullanarak, kullanıcıya EN UYGUN 5 KURSU seç ve öner.
Her kurs için şunları belirt:
- Kurs Adı ve Platform
- Neden Bu Kursu Öneriyorum (kullanıcının profiline göre)
- Tahmini Süre

Yanıt **kısa, açık ve tamamen Türkçe** olmalıdır.
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm
        
        print("📚 ChromaDB kursları kullanılarak öneriler hazırlanıyor...\n")
        recommendations = chain.invoke({
            "courses_context": courses_context,
            "languages": ', '.join(data['top_languages'][:8]),
            "level": level,
            "repo_count": data['public_repos']
        })
        
        return recommendations,retrieved_courses
            
        
            
    
    def _generate_fallback_courses(self, data: Dict) -> str:
        """Temel kurs önerileri"""
        top_lang = data['top_languages'][0] if data['top_languages'] else 'Python'
        
        courses = f"""
### 📚 Önerilen Kurslar

1. **{top_lang} Advanced Concepts** (Udemy)
   - Derin {top_lang} bilgisi için
   - 30-40 saat
   
2. **System Design & Architecture** (Coursera)
   - Büyük sistemler tasarla
   - 20-30 saat
   
3. **Git & GitHub Mastery** (YouTube/FreeCodeCamp)
   - Version control uzmanlığı
   - 10-15 saat
   
4. **Clean Code Principles** (Udemy)
   - Kod kalitesini artır
   - 15-20 saat
   
5. **DevOps Fundamentals** (Pluralsight)
   - CI/CD ve deployment
   - 25-35 saat

💡 **Öneri:** Önce System Design, sonra DevOps, ardından diğerleri.
"""
        return courses
    
    def generate_full_report(self, username: str) -> str:
        """Tam rapor oluştur"""
        try:
            # Veri toplama
            data = self.analyze_profile_data(username)
            
            if data is None:
                return f"❌ {username} kullanıcısı için profil verisi alınamadı.\n\n💡 Kontrol edin:\n- İnternet bağlantınız\n- Kullanıcı adı doğru mu\n- GitHub API erişilebilir mi"
            
            # Skor hesaplama
            score_data = self.calculate_score(data)
            
            # AI analizleri
            ai_analysis = self.generate_ai_analysis(data, score_data)
            course_recommendations,retrieved_courses = self.generate_course_recommendations(data)
            hw_courses=retrieved_courses[:2]
            # Raporu birleştir
            report = f"""
# 🎯 GitHub Profil Analiz Raporu

## 👤 Kullanıcı Bilgileri
- **Kullanıcı Adı:** {data['username']}
- **İsim:** {data['name']}
- **Biyografi:** {data['bio']}
- **Konum:** {data['location']}
- **Şirket:** {data['company']}
- **Hesap Oluşturma:** {data['account_created'][:10]}

## 📊 İstatistikler
- **Toplam Repo:** {data['public_repos']}
- **Takipçi:** {data['followers']}
- **Takip Edilen:** {data['following']}
- **Toplam Yıldız:** {data['total_stars']} ⭐
- **Toplam Fork:** {data['total_forks']} 🔱
- **Aktif Repo (Son 6 Ay):** {data['active_repos_count']}

## 💻 En Çok Kullanılan Diller
{', '.join(data['top_languages'])}

## 🏆 En Popüler Repolar
"""
            for i, repo in enumerate(data['top_repos'], 1):
                report += f"\n{i}. **{repo['name']}** - ⭐ {repo['stargazers_count']} | 🔱 {repo.get('forks_count', 0)}"
                if repo.get('description'):
                    report += f"\n   _{repo['description']}_"
                report += "\n"
            
            report += f"""
## 📈 Profil Skoru
**{score_data['total_score']}/{score_data['max_score']}** - {score_data['rating']}

### Detaylı Skor:
- 📦 Repo Sayısı: {score_data['breakdown']['repo_count']:.1f}/20
- 👥 Takipçi: {score_data['breakdown']['followers']:.1f}/15
- ⭐ Yıldız: {score_data['breakdown']['stars']:.1f}/25
- 🔄 Aktivite: {score_data['breakdown']['activity']:.1f}/15
- 💬 Dil Çeşitliliği: {score_data['breakdown']['language_diversity']:.1f}/15
- 🔱 Fork: {score_data['breakdown']['forks']:.1f}/10

## 🤖 AI Analizi
{ai_analysis}

## 📚 Öğrenme Yol Haritası (ChromaDB Retrieval)
{course_recommendations}

---
*Rapor: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Powered by ChromaDB + Ollama + GitHub API*
"""
            
            return report,hw_courses
            
        except Exception as e:
            return f"❌ Beklenmeyen hata: {str(e)}\n\nLütfen:\n1. İnternet bağlantısını kontrol edin\n2. Ollama'nın çalıştığından emin olun\n3. GitHub API'nin erişilebilir olduğunu doğrulayın\n4. ChromaDB'nin doğru yapılandırıldığını kontrol edin"


# Kullanım örneği
if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║     🤖 GitHub Profil Analiz AI Agent                    ║
║     Powered by Ollama + ChromaDB + LangChain            ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # GitHub token (opsiyonel)
    GITHUB_TOKEN = "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"  # veya None
    
    if not GITHUB_TOKEN:
        print("💡 İpucu: GitHub token kullanarak rate limit'i artırabilirsiniz")
        print("   Token almak için: https://github.com/settings/tokens\n")
    
    # Analyzer'ı başlat
    analyzer = GitHubProfileAnalyzer(
        github_token=GITHUB_TOKEN,
        model_name="llama3.2:3b",  # veya "llama2", "mistral"
        chroma_path="./chroma_db"  # ChromaDB yolu
    )
    
    # Analiz et
    username = input("\n🔍 GitHub kullanıcı adını girin: ").strip()
    
    if not username:
        print("❌ Kullanıcı adı boş olamaz!")
        exit(1)
    
    print("\n" + "="*60)
    print("🚀 Analiz başlatılıyor...")
    print("="*60)
    
    report,hws = analyzer.generate_full_report(username)
    
    print("\n" + "="*60)
    print(hws)
    print("="*60 + "\n")