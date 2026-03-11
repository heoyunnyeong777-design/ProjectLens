import re
from sqlalchemy import text
from langchain_openai import ChatOpenAI
from app.core.database import get_db
from app.core.config import OPENAI_API_KEY
from app.services.embedding_service import get_embedding

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=OPENAI_API_KEY)

SIMILARITY_THRESHOLD = 0.1


def _is_korean(text: str) -> bool:
    return bool(re.search(r'[가-힣]', text))


def _translate_to_english(question: str) -> str:
    if not _is_korean(question):
        return question
    response = llm.invoke(
        f"Translate the following Korean question to English. Output only the translation, nothing else.\n\n{question}"
    )
    translated = response.content.strip()
    print(f"[검색] 번역: '{question}' → '{translated}'")
    return translated


def search_similar_chunks(project_id: int, question: str, top_k: int = 5) -> list:
    # 1. 한국어 번역
    translated = _translate_to_english(question)

    # 2. 영어 쿼리로 임베딩
    print(f"[검색] 쿼리 임베딩 중: '{translated}'")
    question_vector = get_embedding(translated)

    # 3. 파일별 가장 유사한 청크 1개씩, 임계값 이상만 검색
    print(f"[검색] 유사한 청크 검색 중... (임계값: {SIMILARITY_THRESHOLD})")
    with get_db() as conn:
        rows = conn.execute(
            text("""
                SELECT * FROM (
                    SELECT DISTINCT ON (file_path)
                        id,
                        file_path,
                        content,
                        chunk_type,
                        line_start,
                        line_end,
                        1 - (embedding <=> :qv) AS similarity
                    FROM code_chunks
                    WHERE project_id = :project_id
                      AND embedding IS NOT NULL
                      AND 1 - (embedding <=> :qv) >= :threshold
                      AND file_path NOT LIKE '%package-info%'
                      AND file_path NOT LIKE '%Test.java%'
                      AND file_path NOT LIKE '%Tests.java%'
                    ORDER BY file_path, embedding <=> :qv
                ) AS deduped
                ORDER BY similarity DESC
                LIMIT :top_k
            """),
            {
                "project_id": project_id,
                "qv": str(question_vector),
                "threshold": SIMILARITY_THRESHOLD,
                "top_k": top_k,
            }
        ).fetchall()

    chunks = [
        {
            "id":         row[0],
            "file_path":  row[1],
            "content":    row[2],
            "chunk_type": row[3],
            "line_start": row[4],
            "line_end":   row[5],
            "similarity": round(float(row[6]), 4),
        }
        for row in rows
    ]

    print(f"[검색] {len(chunks)}개 청크 발견!")
    for c in chunks:
        print(f"  - {c['file_path']} (유사도: {c['similarity']})")

    return chunks
