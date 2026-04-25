import sqlite3
import json
import os

DB_PATH = os.getenv("DB_PATH", "dedup.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Kunci Deduplikasi: Primary Key pada (topic, event_id)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            topic TEXT,
            event_id TEXT,
            timestamp TEXT,
            source TEXT,
            payload TEXT,
            PRIMARY KEY (topic, event_id)
        )
    ''')
    conn.commit()
    conn.close()

def save_event(event_data: dict) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO events (topic, event_id, timestamp, source, payload) VALUES (?, ?, ?, ?, ?)",
            (
                event_data['topic'],
                event_data['event_id'],
                event_data['timestamp'],
                event_data['source'],
                json.dumps(event_data['payload'])
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Menangkap duplikasi berdasarkan Primary Key
        return False
    finally:
        conn.close()

def get_events_by_topic(topic: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    if topic:
        cursor.execute("SELECT * FROM events WHERE topic = ?", (topic,))
    else:
        cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "topic": r["topic"], "event_id": r["event_id"], 
        "timestamp": r["timestamp"], "source": r["source"], 
        "payload": json.loads(r["payload"])
    } for r in rows]

def get_stats_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM events")
    unique_processed = cursor.fetchone()[0]
    cursor.execute("SELECT DISTINCT topic FROM events")
    topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return unique_processed, topics
