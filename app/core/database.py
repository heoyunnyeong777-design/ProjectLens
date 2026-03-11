from sqlalchemy import create_engine, text
from app.core.config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

# SQLAlchemy 엔진 생성 (Windows cp949 인코딩 문제 우회)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"client_encoding": "utf8"},
    echo=False
)


def get_db():
    """SQLAlchemy connection 반환"""
    return engine.connect()

