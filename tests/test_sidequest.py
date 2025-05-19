import asyncio
import unittest

from sidequest import (
    quest,
    dispatch,
    Worker,
    InMemoryQueue,
    ResultDB,
    QuestContext,
)


QUEUE = InMemoryQueue()


@quest(queue=QUEUE)
async def async_add(a, b):
    await asyncio.sleep(0)
    return a + b


class TestSidequest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        while not QUEUE.empty():
            await QUEUE.receive()
        self.db = ResultDB()
        await self.db.setup()

    async def asyncTearDown(self) -> None:
        await self.db.teardown()

    async def test_async_worker_executes_quest_and_stores_result(self) -> None:
        ctx = async_add(1, 2)
        await dispatch(ctx)
        worker = Worker(QUEUE, self.db)
        await worker.run_forever()
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "async_add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)

    async def test_async_quest_function_returns_context(self) -> None:
        ctx = async_add(1, 2)
        self.assertIsInstance(ctx, QuestContext)
        await dispatch(ctx)
        worker = Worker(QUEUE, self.db)
        await worker.run_forever()
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "async_add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
