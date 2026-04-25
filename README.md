# Pub-Sub Log Aggregator

Layanan aggregator log berbasis HTTP dengan fitur *Deduplication* dan *Idempotent Consumer*.

## Prasyarat
- Docker dan Docker Compose sudah terinstal di sistem.

## Cara Menjalankan (Docker Compose)
Cara termudah untuk menjalankan seluruh sistem (Aggregator + Publisher Otomatis):
```bash
docker-compose up --build
```
- **Aggregator:** Berjalan di `http://localhost:8080`
- **Publisher:** Berjalan di background dan mengirim log otomatis ke aggregator.

## Cara Menjalankan (Standard Docker)
Jika ingin menjalankan layanan Aggregator saja:
1. **Build Image:**
   ```bash
   docker build -t uts-aggregator .
   ```
2. **Run Container:**
   ```bash
   docker run -p 8080:8080 uts-aggregator
   ```

## Dokumentasi API
Setelah aplikasi berjalan, dokumentasi interaktif dapat diakses melalui:
- **Swagger UI:** `http://localhost:8080/docs`
- **ReDoc:** `http://localhost:8080/redoc`

## Pengujian (Unit Test)
Untuk menjalankan rangkaian pengujian otomatis:
```bash
pytest
```
*Catatan: Memerlukan environment Python lokal dengan dependensi terinstal.*
