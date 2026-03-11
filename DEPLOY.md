# Oracle Cloud 배포 가이드

## 1. Oracle Cloud 인스턴스 준비

1. Oracle Cloud Free Tier 인스턴스 생성
   - Shape: VM.Standard.A1.Flex (ARM, 무료)
   - OS: Ubuntu 22.04
   - vCPU: 2, RAM: 12GB (무료 한도)

2. 방화벽 포트 오픈 (Security List)
   - 22 (SSH)
   - 80 (HTTP - 프론트엔드)
   - 8000 (필요 시 백엔드 직접 접근)

3. Ubuntu 방화벽 설정
```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save
```

## 2. 서버에 Docker 설치

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

## 3. 코드 배포

```bash
# 프로젝트 클론
git clone https://github.com/your-repo/ProjectLens.git
git clone https://github.com/your-repo/ProjectLens-front.git

# 환경변수 설정
cd ProjectLens
cp .env.example .env
vi .env  # 실제 값으로 수정
```

## 4. 환경변수 (.env) 수정

```
GITHUB_TOKEN=실제_토큰
OPENAI_API_KEY=실제_키
DB_HOST=postgres
DB_PORT=5432
DB_USER=projectlens
DB_PASSWORD=안전한_비밀번호
DB_NAME=projectlens
```

## 5. Docker Compose 실행

```bash
cd ProjectLens

# 빌드 및 실행
docker compose -f docker-compose.prod.yml up -d --build

# DB 초기화 (최초 1회)
docker exec projectlens-backend python init_db.py

# 로그 확인
docker compose -f docker-compose.prod.yml logs -f
```

## 6. 접속 확인

- 프론트엔드: http://서버IP
- 백엔드 API: http://서버IP/api/projects

## 7. 유용한 명령어

```bash
# 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps

# 재시작
docker compose -f docker-compose.prod.yml restart

# 중지
docker compose -f docker-compose.prod.yml down

# 코드 업데이트 후 재배포
git pull
docker compose -f docker-compose.prod.yml up -d --build
```
