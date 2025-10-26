from fastapi import APIRouter
from pydantic import BaseModel
"""from core.model import StoryGenerator"""
from githubreal import mainagent,minagent2
router = APIRouter(
    prefix="/github",
    tags=["github"]
)



class QueryRequest(BaseModel):
    link: str


class QueryResponse(BaseModel):
    user:str
    stats:str
    languages:str
    popular_repos:str
    profile_score:str
    ai_analysis:str
    learning_path:str
    course_metadata:str


class QueryResponse2(BaseModel):
    ai_report:str
    
    reco:str

@router.post("/request2")
async def ask_question2(request: QueryRequest):
    ai_report, reco = minagent2(request.link)
    
    return QueryResponse2(ai_report=str(ai_report), reco=str(reco["ai_analysis"]))


@router.post("/request")
async def ask_question(request: QueryRequest):
    out = mainagent(request.link)
    
    user=out.get('👤 Kullanıcı Bilgileri', {})
    stats=out.get('📊 İstatistikler', {})
    languages=out.get('💻 En Çok Kullanılan Diller', {})
    popular_repos=out.get('🏆 En Popüler Repolar', {})
    profile_score=out.get('📈 Profil Skoru', {})
    ai_analysis=out.get('🤖 AI Analizi', {})
    learning_path=out.get('📚 Öğrenme Yol Haritası (ChromaDB Retrieval)', {})
    course_metadata=out.get("🔗 Kurs Metadataları (ilk 5'ten seçilenlerin linkleri)", {})
    return QueryResponse(user=str(user), stats=str(stats), languages=str(languages), popular_repos=str(popular_repos), profile_score=str(profile_score), ai_analysis=str(ai_analysis), learning_path=str(learning_path), course_metadata=str(course_metadata))