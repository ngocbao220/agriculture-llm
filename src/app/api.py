from fastapi import FastAPI
from pydantic import BaseModel
from rag import rag_system
import uvicorn

app = FastAPI(title="Agri-RAG API")

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str
    sources: list

@app.post("/ask", response_model=AnswerResponse)
async def ask_agri(request: QuestionRequest):
    result = rag_system.query(request.question)
    return AnswerResponse(
        answer=result["answer"],
        sources=result["sources"]
    )

if __name__ == "__main__":
    # Chạy trên cổng mặc định 9000
    uvicorn.run(app, host="0.0.0.0", port=9000)