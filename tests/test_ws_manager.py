from app.ws.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[dict] = []

    async def accept(self) -> None:
        pass

    async def send_json(self, data: dict) -> None:
        if self.fail:
            raise RuntimeError("connection closed")
        self.sent.append(data)


async def test_broadcast_sends_to_all_connections():
    manager = ConnectionManager()
    ws1, ws2 = FakeWebSocket(), FakeWebSocket()
    await manager.connect(ws1)
    await manager.connect(ws2)

    await manager.broadcast({"robot_id": "r1"})

    assert ws1.sent == [{"robot_id": "r1"}]
    assert ws2.sent == [{"robot_id": "r1"}]


async def test_broadcast_prunes_dead_connections():
    manager = ConnectionManager()
    dead = FakeWebSocket(fail=True)
    alive = FakeWebSocket()
    await manager.connect(dead)
    await manager.connect(alive)

    await manager.broadcast({"robot_id": "r1"})

    assert dead not in manager._connections
    assert alive.sent == [{"robot_id": "r1"}]


async def test_disconnect_removes_connection():
    manager = ConnectionManager()
    ws = FakeWebSocket()
    await manager.connect(ws)

    manager.disconnect(ws)

    assert ws not in manager._connections
