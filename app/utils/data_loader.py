"""Satu-satunya tempat dashboard memuat dataset hasil proses.

app.py tidak membaca data mentah dan tidak melakukan cleaning. Semua pembersihan
ada di notebooks/02, feature engineering + penyimpanan di notebooks/03. Hasilnya
langsung dimuat dari data/clean/spotify_clean.joblib di sini.
"""

import ast
import os

import joblib
import streamlit as st

PROCESSED_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "clean", "spotify_clean.joblib"
)


def _ke_list_sungguhan(nilai):
    """CSV menyimpan list sebagai teks ('["rock", "pop"]'), joblib menyimpan list asli.

    Dashboard selalu butuh list sungguhan untuk filter multi-genre, jadi kedua
    format dinormalkan di sini.
    """
    if isinstance(nilai, (list, tuple, set)):
        return [str(x).strip() for x in nilai]
    if isinstance(nilai, str):
        teks = nilai.strip()
        if teks.startswith("[") and teks.endswith("]"):
            try:
                hasil = ast.literal_eval(teks)
                if isinstance(hasil, (list, tuple, set)):
                    return [str(x).strip() for x in hasil]
            except (ValueError, SyntaxError):
                pass
        return [x.strip() for x in teks.split(",") if x.strip()]
    return []


@st.cache_data(show_spinner=False)
def load_data() -> dict:
    """Kembalikan dict berisi DataFrame: songs, genres_long, artists."""
    if not os.path.exists(PROCESSED_PATH):
        st.error(
            "File `spotify_clean.joblib` belum ada. "
            "Jalankan notebook 01 sampai 04 di folder `notebooks/` secara berurutan "
            "(notebook 03 membuat berkas ini di `data/clean/`)."
        )
        st.stop()
    data = joblib.load(PROCESSED_PATH)
    if "songs" in data and "genre_list" in data["songs"].columns:
        data["songs"] = data["songs"].copy()
        data["songs"]["genre_list"] = data["songs"]["genre_list"].map(_ke_list_sungguhan)
    return data
