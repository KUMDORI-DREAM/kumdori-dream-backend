# kumdori-dream-backend

Webots 기반 **AI 물류창고 안전 모니터링 및 동적 경로 최적화 시스템**의 FastAPI 백엔드입니다.
프로젝트 배경 및 전체 설계는 [docs/](docs/) 참고.

## 스택

* Python 3.12, [uv](https://docs.astral.sh/uv/) (패키지/가상환경 관리)
* FastAPI, Uvicorn, SQLAlchemy (async), Alembic, PostgreSQL
* WebSocket
* Docker / docker-compose
* 향후 연동: ChromaDB, LangGraph, Prometheus, Grafana

## 주요 역할

백엔드는 Webots 로봇 및 Edge Agent와 연동하여 다음 기능을 담당합니다.

* 로봇 Heartbeat 및 Telemetry 수집
* 로봇 상태 및 위치 관리
* Warehouse Graph 및 경로 정보 관리
* A* 기반 경로 계획 결과 관리
* 작업자·장애물·낙상 등 Detection Event 수집
* 위험 구역 및 Risk Cost 관리
* 위험 이벤트 발생 시 Route Replan 처리
* WebSocket 기반 실시간 상태 및 이벤트 전달
* LangGraph 기반 AI 분석 결과 관리
* 원격 조종 Control Lease 관리

## 로컬 개발 (Docker 없이)

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

`http://localhost:8000/api/v1/health` 로 확인합니다.

이 경우 `DATABASE_URL`이 로컬에서 접근 가능한 PostgreSQL을 가리켜야 합니다.

## Docker Compose

```bash
cp .env.example .env
docker compose up -d --build
```

기본으로는 `backend`, `postgres`만 기동됩니다.

추가 인프라는 profile로 분리합니다.

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
  main.py              # FastAPI entrypoint
  core/
    config.py          # 환경설정 (pydantic-settings)

  db/                  # SQLAlchemy Base, async session

  api/v1/              # REST / WebSocket API 라우터

  models/              # ORM 모델
                       # Robot
                       # RobotTelemetry
                       # WarehouseNode
                       # WarehouseEdge
                       # RoutePlan
                       # DetectionEvent
                       # AIAnalysis
                       # ControlLease

  schemas/             # Pydantic 요청/응답 스키마

  services/            # 비즈니스 로직
                       # Robot 상태 관리
                       # Detection Event 처리
                       # Route Planning / Replan
                       # Risk Cost 관리

  routing/             # Warehouse Graph 및 A* 경로 탐색

  websocket/           # Robot / Dashboard 연결 관리

  ai/                  # LangGraph / ChromaDB 연동

alembic/               # DB 마이그레이션

docker/                # Prometheus 등 인프라 설정

tests/                 # API / Routing / Event 자동화 테스트
```

## 주요 처리 흐름

```text
Webots Robot / Edge Agent
          ↓
Heartbeat / Telemetry / Detection Event
          ↓
       FastAPI
          ↓
 ┌────────┼───────────┐
 ▼        ▼           ▼
DB    WebSocket   Routing Service
                     ↓
                 Risk Update
                     ↓
                 Route Replan
```

위험 상황이 감지되면 이벤트를 단순 저장하는 데서 끝내지 않고, 해당 구역의 위험도를 경로 비용에 반영해 필요 시 로봇의 이동 경로를 다시 계산하는 구조를 목표로 합니다.
