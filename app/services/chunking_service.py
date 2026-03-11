import re

# 청크 최대 글자수 (OpenAI 토큰 제한 고려)
MAX_CHUNK_SIZE = 1500


def chunk_files(files: list) -> list:
    """
    파일 목록을 받아서 청크 목록으로 변환해요.
    Java 파일은 메서드 단위, 나머지는 100줄 단위로 쪼개요.
    """
    chunks = []
    for file in files:
        file_path = file["file_path"]
        content = file["content"]
        extension = file["extension"]

        if extension == ".java":
            file_chunks = _chunk_java(file_path, content)
        else:
            file_chunks = _chunk_by_lines(file_path, content)

        chunks.extend(file_chunks)

    print(f"[청킹] 파일 {len(files)}개 → 청크 {len(chunks)}개")
    return chunks


def _chunk_java(file_path: str, content: str) -> list:
    """
    Java 파일을 메서드/클래스 단위로 쪼개요.
    Java로 치면 AST 파싱 대신 중괄호 기반으로 분리하는 거예요.
    """
    chunks = []
    lines = content.split("\n")

    current_chunk_lines = []
    current_start = 1
    brace_depth = 0
    in_method = False

    for i, line in enumerate(lines, 1):
        current_chunk_lines.append(line)
        brace_depth += line.count("{") - line.count("}")

        # 메서드 시작 감지 (public/private/protected + 반환타입 + 메서드명 패턴)
        if re.search(r'(public|private|protected|static)\s+\w+\s+\w+\s*\(', line):
            in_method = True

        # 메서드 끝 감지 (중괄호 depth가 1로 돌아올 때)
        if in_method and brace_depth <= 1 and len(current_chunk_lines) > 3:
            chunk_content = "\n".join(current_chunk_lines).strip()
            if chunk_content and len(chunk_content) > 50:
                chunks.append({
                    "file_path": file_path,
                    "content": chunk_content[:MAX_CHUNK_SIZE],
                    "chunk_type": "METHOD",
                    "line_start": current_start,
                    "line_end": i
                })
            current_chunk_lines = []
            current_start = i + 1
            in_method = False

    # 남은 내용 처리
    if current_chunk_lines:
        chunk_content = "\n".join(current_chunk_lines).strip()
        if chunk_content and len(chunk_content) > 50:
            chunks.append({
                "file_path": file_path,
                "content": chunk_content[:MAX_CHUNK_SIZE],
                "chunk_type": "CLASS",
                "line_start": current_start,
                "line_end": len(lines)
            })

    # 청크가 없으면 파일 전체를 하나의 청크로
    if not chunks:
        chunks.append({
            "file_path": file_path,
            "content": content[:MAX_CHUNK_SIZE],
            "chunk_type": "FILE",
            "line_start": 1,
            "line_end": len(lines)
        })

    return chunks


def _chunk_by_lines(file_path: str, content: str) -> list:
    """
    Java 외 파일 (xml, yml, md 등)은 100줄 단위로 쪼개요.
    """
    chunks = []
    lines = content.split("\n")
    chunk_size = 100

    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i + chunk_size]
        chunk_content = "\n".join(chunk_lines).strip()

        if chunk_content and len(chunk_content) > 20:
            chunks.append({
                "file_path": file_path,
                "content": chunk_content[:MAX_CHUNK_SIZE],
                "chunk_type": "FILE",
                "line_start": i + 1,
                "line_end": min(i + chunk_size, len(lines))
            })

    return chunks
