# kumdori-dream-backend

Webots 기반 Warehouse AI 로봇 관제 백엔드입니다.

## 현재 구현 범위

- FastAPI, SQLAlchemy async, PostgreSQL, Alembic
- 로봇 heartbeat 및 telemetry 저장
- 로봇 상태: `IDLE`, `MOVING`, `REPLANNING`, `WAITING`, `ALERT`, `OFFLINE`
- 안전 이벤트: `PERSON_IN_PATH`, `OBJECT_ON_AISLE`, `AISLE_BLOCKED`, `FALL`
- Warehouse Graph node/edge 관리 API
- Graph 기반 A* route 계획 API
- Webots warehouse 로봇 컨트롤러 및 EdgeAgent heartbeat

## 실행

```bash
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload
```

API 문서는 `http://localhost:8000/docs`에서 확인할 수 있습니다.

Docker를 사용하는 경우:

```bash
cp .env.example .env
docker compose up -d --build
```

## 주요 API

- `GET /api/v1/health`
- `POST /api/v1/robots/{robot_id}/heartbeat`
- `GET /api/v1/robots`
- `GET /api/v1/robots/{robot_id}`
- `POST /api/v1/robots/{robot_id}/safety-events`
- `GET /api/v1/robots/{robot_id}/safety-events`
- `POST /api/v1/warehouse/nodes`
- `POST /api/v1/warehouse/edges`
- `GET /api/v1/warehouse/nodes`
- `GET /api/v1/warehouse/edges`
- `POST /api/v1/routes/plan`

## 프로젝트 구조

```text
app/
  main.py
  api/v1/                 # REST API endpoints
  core/                   # 환경 설정
  db/                     # SQLAlchemy Base 및 async session
  models/                 # Robot, SafetyEvent, WarehouseNode, WarehouseEdge
  schemas/                # API request/response schemas
  route_planner.py        # A* route planner
alembic/                  # DB migrations
docker/                   # Prometheus 설정
webots/
  worlds/                 # warehouse_world.wbt
  controllers/            # warehouse robot controller
```

## Webots 환경 변수

```text
KUMDORI_BACKEND_URL           기본값: http://localhost:8000
KUMDORI_ROBOT_ID              기본값: warehouse-robot-01
KUMDORI_HEARTBEAT_INTERVAL_S  기본값: 1.0
```

## 마이그레이션

```bash
uv run alembic upgrade head
```
