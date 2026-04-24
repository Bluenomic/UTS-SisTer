import sqlite3
import json
import os

# Default ke dedup.db di folder yang sama jika DB_PATH tidak disetel
DB_PATH = os.getenv("DB_PATH", "dedup.db")

def init_db():
    """Inisialisasi tabel database saat aplikasi pertama kali berjalan."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Membuat tabel jika belum ada.
    # Kunci idempontency ada di PRIMARY KEY (topic, event_id)
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
    """
    Menyimpan event ke database.
    Return True jika berhasil disimpan (event baru).
    Return False jika (topic, event_id) sudah ada (duplikat).
    """
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
        # Menangkap error jika kombinasi PRIMARY KEY (topic, event_id) sudah ada -> ini berarti DUPLIKAT!
        return False
    finally:
        conn.close()

def get_events_by_topic(topic: str = None):
    """Mengambil daftar event dari database, bisa difilter berdasarkan topik."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Agar hasil return bisa diakses seperti dictionary
    cursor = conn.cursor()
    
    if topic:
        cursor.execute("SELECT * FROM events WHERE topic = ?", (topic,))
    else:
        cursor.execute("SELECT * FROM events")
        
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for row in rows:
        events.append({
            "topic": row["topic"],
            "event_id": row["event_id"],
            "timestamp": row["timestamp"],
            "source": row["source"],
            "payload": json.loads(row["payload"])
        })
    return events

def get_stats_data():
    """Mengambil statistik unik dan daftar topik dari database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hitung total event unik (karena yang masuk database pasti unik)
    cursor.execute("SELECT COUNT(*) FROM events")
    unique_processed = cursor.fetchone()[0]
    
    # Ambil daftar topik yang ada
    cursor.execute("SELECT DISTINCT topic FROM events")
    topics = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return unique_processed, topics
