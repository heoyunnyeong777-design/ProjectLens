import threading
import traceback
from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from app.services.github_service import collect_files
from app.services.chunking_service import chunk_files
from app.services.embedding_service import get_embeddings_batch
from app.services.analysis_service import run_analysis
from app.core.database import get_db

router = APIRouter()


class ProjectRequest(BaseModel):
    github_url: str


class ProjectResponse(BaseModel):
    project_id: int
    name: str
    status: str
    file_count: int
    message: str


def _set_progress(project_id: int, status: str, progress: int, current_file: str = ""):
    with get_db() as conn:
        conn.execute(
            text("UPDATE projects SET status=:s, progress=:p, current_file=:f WHERE id=:id"),
            {"s": status, "p": progress, "f": current_file, "id": project_id}
        )
        conn.commit()


def _background_task(project_id: int, github_url: str):
    try:
        # 1. 수집
        _set_progress(project_id, "COLLECTING", 10, "GitHub 저장소 연결 중...")
        files, _, _ = collect_files(github_url)
        _set_progress(project_id, "COLLECTING", 30, f"{len(files)}개 파일 수집 완료")

        # 2. 청킹
        _set_progress(project_id, "CHUNKING", 45, "코드 청킹 중...")
        chunks = chunk_files(files)
        _set_progress(project_id, "CHUNKING", 55, f"청크 {len(chunks)}개 생성 완료")

        # 3. 임베딩 (배치 처리)
        texts = [c["content"] for c in chunks]
        _set_progress(project_id, "EMBEDDING", 60, f"임베딩 중... (총 {len(texts)}개 청크)")
        all_embeddings = get_embeddings_batch(texts)
        _set_progress(project_id, "EMBEDDING", 90, "임베딩 완료")

        # 4. 저장
        _set_progress(project_id, "SAVING", 92, "벡터 DB 저장 중...")
        with get_db() as conn:
            conn.execute(text("DELETE FROM code_chunks WHERE project_id=:id"), {"id": project_id})
            for chunk, emb in zip(chunks, all_embeddings):
                conn.execute(
                    text("""INSERT INTO code_chunks
                            (project_id, file_path, content, chunk_type, line_start, line_end, embedding)
                            VALUES (:pid, :fp, :c, :ct, :ls, :le, :emb)"""),
                    {"pid": project_id, "fp": chunk["file_path"], "c": chunk["content"],
                     "ct": chunk["chunk_type"], "ls": chunk.get("line_start"),
                     "le": chunk.get("line_end"), "emb": str(emb)}
                )
            conn.execute(
                text("UPDATE projects SET status='EMBEDDED', progress=100, file_count=:fc, current_file=:cf WHERE id=:id"),
                {"fc": len(files), "cf": f"완료! 청크 {len(chunks)}개 저장됨", "id": project_id}
            )
            conn.commit()

        # 5. LangGraph 분석
        run_analysis(project_id)

    except Exception:
        print(f"[BG ERROR] {traceback.format_exc()}")
        _set_progress(project_id, "ERROR", 0, "오류가 발생했어요.")


@router.post("/projects", response_model=ProjectResponse)
def create_project(request: ProjectRequest):
    parts = request.github_url.rstrip("/").split("/")
    repo_name = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]

    with get_db() as conn:
        existing = conn.execute(
            text("SELECT id FROM projects WHERE github_url=:url"),
            {"url": request.github_url}
        ).fetchone()
        if existing:
            conn.execute(text("DELETE FROM code_chunks WHERE project_id=:id"), {"id": existing[0]})
            conn.execute(text("DELETE FROM projects WHERE id=:id"), {"id": existing[0]})
            conn.commit()

    with get_db() as conn:
        project_id = conn.execute(
            text("INSERT INTO projects (name, github_url, description, status, file_count) "
                 "VALUES (:n, :u, '', 'PENDING', 0) RETURNING id"),
            {"n": repo_name, "u": request.github_url}
        ).fetchone()[0]
        conn.commit()

    threading.Thread(target=_background_task, args=(project_id, request.github_url), daemon=True).start()

    return ProjectResponse(project_id=project_id, name=repo_name, status="PENDING",
                           file_count=0, message="분석을 시작했어요!")


@router.get("/projects")
def get_projects():
    with get_db() as conn:
        rows = conn.execute(
            text("SELECT id, name, github_url, status, file_count, created_at, progress, current_file "
                 "FROM projects ORDER BY created_at DESC")
        ).fetchall()
    return [
        {"id": r[0], "name": r[1], "github_url": r[2], "status": r[3],
         "file_count": r[4], "created_at": str(r[5]), "progress": r[6] or 0, "current_file": r[7] or ""}
        for r in rows
    ]
