"""Dashboard Lagu Populer Spotify — 2.000 lagu terpopuler 1998–2020.

Jalankan dari root project:
    streamlit run app/app.py

File ini HANYA untuk visualisasi dan filter UI. Cleaning ada di notebooks/02,
feature engineering + penyimpanan di notebooks/03. Setiap bagian dashboard adalah
satu fungsi, jadi file ini bisa dibaca dari atas ke bawah seperti daftar isi.
"""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from utils.data_loader import load_data

st.set_page_config(
    page_title="Dashboard Lagu Populer Spotify",
    page_icon=":material/music_note:",
    layout="wide",
)

# ------------------------------------------------------------------ konstanta
HIJAU, BIRU, ORANYE, UNGU, MERAH, ABU = "#1a7f37", "#0969da", "#bf8700", "#8250df", "#cf222e", "#57606a"

FITUR_AUDIO = ["danceability", "energy", "valence", "acousticness",
               "speechiness", "liveness", "instrumentalness"]
KOLOM_KORELASI = ["popularity", "danceability", "energy", "valence", "loudness",
                  "tempo", "duration_min", "acousticness", "speechiness",
                  "instrumentalness", "liveness", "explicit_int"]
KOLOM_SCATTER = FITUR_AUDIO + ["tempo", "loudness", "duration_min", "popularity"]

LABEL_FITUR = {
    "popularity": "Popularity", "danceability": "Danceability", "energy": "Energy",
    "valence": "Valence", "loudness": "Loudness", "tempo": "Tempo",
    "duration_min": "Durasi (menit)", "acousticness": "Acousticness",
    "speechiness": "Speechiness", "instrumentalness": "Instrumentalness",
    "liveness": "Liveness", "explicit_int": "Explicit",
}

MOODS = ["Bahagia & bersemangat", "Tegang & agresif", "Tenang & hangat", "Melankolis"]
WARNA_MOOD = {"Bahagia & bersemangat": HIJAU, "Tegang & agresif": MERAH,
              "Tenang & hangat": BIRU, "Melankolis": UNGU}

MIN_LAGU_GENRE = 10


# ------------------------------------------------------------- filter (cached)
@st.cache_data(show_spinner=False)
def terapkan_filter(tahun_awal: int, tahun_akhir: int, genre_terpilih: tuple,
                    lirik: str, min_popularity: int, hanya_popularity_valid: bool) -> pd.DataFrame:
    """Saring lagu. Filter genre memakai SELURUH genre lagu (multi-genre tetap terhitung)."""
    df = load_data()["songs"]
    mask = df["year"].between(tahun_awal, tahun_akhir) & (df["popularity"] >= min_popularity)
    if lirik == "Explicit":
        mask &= df["explicit"]
    elif lirik == "Non-explicit":
        mask &= ~df["explicit"]
    if hanya_popularity_valid:
        mask &= ~df["is_popularity_missing"]
    if genre_terpilih:
        pilih = set(genre_terpilih)
        mask &= df["genre_list"].apply(lambda daftar: bool(pilih.intersection(daftar)))
    return df[mask].copy()


@st.cache_data(show_spinner=False)
def genres_terfilter(tahun_awal: int, tahun_akhir: int, genre_terpilih: tuple,
                     lirik: str, min_popularity: int, hanya_popularity_valid: bool) -> pd.DataFrame:
    """Tabel lagu x genre dengan filter yang sama seperti tabel lagu."""
    gl = load_data()["genres_long"]
    mask = gl["year"].between(tahun_awal, tahun_akhir) & (gl["popularity"] >= min_popularity)
    if lirik == "Explicit":
        mask &= gl["explicit"]
    elif lirik == "Non-explicit":
        mask &= ~gl["explicit"]
    if hanya_popularity_valid:
        mask &= ~gl["is_popularity_missing"]
    if genre_terpilih:
        mask &= gl["genre"].isin(genre_terpilih)
    return gl[mask].copy()


def agregat_artis(df: pd.DataFrame) -> pd.DataFrame:
    """Agregat per artis dari lagu yang sudah difilter."""
    tabel = df.groupby("artist").agg(
        n_lagu=("song", "count"),
        rata_popularity=("popularity", "mean"),
        pop_tertinggi=("popularity", "max"),
    ).reset_index()
    return tabel


def bar_horizontal(df: pd.DataFrame, x: str, y: str, judul: str, warna=HIJAU, fmt=".2f") -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(cornerRadius=4)
        .encode(
            x=alt.X(f"{x}:Q", title=judul),
            y=alt.Y(f"{y}:N", sort="-x", title=None),
            color=alt.value(warna),
            tooltip=[y, alt.Tooltip(f"{x}:Q", format=fmt)],
        )
        .properties(height=380)
    )


# ------------------------------------------------------------------- sidebar
def sidebar_filters() -> dict:
    with st.sidebar:
        st.header("Filter")
        tahun = st.slider("Rentang tahun rilis", 1998, 2020, (1998, 2020))
        semua_genre = sorted(load_data()["genres_long"]["genre"].dropna().unique())
        genre = st.multiselect(
            "Genre lagu", semua_genre,
            help="Kosongkan untuk semua genre. Lagu multi-genre ikut terhitung di setiap genre yang dipilih.",
        )
        lirik = st.segmented_control("Lirik", ["Semua", "Explicit", "Non-explicit"], default="Semua")
        min_pop = st.slider(
            "Popularity minimum", 0, 90, 0,
            help="Popularity 0 berarti data popularity tidak tersedia (121 lagu di data penuh).",
        )
        pop_valid = st.checkbox("Abaikan lagu tanpa data popularity", value=False)
        st.caption("Semua grafik dan tabel mengikuti filter ini. Pilih genre untuk melihat "
                   "detail tiap genre di tab 'Genre & audio'.")
    return {
        "tahun_awal": int(tahun[0]), "tahun_akhir": int(tahun[1]),
        "genre_terpilih": tuple(genre), "lirik": lirik,
        "min_popularity": int(min_pop), "hanya_popularity_valid": pop_valid,
    }


# ------------------------------------------------------------------ ringkasan
def kpi_row(df: pd.DataFrame) -> None:
    with st.container(horizontal=True):
        st.metric("Total lagu", f"{len(df):,}", border=True)
        st.metric("Total artis", f"{df['artist'].nunique():,}", border=True)
        st.metric("Rentang tahun", f"{df['year'].min()}–{df['year'].max()}", border=True)
        st.metric("Popularity rata-rata", f"{df['popularity'].mean():.0f}", border=True,
                  help="Termasuk lagu tanpa data popularity (nilai 0).")
        st.metric("Tanpa data popularity", f"{df['is_popularity_missing'].mean():.0%}", border=True)


def tab_ringkasan(df: pd.DataFrame) -> None:
    kiri, kanan = st.columns(2)
    with kiri:
        with st.container(border=True):
            st.subheader("Lagu per tahun rilis")
            per_tahun = (df.groupby("year", as_index=False).size()
                         .rename(columns={"size": "jumlah lagu"}))
            st.area_chart(per_tahun, x="year", y="jumlah lagu", color=HIJAU,
                          alt="Jumlah lagu populer per tahun rilis dari 1998 sampai 2020")
    with kanan:
        with st.container(border=True):
            st.subheader("Sebaran popularity")
            bins = list(range(0, 100, 5))
            labels = [f"{b}–{b + 4}" for b in bins]
            kategori = pd.cut(df["popularity"], bins=bins + [100], labels=labels, right=False)
            his = (kategori.value_counts().sort_index()
                   .rename_axis("rentang popularity").reset_index(name="jumlah lagu"))
            st.bar_chart(his, x="rentang popularity", y="jumlah lagu", color=HIJAU,
                         alt="Sebaran popularity lagu, dengan puncak di rentang 0–4 karena 121 lagu tanpa data")

    kiri2, kanan2 = st.columns(2)
    with kiri2:
        with st.container(border=True):
            st.subheader("Mood lagu (valence × energy)")
            hitung = df["mood"].value_counts().reindex(MOODS).dropna()
            mood_df = hitung.rename_axis("mood").reset_index(name="jumlah lagu")
            chart = (
                alt.Chart(mood_df)
                .mark_bar(cornerRadius=4)
                .encode(
                    x=alt.X("jumlah lagu:Q", title="Jumlah lagu"),
                    y=alt.Y("mood:N", sort=MOODS, title=None),
                    color=alt.Color("mood:N", legend=None,
                                    scale=alt.Scale(domain=MOODS,
                                                    range=[WARNA_MOOD[m] for m in MOODS])),
                    tooltip=["mood", "jumlah lagu"],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, alt="Jumlah lagu per mood, terbanyak Bahagia & bersemangat")
    with kanan2:
        with st.container(border=True):
            st.subheader("Temuan utama (dari seluruh dataset)")
            st.info("**Populer bukan soal 'suara'.** Korelasi terkuat fitur audio dengan "
                    "popularity hanya |rho| = 0.07 — tidak ada formula ajaib.")
            st.info("**Lagu keras cenderung nyaring.** Pasangan berkorelasi terkuat: "
                    "energy ↔ loudness (r = 0.65).")
            st.info("**Mood didominasi bahagia-energik.** 57% lagu berada di kuadran "
                    "'Bahagia & bersemangat'.")


# ------------------------------------------------------------ genre & audio
def _lagu_dengan_genre(df: pd.DataFrame, genre: str) -> pd.DataFrame:
    return df[df["genre_list"].apply(lambda daftar: genre in daftar)]


def _detail_satu_genre(lagu: pd.DataFrame, genre: str) -> None:
    with st.container(horizontal=True):
        st.metric("Jumlah lagu", f"{len(lagu):,}")
        valid = lagu[~lagu["is_popularity_missing"]]
        rata_pop = valid["popularity"].mean() if not valid.empty else 0
        st.metric("Popularity rata-rata", f"{rata_pop:.0f}",
                  help="Hanya lagu yang punya data popularity (nilai 0 = tidak tersedia).")
        st.metric("Lagu explicit", f"{lagu['explicit'].mean():.0%}")
        hitung_mood = lagu["mood"].value_counts()
        if not hitung_mood.empty:
            st.metric("Mood dominan", hitung_mood.index[0],
                      help=f"{hitung_mood.iloc[0] / len(lagu):.0%} lagu berada di mood ini.")

    kiri, kanan = st.columns(2)
    with kiri:
        fitur_df = pd.DataFrame({
            "fitur": [LABEL_FITUR[f] for f in FITUR_AUDIO],
            "rata": [lagu[f].mean() for f in FITUR_AUDIO],
        })
        chart = (
            alt.Chart(fitur_df)
            .mark_bar(cornerRadius=4)
            .encode(
                x=alt.X("rata:Q", title="Rata-rata (0–1)", scale=alt.Scale(domain=[0, 1])),
                y=alt.Y("fitur:N", title=None),
                color=alt.value(HIJAU),
                tooltip=[alt.Tooltip("fitur:N", title="Fitur"),
                         alt.Tooltip("rata:Q", title="Rata-rata", format=".2f")],
            )
            .properties(height=230)
        )
        st.altair_chart(chart, alt=f"Rata-rata fitur audio lagu bergenre {genre}")
    with kanan:
        top = lagu.nlargest(5, "popularity")[["song", "artist", "year", "popularity", "mood"]]
        st.dataframe(
            top,
            column_config={
                "song": st.column_config.TextColumn("Lagu"),
                "artist": st.column_config.TextColumn("Artis"),
                "year": st.column_config.NumberColumn("Tahun", format="%d"),
                "popularity": st.column_config.NumberColumn("Popularity", format="%d"),
                "mood": st.column_config.TextColumn("Mood"),
            },
            hide_index=True, height=230,
            alt=f"Lima lagu terpopuler bergenre {genre}",
        )


def tab_genre(df: pd.DataFrame, f: dict) -> None:
    genre_terpilih = [g for g in f["genre_terpilih"] if g]
    fitur = st.selectbox("Pilih fitur audio", FITUR_AUDIO, format_func=lambda f_: LABEL_FITUR[f_],
                         key="fitur_genre")

    if genre_terpilih:
        st.subheader(f"Detail {len(genre_terpilih)} genre yang kamu pilih")
        st.caption("Lagu dengan beberapa genre tampil di blok setiap genrenya — begi"
                   "tulah data multi-genre bekerja, jadi total antar-blok bisa lebih "
                   "besar dari jumlah lagu.")

        baris = []
        for genre in genre_terpilih:
            lagu = _lagu_dengan_genre(df, genre)
            if not lagu.empty:
                baris.append({"genre": genre, "rata": lagu[fitur].mean(), "n_lagu": len(lagu)})
        if baris:
            perbandingan = pd.DataFrame(baris).sort_values("rata", ascending=False)
            chart = bar_horizontal(perbandingan, "rata", "genre",
                                   f"Rata-rata {LABEL_FITUR[fitur].lower()} per genre terpilih")
            st.altair_chart(chart, alt=f"Perbandingan rata-rata {fitur} antar genre terpilih")
            st.caption("Angka di kanan batang = rata-rata fitur; arahkan kursor ke batang "
                       "untuk melihat jumlah lagu tiap genre.")

        for i, genre in enumerate(genre_terpilih):
            lagu = _lagu_dengan_genre(df, genre)
            if lagu.empty:
                st.caption(f":material/search_off: Genre **{genre}** tidak punya lagu pada "
                           "filter yang aktif — coba longgarkan filter tahun atau popularity.")
                continue
            with st.expander(f":material/album: {genre} — {len(lagu):,} lagu",
                             expanded=(i == 0)):
                _detail_satu_genre(lagu, genre)
    else:
        st.info("Pilih satu atau beberapa **genre** di sidebar, lalu bagian ini menampilkan "
                "detail tiap genre: jumlah lagu, popularity, proporsi explicit, mood dominan, "
                "profil fitur audio, dan lagu terpopuler.")

    st.divider()
    st.subheader("Sidik jari audio per genre")
    st.caption("Setiap sumbu = rata-rata fitur audio (0–1) pada genre utama lagu. "
               "Garis putus-putus abu-abu = rata-rata semua lagu sebagai pembanding.")

    hitung_genre = df["primary_genre"].value_counts()
    opsi_genre = hitung_genre.index.tolist()
    default_genre = [g for g in opsi_genre if hitung_genre[g] >= MIN_LAGU_GENRE][:3]

    pilihan = st.multiselect("Genre yang ditampilkan (maks. 5)", opsi_genre,
                             default=default_genre, max_selections=5)

    series = []
    if pilihan:
        profil = df.groupby("primary_genre")[FITUR_AUDIO].mean()
        for genre in pilihan:
            if genre not in profil.index:
                continue
            series.append({
                "value": [round(float(profil.loc[genre, f]), 3) for f in FITUR_AUDIO],
                "name": genre,
                "areaStyle": {"opacity": 0.10},
            })
    rata_semua = [round(float(df[f].mean()), 3) for f in FITUR_AUDIO]
    series.append({
        "value": rata_semua, "name": "Semua lagu",
        "lineStyle": {"type": "dashed", "width": 2},
        "itemStyle": {"color": ABU},
    })
    spec = {
        "tooltip": {},
        "legend": {"top": 0, "type": "scroll"},
        "radar": {"indicator": [{"name": LABEL_FITUR[f], "max": 1} for f in FITUR_AUDIO]},
        "series": [{"type": "radar", "data": series, "symbol": "none"}],
    }
    st.echarts_chart(spec, height=430,
                     alt="Radar chart rata-rata fitur audio per genre dibanding rata-rata semua lagu")

    st.divider()
    st.subheader("Rata-rata fitur per genre")
    st.caption("Dengan genre utama (genre pertama tiap lagu), jadi tiap lagu terhitung tepat sekali.")
    agregat = df.groupby("primary_genre").agg(n_lagu=("song", "count"), rata=(fitur, "mean"))
    agregat = agregat[agregat["n_lagu"] >= MIN_LAGU_GENRE].sort_values("rata", ascending=False)
    if agregat.empty:
        st.info(f"Tidak ada genre dengan minimal {MIN_LAGU_GENRE} lagu pada filter ini.")
        return
    st.caption(f"Hanya genre dengan minimal {MIN_LAGU_GENRE} lagu yang ditampilkan "
               "(rata-rata genre dengan sedikit lagu tidak stabil).")
    chart = bar_horizontal(agregat.reset_index(), "rata", "primary_genre",
                           f"Rata-rata {LABEL_FITUR[fitur].lower()}")
    st.altair_chart(chart, alt=f"Rata-rata {fitur} per genre utama")


# -------------------------------------------------------------- artis & lagu
def tab_artis(df: pd.DataFrame) -> None:
    st.subheader("Artis paling sering muncul di daftar")
    kiri, kanan = st.columns([1, 2])
    with kiri:
        metrik = st.segmented_control(
            "Urutkan berdasarkan",
            ["Jumlah lagu", "Rata-rata popularity", "Popularity tertinggi"],
            default="Jumlah lagu",
        )
    with kanan:
        top_n = st.slider("Jumlah artis", 5, 20, 10)

    kolom_metrik = {"Jumlah lagu": "n_lagu", "Rata-rata popularity": "rata_popularity",
                    "Popularity tertinggi": "pop_tertinggi"}[metrik]
    tabel = agregat_artis(df)
    if metrik == "Rata-rata popularity":
        tabel = tabel[tabel["n_lagu"] >= 3]
        st.caption("Hanya artis dengan minimal 3 lagu supaya rata-ratanya stabil.")
    top = tabel.nlargest(top_n, kolom_metrik).sort_values(kolom_metrik)
    if top.empty:
        st.info("Tidak ada artis yang memenuhi syarat pada filter ini.")
    else:
        chart = bar_horizontal(top, kolom_metrik, "artist", metrik)
        st.altair_chart(chart, alt=f"Artis dengan {metrik.lower()} tertinggi")

    st.divider()
    st.subheader("Proporsi lagu explicit per genre")
    eks = df.groupby("primary_genre").agg(n_lagu=("song", "count"),
                                          pct_explicit=("explicit", "mean"))
    eks = eks[eks["n_lagu"] >= 20].sort_values("pct_explicit", ascending=False)
    if eks.empty:
        st.info("Tidak ada genre dengan minimal 20 lagu pada filter ini.")
    else:
        st.caption("Hip hop jauh di atas genre lain untuk lagu explicit.")
        chart = bar_horizontal(eks.reset_index(), "pct_explicit", "primary_genre",
                               "Proporsi lagu explicit", warna=ORANYE, fmt=".0%")
        st.altair_chart(chart, alt="Proporsi lagu explicit per genre, tertinggi pada hip hop")

    st.divider()
    st.subheader("Lagu dengan popularity tertinggi")
    top_lagu = df.nlargest(15, "popularity")[
        ["artist", "song", "year", "popularity", "primary_genre", "mood", "tempo", "duration_min"]
    ]
    st.dataframe(
        top_lagu,
        column_config={
            "artist": st.column_config.TextColumn("Artis"),
            "song": st.column_config.TextColumn("Lagu"),
            "year": st.column_config.NumberColumn("Tahun", format="%d"),
            "popularity": st.column_config.NumberColumn("Popularity", format="%d"),
            "primary_genre": st.column_config.TextColumn("Genre utama"),
            "mood": st.column_config.TextColumn("Mood"),
            "tempo": st.column_config.NumberColumn("Tempo (BPM)", format="%.0f"),
            "duration_min": st.column_config.NumberColumn("Durasi (menit)", format="%.2f"),
        },
        hide_index=True,
        height=430,
        alt="Lima belas lagu dengan popularity tertinggi pada filter aktif",
    )


# ------------------------------------------------------------------ korelasi
def tab_korelasi(df: pd.DataFrame) -> None:
    if len(df) < 3:
        st.info("Data terlalu sedikit setelah difilter untuk menghitung korelasi.")
        return

    metode = st.segmented_control("Metode korelasi", ["Pearson", "Spearman"], default="Pearson",
                                  help="Spearman memakai peringkat sehingga lebih tahan "
                                       "terhadap distribusi yang miring.")
    st.caption("Kunci membaca: nilai dekat 1 = searah kuat, dekat -1 = berlawanan arah kuat, "
               "dekat 0 = tidak berhubungan. **Korelasi bukan sebab-akibat.**")

    corr = df[KOLOM_KORELASI].corr(method=metode.lower())
    corr_berlabel = corr.rename(index=LABEL_FITUR, columns=LABEL_FITUR)
    corr_long = (corr_berlabel.reset_index(names="fitur_1")
                 .melt(id_vars="fitur_1", var_name="fitur_2", value_name="korelasi"))
    urutan = list(corr_berlabel.columns)

    base = alt.Chart(corr_long).encode(
        x=alt.X("fitur_1:N", title=None, sort=urutan),
        y=alt.Y("fitur_2:N", title=None, sort=urutan[::-1]),
    )
    heatmap = (
        base.mark_rect()
        .encode(color=alt.Color("korelasi:Q", scale=alt.Scale(scheme="redblue", domain=[-1, 1]),
                                title="r"))
    )
    angka = (
        base.mark_text(fontSize=9)
        .encode(
            text=alt.Text("korelasi:Q", format=".2f"),
            color=alt.condition("abs(datum.korelasi) > 0.5",
                                alt.value("#ffffff"), alt.value("#1f2328")),
        )
    )
    st.altair_chart(heatmap + angka,
                    alt=f"Heatmap korelasi {metode} antar fitur lagu",
                    width="content")

    triang = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack()
    if not triang.dropna().empty:
        terkuat = triang.abs().sort_values(ascending=False).head(3)
        baris = ", ".join(
            f"**{LABEL_FITUR[a]} ↔ {LABEL_FITUR[b]}** (r = {triang[(a, b)]:+.2f})"
            for a, b in terkuat.index
        )
        st.info(f"Pasangan berkorelasi terkuat: {baris}. "
                "Catatan: 121 lagu memiliki popularity 0 (tanpa data), yang sedikit "
                "melemahkan korelasi apa pun yang melibatkan popularity.")

    st.divider()
    st.subheader("Eksplorasi hubungan dua fitur")
    col1, col2 = st.columns(2)
    with col1:
        sumbu_x = st.selectbox("Sumbu X", KOLOM_SCATTER, format_func=lambda f: LABEL_FITUR[f],
                               key="scatter_x")
    with col2:
        sumbu_y = st.selectbox("Sumbu Y", KOLOM_SCATTER, index=1,
                               format_func=lambda f: LABEL_FITUR[f], key="scatter_y")
    warna = st.segmented_control("Warna titik", ["Popularity", "Mood", "Tanpa warna"],
                                 default="Popularity")

    if warna == "Popularity":
        encode_warna = alt.Color("popularity:Q", scale=alt.Scale(scheme="viridis"),
                                 title="Popularity")
    elif warna == "Mood":
        encode_warna = alt.Color("mood:N", scale=alt.Scale(domain=MOODS,
                                                           range=[WARNA_MOOD[m] for m in MOODS]))
    else:
        encode_warna = alt.value(ABU)

    scatter = (
        alt.Chart(df)
        .mark_circle(size=36, opacity=0.6)
        .encode(
            x=alt.X(f"{sumbu_x}:Q", title=LABEL_FITUR[sumbu_x]),
            y=alt.Y(f"{sumbu_y}:Q", title=LABEL_FITUR[sumbu_y]),
            color=encode_warna,
            tooltip=[alt.Tooltip("song:N", title="Lagu"),
                     alt.Tooltip("artist:N", title="Artis"),
                     alt.Tooltip("year:Q", title="Tahun", format="%d"),
                     alt.Tooltip("popularity:Q", title="Popularity", format="%d")],
        )
        .properties(height=430)
        .interactive()
    )
    st.altair_chart(scatter, alt=f"Sebaran {sumbu_x} versus {sumbu_y} per lagu")


# ---------------------------------------------------------------------- data
def _mask_cari(view: pd.DataFrame, kueri: str) -> pd.Series:
    mask = pd.Series(False, index=view.index)
    for kolom in ("song", "artist", "genre", "primary_genre"):
        if kolom in view.columns:
            mask |= view[kolom].fillna("").astype(str).str.contains(kueri, case=False, regex=False)
    return mask


def tab_data(df: pd.DataFrame, f: dict) -> None:
    st.subheader("Telusuri dataset hasil proses")
    st.caption("Tabel mengikuti filter sidebar. Bisa dicari, diurutkan (klik header kolom), "
               "dan diunduh sebagai CSV.")

    dataset = st.selectbox("Tabel", ["Per lagu", "Per lagu × genre", "Per artis"])
    if dataset == "Per lagu":
        view = df
        kolom_default = ["artist", "song", "year", "popularity", "primary_genre",
                         "mood", "tempo", "duration_min", "explicit"]
        nama_berkas = "spotify_lagu"
    elif dataset == "Per lagu × genre":
        view = genres_terfilter(f["tahun_awal"], f["tahun_akhir"], f["genre_terpilih"],
                                f["lirik"], f["min_popularity"], f["hanya_popularity_valid"])
        kolom_default = ["artist", "song", "genre", "year", "popularity", "mood"]
        nama_berkas = "spotify_lagu_genre"
    else:
        view = agregat_artis(df).sort_values("n_lagu", ascending=False)
        kolom_default = ["artist", "n_lagu", "rata_popularity", "pop_tertinggi"]
        nama_berkas = "spotify_artis"

    kiri, kanan = st.columns([1, 2])
    with kiri:
        kueri = st.text_input("Cari (lagu, artis, atau genre)", placeholder="mis. Rihanna atau pop")
    with kanan:
        st.write("")

    if kueri.strip():
        view = view[_mask_cari(view, kueri.strip())]

    kolom_tersedia = view.columns.tolist()
    kolom = st.multiselect("Kolom ditampilkan", kolom_tersedia, default=kolom_default)
    shown = view[kolom] if kolom else view

    config = {
        "artist": st.column_config.TextColumn("Artis"),
        "song": st.column_config.TextColumn("Lagu"),
        "genre": st.column_config.TextColumn("Genre"),
        "primary_genre": st.column_config.TextColumn("Genre utama"),
        "key_name": st.column_config.TextColumn("Nada (key)"),
        "mode_name": st.column_config.TextColumn("Mode"),
        "mood": st.column_config.TextColumn("Mood"),
        "year": st.column_config.NumberColumn("Tahun", format="%d"),
        "popularity": st.column_config.NumberColumn("Popularity", format="%d"),
        "tempo": st.column_config.NumberColumn("Tempo (BPM)", format="%.1f"),
        "loudness": st.column_config.NumberColumn("Loudness (dB)", format="%.2f"),
        "duration_min": st.column_config.NumberColumn("Durasi (menit)", format="%.2f"),
        "duration_ms": st.column_config.NumberColumn("Durasi (ms)", format="%d"),
        "n_lagu": st.column_config.NumberColumn("Jumlah lagu", format="%d"),
        "rata_popularity": st.column_config.NumberColumn("Rata-rata popularity", format="%.1f"),
        "pop_tertinggi": st.column_config.NumberColumn("Popularity tertinggi", format="%d"),
        "explicit": st.column_config.CheckboxColumn("Explicit"),
        "is_popularity_missing": st.column_config.CheckboxColumn("Popularity kosong"),
        "is_outlier": st.column_config.CheckboxColumn("Outlier"),
        "n_genres": st.column_config.NumberColumn("Jumlah genre", format="%d"),
    }
    for fitur in FITUR_AUDIO:
        config[fitur] = st.column_config.NumberColumn(LABEL_FITUR[fitur], format="%.2f")

    st.dataframe(shown, column_config={k: v for k, v in config.items() if k in shown.columns},
                 hide_index=True, height=460,
                 alt=f"Tabel data {dataset.lower()} sesuai filter aktif")

    st.download_button(
        "Unduh CSV (sesuai filter & kolom)",
        shown.to_csv(index=False).encode("utf-8"),
        file_name=f"{nama_berkas}.csv",
        mime="text/csv",
    )

    with st.expander("Statistik ringkas kolom numerik"):
        num = shown.select_dtypes("number")
        if num.empty:
            st.write("Tidak ada kolom numerik pada tampilan ini.")
        else:
            st.dataframe(num.describe().T.round(2), alt="Statistik ringkas kolom numerik")


# ----------------------------------------------------------------------- main
def main() -> None:
    st.title("Dashboard Lagu Populer Spotify")
    st.caption("2.000 lagu terpopuler 1998–2020 beserta fitur audio Spotify. "
               "Data dibersihkan dan diolah di notebook 01–04; dashboard ini hanya menampilkan hasilnya.")

    f = sidebar_filters()
    df = terapkan_filter(
        f["tahun_awal"], f["tahun_akhir"], f["genre_terpilih"],
        f["lirik"], f["min_popularity"], f["hanya_popularity_valid"],
    )

    if df.empty:
        st.warning("Tidak ada lagu yang cocok dengan filter. Coba lebarkan rentang tahun, "
                   "kecilkan popularity minimum, haus beberapa genre di sidebar, atau ceklis "
                   "ulang filter lirik.")
        st.stop()

    kpi_row(df)
    st.divider()

    t1, t2, t3, t4, t5 = st.tabs(
        ["Ringkasan", "Genre & audio", "Artis & lagu", "Korelasi", "Data"]
    )
    with t1:
        tab_ringkasan(df)
    with t2:
        tab_genre(df, f)
    with t3:
        tab_artis(df)
    with t4:
        tab_korelasi(df)
    with t5:
        tab_data(df, f)

    st.caption("Sumber data: `data/raw/songs_normalize.csv` (2.000 lagu). "
               "Hasil olahan: `data/clean/spotify_clean.joblib` (lihat notebook 03).")


if __name__ == "__main__":
    main()
