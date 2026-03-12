import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "projectlens")
DB_USER = os.getenv("DB_USER", "projectlens")
DB_PASSWORD = os.getenv("DB_PASSWORD", "projectlens")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, connect_args={"client_encoding": "utf8"}, echo=False)


def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("OK pgvector 확장 활성화 완료")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                github_url VARCHAR,
                gitlab_url VARCHAR,
                access_token VARCHAR,
                tech_stack VARCHAR,
                project_type VARCHAR,
                description TEXT,
                status VARCHAR DEFAULT 'PENDING',
                file_count INTEGER DEFAULT 0,
                progress INTEGER DEFAULT 0,
                current_file VARCHAR DEFAULT '',
                analysis_status VARCHAR DEFAULT 'PENDING',
                analysis_structure TEXT,
                analysis_features TEXT,
                analysis_architecture TEXT,
                analysis_improvements TEXT,
                analysis_report TEXT,
                last_synced TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("OK projects 테이블")

        # 기존 테이블에 누락된 컬럼 추가 (이미 있으면 무시)
        alter_columns = [
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS current_file VARCHAR DEFAULT ''",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS analysis_status VARCHAR DEFAULT 'PENDING'",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS analysis_structure TEXT",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS analysis_features TEXT",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS analysis_architecture TEXT",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS analysis_improvements TEXT",
            "ALTER TABLE projects ADD COLUMN IF NOT EXISTS analysis_report TEXT",
        ]
        for sql in alter_columns:
            try:
                conn.execute(text(sql))
            except Exception:
                pass
        print("OK 누락 컬럼 추가 완료")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS code_chunks (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL,
                file_path VARCHAR NOT NULL,
                content TEXT NOT NULL,
                chunk_type VARCHAR,
                class_name VARCHAR,
                method_name VARCHAR,
                line_start INTEGER,
                line_end INTEGER,
                http_method VARCHAR,
                url_pattern VARCHAR,
                embedding vector(1536),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("OK code_chunks 테이블")

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL,
                session_id VARCHAR NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("OK chat_history 테이블")

        conn.commit()
    print("DB 초기화 완료!")


if __name__ == "__main__":
    init_db()
