from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.services.analysis_service import run_analysis
from app.core.database import get_db

router = APIRouter()


@router.get("/projects/{project_id}/analysis")
def get_analysis(project_id: int):
    with get_db() as conn:
        row = conn.execute(
            text("""SELECT analysis_status, analysis_structure, analysis_features,
                    analysis_improvements, analysis_report
                    FROM projects WHERE id=:id"""),
            {"id": project_id}
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없어요")

    return {
        "analysis_status":  row[0] or "PENDING",
        "structure":        row[1] or "",
        "features":         row[2] or "",
        "improvements":     row[3] or "",
        "report":           row[4] or "",
    }


@router.post("/projects/{project_id}/analyze")
def trigger_analysis(project_id: int):
    with get_db() as conn:
        row = conn.execute(
            text("SELECT status FROM projects WHERE id=:id"),
            {"id": project_id}
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없어요")
    if row[0] != "EMBEDDED":
        raise HTTPException(status_code=400, detail="임베딩이 완료된 프로젝트만 분석할 수 있어요")

    run_analysis(project_id)
    return {"message": "분석이 완료됐어요"}
