from sidequest import (
    quest,
    dispatch,
    Worker,
    InMemoryQueue,
    ResultDB,
    QuestContext,
)
import unittest


QUEUE = InMemoryQueue()


@quest(queue=QUEUE)
def add(a, b):
    return a + b


class TestSidequest(unittest.TestCase):
    def setUp(self) -> None:
        while not QUEUE.empty():
            QUEUE.receive()

    def test_worker_executes_quest_and_stores_result(self) -> None:
        db = ResultDB()
        ctx = add(1, 2)
        dispatch(ctx)
        worker = Worker(QUEUE, db)
        worker.run_forever()
        results = db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)

    def test_quest_function_returns_context(self) -> None:
        db = ResultDB()
        ctx = add(1, 2)
        self.assertIsInstance(ctx, QuestContext)
        dispatch(ctx)
        worker = Worker(QUEUE, db)
        worker.run_forever()
        results = db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
