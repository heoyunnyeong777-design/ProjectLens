from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.search_service import search_similar_chunks
from app.core.config import OPENAI_API_KEY

# LLM 초기화 (서버 시작 시 한 번만)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

# 프롬프트 템플릿
prompt = ChatPromptTemplate.from_template("""
당신은 코드 분석 전문가입니다.
반드시 한국어로 답변하세요.

아래에 관련 코드 조각이 있으면 참고해서 답변하고, 파일명과 라인 번호를 구체적으로 알려주세요.
코드 조각이 없거나 질문이 코드와 무관하다면, 일반 지식으로 친절하게 답변해주세요.

코드 조각:
{context}

질문: {question}

답변:
""")

# 랭체인 LCEL 파이프라인
# prompt → llm → 문자열 파싱
chain = prompt | llm | StrOutputParser()


def ask_question(project_id: int, question: str) -> dict:
    """
    RAG 기반 질문 답변 함수
    1. 유사한 코드 청크 검색
    2. 랭체인으로 GPT에게 전달
    3. 답변 반환
    """
    # 1. 유사한 청크 검색
    chunks = search_similar_chunks(project_id, question, top_k=5)

    # 2. 컨텍스트 조합 (검색된 청크가 없으면 빈 문자열)
    context = ""
    if chunks:
        for i, chunk in enumerate(chunks, 1):
            context += f"\n[{i}] 파일: {chunk['file_path']}"
            if chunk['line_start']:
                context += f" (라인 {chunk['line_start']}~{chunk['line_end']})"
            context += f"\n{chunk['content']}\n"
    else:
        context = "(관련 코드를 찾지 못했습니다)"

    # 3. 랭체인 파이프라인 실행
    print(f"[RAG] LLM 답변 생성 중...")
    answer = chain.invoke({
        "context": context,
        "question": question
    })
    print(f"[RAG] 답변 생성 완료!")

    # 4. 소스 정보 정리
    sources = [
        {
            "file_path": c["file_path"],
            "line_start": c["line_start"],
            "line_end": c["line_end"],
            "similarity": c["similarity"]
        }
        for c in chunks
    ]

    return {
        "answer": answer,
        "sources": sources
    }
