# Laporan UTS Sistem Terdistribusi dan Parallel
**Topik:** Pub-Sub Log Aggregator dengan Idempotent Consumer dan Deduplication

**Nama:** Imam Dzulvan Muffid
**NIM:** 11231031

#### Link Demo Youtube: https://youtu.be/pSVYtmyHP4o

---

### T1 (Bab 1): Karakteristik Sistem Terdistribusi pada Pub-Sub
Sistem terdistribusi didefinisikan sebagai sekumpulan komputer independen yang tampak bagi pengguna sebagai satu sistem koheren (Tanenbaum & Van Steen, 2017). Dalam desain *log aggregator* berbasis *Publish-Subscribe*, karakteristik utama yang muncul adalah *distribution transparency* dan *scalability*. Sistem ini harus menyembunyikan kompleksitas lokasi *producer* (transparansi lokasi) sehingga ribuan sensor dapat mengirim data tanpa perlu mengetahui letak fisik server aggregator.

*Trade-off* yang umum terjadi adalah antara *performance* dan *reliability*. Pada *log aggregator*, sering kali digunakan komunikasi asinkron untuk mencapai *throughput* tinggi (*scalability*), namun hal ini memicu tantangan pada *consistency*. Penggunaan antrean (*internal queue*) memungkinkan sistem menangani lonjakan data (*concurrency*), tetapi menambah risiko *message loss* jika sistem *crash* sebelum data tertulis ke penyimpanan permanen. Oleh karena itu, *fault tolerance* menjadi krusial untuk memastikan sistem dapat pulih dan tetap menyediakan layanan secara berkelanjutan.

### T2 (Bab 2): Arsitektur Client-Server vs Publish-Subscribe
Arsitektur *Client-Server* tradisional bersifat *tightly coupled*, di mana klien harus mengetahui alamat server secara spesifik dan komunikasi biasanya bersifat sinkron. Sebaliknya, arsitektur *Publish-Subscribe* menawarkan pemisahan (*decoupling*) dalam tiga dimensi: ruang, waktu, dan sinkronisasi (Tanenbaum & Van Steen, 2017). *Producer* tidak perlu tahu siapa *consumer*-nya (ruang), keduanya tidak harus aktif pada saat yang sama (waktu), dan pengiriman data tidak memblokir aktivitas *producer* (sinkronisasi).

Pemilihan arsitektur *Pub-Sub* untuk *log aggregator* sangat tepat secara teknis karena skalabilitasnya yang tinggi. Saat jumlah *producer* (sumber log) meningkat drastis, arsitektur *Pub-Sub* mampu bertindak sebagai *buffer* yang mencegah server kewalahan. Dengan adanya perantara (*broker* atau *internal queue*), beban kerja dapat didistribusikan secara lebih merata dan asinkron, yang merupakan keunggulan utama dibandingkan pola *request-reply* pada *Client-Server* konvensional yang cenderung lambat saat menangani ribuan koneksi simultan.

### T3 (Bab 3): At-Least-Once vs Exactly-Once Delivery
Dalam komunikasi sistem terdistribusi, *At-Least-Once delivery* menjamin bahwa pesan akan sampai ke tujuan setidaknya satu kali, namun membuka peluang terjadinya duplikasi jika mekanisme *acknowledgment* (ACK) gagal (Tanenbaum & Van Steen, 2017). Di sisi lain, *Exactly-Once delivery* menjamin pesan sampai tepat satu kali, namun pola ini sangat sulit dan mahal untuk dicapai karena kompleksitas koordinasi antar simpul dalam menghadapi kegagalan jaringan.

Mengingat sulitnya mencapai *Exactly-Once*, penggunaan *Idempotent Consumer* menjadi sangat krusial, terutama saat terjadi *retries*. Ketika pengirim tidak menerima ACK karena gangguan jaringan, ia akan mengirim ulang (*retry*) pesan yang sama. Tanpa sifat *idempotency*, *aggregator* akan memproses data tersebut berulang kali, yang mengakibatkan ketidakkonsistenan data (misalnya, total log yang tercatat menjadi salah). Dengan mengimplementasikan *deduplication* di sisi *consumer*, sistem dapat mensimulasikan efek *Exactly-Once* secara efektif, di mana hasil akhir tetap konsisten meskipun terjadi pengiriman pesan berulang.

### T4 (Bab 4): Penamaan dan Skema Event
Penamaan dalam sistem terdistribusi berfungsi untuk mengidentifikasi entitas secara unik dan mempermudah resolusi alamat (Tanenbaum & Van Steen, 2017). Dalam desain *log aggregator* ini, penamaan *topic* mengikuti pola hierarki (misal: `sensor.suhu.lantai1`) untuk mempermudah kategorisasi dan filter data. Skema penamaan yang baik harus mendukung *openness*, di mana berbagai jenis *producer* dapat bergabung ke dalam sistem tanpa konflik penamaan.

Pemilihan `event_id` sangat krusial untuk mencegah tabrakan data (*collision*). Pendekatan yang paling aman adalah menggunakan *Universally Unique Identifier* (UUID) atau kombinasi antara *hash* konten dengan *timestamp* mikrodetik. Dalam implementasi ini, kombinasi `topic` dan `event_id` bertindak sebagai *identifier* unik global. Dengan desain yang *collision-resistant*, sistem dapat menjamin bahwa setiap entitas log dapat dibedakan secara absolut, yang merupakan fondasi utama bagi mekanisme *deduplication* di sisi *consumer*.

### T5 (Bab 5): Waktu dan Ordering
Sinkronisasi waktu adalah tantangan fundamental karena ketiadaan jam global yang sempurna dalam sistem terdistribusi (Tanenbaum & Van Steen, 2017). Dalam konteks pengumpulan log, *total ordering* (pengurutan mutlak) diperlukan jika urutan kejadian mempengaruhi logika bisnis, misalnya pada sistem transaksi keuangan. Namun, untuk *log aggregator* umum, sering kali cukup menggunakan *causal ordering* atau pengurutan berdasarkan *timestamp* ISO 8601 yang disertakan oleh *producer*.

Penggunaan *physical clock* dengan format ISO 8601 memudahkan manusia dalam membaca data, namun memiliki risiko jika terjadi *clock drift* antar pengirim. Untuk mencapai pengurutan yang lebih akurat secara logis, dapat diusulkan penggunaan *Lamport Clock* atau *Logical Clock*. Dengan *Logical Clock*, setiap event diberi nomor urut yang bertambah secara monoton, sehingga urutan kejadian dapat ditentukan secara relatif terhadap satu sama lain tanpa bergantung pada sinkronisasi jam fisik yang tidak stabil.

### T6 (Bab 6): Failure Modes dan Mitigasi
Sistem terdistribusi harus dirancang untuk menghadapi berbagai jenis kegagalan (*partial failures*). Beberapa titik kegagalan pada *log aggregator* meliputi: *Queue Overflow* (antrean penuh karena lonjakan data), *Database Crash* (kegagalan penyimpanan), dan *Network Partition* (publisher tidak dapat menjangkau aggregator). Menurut Tanenbaum & Van Steen (2017), mitigasi kegagalan dapat dilakukan melalui redundansi dan strategi pemulihan yang tepat.

Strategi mitigasi yang diterapkan meliputi:
1.  **Retry & Exponential Backoff**: *Producer* mencoba mengirim ulang data jika terjadi kegagalan jaringan dengan jeda waktu yang meningkat untuk menghindari beban berlebih (*thundering herd problem*).
2.  **Persistent Dedup Store**: Penggunaan SQLite memastikan bahwa data yang sudah diproses tidak hilang saat sistem *restart*, sehingga proses pemulihan dapat berjalan lebih cepat.
3.  **Graceful Shutdown**: Menghentikan *background consumer* secara bersih untuk memastikan semua data yang sudah ada di antrean sempat tertulis ke database sebelum sistem benar-benar mati.

### T7 (Bab 7): Eventual Consistency melalui Idempotency
*Eventual consistency* adalah model konsistensi di mana semua replika atau salinan data pada akhirnya akan menjadi identik jika tidak ada pembaruan lebih lanjut yang dilakukan (Tanenbaum & Van Steen, 2017). Dalam konteks *log aggregator*, duplikasi data akibat pengiriman ulang sering kali menyebabkan ketidakkonsistenan sementara antara apa yang dikirim oleh *publisher* dan apa yang tersimpan di *aggregator*.

Mekanisme *idempotency* melalui *deduplication* memungkinkan sistem mencapai *eventual consistency*. Meskipun jaringan mengirimkan data yang sama berkali-kali, sistem *consumer* menjamin bahwa hanya satu salinan unik yang akan disimpan secara permanen. Dengan demikian, meskipun terjadi kekacauan data di jaringan, *state* akhir dari database aggregator akan selalu konsisten dan akurat. Ini menunjukkan bahwa *idempotency* bukan sekadar fitur tambahan, melainkan prasyarat teknis untuk mencapai integritas data dalam sistem yang tidak dapat menjamin pengiriman pesan tepat satu kali.

### T8 (Bab 1-7): Metrik Evaluasi Sistem
Untuk mengevaluasi performa sistem terdistribusi, diperlukan metrik kuantitatif yang jelas (Tanenbaum & Van Steen, 2017). Tiga metrik utama yang digunakan adalah:
1.  **Throughput (Events per Second / EPS)**: Dihitung dengan rumus `Total Unique Events / Total Processing Time`. Metrik ini menunjukkan kapasitas sistem dalam menangani beban data per satuan waktu.
2.  **Latency (ms)**: Waktu yang dibutuhkan sejak event diterima oleh API hingga berhasil disimpan di database. Latensi yang rendah sangat penting untuk pemrosesan *real-time*.
3.  **Duplicate Rate (%)**: Dihitung dengan `(Total Duplicates / Total Received) * 100`. Metrik ini membantu mengidentifikasi stabilitas jaringan; *duplicate rate* yang tinggi menandakan sering terjadinya *timeout* atau kegagalan ACK di sisi jaringan.

Data metrik ini sangat mempengaruhi keputusan penskalaan (*scaling*). Jika EPS mendekati batas maksimal atau latensi meningkat secara signifikan, pengembang perlu melakukan *horizontal scaling* dengan menambah jumlah *aggregator* atau menggunakan *distributed message broker* yang lebih kuat seperti Apache Kafka untuk menggantikan antrean in-memory sederhana.

---

## 2. Dokumentasi Implementasi

### Arsitektur Sistem
- **Producer:** Mengirim log via HTTP POST `/publish`. Mendukung batch.
- **Internal Queue:** Menggunakan `asyncio.Queue` untuk decoupling antara penerimaan HTTP dan penulisan ke database.
- **Consumer:** Background worker yang secara asinkron mengambil data dari queue.
- **Deduplication Store:** SQLite dengan `PRIMARY KEY (topic, event_id)` untuk memastikan idempotency di level database.

### Endpoint API
- `POST /publish`: Menerima JSON (single/list).
- `GET /events`: Mengambil data unik yang sudah diproses.
- `GET /stats`: Statistik sistem (received, unique, dropped, uptime).

---

## 3. Referensi
- Tanenbaum, A. S., & Van Steen, M. (2017). *Distributed Systems: Principles and Paradigms*. 3rd Edition. Maarten van Steen.