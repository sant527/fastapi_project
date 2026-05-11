from fastapi import FastAPI, Query, Header, Cookie
from typing import Annotated

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/demo")
async def demo(
    # Path is defined in the route itself — see /demo/{item_id} below

    # Query params — come from URL: /demo?name=john&age=25
    name: str = "default_name",
    age: int = 0,
    is_active: bool = True,
    optional_param: str | None = None,

    # Query param with validation
    score: Annotated[float, Query(ge=0, le=100, description="Score between 0 and 100")] = 0.0,

    # Header params — come from request headers
    user_agent: Annotated[str | None, Header()] = None,

    # Cookie params — come from browser cookies
    session_id: Annotated[str | None, Cookie()] = None,
):
    return {
        "query_params": {
            "name": name,
            "age": age,
            "is_active": is_active,
            "optional_param": optional_param,
            "score": score,
        },
        "header_params": {
            "user_agent": user_agent,
        },
        "cookie_params": {
            "session_id": session_id,
        },
    }


# Path param — part of the URL itself: /demo/42
@app.get("/demo/{item_id}")
async def demo_with_path(item_id: int):
    return {"path_param": {"item_id": item_id}}
