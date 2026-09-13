# kumdori-dream-backend

Webots 기반 AI 자율 순찰 로봇 관제 시스템 — FastAPI 백엔드.
프로젝트 배경 및 설계는 [docs/](docs/) 참고.

## 스택

- Python 3.12, [uv](https://docs.astral.sh/uv/) (패키지/가상환경 관리)
- FastAPI, Uvicorn, SQLAlchemy (async), Alembic, PostgreSQL
- Docker / docker-compose

## 로컬 개발 (Docker 없이)

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

`http://localhost:8000/api/v1/health` 로 확인. 이 경우 `DATABASE_URL`이 로컬에서 접근 가능한 PostgreSQL을 가리켜야 함.

## Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
```

기본으로는 `backend`, `postgres`만 기동됨 (MVP 범위).

추가 인프라는 profile로 분리:

```bash
docker compose --profile stage2 up -d   # + ChromaDB
docker compose --profile stage3 up -d   # + Prometheus, Grafana
docker compose --profile full up -d     # 전체
```

## 마이그레이션 (Alembic)

```bash
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```

## 프로젝트 구조

```text
app/
  main.py          # FastAPI entrypoint
  core/config.py   # 환경설정 (pydantic-settings)
  db/              # SQLAlchemy Base, async session
  api/v1/          # API 라우터
  models/          # ORM 모델
  schemas/         # Pydantic 스키마
alembic/           # DB 마이그레이션
docker/            # 인프라 설정 (prometheus 등)
```
