import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import json
import os

# --- 1. KONFIGURASI DASAR & SESSION STATE ---
st.set_page_config(page_title="ElectaCopilot SR", page_icon="🛡️", layout="wide")

# Inisialisasi Database User Sederhana (Gunakan file JSON untuk persistensi)
USER_DB_FILE = "users_db.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    return {"admin": {"password": "admin123", "role": "admin"}, 
            "user1": {"password": "user123", "role": "member"}}

def save_users(users):
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

if "users" not in st.session_state:
    st.session_state.users = load_users()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. STYLE CSS (WAR ROOM AESTHETIC) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .copy-text { background-color: #1c1f26; border: 1px solid #333; padding: 10px; border-radius: 5px; }
    h1, h2, h3 { color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INTERFACE LOGIN ---
def login_interface():
    st.markdown("<h1 style='text-align: center;'>🛡️ ElectaCopilot Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("Login Form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                users = st.session_state.users
                if username in users and users[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = users[username]["role"]
                    st.success(f"Selamat datang, {username}!")
                    st.rerun()
                else:
                    st.error("Username atau Password salah.")

# --- 4. INTERFACE ADMIN (MANAJEMEN MEMBER) ---
def admin_panel():
    st.title("👥 Admin Control Panel")
    st.divider()
    
    # Fitur: Tambah Member Baru
    with st.expander("➕ Tambah Member Baru"):
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        new_role = st.selectbox("Role", ["member", "admin"])
        if st.button("Simpan Member"):
            if new_user and new_pass:
                st.session_state.users[new_user] = {"password": new_pass, "role": new_role}
                save_users(st.session_state.users)
                st.success(f"User {new_user} berhasil ditambahkan.")
                st.rerun()

    # Fitur: Daftar & Edit Member
    st.subheader("Daftar Member Aplikasi")
    users = st.session_state.users
    user_list = []
    for u, data in users.items():
        user_list.append({"Username": u, "Role": data["role"]})
    
    df_users = pd.DataFrame(user_list)
    st.table(df_users)

    # Edit / Reset Member
    target_user = st.selectbox("Pilih Member untuk dikelola:", list(users.keys()))
    col_edit1, col_edit2 = st.columns(2)
    
    with col_edit1:
        new_password = st.text_input("Reset Password ke:", type="password")
        if st.button("Update Password"):
            st.session_state.users[target_user]["password"] = new_password
            save_users(st.session_state.users)
            st.success(f"Password {target_user} diperbarui.")

    with col_edit2:
        if st.button("🚨 Hapus Member"):
            if target_user != "admin": # Melindungi akun admin utama
                del st.session_state.users[target_user]
                save_users(st.session_state.users)
                st.warning(f"User {target_user} telah dihapus.")
                st.rerun()
            else:
                st.error("Admin utama tidak bisa dihapus.")

# --- 5. INTERFACE CHAT UTAMA ---
def main_app():
    # Sidebar
    with st.sidebar:
        st.title(f"🛡️ ElectaCopilot")
        st.write(f"User: **{st.session_state.username}** ({st.session_state.user_role})")
        st.divider()
        
        # Menu Navigasi
        menu = ["Chat Room", "Data Analytics"]
        if st.session_state.user_role == "admin":
            menu.append("Admin Panel")
        
        choice = st.radio("Navigasi", menu)
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    # Logika Konten Berdasarkan Pilihan Menu
    if choice == "Admin Panel":
        admin_panel()
    
    elif choice == "Data Analytics":
        st.title("📊 Data & Evidence")
        uploaded_csv = st.file_uploader("Upload CSV Pemilu", type="csv")
        if uploaded_csv:
            df = pd.read_csv(uploaded_csv)
            st.dataframe(df, use_container_width=True)

    else:
        st.title("💬 Command Center")
        
        # Penanganan Model Gemini (Gunakan Key dari Secrets)
        if "GEMINI_API_KEY" in st.secrets:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            model = genai.GenerativeModel("gemini-3-pro-preview")
        else:
            st.error("API Key tidak ditemukan di Secrets.")
            return

        # Tampilan Riwayat Chat dengan Fitur Delete & Copy
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # Fitur Copy & Delete
                col_c1, col_c2, col_c3 = st.columns([1, 1, 8])
                with col_c1:
                    # Streamlit secara native menyediakan tombol copy pada code block
                    # Kita tampilkan konten dalam code block singkat agar mudah dicopy
                    if st.button("📋", key=f"copy_{i}"):
                        st.info("Gunakan tombol copy pada box di bawah ini.")
                with col_c2:
                    if st.button("🗑️", key=f"del_{i}"):
                        st.session_state.messages.pop(i)
                        st.rerun()
                
                # Jika tombol copy ditekan, tampilkan teks dalam format code agar mudah dicopy
                if st.session_state.get(f"copy_{i}"):
                    st.code(msg["content"])

        # Input Chat
        if prompt := st.chat_input("Berikan instruksi strategis..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                response = model.generate_content(prompt)
                full_res = response.text
                st.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                st.rerun()

# --- 6. EKSEKUSI APLIKASI ---
if not st.session_state.authenticated:
    login_interface()
else:
    main_app()
