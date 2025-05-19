# Sidequest

Sidequest is a simple task management library. Tasks, known as *quests*, are
registered with the `@quest` decorator. Quests can be dispatched to a message
queue and later executed by a worker. Results of quest executions are stored in
a SQLite database.

```python
from sidequest import quest, dispatch, Worker, InMemoryQueue, ResultDB

QUEUE = InMemoryQueue()

@quest(queue=QUEUE)
def hello(name):
    return f"Hello {name}!"

db = ResultDB()
hello_ctx = hello("World")
dispatch(hello_ctx)
worker = Worker(QUEUE, db)
worker.run_forever()

print(db.fetch_all())
```
