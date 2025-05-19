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

### Chaining quests

Below is an example of chaining quests together. The result of one quest can be used as the input to another by referencing the context's `cast` property.

```python
@quest(queue=QUEUE)
async def add(a: int, b: int) -> int:
    await asyncio.sleep(0)
    return a + b

@quest(queue=QUEUE)
async def multiply(a: int, b: int) -> int:
    return a * b

async def chain() -> None:
    db = ResultDB()
    await db.setup()
    first = add(1, 2)
    second = add(3, 4)
    combined = multiply(first.cast, second.cast)
    await dispatch(combined)
    worker = Worker(QUEUE, db)
    await worker.run_forever()
    print(await db.fetch_result(combined.id))

asyncio.run(chain())
```

### Custom input and result types

Quests can accept and return custom objects. When using a `BaseModel` or dataclass Pydantic will automatically handle serialization.

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    value: int

@quest(queue=QUEUE)
async def process(item: Item) -> Item:
    return Item(name=item.name.upper(), value=item.value + 1)

async def custom() -> None:
    db = ResultDB()
    await db.setup()
    ctx = process(Item(name="foo", value=3))
    await dispatch(ctx)
    worker = Worker(QUEUE, db)
    await worker.run_forever()
    print(await db.fetch_result(ctx.id))

asyncio.run(custom())
```
