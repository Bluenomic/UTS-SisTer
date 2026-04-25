import httpx
import asyncio
import time
import os
import random

AGGREGATOR_URL = os.getenv("AGGREGATOR_URL", "http://localhost:8080/publish")

async def start_publishing():
    print(f"Publisher Service started. Sending events to {AGGREGATOR_URL}...")
    
    sent_ids = []
    
    async with httpx.AsyncClient() as client:
        while True:
            try:
                is_duplicate = len(sent_ids) > 0 and random.random() < 0.3
                
                if is_duplicate:
                    event_id = random.choice(sent_ids)
                    topic = "sensor.power"
                    msg_type = "DUPLICATE"
                else:
                    event_id = f"evt-{random.randint(1000, 9999)}"
                    topic = random.choice(["sensor.temp", "sensor.humidity", "sensor.power"])
                    sent_ids.append(event_id)
                    msg_type = "NEW"
                
                payload = {
                    "topic": topic,
                    "event_id": event_id,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "source": "docker-publisher-service",
                    "payload": {"value": random.uniform(10.0, 50.0)}
                }
                
                response = await client.post(AGGREGATOR_URL, json=payload)
                print(f"[{msg_type}] Sent {event_id} to {topic} - Status: {response.status_code}")
                
                if len(sent_ids) > 100:
                    sent_ids.pop(0)
                    
            except Exception as e:
                print(f"Error connecting to aggregator: {e}")
            
            await asyncio.sleep(10)

if __name__ == "__main__":
    time.sleep(5)
    asyncio.run(start_publishing())
