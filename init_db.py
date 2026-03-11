from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://projectlens:projectlens@localhost:5433/projectlens"

engine = create_engine(
    DATABASE_URL,
    connect_args={"client_encoding": "utf8"},
    echo=False
)


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
                last_synced TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("OK projects 테이블")

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
