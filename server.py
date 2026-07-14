import asyncio
import uuid
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from orchestrator import run_trial
from interfaces import AgentOutput

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TrialRequest(BaseModel):
    case_text: str

# In-memory store: trial_id -> asyncio.Queue
trial_queues = {}

@app.post("/trial/start")
async def start_trial(req: TrialRequest):
    trial_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    trial_queues[trial_id] = queue

    def on_event(event_type: str, payload):
        queue.put_nowait((event_type, payload))

    # Launch trial in background
    asyncio.create_task(run_trial(req.case_text, on_event=on_event))

    return {"trial_id": trial_id}

@app.get("/trial/stream/{trial_id}")
async def stream_trial(trial_id: str):
    if trial_id not in trial_queues:
        return {"error": "Trial not found"}

    queue = trial_queues[trial_id]

    async def event_generator():
        while True:
            event_type, payload = await queue.get()
            
            # Serialize payload
            if hasattr(payload, "model_dump_json"):
                data = payload.model_dump_json()
            else:
                data = json.dumps(payload)
                
            yield f"event: {event_type}\ndata: {data}\n\n"
            
            if event_type == "verdict_document_ready":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
