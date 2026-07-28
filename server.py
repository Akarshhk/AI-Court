import asyncio
import uuid
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

from orchestrator import run_trial
from interfaces import AgentOutput
from rag.ingest import ingest_case, ingest_custom_document
from rag.document_parser import extract_text
from rag.generic_chunker import chunk_generic
from rag.case_validator import validate_case_document
from typing import List
from fastapi import FastAPI, Request, UploadFile, File, HTTPException

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
UPLOADED_CASE_TEXT = ""
UPLOADED_RAG_STATE = ([], {}, [])
LAST_RAG_STATE = ([], {}, [])

@app.post("/case/upload")
async def upload_case(files: List[UploadFile] = File(...)):
    global UPLOADED_CASE_TEXT, UPLOADED_RAG_STATE
    
    # Check for running trials
    if trial_queues:
        raise HTTPException(status_code=409, detail="A trial is already in progress")
        
    all_extracted_text = ""
    all_chunks = []
    
    for file in files:
        ext = file.filename.split('.')[-1].lower() if file.filename else ""
        if f".{ext}" not in [".txt", ".pdf", ".docx"]:
            raise HTTPException(status_code=400, detail=f"Could not read {file.filename} — please upload .txt, .pdf, or .docx files under 5MB.")
            
        file_bytes = await file.read()
        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"File {file.filename} is too large. Please upload files under 5MB.")
            
        try:
            extracted_text = extract_text(file_bytes, file.filename)
            chunks = chunk_generic(extracted_text)
            all_extracted_text += extracted_text + "\n\n"
            all_chunks.extend(chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error parsing file {file.filename}: {str(e)}")
            
    try:
        validation_result = await validate_case_document(all_extracted_text)
        
        UPLOADED_RAG_STATE = ingest_custom_document(all_chunks)
        UPLOADED_CASE_TEXT = all_extracted_text
        
        preview = all_extracted_text[:500] + ("..." if len(all_extracted_text) > 500 else "")
        return {
            "case_text_preview": preview,
            "chunk_count": len(all_chunks),
            "ready": True,
            "case_validation": validation_result.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail="An error occurred while processing the file.")

@app.post("/trial/start")
async def start_trial(req: TrialRequest):
    global UPLOADED_CASE_TEXT, UPLOADED_RAG_STATE, LAST_RAG_STATE
    
    # If case_text is empty, we assume it's using the already-ingested UPLOADED_CASE_TEXT
    if req.case_text:
        rag_state = ingest_case(req.case_text)
        full_text = req.case_text
    else:
        rag_state = UPLOADED_RAG_STATE
        full_text = UPLOADED_CASE_TEXT
        
    LAST_RAG_STATE = rag_state
        
    trial_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    trial_queues[trial_id] = queue

    def on_event(event_type: str, payload):
        queue.put_nowait((event_type, payload))

    # Launch trial in background
    asyncio.create_task(run_trial(full_text, rag_state, on_event=on_event))

    return {"trial_id": trial_id}

@app.get("/case/chunks")
async def get_case_chunks():
    store, _, _ = LAST_RAG_STATE
    return {"chunks": [c.model_dump() for c in store]}

@app.get("/trial/stream/{trial_id}")
async def stream_trial(trial_id: str):
    if trial_id not in trial_queues:
        return {"error": "Trial not found"}

    queue = trial_queues[trial_id]

    async def event_generator():
        try:
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
        finally:
            if trial_id in trial_queues:
                del trial_queues[trial_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")
