# Spotify Songs — Data Analyst Project

https://project-songanalyst-dhaval.streamlit.app/

Analisis **2.000 lagu terpopuler (1998–2020)** beserta fitur audio Spotify
(danceability, energy, valence, tempo, dll.): dari pemahaman data, pembersihan,
feature engineering, EDA + heatmap korelasi, storytelling, sampai dashboard
Streamlit interaktif.

## Alur pengerjaan

| # | Notebook / Berkas | Isi |
|---|---|---|
| 1 | `notebooks/01_data_understanding.ipynb` | Mengenal data: tipe kolom, statistik, masalah kualitas, pertanyaan analitis |
| 2 | `notebooks/02_data_cleaning.ipynb` | Rapikan `set()` di genre, pecah multi-genre, buang duplikat, tandai popularity 0, simpan `songs_clean.csv` |
| 3 | `notebooks/03_feature_engineering.ipynb` | Fitur turunan (`decade`, `mood`, band, `key_name`, outlier), tabel `genres_long` & `artists`, **simpan CSV + joblib** |
| 4 | `notebooks/04_eda_korelasi.ipynb` | EDA, profil genre (radar), tren per dekade, **heatmap Pearson + Spearman**, insight |
| 5 | `notebooks/05_data_storytelling.ipynb` | **Storytelling**: pola Hook→Angka→Makna→Rekomendasi, 3 cerita utuh + naskah 30 detik |
| 6 | `app/app.py` | Dashboard Streamlit 5 tab: Ringkasan, Genre & audio, Artis & lagu, Korelasi, Data |

## Struktur

```
project/
├── data/
│   ├── raw/songs_normalize.csv          # data asli (read-only, jangan diubah)
│   └── clean/
│       ├── songs_clean.csv              # hasil cleaning (notebook 02)
│       ├── songs_final.csv              # cleaning + feature engineering (notebook 03)
│       ├── genres_long.csv              # 1 baris = 1 lagu x 1 genre
│       ├── artists.csv                  # agregat per artis
│       └── spotify_clean.joblib         # dict ketiga tabel -> sumber dashboard
├── notebooks/                           # 5 notebook berurutan (sudah dieksekusi + ada outputnya)
│   └── lihat daftar di tabel "Alur pengerjaan"
├── app/
│   ├── app.py                           # dashboard (hanya visualisasi + filter UI)
│   └── utils/data_loader.py             # muat joblib dengan @st.cache_data
├── .streamlit/config.toml               # tema & konfigurasi tampilan
├── docs/plan.md                         # prompt awal + ringkasan keputusan
└── requirements.txt
```

## Cara menjalankan

```bash
# 1. Install dependency (sekali saja)
pip install -r requirements.txt

# 2. Jalankan notebook 01 -> 05 berurutan dari folder notebooks/
#    (notebook 03 yang membuat data/clean/spotify_clean.joblib)

# 3. Jalankan dashboard dari folder root project:
streamlit run app/app.py
```

Dashboard membaca `data/clean/spotify_clean.joblib`. Jika berkas itu belum ada, app
otomatis menampilkan instruksi untuk menjalankan notebook 03 lebih dulu.

## Fitur dashboard

- **Filter sidebar**: rentang tahun, genre (bisa beberapa sekaligus), lirik
  (explicit/non-explicit), popularity minimum, dan opsi "abaikan lagu tanpa data
  popularity". Semua grafik & tabel mengikuti filter ini.
- **Detail per genre**: pilih genre di sidebar → tab **Genre & audio** menampilkan
  untuk **tiap genre** yang dipilih: jumlah lagu, rata-rata popularity, proporsi
  explicit, mood dominan, profil 7 fitur audio, dan 5 lagu terpopulernya.
- **5 tab**: Ringkasan (KPI, lagu per tahun, sebaran popularity & mood),
  Genre & audio (radar + detail per genre), Artis & lagu, Korelasi
  (heatmap Pearson/Spearman + eksplorasi scatter), Data (tabel, pencarian, unduh CSV).

Catatan: filter genre memakai **seluruh genre lagu** (multi-genre tetap terhitung),
seperti tabel `genres_long` di notebook 03 — jadi jumlah lagu per genre bisa
berjumlah lebih besar dari total lagu unik.

## Ringkasan insight (hasil notebook 04)

1. **Tidak ada "formula ajaib" untuk populer** — korelasi terkuat fitur audio dengan
   popularity hanya |rho| = 0.07 (energy & valence).
2. **Energy ↔ loudness** adalah pasangan berkorelasi terkuat (Pearson r = 0.65) —
   ciri khas era "loudness war".
3. **Tren 1998–2020:** lagu makin pendek (4.21 → 3.63 menit) dan sedikit lebih keras
   (loudness −6.07 → −5.46 dB); acousticness menurun.
4. **Dua genre menutupi 85% data:** pop (902) dan hip hop (744) dari 1.926 lagu.
5. **Hip hop paling eksplisit (55%)**, versus rock 8% dan pop 10%; secara keseluruhan
   27.7% lagu eksplisit dan naik tiap dekade.
6. **Mood didominasi "Bahagia & bersemangat" (57%)**; kuadran "Tenang & hangat"
   paling jarang (2.7%).
7. **Speechiness berkorelasi dengan explicit** (Spearman 0.39).
8. **Artis dengan lagu terbanyak belum tentu yang terpopuler** (Rihanna 23 lagu vs
   Eminem rata-rata popularity tertinggi di top-10).

## Keputusan penting (kenapa begitu)

- **`data/clean` adalah kontrak tunggal**: `app.py` tidak pernah membaca data mentah
  atau melakukan cleaning. Perubahan logika cukup di notebook, lalu regenerate.
- **`popularity = 0` ditandai, bukan diimputasi** (`is_popularity_missing`, 121 lagu)
  — menebak popularity = membuat data palsu. Dashboard punya checkbox untuk
  mengecualikannya.
- **Multi-genre tidak dobel hitung**: `primary_genre` untuk statistik per-lagu,
  `genres_long` untuk statistik per-genre.
- **Outlier hanya ditandai** (`is_outlier`), tidak dihapus.
- **Spearman disertakan bersama Pearson** karena sebaran popularity/durasi miring.
- **Duplikat**: 59 duplikat persis dibuang; untuk pasangan `artist`+`song` dengan
  metadata berbeda, disimpan yang popularity tertinggi (2000 → 1.926 lagu).

## Keterbatasan data

- Tidak ada info streaming, tanggal rilis presisi, harga, label, atau lirik.
- 121 lagu (6.3%) tanpa data popularity.
- Genre kecil (< 10 lagu) kurang representatif — sudah diberi penanda di dashboard.

## Teknologi

pandas · numpy · matplotlib · seaborn (notebook) · **streamlit** + **altair** +
echarts radar (dashboard) · joblib (penyimpanan artefak)
