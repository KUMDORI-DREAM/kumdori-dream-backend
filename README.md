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

## Robot API

- `POST /api/v1/robots/{robot_id}/heartbeat` — 위치/상태/배터리 보고. Robot을 upsert하고 RobotTelemetry를 적재.
- `GET /api/v1/robots` — 등록된 로봇 목록 및 최신 상태.
- `GET /api/v1/robots/{robot_id}` — 단일 로봇 상태 조회.

## Webots 연동

`webots/controllers/patrol_robot_controller/`의 컨트롤러가 Edge Agent 역할을 겸해 매 스텝 위치를 계산하고,
`edge_agent.EdgeAgent`가 백그라운드 스레드로 heartbeat를 백엔드에 전송한다(기본 1초 간격, 실패해도 시뮬레이션은 계속 진행).

환경변수로 동작을 조정할 수 있다 (Webots 실행 전 설정):

```text
KUMDORI_BACKEND_URL           기본값 http://localhost:8000
KUMDORI_ROBOT_ID               기본값 patrol-robot-01
KUMDORI_HEARTBEAT_INTERVAL_S   기본값 1.0 (초)
```

## 프로젝트 구조

```text
app/
  main.py          # FastAPI entrypoint
  core/config.py   # 환경설정 (pydantic-settings)
  db/              # SQLAlchemy Base, async session
  api/v1/          # API 라우터, 엔드포인트
  models/          # ORM 모델 (Robot, RobotTelemetry)
  schemas/         # Pydantic 스키마
alembic/           # DB 마이그레이션
docker/            # 인프라 설정 (prometheus 등)
webots/
  worlds/          # Webots World 파일
  controllers/     # 로봇 Controller + Edge Agent
```
