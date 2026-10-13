# Plan: Spotify Songs Data Analyst Project

Dokumen ini menyimpan prompt awal, keputusan yang disepakati, dan struktur akhir
project. Status: **selesai dikerjakan dan diverifikasi**.

## Prompt awal

> saya ingin membuat project dashboard analyst berdasarkan dataset yang saya miliki yaitu di dalem folder data dalam folder raw. disini saya sediakan data steam anda bisa coba pahami isi datanya apa aja. disini saya ingin melakukan analyst terkait dataset tersebut dengan struktur pengerjaan :
>
> 1. Data Understanding
> 2. Data Processing / Data Cleaning
> 3. Feature engineering
> 4. Save Joblib atau Save Dataset yang udah dibersihin atau di proses
> 4. EDA ( Exploratory Data Analyst ) sebagai data visualisasi
> 5. Heatmap untuk korelasi
> 6. Membuat Dashboard terkait dataset tersebut menggunakan streamliat di folder app.
>
> jadilah seorang data science dan bantu saya dalam membuat project ini dan koreksi apa aja kira-kira yang harus ditambahkan kalau ada yang kurang.
>
> berikan rekomendasi dari dirimu terkait project ini.

## Keputusan yang dikonfirmasi user

1. **Dataset: Spotify** (`songs_normalize.csv`, 2.000 lagu) — bukan Steam. Berkas
   dipindah dari root project ke `data/raw/` (folder `raw`/`clean` sudah ada).
2. **Dashboard: 5 tab, tanpa machine learning.**
3. Seluruh isi project memakai **Bahasa Indonesia**, gaya mentor (komentar
   menjelaskan *kenapa*, bukan sintaks).

## Koreksi terhadap struktur prompt

| Prompt asli | Perbaikan |
|---|---|
| Nomor 4 muncul dua kali, tidak ada 6 | Tahap diurutkan ulang jadi 1–6 (Understanding → Cleaning → FE + Save → EDA → Heatmap → Dashboard) |
| Save joblib "atau" CSV | Keduanya dibuat: CSV (portabel) + joblib (cepat, menjaga tipe) |
| EDA dan heatmap digabung satu tahap | Dipisah eksplisit: notebook 04 = EDA lalu heatmap Pearson + Spearman di bagian akhir |
| Data steam (tidak ada di folder) | Diganti Spotify sesuai permintaan user saat ditanya; kejujuran data diutamakan (popularity 0 ditandai, bukan diimputasi) |

## Struktur akhir

```
project/
├── data/
│   ├── raw/songs_normalize.csv          # read-only
│   └── clean/
│       ├── songs_clean.csv              # output notebook 02
│       ├── songs_final.csv              # output notebook 03 (fitur lengkap)
│       ├── genres_long.csv              # 1 lagu x 1 genre
│       ├── artists.csv                  # agregat artis
│       └── spotify_clean.joblib         # dict {songs, genres_long, artists}
├── notebooks/
│   ├── 01_data_understanding.ipynb      # + section cerita "Hook→Angka→Makna"
│   ├── 02_data_cleaning.ipynb           # + cerita "2.000 jadi 1.926"
│   ├── 03_feature_engineering.ipynb     # + save CSV & joblib + cerita fitur
│   ├── 04_eda_korelasi.ipynb            # EDA + heatmap + insight + panduan storytelling
│   └── 05_data_storytelling.ipynb       # 3 cerita utuh + naskah 30 detik (permintaan user)
├── app/
│   ├── app.py                           # 5 tab + detail per genre (native + Altair + ECharts)
│   └── utils/data_loader.py             # @st.cache_data, normalisasi genre_list
├── .streamlit/config.toml               # tema hijau + palet chart
├── docs/plan.md
├── README.md
└── requirements.txt
```

## BUG yang ditemukan & diperbaiki saat verifikasi (regresi penting)

**Bug:** memilih genre apa pun di sidebar membuat dashboard menampilkan
"Tidak ada lagu yang cocok dengan filter".

**Akar masalah:** notebook 02 menyimpan `songs_clean.csv` dengan kolom `genre_list`
bertipe **list**. CSV tidak punya tipe list, jadi saat notebook 03 memuat CSV, kolom
itu terbaca sebagai **teks** `"['rock', 'pop']"`. Filter dashboard memakai
`set.intersection` yang butuh list — intersection dengan sebuah string selalu kosong,
sehingga hasil filter selalu 0 lagu. Not found saat pengujian awal karena tes awal
belum menguji pemilihan genre.

**Perbaikan (2 lapis):**
1. `notebooks/03` membangun ulang `genre_list` sebagai list sungguhan setelah memuat
   CSV (sumber data), plus `assert isinstance(..., list)`.
2. `app/utils/data_loader.py` menormalkan `genre_list` (list / teks / CSV-string) jadi
   list asli setelah `joblib.load`, sehingga app tetap benar walau joblib dibuat dari
   sumber lain.

**Bukti perbaikan (uji headless `AppTest`):** genre `pop` → 1.568 lagu,
`rock` → 225 lagu (membership, sama dengan tabel `genres_long` di notebook 03),
kombinasi `rock` + `hip hop` → 961 lagu. Total **17/17 uji lulus**.

## Profiling dataset (hasil eksekusi)

- 2.000 baris × 18 kolom, tanpa null. Tahun 1998–2020.
- `genre`: literal `set()` = 22 lagu (genre tak diketahui); 1.279 lagu multi-genre;
  15 genre unik setelah dipecah (pop 1.568 lagu di tabel explode).
- `popularity`: 126 bernilai 0 (setelah dedup: 121) — data tidak tersedia.
- Duplikat: 59 duplikat persis + 15 duplikat pasangan `artist`+`song` (metadata beda).
- Hasil cleaning: **1.926 lagu unik, 835 artis**, 23 kolom → 32 kolom setelah FE.
- Fitur audio 0–1; `key` 0–11; `mode` 0/1; loudness −20.5…−0.3 dB; tempo 60–211 BPM.

## Angka kunci (untuk reproduksi)

| Metrik | Nilai |
|---|---|
| Lagu setelah cleaning | 1.926 |
| Artis | 835 |
| Rata-rata popularity (data ada) | 63.8 |
| Tanpa data popularity | 121 (6.3%) |
| Median durasi / tempo | 3.72 menit / 120 BPM |
| Major : Minor | 55.3% : 44.7% |
| Explicit | 27.7% |
| Mood: Bahagia / Tegang / Melankolis / Tenang | 57.1% / 33.9% / 6.3% / 2.7% |
| Korelasi terkuat | energy ↔ loudness (Pearson 0.65) |
| Popularity vs fitur audio terkuat | |rho| = 0.07 (sangat lemah) |
| Genre terbesar | pop 902, hip hop 744, rock 155 |

## Verifikasi (sudah dijalankan)

1. Notebook 01–04 dieksekusi berurutan dengan `jupyter nbconvert --execute`, tanpa error.
2. Assert kunci lulus: 1 lagu = 1 baris, tidak ada null, tidak ada `set()` di genre,
   joblib load ulang mengembalikan 3 tabel (1.926 / 3.562 / 835 baris).
3. Dashboard dites headless dengan `streamlit.testing.v1.AppTest`: 13 pemeriksaan
   lulus (semua tab, radar, heatmap Pearson & Spearman, filter tahun & popularity,
   pencarian data, unduh CSV).
4. Server sungguhan dites: `streamlit run app/app.py` (headless) mulai bersih,
   `/healthz` membalas 200.

## Opsi lanjutan (belum dikerjakan)

- [ ] Clustering lagu (KMeans) untuk rekomendasi/mood playlist
- [ ] Enrichment genre/harga dari dataset Steam lain
- [ ] Deploy ke Streamlit Community Cloud untuk portofolio
