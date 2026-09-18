from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import robot_position_manager

router = APIRouter(tags=["ws"])


@router.websocket("/ws/robots")
async def robot_positions_ws(websocket: WebSocket) -> None:
    await robot_position_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        robot_position_manager.disconnect(websocket)
