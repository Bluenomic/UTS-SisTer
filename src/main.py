from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Optional, List, Union
import time
import asyncio
import logging

from src.models import Event
from src.database import init_db, save_event, get_events_by_topic, get_stats_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class SystemState:
    def __init__(self):
        self.received = 0
        self.duplicate_dropped = 0
        self.start_time = time.time()
        # Internal Queue pemrosesan asinkron
        self.event_queue = asyncio.Queue()

state = SystemState()

async def event_consumer():
    """Background Worker (Consumer)"""
    while True:
        try:
            event_dict = await state.event_queue.get()
            # Idempotency Check
            if not save_event(event_dict):
                state.duplicate_dropped += 1
                logger.warning(f"DUPLICATE DETECTED: Topic='{event_dict['topic']}', EventID='{event_dict['event_id']}'")
            else:
                logger.info(f"PROCESSED: Topic='{event_dict['topic']}', EventID='{event_dict['event_id']}'")
        except asyncio.CancelledError:
            break
        finally:
            state.event_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Jalankan Background Task saat aplikasi start
    consumer_task = asyncio.create_task(event_consumer())
    yield
    consumer_task.cancel()

app = FastAPI(title="Pub-Sub Log Aggregator UTS", lifespan=lifespan)

@app.post("/publish")
async def publish_event(events: Union[Event, List[Event]]):
    """Producer: Menerima event dan memasukkannya ke Queue"""
    if not isinstance(events, list):
        events = [events]
    
    for event in events:
        state.received += 1
        event_dict = event.model_dump()
        event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        await state.event_queue.put(event_dict)
        
    return {"status": "success", "message": f"{len(events)} event(s) queued"}

@app.get("/events")
async def list_events(topic: Optional[str] = None):
    return {"events": get_events_by_topic(topic)}

@app.get("/stats")
async def get_system_stats():
    unique_processed, topics = get_stats_data()
    return {
        "received": state.received,
        "unique_processed": unique_processed,
        "duplicate_dropped": state.duplicate_dropped,
        "topics": topics,
        "uptime_seconds": round(time.time() - state.start_time, 2)
    }
