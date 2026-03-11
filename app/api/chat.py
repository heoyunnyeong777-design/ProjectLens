import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.services.rag_service import ask_question
from app.core.database import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    project_id: int
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list
    question: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    with get_db() as conn:
        project = conn.execute(
            text("SELECT status FROM projects WHERE id=:id"),
            {"id": request.project_id}
        ).fetchone()

    if not project:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없어요")
    if project[0] != "EMBEDDED":
        raise HTTPException(status_code=400, detail="임베딩이 완료된 프로젝트만 질문할 수 있어요")

    result = ask_question(request.project_id, request.question)

    try:
        with get_db() as conn:
            conn.execute(
                text("INSERT INTO chat_history (project_id, question, answer, sources) "
                     "VALUES (:pid, :q, :a, :s)"),
                {"pid": request.project_id, "q": request.question,
                 "a": result["answer"], "s": json.dumps(result["sources"], ensure_ascii=False)}
            )
            conn.commit()
    except Exception as e:
        print(f"[WARN] 히스토리 저장 실패: {e}")

    return ChatResponse(answer=result["answer"], sources=result["sources"], question=request.question)


@router.get("/chat/history/{project_id}")
def get_chat_history(project_id: int):
    with get_db() as conn:
        rows = conn.execute(
            text("SELECT question, answer, created_at FROM chat_history "
                 "WHERE project_id=:pid ORDER BY created_at DESC LIMIT 20"),
            {"pid": project_id}
        ).fetchall()

    return [{"question": r[0], "answer": r[1], "created_at": str(r[2])} for r in rows]
