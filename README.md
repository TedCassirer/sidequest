# SideQuest

SideQuest is a simple task management library. Tasks, known as *quests*, are
registered with the `@quest` decorator. Quests can be dispatched to a message
queue and later executed by a worker. Results of quest executions are stored in
a SQLite database.

```python
from sidequest import (
    quest,
    dispatch,
    Worker,
    BaseWorker,
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
    await db.setup()
    hello_ctx = hello("World")
    await dispatch(hello_ctx)
    worker = Worker(QUEUE, db)
    await worker.run_forever()
    print(await db.fetch_all())


asyncio.run(main())
```

## Custom workers

`Worker` is built on top of the :class:`BaseWorker` class. You can subclass
`BaseWorker` to implement custom behaviour. For example, a worker that sends
heartbeat signals for long running quests might override :meth:`handle_message`
or :meth:`execute_quest`.

```python
from sidequest import Worker

class HeartbeatWorker(Worker):
    async def execute_quest(self, quest, args, kwargs):
        # emit heartbeat here
        return await super().execute_quest(quest, args, kwargs)
```
