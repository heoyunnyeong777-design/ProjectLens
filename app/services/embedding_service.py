from openai import OpenAI

client = OpenAI()

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536차원, 저렴하고 빠름
EMBEDDING_DIM = 1536

print("[임베딩] OpenAI text-embedding-3-small 사용")


def get_embedding(text: str) -> list:
    """
    텍스트 하나를 벡터로 변환해요.
    반환값: 1536개 숫자 리스트
    """
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding


def get_embeddings_batch(texts: list) -> list:
    """
    여러 텍스트를 한 번에 벡터로 변환해요.
    OpenAI API 배치 처리 사용
    """
    print(f"  [임베딩] {len(texts)}개 청크 변환 시작...")
    response = client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL
    )
    print(f"  [임베딩] 완료!")
    return [item.embedding for item in response.data]
