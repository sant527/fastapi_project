from fastapi import FastAPI
from code.routes import demo

app = FastAPI()
app.include_router(demo.router)