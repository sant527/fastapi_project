# Is fastapi built on typehints

> Yes, FastAPI is fundamentally built around Python's type hints. Here's a quick summary of how:

**Type hints drive almost everything in FastAPI:**

* **Request validation** — When you declare a path/query parameter or request body with a type hint, FastAPI automatically validates incoming data against that type.
* **Serialization** — Response data is automatically converted/serialized based on the declared return type.
* **Automatic docs** — FastAPI reads your type hints to generate the interactive OpenAPI (Swagger) docs at `/docs` with no extra work.
* **Dependency injection** — FastAPI's `Depends()` system uses type hints to figure out what to inject and where.
* **Editor support** — Because everything is typed, you get full autocomplete and error checking in your IDE.

A simple example illustrates this well:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

Here, just by writing `item_id: int`, FastAPI will:

1. Extract `item_id` from the URL path
2. Validate it's an integer (returning a clear error if not)
3. Pass it correctly typed to your function
4. Document it in the Swagger UI


# path and query parameters

## Flask Query Parameters

Just call `request.args.get()` for each one:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/items/<int:item_id>")
def read_item(item_id):
    q     = request.args.get("q", None)
    page  = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    sort  = request.args.get("sort", "asc")

    return jsonify({
        "item_id": item_id,
        "q":       q,
        "page":    page,
        "limit":   limit,
        "sort":    sort
    })
```

A request like `/items/42?q=hello&page=2&limit=5&sort=desc` would give you all of them.

## where as in the fastapi

**Compare with FastAPI — much cleaner:**

```python
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None, page: int = 1, limit: int = 10, sort: str = "asc"):
    return {"item_id": item_id, "q": q, "page": page, "limit": limit, "sort": sort}
```

In FastAPI you just **add parameters to the function** — no manual fetching. Flask requires a `request.args.get()` call for every single query param, which gets verbose fast.


# `async def` vs `def` in FastAPI — The Silent Killer

FastAPI won't warn you — it silently runs and everything looks fine until you hit load.

The mistake feels natural because people think:

> *"I'm using FastAPI which is async, so I should write `async def` everywhere"*

But that's wrong. The rule should be:

```
Is the work inside truly async (awaitable)?      →  use async def
Is the work blocking (DB calls, file I/O, CPU)?  →  use plain def
```

---

## The Real-World Guide

```python
# ✅ Use async def — when you're awaiting something
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(...)   # truly async, non-blocking

# ✅ Use plain def — when using sync libraries
def get_user(user_id: int, db: Session = Depends(get_db)):
    db.query(User)...                # FastAPI runs in threadpool, safe

# ❌ The silent killer
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db.query(User)...                # looks fine, blocks event loop
```

---

## Why It's Dangerous

- Works perfectly in **development** with low traffic
- Under **load**, the event loop gets choked
- **All requests slow down together** — not just the DB-heavy ones

---

## The Simple Mental Check

Before writing any endpoint, ask:

> *"Am I using `await` inside this function?"*
> - **Yes** → `async def`
> - **No** → plain `def`



# FastAPI Dependency Injection — How It Really Works

> FastAPI was **designed around dependency injection** — so it knows what to do with a generator.  
> Flask was designed around **simplicity and explicitness** — you wire everything up yourself.

---

## The Core Idea

In FastAPI, `Depends()` is not just a utility — it's the **backbone of the entire framework**. FastAPI was built from the ground up expecting you to declare *what you need*, and it figures out *how to get it*.

A generator dependency like `get_db` is the perfect example of this:

```python
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db        # ← Phase 1: open & hand over
    finally:
        db.close()      # ← Phase 2: always clean up
```

`yield` splits the function into two phases — **before** and **after** the endpoint runs.

---

## What FastAPI Does Internally

FastAPI inspects `get_db`, sees a `yield`, and knows it's a generator. It then wraps it automatically:

```python
# What FastAPI does under the hood
gen = get_db()
db = next(gen)           # runs up to yield → opens session

# injects db into your endpoint → endpoint runs

try:
    next(gen)            # resumes after yield → finally block runs
except StopIteration:
    pass                 # generator exhausted, session closed ✓
```

This is the **same mechanic** as Python's `contextmanager`:

```python
# These two are conceptually identical
with get_db() as db:     # context manager style
    ...

db = Depends(get_db)     # FastAPI DI style
```

---

## The Lifecycle — Step by Step

```
Request comes in
      ↓
FastAPI calls get_db()
      ↓
db = SessionLocal()       ← connection opened
      ↓
yield db                  ← PAUSE — hands session to endpoint
      ↓
  ┌─────────────────────┐
  │   endpoint runs     │
  │   db.query(...)     │
  │   return response   │
  └─────────────────────┘
      ↓
generator resumes
      ↓
finally: db.close()       ← connection closed — always
      ↓
Response sent
```

---

## Why `finally` Is Critical

```python
try:
    yield db
finally:
    db.close()   # runs even if endpoint raises an exception
```

Without `finally`:

```
endpoint raises HTTPException(404)
  → generator never resumes
  → db.close() never called
  → connection leaked 💀
```

With `finally`:

```
endpoint raises HTTPException(404)
  → FastAPI catches it
  → resumes generator
  → finally block runs
  → db.close() called ✓
  → exception re-raised and returned as 404
```

---

## Flask — No Magic, All Manual

Flask has no DI system. You wire everything yourself using `g` (request-scoped global storage) and `teardown_appcontext`:

```python
from flask import Flask, g
from database import SessionLocal

app = Flask(__name__)

def get_db():
    if 'db' not in g:
        g.db = SessionLocal()   # stored on request context
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)      # manually closed after request
    if db is not None:
        db.close()

@app.route("/users/<int:user_id>")
def get_user(user_id):
    db = get_db()               # you call it yourself
    ...
```

No generator recognition. No automatic lifecycle. You own it entirely.

---

## Side by Side

| | FastAPI | Flask |
|---|---|---|
| Session open | inside `get_db` generator | inside `get_db` manually |
| Session close | `finally` after `yield` | `@teardown_appcontext` |
| Who calls it | FastAPI automatically via `Depends()` | You call `get_db()` yourself |
| Exception safety | `finally` handles it | `teardown_appcontext` gets `exception` arg |
| Generator support | ✅ built-in | ❌ not recognized |
| Philosophy | Declare what you need | Wire it up yourself |

---

## The Generator Type Hint — What It Means

```python
def get_db() -> Generator[Session, None, None]:
```

| Position | Type | Meaning |
|---|---|---|
| 1st | `Session` | Type of value produced by `yield` |
| 2nd | `None` | Type sent **into** the generator (unused here) |
| 3rd | `None` | Return type after generator exhausts |

You could also write it as:
```python
from typing import Iterator

def get_db() -> Iterator[Session]:   # simpler, same effect
```

---

## Key Takeaway

> FastAPI's `Depends()` doesn't just inject values — it manages **entire lifecycles**.  
> The generator pattern gives you `setup → use → teardown` in a single readable function,  
> and FastAPI handles all the wiring so your endpoints stay clean.

```python
# Your endpoint just declares what it needs
def get_user(user_id: int, db: Session = Depends(get_db)):
    ...
# FastAPI handles open → inject → close
```

# `Depends()` With No Argument — The Shortcut

## What It Is

```python
class ItemQuery(BaseModel):
    page: int = 1
    limit: int = 10

def read_item(params: ItemQuery = Depends()):  # ← no argument inside Depends
```

`Depends()` with nothing inside is shorthand for `Depends(ItemQuery)` — FastAPI looks at the **type hint** and uses that as the dependency.

These two are identical:

```python
# Explicit
def read_item(params: ItemQuery = Depends(ItemQuery)):
    ...

# Shorthand — FastAPI infers ItemQuery from the type hint
def read_item(params: ItemQuery = Depends()):
    ...
```

---

## How FastAPI Infers It

```python
params: ItemQuery = Depends()
  ↑                    ↑
type hint            no arg

FastAPI sees no arg → looks left at type hint → uses ItemQuery as the callable
```

It only works because the type hint **is itself a callable** (a Pydantic class).  
FastAPI just calls `ItemQuery(...)` with fields resolved from the query string.

---

## When It Works vs Doesn't

```python
# ✅ Works — type hint is a callable class
params: ItemQuery = Depends()

# ✅ Works — plain function, but must be explicit (no shorthand)
commons: dict = Depends(common_params)

# ❌ Doesn't work — primitives aren't meaningful callables
page: int = Depends()   # makes no sense, FastAPI will error
```

---

## Key Takeaway

> `Depends()` with no argument is purely a **convenience shortcut**  
> to avoid repeating the class name twice — nothing more.


# FastAPI Eager Resolution — Figure Out Upfront, Execute Cheaply Later

> FastAPI does **not** look at the URL request at startup — it can't, no request has come in yet.  
> It maps everything by inspecting **type hints at startup**, then executes the pre-built plan per request.

This pattern is called **"eager resolution"** — and it's everywhere once you know it.

---

## The Two Phases

```
STARTUP — no requests yet
  FastAPI reads function signatures
  applies default rules (primitive = query string)
  builds and caches the dependency plan

  ↓ server starts

REQUEST TIME — GET /users?page=2&limit=5
  FastAPI executes the pre-built plan
  pulls page=2 from the actual URL
  pulls limit=5 from the actual URL
  calls common_params(page=2, limit=5)
```

Think of it like a recipe vs cooking:

```
Startup  = writing the recipe ("page comes from query string")
Request  = actually cooking   ("pull page=2 from this URL")
```

FastAPI writes the recipe once. Every request just follows it.

---

## Why This Pattern Exists

If FastAPI inspected every function signature **on every request**:

```
Request 1 → inspect signatures → build plan → execute → respond
Request 2 → inspect signatures → build plan → execute → respond
Request 3 → inspect signatures → build plan → execute → respond
```

Python's `inspect` module is **slow** — reading type hints, traversing signatures, resolving annotations. Doing this thousands of times per second would kill performance.

Instead:

```
Startup   → inspect once → cache plan
Request 1 → execute cached plan → respond  ⚡
Request 2 → execute cached plan → respond  ⚡
Request 3 → execute cached plan → respond  ⚡
```

---

## What Gets Cached at Startup

```python
@router.get("/users")
def list_users(
    commons: dict = Depends(common_params),
    db: Session = Depends(get_db),
    user_id: int,
    x_api_key: str = Header(None)
):
```

FastAPI builds and caches this entire tree:

```
list_users dependency graph:
  ├── user_id       → primitive, no path match → query string
  ├── x_api_key     → explicit Header()        → headers
  ├── common_params → plain function
  │     ├── page    → primitive → query string
  │     └── limit   → primitive → query string
  └── get_db        → generator function
        └── yields Session → inject, close after request
```

This entire tree is resolved **once** and reused for every request to `/users`.

---

## Same Pattern Everywhere

```python
# Python decorators — run at import time, not call time
@app.get("/users")       # executes immediately when Python loads the file
def list_users():        # not when someone hits /users
    ...
```

```python
# SQLAlchemy — configured at startup
engine = create_engine(...)     # connection pool built at startup
SessionLocal = sessionmaker()   # factory configured at startup
# actual DB connections happen per request
```

```python
# FastAPI — routes and dependency graphs built at startup
router = APIRouter()
@router.get("/users")           # dependency graph built here
# actual param pulling happens per request
```

---

## Key Takeaway

> By the time your server prints:
> ```
> INFO:     Uvicorn running on http://0.0.0.0:8000
> ```
> FastAPI already knows **exactly** where every parameter of every endpoint comes from.  
> The request just brings the actual **values** to fill in.



# FastAPI — All Parameter Sources in One Example

> Every possible source a parameter can come from in FastAPI, in a single endpoint.

---

## The Full Example

```python
from fastapi import FastAPI, APIRouter, Depends, Header, Cookie, Path, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Generator

app = FastAPI()
router = APIRouter()

# ── Grouped query params via Depends ──────────────────────────────
class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 10
    sort: str = "asc"

# ── Request body ──────────────────────────────────────────────────
class ItemBody(BaseModel):
    name: str
    price: float
    category: str

# ── DB session dependency ─────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Auth dependency ───────────────────────────────────────────────
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "secret":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@router.post("/shop/{category}/{item_id}")
def full_example(

    # ── 1. PATH PARAMS ──────────────────────────────────────────
    # Matched by name against /{category}/{item_id} in route string
    category: str,
    item_id: int,

    # ── 2. QUERY PARAMS (primitive) ─────────────────────────────
    # Primitives not in path → automatically query string
    q: str = None,
    in_stock: bool = True,

    # ── 3. QUERY PARAMS (forced explicit) ───────────────────────
    # Query() lets you add validation, alias, description
    min_price: float = Query(0.0, ge=0, description="Minimum price filter"),
    max_price: float = Query(9999.0, le=99999),

    # ── 4. QUERY PARAMS (grouped via Depends) ───────────────────
    # Pydantic model fields → each resolves as query string
    pagination: PaginationParams = Depends(),

    # ── 5. REQUEST BODY ─────────────────────────────────────────
    # Pydantic model without Depends → JSON body
    body: ItemBody,

    # ── 6. BODY (single field forced) ───────────────────────────
    # Body() forces a single value to come from JSON body
    discount: float = Body(0.0),

    # ── 7. HEADERS ──────────────────────────────────────────────
    # Must be explicit — FastAPI never assumes headers
    user_agent: str = Header(None),
    accept_language: str = Header(None),

    # ── 8. HEADER via Depends (auth pattern) ────────────────────
    # Dependency that itself reads from headers
    api_key: str = Depends(verify_api_key),

    # ── 9. COOKIES ──────────────────────────────────────────────
    # Must be explicit — FastAPI never assumes cookies
    session_id: str = Cookie(None),
    theme: str = Cookie("light"),

    # ── 10. DATABASE SESSION via Depends ────────────────────────
    # Generator dependency — opens before, closes after
    db: Session = Depends(get_db),

):
    return {
        "category":        category,
        "item_id":         item_id,
        "q":               q,
        "in_stock":        in_stock,
        "min_price":       min_price,
        "max_price":       max_price,
        "page":            pagination.page,
        "limit":           pagination.limit,
        "sort":            pagination.sort,
        "item_name":       body.name,
        "item_price":      body.price,
        "discount":        discount,
        "user_agent":      user_agent,
        "accept_language": accept_language,
        "api_key":         api_key,
        "session_id":      session_id,
        "theme":           theme,
    }
```

---

## A Matching Request

```
POST /shop/electronics/42?q=laptop&in_stock=true&min_price=100&page=2&limit=5

Headers:
  X-Api-Key: secret
  User-Agent: Mozilla/5.0
  Accept-Language: en-US

Cookies:
  session_id: abc123
  theme: dark

Body:
{
  "name": "Laptop",
  "price": 999.99,
  "category": "electronics",
  "discount": 10.5
}
```

---

## Full Dependency Graph

```
full_example
  ├── category          → path param        (matched in route string)
  ├── item_id           → path param        (matched in route string)
  ├── q                 → query string      (primitive, no path match)
  ├── in_stock          → query string      (primitive, no path match)
  ├── min_price         → query string      (explicit Query())
  ├── max_price         → query string      (explicit Query())
  ├── pagination        → Depends()
  │     ├── page        → query string      (primitive field)
  │     ├── limit       → query string      (primitive field)
  │     └── sort        → query string      (primitive field)
  ├── body              → request body      (Pydantic model, no Depends)
  ├── discount          → request body      (explicit Body())
  ├── user_agent        → header            (explicit Header())
  ├── accept_language   → header            (explicit Header())
  ├── api_key           → Depends(verify_api_key)
  │     └── x_api_key  → header            (inside dependency)
  ├── session_id        → cookie            (explicit Cookie())
  ├── theme             → cookie            (explicit Cookie())
  └── db                → Depends(get_db)
        └── Session     → generator        (open → inject → close)
```

---

## All Sources — Quick Reference

| Source | How FastAPI knows | Example |
|---|---|---|
| Path | name matches `{x}` in route | `item_id: int` |
| Query (auto) | primitive, no path match | `q: str = None` |
| Query (explicit) | `Query()` with validation | `min_price: float = Query(0.0, ge=0)` |
| Query (grouped) | Pydantic + `Depends()` | `pagination: PaginationParams = Depends()` |
| Body | Pydantic model, no Depends | `body: ItemBody` |
| Body (single field) | `Body()` explicit | `discount: float = Body(0.0)` |
| Header | `Header()` explicit | `user_agent: str = Header(None)` |
| Cookie | `Cookie()` explicit | `session_id: str = Cookie(None)` |
| Dependency | `Depends(fn)` | `db: Session = Depends(get_db)` |
| Nested dependency | `Depends()` inside a `Depends()` | `api_key: str = Depends(verify_api_key)` |