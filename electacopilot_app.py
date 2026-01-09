import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import json
import os

# --- 1. KONFIGURASI SISTEM & INSTRUKSI ---
st.set_page_config(page_title="ElectaCopilot", page_icon="🛡️", layout="wide")

# Masukkan System Instruction Anda di sini agar terpusat
SYSTEM_INSTRUCTION = """
You are "ElectaCopilot", a Strategic Political AI Consultant for the Riau region. 
Your persona is a Senior Political Consultant: sharp, secretive, professional, and winning-oriented.
You are in a "Digital War Room".

You have access to three key data sources (Knowledge Base):
1. ELECTION_DATA_CSV: 2024 Election results for Dapil Riau.
2. STRATEGY_BLUEPRINT (PDF Content - Riau Specific).
3. POLITICAL_MARKETING_STRATEGY (PDF Content - General Theory).

RESPONSE FORMAT:
Your response must be in valid JSON format ONLY, structured as follows:
{
  "active_view": "string (DASHBOARD|CHAT|MAP)",
  "current_status": "string (SAFE|CRITICAL|ANOMALY)",
  "text_response": "string (The actual Markdown formatted response to the user)",
  "data_payload": "object (Optional: data for charts)",
  "suggested_ui_action": "string (Short button label)"
}

OPERATIONAL RULES:
- If asked "How is Party X positioned?", look at CSV, calculate share, apply SWOT and STP/4P analysis.
- ALWAYS display data in Markdown Tables.
- If margin < 2% or competitor gain is high, set current_status to CRITICAL.
- Reference specific concepts like "Push Marketing", "Floating Mass", etc.
"""

# --- 2. MANAJEMEN USER (DATABASE LOKAL) ---
USER_DB_FILE = "users_db.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    # Default Akun
    return {"admin": {"password": "admin123", "role": "admin"}, 
            "user1": {"password": "user123", "role": "member"}}

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

# Inisialisasi Session State
if "users" not in st.session_state: st.session_state.users = load_users()
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "messages" not in st.session_state: st.session_state.messages = []

# --- 3. CUSTOM CSS (AESTHETIC CHATGPT/GEMINI) ---
st.markdown("""
    <style>
    .stApp { background-color: #1a1a1a; color: #ececec; }
    .stChatMessage { border-bottom: 1px solid #333; padding: 25px 5%; background-color: transparent !important; }
    .stChatInputContainer { padding-bottom: 30px; }
    h1, h2, h3 { color: #d4af37 !important; }
    .stButton>button { border-radius: 8px; font-size: 12px; height: 30px; }
    /* Table Styling */
    .stMarkdown table { width: 100%; border-collapse: collapse; }
    .stMarkdown th { background-color: #333; color: #d4af37; padding: 8px; }
    .stMarkdown td { border: 1px solid #444; padding: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. KOMPONEN LOGIN ---
def login_ui():
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>🛡️ ElectaCopilot Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("Login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk ke War Room"):
                db = st.session_state.users
                if u in db and db[u]["password"] == p:
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.session_state.role = db[u]["role"]
                    st.rerun()
                else:
                    st.error("Kredensial salah.")

# --- 5. PANEL ADMIN ---
def admin_panel():
    st.title("👥 Manajemen Akun Member")
    users = st.session_state.users
    
    # List User
    df = pd.DataFrame([{"User": k, "Role": v["role"]} for k, v in users.items()])
    st.table(df)
    
    # Form Tambah/Edit/Reset
    with st.expander("Kelola Akun"):
        target = st.selectbox("Pilih Akun", list(users.keys()))
        new_p = st.text_input("Password Baru", type="password")
        new_r = st.selectbox("Role", ["member", "admin"], index=0 if users[target]["role"] == "member" else 1)
        
        c1, c2 = st.columns(2)
        if c1.button("Update Akun"):
            st.session_state.users[target] = {"password": new_p if new_p else users[target]["password"], "role": new_r}
            save_users(st.session_state.users)
            st.success("Berhasil diperbarui.")
        if c2.button("Hapus Akun") and target != "admin":
            del st.session_state.users[target]
            save_users(st.session_state.users)
            st.rerun()

# --- 6. CORE CHAT ENGINE ---
def chat_room():
    st.title("💬 Strategy Command Center")
    
    # Inisialisasi API Gemini
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("API Key Hilang! Cek Streamlit Secrets.")
        return

    genai.configure(api_key=api_key)
    # Memanggil Model Gemini 3 Pro Preview
    model = genai.GenerativeModel(
        model_name="gemini-3-pro-preview",
        system_instruction=SYSTEM_INSTRUCTION
    )

    # Menampilkan Pesan
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Baris tombol Copy & Delete
            col_a, col_b, _ = st.columns([0.05, 0.05, 0.9])
            if col_a.button("📋", key=f"cp_{i}"):
                st.code(msg["content"]) # Code block memberikan tombol copy otomatis
            if col_b.button("🗑️", key=f"dl_{i}"):
                st.session_state.messages.pop(i)
                st.rerun()

    # Chat Input
    if prompt := st.chat_input("Tanyakan strategi kemenangan..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                res = model.generate_content(prompt)
                # Parsing respons JSON dari AI
                data = json.loads(res.text)
                txt = data.get("text_response", "Gagal memproses narasi.")
                status = data.get("current_status", "SAFE")
                
                # Tampilkan teks
                st.markdown(txt)
                
                # Jika Kritis, tampilkan alert merah
                if status == "CRITICAL":
                    st.error("🚨 PERINGATAN: Wilayah/Kondisi ini terdeteksi KRITIS.")
                
                st.session_state.messages.append({"role": "assistant", "content": txt})
            except Exception as e:
                # Fallback jika AI tidak menjawab dalam JSON yang valid
                st.markdown(res.text)
                st.session_state.messages.append({"role": "assistant", "content": res.text})

# --- 7. NAVIGASI UTAMA ---
if not st.session_state.authenticated:
    login_ui()
else:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2829/2829800.png", width=100)
        st.title("ElectaCopilot")
        st.write(f"Logged in: **{st.session_state.username}**")
        st.divider()
        
        menu = ["Chat Room", "Data Analytics"]
        if st.session_state.role == "admin":
            menu.append("Admin Panel")
            
        choice = st.radio("Menu", menu)
        
        if st.button("Log Out"):
            st.session_state.authenticated = False
            st.rerun()

    if choice == "Chat Room":
        chat_room()
    elif choice == "Data Analytics":
        st.title("📊 Data Analytics Hub")
        csv_file = st.file_uploader("Upload CSV Pemilu Terbaru", type="csv")
        if csv_file:
            df = pd.read_csv(csv_file)
            st.dataframe(df, use_container_width=True)
            # Contoh grafik otomatis
            if "Suara_Total" in df.columns:
                fig = px.bar(df, x=df.columns[0], y="Suara_Total", template="plotly_dark")
                st.plotly_chart(fig)
    elif choice == "Admin Panel":
        admin_panel()
