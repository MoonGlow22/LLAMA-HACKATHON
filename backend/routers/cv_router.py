from fastapi import APIRouter
from pydantic import BaseModel
from fastapi import UploadFile, File
"""from core.model import StoryGenerator"""
from cv_mechanism.converter import full_stream
router = APIRouter(
    prefix="/cv",
    tags=["cv"]
)



class RequestLink(BaseModel):
    link: str




class QueryResponse2(BaseModel):
    short_summary:str
    key_strength:str
    weakness:str
    jobs:str
    suggests:str
    ats:str
    interview:str
    questions:str
    cv_score:str


@router.post("/cvextract")
async def cv_extract(file: UploadFile = File(...)):
    # PDF'i kaydet
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Model analizini çalıştır
    out = full_stream(temp_path)
    (short_summary, key_strength, weakness, jobs, suggests, ats, interview, questions, cv_score) = out.values()
    return QueryResponse2(
        short_summary=short_summary,
        key_strength=key_strength,
        weakness=weakness,
        jobs=jobs,
        suggests=suggests,
        ats=ats,
        interview=interview,
        questions=questions,
        cv_score=cv_score
    )