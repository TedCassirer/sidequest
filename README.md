# Sidequest

Sidequest is a simple task management library. Tasks, known as *quests*, are
registered with the `@quest` decorator. Quests can be dispatched to a message
queue and later executed by a worker. Results of quest executions are stored in
a SQLite database.

```python
from sidequest import quest, dispatch, Worker, InMemoryQueue, ResultDB

@quest
def hello(name):
    return f"Hello {name}!"

queue = InMemoryQueue()
db = ResultDB()

dispatch(queue, "hello", "World")
worker = Worker(queue, db)
worker.run_forever()

print(db.fetch_all())
```
