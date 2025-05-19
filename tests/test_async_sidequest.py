import asyncio
import unittest

from sidequest import (
    quest,
    adispatch,
    AsyncWorker,
    AsyncInMemoryQueue,
    AsyncResultDB,
)
from sidequest.db import SQLALCHEMY_AVAILABLE



@quest
async def async_add(a, b):
    await asyncio.sleep(0)
    return a + b


class TestAsyncSidequest(unittest.IsolatedAsyncioTestCase):
    @unittest.skipUnless(SQLALCHEMY_AVAILABLE, "SQLAlchemy required")
    async def test_async_worker_executes_quest_and_stores_result(self) -> None:
        queue = AsyncInMemoryQueue()
        db = AsyncResultDB()
        await adispatch(queue, "async_add", 1, 2)
        worker = AsyncWorker(queue, db)
        await worker.run_forever()
        results = await db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "async_add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
