from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Optional, List, Union
import time
import asyncio
import logging

from src.models import Event
from src.database import init_db, save_event, get_events_by_topic, get_stats_data

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# State management
class SystemState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.received = 0
        self.duplicate_dropped = 0
        self.start_time = time.time()
        self.event_queue = asyncio.Queue()

state = SystemState()

async def event_consumer():
    """Background worker yang mengambil event dari queue dan menyimpannya ke database."""
    while True:
        try:
            event_dict = await state.event_queue.get()
            is_new_event = save_event(event_dict)
            if not is_new_event:
                state.duplicate_dropped += 1
                logger.warning(f"DUPLICATE DETECTED: Topic='{event_dict['topic']}', EventID='{event_dict['event_id']}'")
            else:
                logger.info(f"PROCESSED: Topic='{event_dict['topic']}', EventID='{event_dict['event_id']}'")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"ERROR processing event: {e}")
        finally:
            state.event_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Dijalankan saat server pertama kali menyala
    state.reset()
    init_db()
    # Jalankan consumer sebagai background task
    consumer_task = asyncio.create_task(event_consumer())
    logger.info("Background Event Consumer started.")
    yield
    # Batalkan task saat server shutdown
    consumer_task.cancel()
    await asyncio.gather(consumer_task, return_exceptions=True)

app = FastAPI(title="Pub-Sub Log Aggregator UTS", lifespan=lifespan)

@app.post("/publish")
async def publish_event(events: Union[Event, List[Event]]):
    """Menerima batch atau single event dan memasukkannya ke internal queue."""
    # Konversi ke list jika input adalah single event
    if not isinstance(events, list):
        events = [events]
    
    for event in events:
        state.received += 1
        
        # Persiapkan data untuk disimpan
        event_dict = event.model_dump()
        event_dict['timestamp'] = event_dict['timestamp'].isoformat()
        
        # Masukkan ke queue (Producer)
        await state.event_queue.put(event_dict)
        
    return {
        "status": "success", 
        "message": f"{len(events)} event(s) received and queued for processing"
    }

@app.get("/events")
async def list_events(topic: Optional[str] = None):
    # Jika tidak memberikan parameter ?topic=... maka akan mengembalikan semua
    events = get_events_by_topic(topic)
    return {"events": events}

@app.get("/stats")
async def get_system_stats():
    unique_processed, topics = get_stats_data()
    uptime_seconds = time.time() - state.start_time
    
    return {
        "received": state.received,
        "unique_processed": unique_processed,
        "duplicate_dropped": state.duplicate_dropped,
        "topics": topics,
        "uptime_seconds": round(uptime_seconds, 2),
        "queue_size": state.event_queue.qsize()
    }
