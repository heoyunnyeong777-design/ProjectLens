from github import Github
from app.core.config import GITHUB_TOKEN

ALLOWED_EXTENSIONS = {".java", ".jsp", ".xml", ".yml", ".yaml", ".md", ".sql", ".json"}
SKIP_DIRS = {"target", "build", ".git", ".idea", "node_modules", ".mvn", "dist"}


def collect_files(github_url: str):
    client = Github(GITHUB_TOKEN)
    owner, repo_name = _parse_url(github_url)

    print(f"[GitHub] {owner}/{repo_name} 저장소 접속 중...")
    repo = client.get_repo(f"{owner}/{repo_name}")

    print(f"[GitHub] 파일 트리 가져오는 중...")
    tree = repo.get_git_tree(repo.default_branch, recursive=True)

    target_blobs = [
        item for item in tree.tree
        if item.type == "blob"
        and not any(d in SKIP_DIRS for d in item.path.split("/"))
        and _ext(item.path) in ALLOWED_EXTENSIONS
        and (item.size or 0) <= 1_000_000
    ]

    print(f"[GitHub] {len(target_blobs)}개 파일 내용 수집 중...")
    files = []
    for blob in target_blobs:
        try:
            content = repo.get_contents(blob.path).decoded_content.decode("utf-8")
            files.append({
                "file_path": blob.path,
                "content": content,
                "extension": _ext(blob.path),
                "size": blob.size
            })
            print(f"  [수집] {blob.path}")
        except Exception as e:
            print(f"  [스킵] {blob.path} - {e}")

    print(f"[GitHub] 총 {len(files)}개 파일 수집 완료")
    return files, repo.name, repo.description


def _parse_url(url: str) -> tuple[str, str]:
    parts = url.rstrip("/").replace(".git", "").split("/")
    return parts[-2], parts[-1]


def _ext(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
