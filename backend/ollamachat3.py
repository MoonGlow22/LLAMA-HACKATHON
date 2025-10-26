from typing import Dict, List, Optional
import requests
import json
from langchain_ollama.llms import OllamaLLM
from datetime import datetime, timedelta
from langchain_core.prompts import ChatPromptTemplate
import time
import chromadb
from chromadb.utils import embedding_functions
import base64
import re
import logging

class GitHubRepoAnalyzer:
    """Gelişmiş GitHub repo ve kullanıcı analizi yapan AI agent"""
    
    def __init__(self, github_token: Optional[str] = None, model_name: str = "llama3.1:8b",
                 chroma_path: str = "./chroma_db"):
        """
        Args:
            github_token: GitHub API token (ZORUNLU - detaylı analiz için)
            model_name: Ollama model adı
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
            #print(f"✅ Ollama modeli '{model_name}' başarıyla yüklendi")
        except Exception as e:
            print(f"⚠️ Ollama bağlantı hatası: {e}")
            self.llm = None
        
        # ChromaDB başlat
        try:
            self.embedding_fn = embedding_functions.OllamaEmbeddingFunction(
                model_name="nomic-embed-text",
                url="http://localhost:11434/api/embeddings"
            )
            
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            
            # GitHub repos koleksiyonu
            try:
                self.repos_collection = self.chroma_client.get_collection(
                    name="github_repos",
                    embedding_function=self.embedding_fn
                )
                print(f"✅ ChromaDB 'github_repos' koleksiyonu yüklendi")
            except:
                self.repos_collection = self.chroma_client.create_collection(
                    name="github_repos",
                    embedding_function=self.embedding_fn,
                    metadata={"description": "Popular GitHub repositories"}
                )
                #print(f"✅ ChromaDB 'github_repos' koleksiyonu oluşturuldu")
                
        except Exception as e:
            #print(f"⚠️ ChromaDB bağlantı hatası: {e}")
            self.repos_collection = None
    
    
    
    def get_repo_details(self, owner: str, repo: str) -> Optional[Dict]:
        """Repo detaylarını çek"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = self._make_request(url)
        return response.json() if response else None
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict:
        """Repo dillerini çek - Temel beceriler için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/languages"
        response = self._make_request(url)
        return response.json() if response else {}
    
    def get_commit_activity(self, owner: str, repo: str) -> List[Dict]:
        """Haftalık commit aktivitesi - Disiplin ve süreklilik için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/stats/commit_activity"
        response = self._make_request(url)
        
        if response:
            # GitHub bazen 202 döner (hesaplama yapıyor), tekrar dene
            if response.status_code == 202:
                time.sleep(3)
                response = self._make_request(url)
        
        return response.json() if response else []
    
    def get_contributors(self, owner: str, repo: str) -> List[Dict]:
        """Katkıda bulunanlar - Ekip çalışması için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
        response = self._make_request(url)
        return response.json() if response else []
    
    def get_commits(self, owner: str, repo: str, max_commits: int = 50) -> List[Dict]:
        """Son commit'ler - Kod kalitesi ve profesyonellik için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"per_page": max_commits}
        response = self._make_request(url, params)
        return response.json() if response else []
    
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """README - İletişim/Dokümantasyon becerisi için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        response = self._make_request(url)
        
        if response:
            try:
                content = response.json().get('content', '')
                return base64.b64decode(content).decode('utf-8')
            except:
                pass
        return None
    
    def get_issues(self, owner: str, repo: str, state: str = "all", max_issues: int = 50) -> List[Dict]:
        """Issue'lar - İletişim becerisi ve problem çözme için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params = {"state": state, "per_page": max_issues}
        response = self._make_request(url, params)
        return response.json() if response else []
    
    def get_issue_comments(self, owner: str, repo: str, issue_number: int) -> List[Dict]:
        """Issue yorumları - İletişim kalitesi için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        response = self._make_request(url)
        return response.json() if response else []
    
    def get_pull_requests(self, owner: str, repo: str, state: str = "all", max_prs: int = 30) -> List[Dict]:
        """PR'lar - Code review kalitesi için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params = {"state": state, "per_page": max_prs}
        response = self._make_request(url, params)
        return response.json() if response else []
    
    def get_pr_reviews(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """PR yorumları - Code review derinliği için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
        response = self._make_request(url)
        return response.json() if response else []
    
    def get_pr_comments(self, owner: str, repo: str, pr_number: int) -> List[Dict]:
        """PR comment'leri - Teknik derinlik için"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        response = self._make_request(url)
        return response.json() if response else []
    
    def get_user_events(self, username: str, max_events: int = 100) -> List[Dict]:
        """Kullanıcı aktiviteleri - Açık kaynak katkıları için"""
        url = f"{self.base_url}/users/{username}/events"
        params = {"per_page": max_events}
        response = self._make_request(url, params)
        return response.json() if response else []
    
    
    
    def analyze_commit_messages(self, commits: List[Dict]) -> Dict:
        """Commit mesajlarını analiz et - Profesyonellik için"""
        print("📝 Commit mesajları analiz ediliyor...")
        
        conventional_pattern = re.compile(r'^(feat|fix|docs|style|refactor|test|chore|perf|ci|build|revert)(\(.+\))?:', re.IGNORECASE)
        
        total = len(commits)
        conventional_count = 0
        avg_length = 0
        descriptive_count = 0  # 20 karakterden uzun
        
        for commit in commits:
            try:
                message = commit['commit']['message'].split('\n')[0]  # İlk satır
                avg_length += len(message)
                
                if conventional_pattern.match(message):
                    conventional_count += 1
                
                if len(message) >= 20:
                    descriptive_count += 1
            except:
                continue
        
        return {
            'total_commits': total,
            'conventional_commits': conventional_count,
            'conventional_percentage': (conventional_count / total * 100) if total > 0 else 0,
            'avg_message_length': avg_length / total if total > 0 else 0,
            'descriptive_commits': descriptive_count,
            'descriptive_percentage': (descriptive_count / total * 100) if total > 0 else 0
        }
    
    def analyze_readme_quality(self, readme: str) -> Dict:
        """README kalitesini analiz et - Dokümantasyon becerisi için"""
        if not readme:
            return {'has_readme': False, 'quality_score': 0}
        
        print("📚 README kalitesi analiz ediliyor...")
        
        quality_indicators = {
            'has_title': bool(re.search(r'^#\s+.+', readme, re.MULTILINE)),
            'has_description': len(readme) > 200,
            'has_installation': 'install' in readme.lower() or 'setup' in readme.lower(),
            'has_usage': 'usage' in readme.lower() or 'example' in readme.lower(),
            'has_contributing': 'contribut' in readme.lower(),
            'has_license': 'license' in readme.lower(),
            'has_badges': bool(re.search(r'\[!\[.+\]\(.+\)\]', readme)),
            'has_code_blocks': '```' in readme,
            'has_images': bool(re.search(r'!\[.+\]\(.+\)', readme)),
        }
        
        quality_score = sum(quality_indicators.values()) / len(quality_indicators) * 100
        
        return {
            'has_readme': True,
            'length': len(readme),
            'quality_indicators': quality_indicators,
            'quality_score': quality_score
        }
    
    def analyze_issue_communication(self, issues: List[Dict], owner: str, repo: str) -> Dict:
        """Issue'lardaki iletişim kalitesini analiz et"""
        print("💬 Issue iletişim kalitesi analiz ediliyor...")
        
        created_issues = [i for i in issues if not i.get('pull_request')]
        
        analysis = {
            'total_issues': len(created_issues),
            'open_issues': len([i for i in created_issues if i['state'] == 'open']),
            'closed_issues': len([i for i in created_issues if i['state'] == 'closed']),
            'avg_title_length': 0,
            'has_labels': 0,
            'has_description': 0,
            'professional_titles': 0,
        }
        
        if not created_issues:
            return analysis
        
        total_title_length = 0
        
        for issue in created_issues[:20]:  # İlk 20 issue
            title = issue.get('title', '')
            body = issue.get('body', '')
            labels = issue.get('labels', [])
            
            total_title_length += len(title)
            
            if labels:
                analysis['has_labels'] += 1
            
            if body and len(body) > 50:
                analysis['has_description'] += 1
            
            # Profesyonel başlık kontrolü (Bug:, Feature:, vb.)
            if re.match(r'^(bug|feature|enhancement|question|documentation|help):', title, re.IGNORECASE):
                analysis['professional_titles'] += 1
        
        total = min(len(created_issues), 20)
        analysis['avg_title_length'] = total_title_length / total if total > 0 else 0
        analysis['label_usage_rate'] = (analysis['has_labels'] / total * 100) if total > 0 else 0
        analysis['description_rate'] = (analysis['has_description'] / total * 100) if total > 0 else 0
        analysis['professional_title_rate'] = (analysis['professional_titles'] / total * 100) if total > 0 else 0
        
        return analysis
    
    def analyze_code_review_quality(self, prs: List[Dict], owner: str, repo: str) -> Dict:
        """Code review kalitesini analiz et"""
        print("🔍 Code review kalitesi analiz ediliyor...")
        
        analysis = {
            'total_prs': len(prs),
            'reviewed_prs': 0,
            'avg_review_depth': 0,
            'constructive_feedback': 0,
            'total_review_comments': 0
        }
        
        if not prs:
            return analysis
        
        total_depth = 0
        
        for pr in prs[:10]:  # İlk 10 PR
            pr_number = pr['number']
            
            # PR yorumları
            comments = self.get_pr_comments(owner, repo, pr_number)
            reviews = self.get_pr_reviews(owner, repo, pr_number)
            
            if comments or reviews:
                analysis['reviewed_prs'] += 1
                analysis['total_review_comments'] += len(comments) + len(reviews)
            
            # Yorum derinliği analizi
            for comment in comments[:5]:
                body = comment.get('body', '')
                if len(body) > 100:  # Detaylı yorum
                    total_depth += 1
                if any(word in body.lower() for word in ['suggest', 'consider', 'recommend', 'could', 'maybe']):
                    analysis['constructive_feedback'] += 1
            
            time.sleep(0.5)  # Rate limit
        
        total_prs = min(len(prs), 10)
        if total_prs > 0:
            analysis['review_rate'] = (analysis['reviewed_prs'] / total_prs * 100)
            analysis['avg_review_depth'] = total_depth / total_prs
            analysis['constructive_rate'] = (analysis['constructive_feedback'] / max(analysis['total_review_comments'], 1) * 100)
        
        return analysis
    
    def analyze_problem_solving(self, issues: List[Dict]) -> Dict:
        """Problem çözme yeteneğini analiz et"""
        print("🎯 Problem çözme yeteneği analiz ediliyor...")
        
        created_issues = [i for i in issues if not i.get('pull_request')]
        closed_by_creator = []
        
        for issue in created_issues[:30]:
            if issue['state'] == 'closed':
                # Issue kapatılma süresini hesapla
                try:
                    created = datetime.strptime(issue['created_at'], '%Y-%m-%dT%H:%M:%SZ')
                    closed = datetime.strptime(issue['closed_at'], '%Y-%m-%dT%H:%M:%SZ')
                    resolution_time = (closed - created).days
                    
                    closed_by_creator.append({
                        'issue': issue['title'],
                        'resolution_days': resolution_time,
                        'labels': [l['name'] for l in issue.get('labels', [])]
                    })
                except:
                    pass
        
        if closed_by_creator:
            avg_resolution = sum(i['resolution_days'] for i in closed_by_creator) / len(closed_by_creator)
            
            # Issue tiplerini kategorize et
            bug_issues = [i for i in closed_by_creator if any('bug' in l.lower() for l in i['labels'])]
            feature_issues = [i for i in closed_by_creator if any('feature' in l.lower() or 'enhancement' in l.lower() for l in i['labels'])]
        else:
            avg_resolution = 0
            bug_issues = []
            feature_issues = []
        
        return {
            'total_created': len(created_issues),
            'total_resolved': len(closed_by_creator),
            'resolution_rate': (len(closed_by_creator) / len(created_issues) * 100) if created_issues else 0,
            'avg_resolution_days': avg_resolution,
            'bug_fixes': len(bug_issues),
            'feature_implementations': len(feature_issues),
        }
    
    def analyze_open_source_contributions(self, events: List[Dict], username: str) -> Dict:
        """Açık kaynak katkılarını analiz et"""
        print("🌍 Açık kaynak katkıları analiz ediliyor...")
        
        contributions = {
            'external_repos': set(),
            'pr_events': 0,
            'issue_events': 0,
            'review_events': 0,
            'total_external_activity': 0
        }
        
        for event in events:
            repo_name = event.get('repo', {}).get('name', '')
            event_type = event.get('type', '')
            
            # Kullanıcının kendi reposu değilse
            if username.lower() not in repo_name.lower():
                contributions['external_repos'].add(repo_name)
                contributions['total_external_activity'] += 1
                
                if event_type == 'PullRequestEvent':
                    contributions['pr_events'] += 1
                elif event_type == 'IssuesEvent':
                    contributions['issue_events'] += 1
                elif event_type == 'PullRequestReviewEvent':
                    contributions['review_events'] += 1
        
        return {
            'unique_external_repos': len(contributions['external_repos']),
            'total_external_activity': contributions['total_external_activity'],
            'external_prs': contributions['pr_events'],
            'external_issues': contributions['issue_events'],
            'external_reviews': contributions['review_events'],
            'community_engagement_score': min(len(contributions['external_repos']) * 10, 100)
        }
    
    def analyze_commit_activity_discipline(self, commit_activity: List[Dict]) -> Dict:
        """Commit disiplini ve sürekliliği analiz et"""
        if not commit_activity:
            return {'consistency_score': 0, 'active_weeks': 0}
        
        print("📊 Commit disiplini analiz ediliyor...")
        
        total_weeks = len(commit_activity)
        active_weeks = sum(1 for week in commit_activity if week.get('total', 0) > 0)
        total_commits = sum(week.get('total', 0) for week in commit_activity)
        
        # Haftalık ortalama
        avg_commits_per_week = total_commits / total_weeks if total_weeks > 0 else 0
        
        # Süreklilik skoru (aktif hafta yüzdesi)
        consistency_score = (active_weeks / total_weeks * 100) if total_weeks > 0 else 0
        
        return {
            'total_weeks_analyzed': total_weeks,
            'active_weeks': active_weeks,
            'total_commits_year': total_commits,
            'avg_commits_per_week': avg_commits_per_week,
            'consistency_score': consistency_score,
            'work_rhythm': 'Yüksek' if consistency_score > 70 else 'Orta' if consistency_score > 40 else 'Düşük'
        }
    
    def calculate_comprehensive_score(self, all_metrics: Dict) -> Dict:
        """Kapsamlı skor hesapla"""
        
        score_components = {
            'technical_skills': 0,  # Dil çeşitliliği, commit kalitesi
            'collaboration': 0,  # Ekip çalışması, PR reviews
            'communication': 0,  # README, issue kalitesi
            'discipline': 0,  # Commit düzeni, süreklilik
            'problem_solving': 0,  # Issue çözme, hata yönetimi
            'community_impact': 0,  # Yıldız, fork, dış katkılar
        }
        
        # Teknik beceriler (0-20)
        lang_diversity = min(len(all_metrics.get('languages', {})) * 3, 15)
        commit_quality = all_metrics.get('commit_analysis', {}).get('conventional_percentage', 0) / 5
        score_components['technical_skills'] = lang_diversity + commit_quality
        
        # İşbirliği (0-15)
        collab_metrics = all_metrics.get('collaboration', {})
        contributor_score = min(collab_metrics.get('contributors_count', 0) * 2, 8)
        review_score = collab_metrics.get('code_review', {}).get('review_rate', 0) / 15
        score_components['collaboration'] = contributor_score + review_score
        
        # İletişim (0-20)
        readme_score = all_metrics.get('readme_analysis', {}).get('quality_score', 0) / 5
        issue_comm = all_metrics.get('issue_communication', {})
        comm_score = (issue_comm.get('professional_title_rate', 0) + issue_comm.get('description_rate', 0)) / 20
        score_components['communication'] = readme_score + comm_score
        
        # Disiplin (0-15)
        discipline = all_metrics.get('commit_discipline', {})
        score_components['discipline'] = discipline.get('consistency_score', 0) / 100 * 15
        
        # Problem çözme (0-15)
        problem_solving = all_metrics.get('problem_solving', {})
        score_components['problem_solving'] = problem_solving.get('resolution_rate', 0) / 100 * 15
        
        # Topluluk etkisi (0-15)
        impact_score = min(all_metrics.get('stars', 0) / 50, 7)
        community_score = all_metrics.get('open_source', {}).get('community_engagement_score', 0) / 100 * 8
        score_components['community_impact'] = impact_score + community_score
        
        total_score = sum(score_components.values())
        
        return {
            'total_score': round(total_score, 1),
            'max_score': 100,
            'components': score_components,
            'rating': self._get_comprehensive_rating(total_score),
            'level': self._get_developer_level(total_score)
        }
    
    def _get_comprehensive_rating(self, score: float) -> str:
        """Kapsamlı değerlendirme"""
        if score >= 85:
            return "🏆 Olağanüstü"
        elif score >= 70:
            return "⭐ Mükemmel"
        elif score >= 55:
            return "💎 Çok İyi"
        elif score >= 40:
            return "👍 İyi"
        elif score >= 25:
            return "📈 Gelişmekte"
        else:
            return "🌱 Başlangıç"
    
    def _get_developer_level(self, score: float) -> str:
        """Geliştirici seviyesi"""
        if score >= 80:
            return "Senior/Lead Developer"
        elif score >= 60:
            return "Mid-Level Developer"
        elif score >= 35:
            return "Junior Developer"
        else:
            return "Entry-Level Developer"
    
    def analyze_repo_comprehensive(self, owner: str, repo: str) -> Optional[Dict]:
        """Kapsamlı repo analizi"""
        print(f"\n🚀 {owner}/{repo} detaylı analiz başlıyor...\n")
        
        # Temel bilgiler
        repo_data = self.get_repo_details(owner, repo)
        if not repo_data:
            return None
        
        print(f"✅ Repo: {repo_data.get('full_name')}")
        
        # Tüm metrikleri topla
        all_metrics = {
            'owner': owner,
            'repo': repo,
            'full_name': repo_data.get('full_name'),
            'description': repo_data.get('description', 'No description'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'size': repo_data.get('size', 0),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'primary_language': repo_data.get('language'),
            'topics': repo_data.get('topics', []),
            'license': repo_data['license']['name'] if repo_data.get('license') else 'No License',
            'html_url': repo_data.get('html_url'),
        }
        
        # 1. Diller (Temel Beceriler)
        languages = self.get_repo_languages(owner, repo)
        total_bytes = sum(languages.values())
        all_metrics['languages'] = languages
        all_metrics['language_percentages'] = {
            lang: (bytes_count / total_bytes * 100)
            for lang, bytes_count in languages.items()
        } if total_bytes > 0 else {}
        
        # 2. Commit Aktivitesi (Disiplin)
        commit_activity = self.get_commit_activity(owner, repo)
        all_metrics['commit_discipline'] = self.analyze_commit_activity_discipline(commit_activity)
        
        # 3. İşbirliği Metrikleri
        contributors = self.get_contributors(owner, repo)
        all_metrics['collaboration'] = {
            'contributors_count': len(contributors),
            'top_contributors': contributors[:5]
        }
        
        # 4. Commit Mesajları (Kod Kalitesi)
        commits = self.get_commits(owner, repo, max_commits=50)
        all_metrics['commit_analysis'] = self.analyze_commit_messages(commits)
        
        # 5. README (Dokümantasyon)
        readme = self.get_readme(owner, repo)
        all_metrics['readme_analysis'] = self.analyze_readme_quality(readme)
        
        # 6. Issue İletişimi
        issues = self.get_issues(owner, repo, state="all", max_issues=50)
        all_metrics['issue_communication'] = self.analyze_issue_communication(issues, owner, repo)
        
        # 7. Problem Çözme
        all_metrics['problem_solving'] = self.analyze_problem_solving(issues)
        
        # 8. Code Review
        prs = self.get_pull_requests(owner, repo, state="all", max_prs=20)
        all_metrics['collaboration']['code_review'] = self.analyze_code_review_quality(prs, owner, repo)
        
        # 9. Açık Kaynak Katkıları
        events = self.get_user_events(owner, max_events=100)
        all_metrics['open_source'] = self.analyze_open_source_contributions(events, owner)
        
        # 10. Kapsamlı Skor
        all_metrics['comprehensive_score'] = self.calculate_comprehensive_score(all_metrics)
        
        print(f"\n✅ Tüm metrikler toplandı ve analiz edildi\n")
        
        return all_metrics
    
    def _llm_score_metric(self, metric_name: str, data: Dict, criteria: str) -> float:
        """LLM kullanarak metrik skorlama - Geliştirilmiş versiyon"""
        if self.llm is None:
            return 0.0
        
        try:
            prompt = f"""
            Sen bir yazılım geliştirme uzmanısın. Aşağıdaki verilere dayanarak {metric_name} için 0-100 arası puan ver.

            Değerlendirme Kriterleri: {criteria}

            Veri: {json.dumps(data, indent=2, ensure_ascii=False)}

            ÇOK ÖNEMLİ: SADECE SAYISAL PUANI DÖNDÜR, BAŞKA HİÇBİR ŞEY YAZMA!
            Örnek çıktılar: 85 veya 72.5 veya 90

            Puan:
            """
            
            response = self.llm.invoke(prompt)
            print(f"🔍 LLM ham yanıtı ({metric_name}): {repr(response)}")
            
            # Sayısal değeri çıkarmak için regex kullan
            import re
            numbers = re.findall(r'\b\d{1,3}(?:\.\d+)?\b', response)
            
            if numbers:
                score = float(numbers[0])
                clamped_score = max(0, min(100, score))  # 0-100 arası sınırla
                print(f"✅ {metric_name} LLM skoru: {clamped_score}")
                return clamped_score
            else:
                print(f"⚠️ {metric_name}: LLM'den sayısal puan alınamadı, fallback kullanılıyor")
                return self._calculate_fallback_score(metric_name, data)
        except Exception as e:
            print(f"⚠️ LLM skorlama hatası ({metric_name}): {e}")
            return 0.0

    def _llm_comprehensive_score(self, all_metrics: Dict) -> Dict:
        """LLM ile kapsamlı skor hesaplama"""
        if self.llm is None:
            return self.calculate_comprehensive_score(all_metrics)
        
        try:
            prompt = f"""
            Sen deneyimli bir yazılım geliştirme mentorusun. Aşağıdaki GitHub repo metriklerini değerlendirerek 
            geliştiricinin genel yetenek seviyesini 0-100 arasında puanla.

            METRİKLER:
            {json.dumps(all_metrics, indent=2, ensure_ascii=False)}

            Aşağıdaki bileşenleri dikkate alarak puan ver:
            1. Teknik Beceriler (20 puan): Programlama dili çeşitliliği, kod kalitesi
            2. İşbirliği (15 puan): Ekip çalışması, code review katılımı
            3. İletişim (20 puan): README kalitesi, issue iletişimi, dokümantasyon
            4. Disiplin (15 puan): Commit düzeni, süreklilik, düzenli çalışma
            5. Problem Çözme (15 puan): Issue çözme yeteneği, hata yönetimi
            6. Topluluk Etkisi (15 puan): Açık kaynak katkıları, topluluk etkileşimi

            CEVAP FORMATI (JSON):
            {{
                "total_score": 85,
                "technical_skills": 18,
                "collaboration": 12,
                "communication": 17,
                "discipline": 14,
                "problem_solving": 13,
                "community_impact": 11,
                "reasoning": "Kısa açıklama buraya"
            }}
            """
            
            response = self.llm.invoke(prompt)
            
            # JSON çıktıyı parse et
            try:
                score_data = json.loads(response.strip())
            except:
                # Eğer JSON parse edilemezse, fallback kullan
                return self.calculate_comprehensive_score(all_metrics)
            
            # Puanları kontrol et
            total = score_data.get("total_score", 0)
            components = {
                'technical_skills': score_data.get("technical_skills", 0),
                'collaboration': score_data.get("collaboration", 0),
                'communication': score_data.get("communication", 0),
                'discipline': score_data.get("discipline", 0),
                'problem_solving': score_data.get("problem_solving", 0),
                'community_impact': score_data.get("community_impact", 0),
            }
            
            return {
                'total_score': round(total, 1),
                'max_score': 100,
                'components': components,
                'rating': self._get_comprehensive_rating(total),
                'level': self._get_developer_level(total),
                'reasoning': score_data.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"⚠️ LLM kapsamlı skorlama hatası: {e}")
            return self.calculate_comprehensive_score(all_metrics)
    
    def analyze_readme_quality_with_llm(self, readme: str) -> Dict:
        """LLM ile README kalitesini analiz et"""
        if not readme:
            return {'has_readme': False, 'quality_score': 0}
        
        print("📚 LLM ile README kalitesi analiz ediliyor...")
        
        if self.llm is None:
            return self.analyze_readme_quality(readme)
        
        try:
            prompt = f"""
            Aşağıdaki README dosyasının kalitesini 0-100 arasında puanla. Değerlendirme kriterleri:
            - Açık ve anlaşılır başlık
            - Proje açıklaması
            - Kurulum talimatları
            - Kullanım örnekleri
            - Katkıda bulunma rehberi
            - Lisans bilgisi
            - Formatlama ve düzen
            - Kod blokları ve örnekler
            - Görsel öğeler (badge, diagram)

            README İçeriği:
            {readme[:3000]}  # İlk 3000 karakter

            Sadece sayısal puanı döndür (açıklama yapma). Örnek: 75
            """
            
            score = self._llm_score_metric("README kalitesi", {"content_preview": readme[:500]}, prompt)
            
            return {
                'has_readme': True,
                'length': len(readme),
                'quality_score': score,
                'llm_scored': True
            }
            
        except Exception as e:
            print(f"⚠️ LLM README analiz hatası: {e}")
            return self.analyze_readme_quality(readme)
    
    def analyze_commit_quality_with_llm(self, commits: List[Dict]) -> Dict:
        """LLM ile commit kalitesini analiz et"""
        print("📝 LLM ile commit mesajları analiz ediliyor...")
        
        if self.llm is None or not commits:
            return self.analyze_commit_messages(commits)
        
        try:
            # Commit mesajlarını örnekle
            sample_commits = commits[:10]  # İlk 10 commit
            commit_messages = [commit['commit']['message'].split('\n')[0] for commit in sample_commits if commit.get('commit')]
            
            prompt = f"""
            Aşağıdaki commit mesajlarının kalitesini 0-100 arasında puanla. Değerlendirme kriterleri:
            - Conventional commits standardına uygunluk
            - Açıklayıcı ve anlaşılır olma
            - Değişikliğin kapsamını yansıtma
            - Profesyonel dil kullanımı
            - Tutarlılık

            Commit Mesajları:
            {json.dumps(commit_messages, indent=2, ensure_ascii=False)}

            Sadece sayısal puanı döndür (açıklama yapma). Örnek: 80
            """
            
            score = self._llm_score_metric("Commit kalitesi", {"messages": commit_messages}, prompt)
            
            return {
                'total_commits': len(commits),
                'sampled_commits': len(commit_messages),
                'quality_score': score,
                'llm_scored': True
            }
            
        except Exception as e:
            print(f"⚠️ LLM commit analiz hatası: {e}")
            return self.analyze_commit_messages(commits)
    
    def analyze_code_review_with_llm(self, prs: List[Dict], owner: str, repo: str) -> Dict:
        """LLM ile code review kalitesini analiz et"""
        print("🔍 LLM ile code review kalitesi analiz ediliyor...")
        
        if self.llm is None or not prs:
            return self.analyze_code_review_quality(prs, owner, repo)
        
        try:
            # PR yorumlarını topla
            review_data = []
            for pr in prs[:5]:  # İlk 5 PR
                pr_number = pr['number']
                comments = self.get_pr_comments(owner, repo, pr_number)
                
                for comment in comments[:3]:  # Her PR'den ilk 3 yorum
                    review_data.append({
                        'pr_title': pr.get('title', ''),
                        'comment_body': comment.get('body', '')[:200],  # İlk 200 karakter
                        'comment_length': len(comment.get('body', ''))
                    })
                
                time.sleep(0.3)  # Rate limit
            
            if not review_data:
                return self.analyze_code_review_quality(prs, owner, repo)
            
            prompt = f"""
            Aşağıdaki code review yorumlarının kalitesini 0-100 arasında puanla. Değerlendirme kriterleri:
            - Yapıcı geri bildirim
            - Teknik derinlik
            - Açıklayıcı olma
            - Profesyonel dil
            - İyileştirme önerileri

            Review Verileri:
            {json.dumps(review_data, indent=2, ensure_ascii=False)}

            Sadece sayısal puanı döndür (açıklama yapma). Örnek: 70
            """
            
            score = self._llm_score_metric("Code review kalitesi", {"reviews": review_data}, prompt)
            
            return {
                'total_prs': len(prs),
                'reviewed_samples': len(review_data),
                'quality_score': score,
                'llm_scored': True
            }
            
        except Exception as e:
            print(f"⚠️ LLM code review analiz hatası: {e}")
            return self.analyze_code_review_quality(prs, owner, repo)

    # Mevcut metodları güncelle - LLM entegrasyonu için
    def analyze_repo_comprehensive(self, owner: str, repo: str, use_llm_scoring: bool = True) -> Optional[Dict]:
        """Kapsamlı repo analizi (LLM skorlama seçeneği ile)"""
        print(f"\n🚀 {owner}/{repo} detaylı analiz başlıyor...\n")
        
        # Temel bilgiler
        repo_data = self.get_repo_details(owner, repo)
        if not repo_data:
            return None
        
        print(f"✅ Repo: {repo_data.get('full_name')}")
        
        # Tüm metrikleri topla
        all_metrics = {
            'owner': owner,
            'repo': repo,
            'full_name': repo_data.get('full_name'),
            'description': repo_data.get('description', 'No description'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'size': repo_data.get('size', 0),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'primary_language': repo_data.get('language'),
            'topics': repo_data.get('topics', []),
            'license': repo_data['license']['name'] if repo_data.get('license') else 'No License',
            'html_url': repo_data.get('html_url'),
        }
        
        # 1. Diller (Temel Beceriler)
        languages = self.get_repo_languages(owner, repo)
        total_bytes = sum(languages.values())
        all_metrics['languages'] = languages
        all_metrics['language_percentages'] = {
            lang: (bytes_count / total_bytes * 100)
            for lang, bytes_count in languages.items()
        } if total_bytes > 0 else {}
        
        # 2. Commit Aktivitesi (Disiplin)
        commit_activity = self.get_commit_activity(owner, repo)
        all_metrics['commit_discipline'] = self.analyze_commit_activity_discipline(commit_activity)
        
        # 3. İşbirliği Metrikleri
        contributors = self.get_contributors(owner, repo)
        all_metrics['collaboration'] = {
            'contributors_count': len(contributors),
            'top_contributors': contributors[:5]
        }
        
        # 4. Commit Mesajları (Kod Kalitesi) - LLM veya normal
        commits = self.get_commits(owner, repo, max_commits=50)
        if use_llm_scoring and self.llm:
            all_metrics['commit_analysis'] = self.analyze_commit_quality_with_llm(commits)
        else:
            all_metrics['commit_analysis'] = self.analyze_commit_messages(commits)
        
        # 5. README (Dokümantasyon) - LLM veya normal
        readme = self.get_readme(owner, repo)
        if use_llm_scoring and self.llm:
            all_metrics['readme_analysis'] = self.analyze_readme_quality_with_llm(readme)
        else:
            all_metrics['readme_analysis'] = self.analyze_readme_quality(readme)
        
        # 6. Issue İletişimi
        issues = self.get_issues(owner, repo, state="all", max_issues=50)
        all_metrics['issue_communication'] = self.analyze_issue_communication(issues, owner, repo)
        
        # 7. Problem Çözme
        all_metrics['problem_solving'] = self.analyze_problem_solving(issues)
        
        # 8. Code Review - LLM veya normal
        prs = self.get_pull_requests(owner, repo, state="all", max_prs=20)
        if use_llm_scoring and self.llm:
            all_metrics['collaboration']['code_review'] = self.analyze_code_review_with_llm(prs, owner, repo)
        else:
            all_metrics['collaboration']['code_review'] = self.analyze_code_review_quality(prs, owner, repo)
        
        # 9. Açık Kaynak Katkıları
        events = self.get_user_events(owner, max_events=100)
        all_metrics['open_source'] = self.analyze_open_source_contributions(events, owner)
        
        # 10. Kapsamlı Skor - LLM veya normal
        if use_llm_scoring and self.llm:
            all_metrics['comprehensive_score'] = self._llm_comprehensive_score(all_metrics)
        else:
            all_metrics['comprehensive_score'] = self.calculate_comprehensive_score(all_metrics)
        
        print(f"\n✅ Tüm metrikler toplandı ve analiz edildi\n")
        
        return all_metrics

    # Diğer mevcut metodlar aynı kalacak...
    def _make_request(self, url: str, params: Optional[Dict] = None, max_retries: int = 3):
        """Retry mantığı ile güvenli istek"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 403:
                    remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    if remaining == '0':
                        reset_time = response.headers.get('X-RateLimit-Reset', 'Bilinmiyor')
                        print(f"⚠️ Rate limit aşıldı. Reset: {reset_time}")
                    return None
                
                if response.status_code == 200:
                    return response
                    
                print(f"⚠️ HTTP {response.status_code}, deneme {attempt + 1}/{max_retries}")
                
            except Exception as e:
                print(f"❌ İstek hatası: {str(e)[:80]}")
            
            if attempt < max_retries - 1:
                time.sleep((attempt + 1) * 2)
        
        return None

    # Diğer mevcut metodlar (get_repo_details, get_repo_languages, vb.) aynı kalacak...
    # Sadece yukarıdaki güncellenmiş metodları ekledim.

    def _get_comprehensive_rating(self, score: float) -> str:
        """Kapsamlı değerlendirme"""
        if score >= 85:
            return "🏆 Olağanüstü"
        elif score >= 70:
            return "⭐ Mükemmel"
        elif score >= 55:
            return "💎 Çok İyi"
        elif score >= 40:
            return "👍 İyi"
        elif score >= 25:
            return "📈 Gelişmekte"
        else:
            return "🌱 Başlangıç"
    
    def _get_developer_level(self, score: float) -> str:
        """Geliştirici seviyesi"""
        if score >= 80:
            return "Senior/Lead Developer"
        elif score >= 60:
            return "Mid-Level Developer"
        elif score >= 35:
            return "Junior Developer"
        else:
            return "Entry-Level Developer"
    
    def generate_ai_deep_analysis(self, metrics: Dict) -> str:
        """Derinlemesine AI analizi (LLM destekli rapor oluşturur)"""
        if self.llm is None:
            return "⚠️ AI analizi yapılamıyor - Ollama bağlantısı yok"
        
        # Metrikleri özet metin haline getir
        repo_name = metrics.get("full_name", "Bilinmiyor")
        score_info = metrics.get("comprehensive_score", {})
        readme = metrics.get("readme_analysis", {})
        issue_comm = metrics.get("issue_communication", {})
        discipline = metrics.get("commit_discipline", {})
        problem_solving = metrics.get("problem_solving", {})
        open_source = metrics.get("open_source", {})
        
        # Prompt oluştur
        prompt_template = ChatPromptTemplate.from_template("""
        Sen deneyimli bir yazılım mühendisi mentorusun.
        Aşağıda bir GitHub projesinin analitik metrikleri var.
        Bu verilerden yola çıkarak geliştiricinin teknik becerilerini, iletişim tarzını,
        profesyonellik düzeyini ve açık kaynak topluluğundaki etkisini değerlendir.

        Format:
        - **Genel Değerlendirme**
        - **Güçlü Yönler**
        - **Geliştirilebilir Alanlar**
        - **Profesyonel Gelişim Önerileri**

        Repo: {repo}
        Toplam Skor: {score} / 100 ({rating}, Seviye: {level})

        📊 Öne çıkan metrikler:
        - README Kalitesi: {readme_score:.1f}%
        - Commit Disiplini: {consistency:.1f}% ({work_rhythm})
        - Issue İletişimi: {issue_desc_rate:.1f}% açıklamalı, {issue_prof_rate:.1f}% profesyonel başlık
        - Problem Çözme: {resolution_rate:.1f}% başarı, ortalama çözüm süresi {resolution_days:.1f} gün
        - Açık Kaynak Katkısı: {ext_repos} farklı repo, {community_score:.1f} topluluk skoru

        Analizini detaylı, içgörü dolu ve doğal bir Türkçe ile yaz.
        Gereksiz teknik jargondan kaçın ama profesyonel bir ton kullan.
                """)
        
        prompt = prompt_template.format(
            repo=repo_name,
            score=score_info.get("total_score", 0),
            rating=score_info.get("rating", "Bilinmiyor"),
            level=score_info.get("level", "Bilinmiyor"),
            readme_score=readme.get("quality_score", 0),
            consistency=discipline.get("consistency_score", 0),
            work_rhythm=discipline.get("work_rhythm", "Bilinmiyor"),
            issue_desc_rate=issue_comm.get("description_rate", 0),
            issue_prof_rate=issue_comm.get("professional_title_rate", 0),
            resolution_rate=problem_solving.get("resolution_rate", 0),
            resolution_days=problem_solving.get("avg_resolution_days", 0),
            ext_repos=open_source.get("unique_external_repos", 0),
            community_score=open_source.get("community_engagement_score", 0),
        )
        
        # LLM çağrısı
        print("🤖 AI analizi başlatılıyor...")
        try:
            analysis_text = self.llm.invoke(prompt)
            return analysis_text.strip()
        except Exception as e:
            return f"⚠️ AI analizi sırasında hata: {e}"
    def print_analysis_report(self,metrics: dict, ai_analysis: str):
        """Analiz sonuçlarını konsola yazdırır (PDF yerine terminalde gösterir)"""

        repo_name = metrics.get("full_name", "Bilinmiyor")
        score_info = metrics.get("comprehensive_score", {})
        readme = metrics.get("readme_analysis", {})
        discipline = metrics.get("commit_discipline", {})
        problem_solving = metrics.get("problem_solving", {})
        open_source = metrics.get("open_source", {})
        collaboration = metrics.get("collaboration", {})
        langs = metrics.get("language_percentages", {})

        print("=" * 70)
        print(f"📄 GITHUB PROJE ANALİZ RAPORU")
        print("=" * 70)
        print(f"📁 Repo Adı         : {repo_name}")
        print(f"⭐ Toplam Skor      : {score_info.get('total_score', 0)} / 100 ({score_info.get('rating', '-')})")
        print(f"💻 Seviye           : {score_info.get('level', '-')}")
        print(f"📂 Birincil Dil     : {metrics.get('primary_language', 'Bilinmiyor')}")
        print(f"📊 Katkıda Bulunanlar : {collaboration.get('contributors_count', 0)}")
        print(f"📅 Son Güncelleme   : {metrics.get('updated_at', 'Bilinmiyor')}")
        print(f"🔗 Repo Linki       : {metrics.get('html_url', '')}")
        print()

        print("📚 Kullanılan Diller")
        print("-" * 70)
        if langs:
            for lang, pct in langs.items():
                print(f"  - {lang}: {pct:.1f}%")
        else:
            print("  Dil bilgisi bulunamadı.")
        print()

        print("📈 Önemli Metrikler")
        print("-" * 70)
        print(f"• README Kalitesi        : {readme.get('quality_score', 0):.1f}%")
        print(f"• Commit Disiplini       : {discipline.get('consistency_score', 0):.1f}% ({discipline.get('work_rhythm', '-')})")
        print(f"• Problem Çözme Başarısı : {problem_solving.get('resolution_rate', 0):.1f}%")
        print(f"• Ortalama Çözüm Süresi  : {problem_solving.get('avg_resolution_days', 0):.1f} gün")
        print(f"• Açık Kaynak Katkısı    : {open_source.get('unique_external_repos', 0)} repo")
        print(f"• Topluluk Skoru         : {open_source.get('community_engagement_score', 0):.1f}")
        print()

        print("🤖 AI Değerlendirmesi")
        print("-" * 70)
        ai_paragraphs = ai_analysis.split("\n")
        for p in ai_paragraphs:
            if p.strip():
                print(f"  {p.strip()}")
        print("=" * 70)

    def export_analysis_report(self, metrics: Dict, ai_analysis: str, output_path: str = None) -> str:
        """Analiz sonuçlarını profesyonel PDF raporu olarak dışa aktarır"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors

        repo_name = metrics.get("full_name", "Bilinmiyor")
        score_info = metrics.get("comprehensive_score", {})
        readme = metrics.get("readme_analysis", {})
        discipline = metrics.get("commit_discipline", {})
        problem_solving = metrics.get("problem_solving", {})
        open_source = metrics.get("open_source", {})
        collaboration = metrics.get("collaboration", {})
        langs = metrics.get("language_percentages", {})

        if output_path is None:
            safe_name = repo_name.replace("/", "_")
            output_path = f"./{safe_name}_analysis_report2.pdf"

        # PDF oluştur
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Özel stiller
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            alignment=1,
            fontSize=18,
            spaceAfter=12,
            textColor=colors.HexColor("#2E4053"),
        )

        section_style = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#154360"),
            spaceAfter=8,
        )

        body_style = ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
        )

        # Başlık
        story.append(Paragraph(f"GitHub Proje Analiz Raporu - {repo_name}", title_style))
        story.append(Spacer(1, 12))

        # Genel Bilgiler Tablosu
        table_data = [
            ["⭐ Toplam Skor", f"{score_info.get('total_score', 0)} / 100 ({score_info.get('rating', '')})"],
            ["💻 Seviye", score_info.get("level", "")],
            ["📂 Birincil Dil", metrics.get("primary_language", "Bilinmiyor")],
            ["📊 Katkıda Bulunanlar", str(collaboration.get("contributors_count", 0))],
            ["📅 Son Güncelleme", metrics.get("updated_at", "Bilinmiyor")],
            ["🔗 Repo Linki", f"<a href='{metrics.get('html_url', '')}'>{metrics.get('html_url', '')}</a>"],
        ]

        t = Table(table_data, colWidths=[150, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#D6EAF8")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
            ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.gray),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ]))
        story.append(t)
        story.append(Spacer(1, 14))

        # Dil Kullanımı
        story.append(Paragraph("📚 Kullanılan Diller", section_style))
        if langs:
            lang_text = ", ".join([f"{lang}: {pct:.1f}%" for lang, pct in langs.items()])
        else:
            lang_text = "Dil bilgisi bulunamadı."
        story.append(Paragraph(lang_text, body_style))
        story.append(Spacer(1, 12))

        # Önemli metrikler özeti
        story.append(Paragraph("📈 Önemli Metrikler", section_style))
        story.append(Paragraph(
            f"• README Kalitesi: {readme.get('quality_score', 0):.1f}%<br/>"
            f"• Commit Disiplini: {discipline.get('consistency_score', 0):.1f}% ({discipline.get('work_rhythm', '-')})<br/>"
            f"• Problem Çözme: {problem_solving.get('resolution_rate', 0):.1f}% başarı, "
            f"ortalama çözüm süresi {problem_solving.get('avg_resolution_days', 0):.1f} gün<br/>"
            f"• Açık Kaynak Katkısı: {open_source.get('unique_external_repos', 0)} repo, "
            f"Topluluk skoru {open_source.get('community_engagement_score', 0):.1f}",
            body_style
        ))
        story.append(Spacer(1, 14))

        # AI Analizi
        story.append(Paragraph("🤖 AI Değerlendirmesi", section_style))
        ai_paragraphs = ai_analysis.split("\n")
        for p in ai_paragraphs:
            if p.strip():
                story.append(Paragraph(p.strip(), body_style))
                story.append(Spacer(1, 6))

        # PDF'i kaydet
        doc.build(story)
        print(f"📄 PDF raporu oluşturuldu: {output_path}")
        return output_path
    def analyze_requirements_modernization(self, owner: str, repo: str) -> Dict:
        """
        Analyze the requirements.txt file of a GitHub repository and suggest
        more modern or efficient Python libraries/frameworks.

        Returns a structured English report with both static and AI-driven modernization suggestions.
        """
        logging.info("🧩 Starting requirements.txt modernization analysis...")

        # 1. Fetch requirements.txt
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/requirements.txt"
        response = self._make_request(url)

        if not response or response.status_code != 200:
            logging.warning("⚠️ requirements.txt not found or inaccessible.")
            return {"found": False, "recommendations": [], "ai_analysis": "requirements.txt not found."}

        try:
            content = response.json().get("content", "")
            decoded = base64.b64decode(content).decode("utf-8")
        except Exception as e:
            logging.error(f"❌ Failed to decode requirements.txt: {e}")
            return {"found": False, "recommendations": [], "ai_analysis": "Decoding error."}

        # 2. Extract package names
        pattern = re.compile(r"^([a-zA-Z0-9_\-]+)", re.MULTILINE)
        packages = sorted(set(pattern.findall(decoded)))
        logging.info(f"📦 Detected libraries: {', '.join(packages) if packages else 'None'}")

        if not packages:
            return {"found": True, "packages": [], "recommendations": [], "ai_analysis": "No packages detected."}

        # 3. Static modernization map
        modernization_map = {
            "tensorflow": "PyTorch or JAX (modern, flexible deep learning alternatives)",
            "flask": "FastAPI (async-ready, modern Python web framework)",
            "django": "Django REST Framework or FastAPI (for modern REST APIs)",
            "numpy": "Consider JAX for GPU-accelerated numerical computing",
            "pandas": "Polars (faster DataFrame library with lazy evaluation)",
            "matplotlib": "Plotly or Altair (interactive and modern plotting)",
            "requests": "httpx (async HTTP client with better performance)",
            "sqlalchemy": "SQLModel (modern ORM combining SQLAlchemy + Pydantic)",
            "beautifulsoup4": "Selectolax (faster HTML parsing library)",
            "keras": "PyTorch Lightning or HuggingFace Transformers",
            "scikit-learn": "Consider LightGBM or AutoML frameworks for scalability",
        }

        # 4. Static recommendations
        recommendations = []
        for pkg in packages:
            suggestion = None
            for old_lib, modern_alt in modernization_map.items():
                if old_lib.lower() in pkg.lower():
                    suggestion = modern_alt
                    break
            recommendations.append({
                "package": pkg,
                "suggestion": suggestion or "No clear modern alternative found. May already be up-to-date."
            })

        # 5. Optional: AI-powered modernization analysis
        if self.llm:
            logging.info("🤖 Running deep modernization analysis via LLM...")

            system_prompt = (
                "You are a senior Python software architect specializing in modernizing legacy codebases. "
                "Your task is to analyze dependencies listed in a requirements.txt file and recommend "
                "more modern, efficient, or actively maintained alternatives. "
                "Provide structured, concise, and insightful suggestions."
            )

            pkg_list_str = "\n".join([f"- {r['package']}: {r['suggestion']}" for r in recommendations])
            user_prompt = f"""
    Here is the requirements.txt content extracted from a GitHub repository:

    {pkg_list_str}

    For each listed package:
    1. Suggest a modern replacement (if relevant)
    2. Explain why it’s an improvement (e.g., performance, async support, active maintenance)
    3. End with a short modernization summary (2–3 sentences)
    """

            try:
                ai_prompt = f"{system_prompt}\n\n{user_prompt}"
                ai_text = self.llm.invoke(ai_prompt)
            except Exception as e:
                logging.error(f"⚠️ LLM analysis failed: {e}")
                ai_text = f"⚠️ LLM analysis failed: {e}"
        else:
            ai_text = "⚠️ AI analysis unavailable (Ollama connection missing)."

        return {
            
            "packages": packages,
            "recommendations": recommendations,
            "ai_analysis": ai_text.strip() if isinstance(ai_text, str) else ai_text,
        }
if __name__=="__main__":
    analyzer = GitHubRepoAnalyzer(github_token="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")
    metrics = analyzer.analyze_repo_comprehensive("BarrileteChapin","FCC-MCP-Course",use_llm_scoring=False)
    ai_report = analyzer.generate_ai_deep_analysis(metrics)
    repo=analyzer.analyze_requirements_modernization("BarrileteChapin","FCC-MCP-Course")
    #pdf_path = analyzer.export_analysis_report(metrics, ai_report)

    print(type(str(ai_report)))
    
    print("\n📋 İkinci:")
    print(type(str(repo["ai_analysis"])))