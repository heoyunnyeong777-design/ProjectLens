# 프로젝트 테이블 컬럼 정의
# 실제 테이블은 Docker로 이미 생성했어요
# 여기서는 참고용으로만 사용해요

# projects 테이블
# id, name, gitlab_url, access_token, tech_stack,
# project_type, description, status, last_synced, created_at

# code_chunks 테이블
# id, project_id, file_path, content, chunk_type,
# class_name, method_name, line_start, line_end,
# http_method, url_pattern, embedding, created_at

# chat_history 테이블
# id, project_id, session_id, question, answer, sources, created_at
