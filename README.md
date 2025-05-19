# Sidequest

Sidequest is a simple task management library. Tasks, known as *quests*, are
registered with the `@quest` decorator. Quests can be dispatched to a message
queue and later executed by a worker. Results of quest executions are stored in
a SQLite database.

```python
from sidequest import (
    quest,
    dispatch,
    Worker,
    InMemoryQueue,
    ResultDB,
)
import asyncio

QUEUE = InMemoryQueue()


@quest(queue=QUEUE)
async def hello(name):
    return f"Hello {name}!"


async def main() -> None:
    db = ResultDB()
    hello_ctx = hello("World")
    await dispatch(hello_ctx)
    worker = Worker(QUEUE, db)
    await worker.run_forever()
    print(await db.fetch_all())


asyncio.run(main())
```
