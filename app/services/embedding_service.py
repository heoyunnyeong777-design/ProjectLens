from sentence_transformers import SentenceTransformer

# 모델 로드 (처음 실행 시 자동 다운로드 약 90MB)
print("[임베딩] 모델 로딩 중...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("[임베딩] 모델 로딩 완료!")


def get_embedding(text: str) -> list:
    """
    텍스트 하나를 벡터로 변환해요.
    반환값: 384개 숫자 리스트
    """
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def get_embeddings_batch(texts: list) -> list:
    """
    여러 텍스트를 한 번에 벡터로 변환해요.
    로컬 모델이라 API 비용 없음! 완전 무료!
    """
    print(f"  [임베딩] {len(texts)}개 청크 변환 시작...")
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    print(f"  [임베딩] 완료!")
    return [e.tolist() for e in embeddings]
