from fastapi import FastAPI

from .monitor import MonitorThread


thread = MonitorThread()

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    thread.start()


@app.on_event("shutdown")
def shutdown_event():
    thread.stop()
    thread.join()


@app.get("/")
def read_root():
    return thread.devices


@app.post("/")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
