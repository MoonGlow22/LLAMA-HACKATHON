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
from  backend.githubreal import GLOBAL_USER
load_dotenv()

router = APIRouter(
    prefix="",
    tags=[""]
)

class DashboardResponse(BaseModel):
    name: str
    course_1: str
    course_2: str
    link_1: Optional[str] = None
    link_2: Optional[str] = None
    q1: Optional[str] = None
    q2: Optional[str] = None

@router.get("/userstats", response_model=DashboardResponse)
async def get_user_stats():
    df = pd.read_csv("backend/users.csv")
    username=GLOBAL_USER["username"]
    row=df[df['name'] == username].iloc[0]
    return DashboardResponse(
        name=row['name'],
        course_1=row['course_1'],
        course_2=row['course_2'],
        link_1=row.get('link_1'),
        link_2=row.get('link_2'),
        q1=row.get('q1'),
        q2=row.get('q2')
    )

