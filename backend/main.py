from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from routers import github_router,cv_router,chat_routers


class User(BaseModel):
    name: str
    age: int



app = FastAPI(
    title="Your Assistant/",
    description="API to interact with the Your Asisstant backend services.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""app.include_router(story.router, prefix=settings.API_PREFIX)
app.include_router(jo b.router, prefix=settings.API_PREFIX)
"""

app.include_router(github_router.router)
app.include_router(cv_router.router)
app.include_router(chat_routers.router)
"""@app.post("/users/")
def create_user(user: User):
    return {"user": user}"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)