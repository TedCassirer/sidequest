import asyncio
import unittest

from sidequest import (
    quest,
    adispatch,
    AsyncWorker,
    AsyncInMemoryQueue,
    AsyncResultDB,
    QuestContext,
)


ASYNC_QUEUE = AsyncInMemoryQueue()


@quest(queue=ASYNC_QUEUE)
async def async_add(a, b):
    await asyncio.sleep(0)
    return a + b


class TestAsyncSidequest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        while not ASYNC_QUEUE.empty():
            await ASYNC_QUEUE.receive()

    async def test_async_worker_executes_quest_and_stores_result(self) -> None:
        db = AsyncResultDB()
        ctx = async_add(1, 2)
        await adispatch(ctx)
        worker = AsyncWorker(ASYNC_QUEUE, db)
        await worker.run_forever()
        results = await db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "async_add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)

    async def test_async_quest_function_returns_context(self) -> None:
        db = AsyncResultDB()
        ctx = async_add(1, 2)
        self.assertIsInstance(ctx, QuestContext)
        await adispatch(ctx)
        worker = AsyncWorker(ASYNC_QUEUE, db)
        await worker.run_forever()
        results = await db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "async_add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
