FROM python:3.11-slim

WORKDIR /app

# Praktik terbaik Docker: Jangan jalankan aplikasi sebagai Root User jika memungkinkan
# Membuat user non-root bernama 'appuser'
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app
USER appuser

# Copy file requirements dulu agar Docker bisa melakukan caching jika tidak ada perubahan
COPY requirements.txt .

# Install dependencies tanpa menyimpan cache instalasi agar image lebih ringan
RUN pip install --no-cache-dir -r requirements.txt

# Copy folder src/
COPY src/ ./src/

# Buat folder khusus untuk menyimpan file database, 
# pindah ke user root sebentar untuk membuat folder lalu kembalikan akses ke appuser
USER root
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data
USER appuser

# Set Environment Variable agar SQLite tersimpan di folder /app/data
ENV DB_PATH=/app/data/dedup.db

EXPOSE 8080

# Jalankan uvicorn server saat container menyala
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
