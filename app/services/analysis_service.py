import traceback
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import text
from app.services.search_service import search_similar_chunks
from app.core.database import get_db
from app.core.config import OPENAI_API_KEY

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)
parser = StrOutputParser()


# ── State ────────────────────────────────────────────

class AnalysisState(TypedDict):
    project_id: int
    structure: str
    features: str
    improvements: str
    report: str


# ── 노드 ─────────────────────────────────────────────

def analyze_structure(state: AnalysisState) -> AnalysisState:
    print("[LangGraph] 노드1: 구조 분석 중...")
    chunks = search_similar_chunks(state["project_id"], "project structure controller service repository package", top_k=5)
    prompt = ChatPromptTemplate.from_template("""
다음 코드를 분석해서 프로젝트의 전체 구조를 한국어로 설명해주세요.
어떤 패키지와 클래스들로 구성되어 있는지, MVC 패턴인지 등을 설명해주세요.
3~5문장으로 간결하게 작성해주세요.

코드:
{context}

프로젝트 구조 분석:
""")
    result = (prompt | llm | parser).invoke({"context": _build_context(chunks)})
    print("[LangGraph] 노드1 완료!")
    return {**state, "structure": result}


def analyze_features(state: AnalysisState) -> AnalysisState:
    print("[LangGraph] 노드2: 핵심 기능 분석 중...")
    chunks = search_similar_chunks(state["project_id"], "main features business logic service method", top_k=5)
    prompt = ChatPromptTemplate.from_template("""
다음 코드와 프로젝트 구조 정보를 바탕으로 핵심 기능들을 한국어로 설명해주세요.
주요 기능이 무엇인지, 어떤 파일에서 처리하는지 설명해주세요.
3~5문장으로 간결하게 작성해주세요.

프로젝트 구조:
{structure}

코드:
{context}

핵심 기능 분석:
""")
    result = (prompt | llm | parser).invoke({"context": _build_context(chunks), "structure": state["structure"]})
    print("[LangGraph] 노드2 완료!")
    return {**state, "features": result}


def analyze_improvements(state: AnalysisState) -> AnalysisState:
    print("[LangGraph] 노드3: 개선점 분석 중...")
    chunks = search_similar_chunks(state["project_id"], "exception handling error validation test", top_k=5)
    prompt = ChatPromptTemplate.from_template("""
다음 코드와 프로젝트 정보를 바탕으로 개선할 수 있는 점들을 한국어로 설명해주세요.
예외처리, 테스트, 성능, 코드 품질 등의 관점에서 분석해주세요.
3~5문장으로 간결하게 작성해주세요.

프로젝트 구조: {structure}
핵심 기능: {features}

코드:
{context}

개선점 분석:
""")
    result = (prompt | llm | parser).invoke({
        "context": _build_context(chunks),
        "structure": state["structure"],
        "features": state["features"]
    })
    print("[LangGraph] 노드3 완료!")
    return {**state, "improvements": result}


def generate_report(state: AnalysisState) -> AnalysisState:
    print("[LangGraph] 노드4: 최종 보고서 생성 중...")
    prompt = ChatPromptTemplate.from_template("""
아래 분석 결과들을 종합해서 프로젝트 분석 보고서를 한국어로 작성해주세요.
제목과 각 섹션을 명확하게 구분해서 작성해주세요.

프로젝트 구조: {structure}
핵심 기능: {features}
개선점: {improvements}

최종 보고서:
""")
    result = (prompt | llm | parser).invoke({
        "structure": state["structure"],
        "features": state["features"],
        "improvements": state["improvements"]
    })
    print("[LangGraph] 노드4 완료!")
    return {**state, "report": result}


# ── 그래프 ───────────────────────────────────────────

def _build_context(chunks: list) -> str:
    return "".join(f"\n[{i}] 파일: {c['file_path']}\n{c['content']}\n" for i, c in enumerate(chunks, 1))


def _build_graph():
    graph = StateGraph(AnalysisState)
    graph.add_node("analyze_structure", analyze_structure)
    graph.add_node("analyze_features", analyze_features)
    graph.add_node("analyze_improvements", analyze_improvements)
    graph.add_node("generate_report", generate_report)
    graph.set_entry_point("analyze_structure")
    graph.add_edge("analyze_structure", "analyze_features")
    graph.add_edge("analyze_features", "analyze_improvements")
    graph.add_edge("analyze_improvements", "generate_report")
    graph.add_edge("generate_report", END)
    return graph.compile()


analysis_graph = _build_graph()


# ── 공개 함수 ─────────────────────────────────────────

def analyze_project(project_id: int) -> dict:
    """LangGraph 워크플로우 실행 후 결과 반환"""
    print(f"[분석] 프로젝트 {project_id} 분석 시작!")
    final_state = analysis_graph.invoke(AnalysisState(
        project_id=project_id, structure="", features="", improvements="", report=""
    ))
    return {k: final_state[k] for k in ("structure", "features", "improvements", "report")}


def run_analysis(project_id: int):
    """분석 실행 후 결과를 DB에 저장"""
    try:
        with get_db() as conn:
            conn.execute(text("UPDATE projects SET analysis_status='ANALYZING' WHERE id=:id"), {"id": project_id})
            conn.commit()

        result = analyze_project(project_id)

        with get_db() as conn:
            conn.execute(
                text("""UPDATE projects SET
                    analysis_status='DONE', analysis_structure=:structure,
                    analysis_features=:features, analysis_improvements=:improvements,
                    analysis_report=:report WHERE id=:id"""),
                {**result, "id": project_id}
            )
            conn.commit()
        print(f"[분석] 저장 완료! project_id={project_id}")

    except Exception:
        print(f"[분석 ERROR] {traceback.format_exc()}")
        with get_db() as conn:
            conn.execute(text("UPDATE projects SET analysis_status='ERROR' WHERE id=:id"), {"id": project_id})
            conn.commit()
