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


@quest(queue=QUEUE)
async def fail() -> int:
    raise RuntimeError("boom")


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
        _, quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, 3)
        self.assertIsNone(error)

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
        _, quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, 3)
        self.assertIsNone(error)

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
        await wf.dispatch()
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        self.assertEqual(len(wf.contexts()), 3)
        result = await wf.result(self.db)
        self.assertEqual(result, 18)

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
        _, quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "model_manip")
        self.assertEqual(result, _TestModel(name="test_modified", value=3))
        self.assertIsNone(error)

    async def test_multiple_workers(self) -> None:
        ctx1 = add(1, 2)
        ctx2 = add(3, 4)
        ctx3 = add(ctx1.cast, ctx2.cast)
        await dispatch(ctx3)
        w1 = Worker(QUEUE, self.db)
        w2 = Worker(QUEUE, self.db)
        t1 = asyncio.create_task(w1.run_forever())
        t2 = asyncio.create_task(w2.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        w1.stop()
        w2.stop()
        await asyncio.gather(t1, t2)
        result = await self.db.fetch_result(ctx3.id)
        self.assertEqual(result, 10)
        results = await self.db.fetch_all()
        self.assertEqual(len(results), 3)

    async def test_workflow_status_tracking(self) -> None:
        c1 = add(1, 2)
        c2 = fail()
        root = add(c1.cast, c2.cast)
        wf = Workflow(root)
        await wf.dispatch(self.db)
        states = {cid: status for cid, _, status in await wf.statuses(self.db)}
        self.assertEqual(states[c1.id], "PENDING")
        self.assertEqual(states[c2.id], "PENDING")
        self.assertEqual(states[root.id], "WAITING")
        worker = Worker(QUEUE, self.db)
        task = asyncio.create_task(worker.run_forever())
        while not QUEUE.empty():
            await asyncio.sleep(0)
        worker.stop()
        await task
        states = {cid: status for cid, _, status in await wf.statuses(self.db)}
        self.assertEqual(states[c1.id], "SUCCESS")
        self.assertEqual(states[c2.id], "FAILED")
        self.assertEqual(states[root.id], "FAILED")


if __name__ == "__main__":
    unittest.main()
