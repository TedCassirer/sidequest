import asyncio
import unittest

import pydantic

from sidequest import (
    quest,
    dispatch,
    Worker,
    InMemoryQueue,
    ResultDB,
    QuestContext,
    Workflow,
    QuestStatus,
)


QUEUE = InMemoryQueue()


class _TestModel(pydantic.BaseModel):
    """A simple model for testing."""

    name: str
    value: int


@quest(queue=QUEUE)
async def add(a: int, b: int) -> int:
    await asyncio.sleep(0)
    return a + b


@quest(queue=QUEUE)
async def model_manip(a: int, b: _TestModel) -> _TestModel:
    return _TestModel(
        name=f"{b.name}_modified",
        value=a + b.value,
    )


class TestSideQuest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        while not QUEUE.empty():
            await QUEUE.receive()
        self.db = ResultDB()
        await self.db.setup()

    async def asyncTearDown(self) -> None:
        await self.db.teardown()

    async def test_async_worker_executes_quest_and_stores_result(self) -> None:
        ctx = add(1, 2)
        await dispatch(ctx)
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 1)
        _, quest_name, result, error, status, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, 3)
        self.assertIsNone(error)
        self.assertEqual(status, QuestStatus.SUCCESS.value)

    async def test_async_quest_function_returns_context(self) -> None:
        ctx = add(1, 2)
        self.assertIsInstance(ctx, QuestContext)
        await dispatch(ctx)
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 1)
        _, quest_name, result, error, status, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, 3)
        self.assertIsNone(error)
        self.assertEqual(status, QuestStatus.SUCCESS.value)

    async def test_workflow_chaining(self) -> None:
        ctx1 = add(1, 2)
        ctx2 = add(5, 10)
        ctx3 = add(ctx1.cast, ctx2.cast)
        await dispatch(ctx3)
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 3)
        result = await self.db.fetch_result(ctx3.id)
        self.assertEqual(result, 18)

    async def test_workflow_object(self) -> None:
        ctx1 = add(1, 2)
        ctx2 = add(5, 10)
        root = add(ctx1.cast, ctx2.cast)
        wf = Workflow(root)
        await wf.dispatch(self.db)
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        self.assertEqual(len(wf.contexts()), 3)
        result = await wf.result(self.db)
        self.assertEqual(result, 18)

    async def test_workflow_status_monitor(self) -> None:
        ctx1 = add(1, 2)
        ctx2 = add(3, 4)
        root = add(ctx1.cast, ctx2.cast)
        wf = Workflow(root)
        await wf.dispatch(self.db)
        # all quests registered as pending
        pending = await wf.status(self.db)
        self.assertTrue(all(status == QuestStatus.PENDING.value for status in pending.values()))
        worker = Worker(QUEUE, self.db)
        await worker.run_forever()
        final = await wf.status(self.db)
        self.assertTrue(all(status == QuestStatus.SUCCESS.value for status in final.values()))

    async def test_quest_with_model(self) -> None:
        ctx = model_manip(1, _TestModel(name="test", value=2))
        await dispatch(ctx)
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 1)
        _, quest_name, result, error, status, _ = results[0]
        self.assertEqual(quest_name, "model_manip")
        self.assertEqual(result, _TestModel(name="test_modified", value=3))
        self.assertIsNone(error)
        self.assertEqual(status, QuestStatus.SUCCESS.value)


if __name__ == "__main__":
    unittest.main()
