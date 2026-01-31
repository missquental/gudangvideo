# gudang_video.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sqlite3
import hashlib

# Konfigurasi halaman
st.set_page_config(
    page_title="Gudang Video",
    page_icon="🎥",
    layout="wide"
)

# Inisialisasi database
def init_db():
    conn = sqlite3.connect('videos.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS videos
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT UNIQUE,
                  original_name TEXT,
                  upload_date TEXT,
                  file_size INTEGER,
                  hash_value TEXT)''')
    conn.commit()
    conn.close()

# Fungsi untuk menghitung hash file
def calculate_hash(file):
    hasher = hashlib.md5()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    file.seek(0)  # Reset pointer ke awal
    return hasher.hexdigest()

# Fungsi untuk menyimpan video
def save_video(uploaded_file):
    if not os.path.exists("videos"):
        os.makedirs("videos")
    
    file_path = os.path.join("videos", uploaded_file.name)
    
    # Simpan file
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Hitung ukuran file dan hash
    file_size = os.path.getsize(file_path)
    uploaded_file.seek(0)
    file_hash = calculate_hash(uploaded_file)
    
    # Simpan ke database
    conn = sqlite3.connect('videos.db')
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO videos 
                     (filename, original_name, upload_date, file_size, hash_value) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (uploaded_file.name, uploaded_file.name, 
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   file_size, file_hash))
        conn.commit()
        return True, "Video berhasil disimpan!"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Video dengan nama yang sama sudah ada!"
    finally:
        conn.close()

# Fungsi untuk mendapatkan daftar video
def get_videos():
    conn = sqlite3.connect('videos.db')
    df = pd.read_sql_query("SELECT * FROM videos ORDER BY upload_date DESC", conn)
    conn.close()
    return df

# Fungsi untuk menghapus video
def delete_video(filename):
    conn = sqlite3.connect('videos.db')
    c = conn.cursor()
    c.execute("DELETE FROM videos WHERE filename=?", (filename,))
    conn.commit()
    conn.close()
    
    # Hapus file fisik
    file_path = os.path.join("videos", filename)
    if os.path.exists(file_path):
        os.remove(file_path)

# Inisialisasi
init_db()

st.title("🎥 Gudang Video")
st.markdown("---")

# Tab navigasi
tab1, tab2 = st.tabs(["📤 Upload Video", "📁 Daftar Video"])

with tab1:
    st.subheader("Upload Video Baru")
    uploaded_file = st.file_uploader(
        "Pilih file video", 
        type=['mp4', 'avi', 'mov', 'mkv'],
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.video(uploaded_file)
        with col2:
            st.info(f"**Nama File:** {uploaded_file.name}")
            st.info(f"**Ukuran:** {uploaded_file.size / (1024*1024):.2f} MB")
            st.info(f"**Tipe:** {uploaded_file.type}")
            
            if st.button("💾 Simpan Video", type="primary"):
                success, message = save_video(uploaded_file)
                if success:
                    st.success(message)
                else:
                    st.error(message)

with tab2:
    st.subheader("Daftar Video Tersedia")
    
    videos_df = get_videos()
    
    if len(videos_df) > 0:
        # Tampilkan dalam bentuk tabel interaktif
        for index, row in videos_df.iterrows():
            with st.expander(f"📹 {row['original_name']} - {row['upload_date']}", expanded=False):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**Ukuran:** {row['file_size'] / (1024*1024):.2f} MB")
                    st.write(f"**Hash:** `{row['hash_value'][:16]}...`")
                    
                with col2:
                    # URL untuk streaming
                    stream_url = f"https://gudangvideo.streamlit.app/videos/{row['filename']}"
                    st.code(stream_url, language="url")
                    st.markdown(f"[🔗 Link Streaming]({stream_url})")
                    
                with col3:
                    if st.button("🗑️ Hapus", key=f"delete_{row['id']}"):
                        delete_video(row['filename'])
                        st.success("Video dihapus!")
                        st.experimental_rerun()
                        
                # Preview video
                video_path = os.path.join("videos", row['filename'])
                if os.path.exists(video_path):
                    st.video(video_path)
    else:
        st.info("Belum ada video yang diupload. Silakan upload video terlebih dahulu.")

# Footer
st.markdown("---")
st.caption("© 2024 Gudang Video - Sistem Penyimpanan & Streaming")
