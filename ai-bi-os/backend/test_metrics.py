import asyncio
from app.routers.analytics import get_metrics_explorer
import json

async def main():
    import sqlite3
    conn = sqlite3.connect('data/datamind.db')
    user = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
    # Force set the active dataset for this test to f32b7be3-5257-414e-bbb2-9578a04c8154
    from app.services.state_manager import get_state_manager
    sm = get_state_manager()
    await sm.set_active_dataset(user[0], "f32b7be3-5257-414e-bbb2-9578a04c8154")
    res = await get_metrics_explorer({"id": user[0]})
    print(json.dumps(res, indent=2))

asyncio.run(main())
