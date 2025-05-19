from sidequest import quest, dispatch, Worker, InMemoryQueue, ResultDB
import unittest


@quest
def add(a, b):
    return a + b


class TestSidequest(unittest.TestCase):
    def test_worker_executes_quest_and_stores_result(self) -> None:
        queue = InMemoryQueue()
        db = ResultDB()
        dispatch(queue, "add", 1, 2)
        worker = Worker(queue, db)
        worker.run_forever()
        results = db.fetch_all()
        self.assertEqual(len(results), 1)
        quest_name, result, error, _ = results[0]
        self.assertEqual(quest_name, "add")
        self.assertEqual(result, "3")
        self.assertIsNone(error)


if __name__ == "__main__":
    unittest.main()
