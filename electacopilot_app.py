import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURASI HALAMAN & BRANDING ---
st.set_page_config(
    page_title="ElectaCopilot | Digital War Room",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS untuk tema "Digital War Room" (Dark & Gold Accent)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    h1, h2, h3 { color: #d4af37 !important; }
    .stButton>button { background-color: #d4af37; color: black; font-weight: bold; border-radius: 8px; }
    .stChatMessage { border-radius: 12px; border: 1px solid #333; }
    [data-testid="stSidebar"] { background-color: #1c1f26; border-right: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SIDEBAR: SETUP & INPUT DATA ---
with st.sidebar:
    st.title("🛡️ ElectaCopilot Hub")
    st.caption("Your AI Political Advantage")
    st.divider()

    # --- PENANGANAN API KEY (SECRETS FIRST) ---
    # Mencoba mengambil kunci dari Streamlit Secrets (untuk deployment)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        st.success("✅ API Key terhubung aman.")
    else:
        # Fallback: Input manual jika dijalankan lokal tanpa secrets.toml
        api_key = st.text_input("⚠️ Masukkan Gemini API Key (Mode Lokal):", type="password")
        if not api_key:
             st.warning("Silakan masukkan API Key untuk memulai.")

    st.divider()
    st.subheader("📁 Knowledge Base")
    uploaded_csv = st.file_uploader("1. Upload Data Pemilu (CSV)", type="csv")
    uploaded_pdf = st.file_uploader("2. Upload Blueprint Strategi (PDF)", type="pdf")
    
    st.divider()
    st.subheader("⚙️ Operational Mode")
    status_mode = st.radio("Pilih Fokus Analisis:", 
                           ["🔍 Strategic Analysis", "🚨 Crisis Management", "🛡️ Guardian (Anti-Fraud)"])

# --- 3. LOGIKA BACKEND AI ---
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # Setup Model dengan Persona ElectaCopilot
        # Catatan: Untuk aplikasi RAG penuh, Anda perlu menambahkan logika
        # untuk membaca konten PDF/CSV dan mengirimnya bersama prompt.
        # Kode ini adalah kerangka dasar untuk koneksi API.
        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            system_instruction="""Anda adalah ElectaCopilot, Asisten Strategis Politik Senior. 
            Tugas Anda adalah memberikan analisis tajam berdasarkan data dan strategi pemenangan. 
            Gunakan tabel Markdown untuk menyajikan data angka. Bersikaplah profesional, rahasia, dan taktis."""
        )
    except Exception as e:
        st.error(f"Koneksi API Gagal: {e}")

# Inisialisasi Chat History di Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    # Pesan sambutan default
    st.session_state.chat_history.append({
        "role": "assistant", 
        "content": "Halo. Saya **ElectaCopilot**. Sistem siap. Data apa yang ingin kita bedah hari ini?"
    })

# --- 4. TAMPILAN UTAMA (SPLIT SCREEN LAYOUT) ---
col1, col2 = st.columns([1.3, 1], gap="medium")

# === PANEL KIRI: INTERFACE CHAT ===
with col1:
    st.subheader("💬 ElectaCopilot Command Center")
    
    # Container untuk chat messages agar bisa di-scroll
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input User
    if prompt := st.chat_input("Ketik perintah strategis Anda di sini..."):
        if not model:
            st.error("⚠️ Mohon masukkan API Key terlebih dahulu di sidebar.")
        else:
            # Tampilkan pesan user
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            # Proses AI
            with chat_container:
                with st.chat_message("assistant"):
                    with st.spinner("ElectaCopilot sedang menganalisis..."):
                        try:
                            # Mengirim prompt ke Gemini
                            response = model.generate_content(prompt)
                            full_response = response.text
                            st.markdown(full_response)
                            # Simpan respon ke history
                            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                        except Exception as e:
                            st.error(f"Terjadi kesalahan analisis: {e}")

# === PANEL KANAN: VISUALISASI DATA ===
with col2:
    st.subheader("📊 Live Data Evidence")
    
    if uploaded_csv:
        try:
            df = pd.read_csv(uploaded_csv)
            
            # Kartu Statistik Ringkas (Contoh)
            st.markdown("#### 📈 Snapshot Data")
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric(label="Total Baris Data", value=len(df))
            # (Anda bisa menambahkan metrik lain di sini sesuai kolom CSV Anda)
            
            st.divider()

            # Visualisasi Interaktif (Plotly)
            # Pastikan CSV Anda memiliki kolom 'Nama_Caleg' dan 'Suara_Caleg' untuk contoh ini bekerja
            if 'Nama_Caleg' in df.columns and 'Suara_Caleg' in df.columns:
                st.markdown("#### Top Perolehan Suara")
                # Mengambil 5 data teratas untuk demo chart
                top_df = df.nlargest(5, 'Suara_Caleg') if len(df) > 5 else df
                
                fig = px.bar(top_df, x='Nama_Caleg', y='Suara_Caleg',
                             color='Suara_Caleg', 
                             color_continuous_scale=px.colors.sequential.Redor_r, # Warna tema kemerahan/emas
                             template="plotly_dark",
                             title="Leaderboard Sementara")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
            
            # Preview Tabel Data Mentah
            with st.expander("🔍 Lihat Raw Data (Tabel)"):
                st.dataframe(df, use_container_width=True)

        except Exception as e:
             st.error(f"Gagal membaca CSV. Pastikan format file benar. Error: {e}")
    else:
        # Tampilan Placeholder jika belum ada data
        st.info("ℹ️ Menunggu input data CSV di sidebar untuk mengaktifkan panel visualisasi.")
        st.markdown("""
            <div style='text-align: center; color: gray; margin-top: 50px;'>
                <h3>Awaiting Data Stream...</h3>
                <p>Silakan unggah file hasil pemilu di sidebar.</p>
            </div>
        """, unsafe_allow_html=True)

    # Indikator Status di bagian bawah
    st.divider()
    st.caption(f"Sistem Mode Aktif: **{status_mode}**")
