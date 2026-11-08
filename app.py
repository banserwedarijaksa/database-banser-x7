import streamlit as st
import pandas as pd
import datetime
import time 
import io
import altair as alt
import gspread
from streamlit_cookies_controller import CookieController

# Import tambahan untuk Foto dan Google Drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from PIL import Image

# ---------------------------------
# 1. KONFIGURASI DATABASE & GOOGLE DRIVE
# ---------------------------------
@st.cache_resource
def init_connection():
    secrets_dict = dict(st.secrets["gcp_service_account"])
    
    # 1. Koneksi ke Google Sheets
    gc = gspread.service_account_from_dict(secrets_dict)
    
    # 2. Koneksi ke Google Drive API
    SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_info(secrets_dict, scopes=SCOPES)
    drive_srv = build('drive', 'v3', credentials=creds)
    
    return gc, drive_srv

client, drive_service = init_connection()
SHEET_NAME = 'Database_Banser_X7' 
sheet = client.open(SHEET_NAME).sheet1

# ID Folder Google Drive Anda
FOLDER_ID = '1XMW4XN42EgiYkuGKxugr__7Ix57hiY_e'

# --- FUNGSI PENGOLAHAN DATA ---
def insert_data(data):
    sheet.append_row(list(data))

def get_all_data():
    records = sheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=[
            'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 'nomor_hp', 
            'alamat_tinggal', 'pekerjaan', 'pendidikan_terakhir', 
            'tingkat_pengkaderan', 'satkoryon', 'satkorkel', 
            'minat', 'bakat', 'grade_anggota', 'status_keanggotaan', 
            'foto_anggota', 'waktu_input', 'admin'
        ])
    df = pd.DataFrame(records)
    df.columns = [
        'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 'nomor_hp', 
        'alamat_tinggal', 'pekerjaan', 'pendidikan_terakhir', 
        'tingkat_pengkaderan', 'satkoryon', 'satkorkel', 
        'minat', 'bakat', 'grade_anggota', 'status_keanggotaan', 
        'foto_anggota', 'waktu_input', 'admin'
    ]
    return df

# --- FUNGSI KOMPRESI & UNGGAH FOTO ---
def compress_image(uploaded_file):
    img = Image.open(uploaded_file)
    # Jika foto format PNG transparan, ubah ke RGB
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    # Kecilkan dimensi maksimal 1024x1024
    img.thumbnail((1024, 1024))
    
    # Simpan ke dalam memori komputer sementara (BytesIO)
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=75, optimize=True)
    output.seek(0)
    return output

def upload_to_drive(file_stream, filename, folder_id):
    media = MediaIoBaseUpload(file_stream, mimetype='image/jpeg', resumable=True)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    # Eksekusi unggah ke Google Drive
    file = drive_service.files().create(
        body=file_metadata, 
        media_body=media, 
        fields='id, webViewLink'
    ).execute()
    
    # Mengembalikan tautan/link foto tersebut
    return file.get('webViewLink')

# ---------------------------------
# 2. DATA REFERENSI SATKORKEL
# ---------------------------------
data_desa = {
    "Wedarijaksa": ["Bangsalrejo", "Bumiayu", "Jatimulyo", "Jetak", "Jontro", "Kepoh", "Margorejo", "Ngurenrejo", "Ngurensiti", "Pagerharjo", "Panggungroyom", "Sidoharjo", "Sukoharjo", "Suwaduk", "Tawangharjo", "Tlogoharum", "Tluwuk", "Wedarijaksa"],
    "Trangkil": ["Asempapan", "Guyangan", "Kadilangu", "Kajar", "Karanglegi", "Karangwage", "Kertomulyo", "Ketanen", "Krandan", "Mojoagung", "Pasucen", "Rejoagung", "Sambilawang", "Tegalharjo", "Tlutup", "Trangkil"],
    "Margoyoso": ["Bulumanis Kidul", "Bulumanis Lor", "Cebolek Kidul", "Kajen", "Kertomulyo", "Langgenharjo", "Margotuhu Kidul", "Margoyoso", "Ngagel", "Pangkalan", "Pohijo", "Purwodadi", "Purworejo", "Sekarjalak", "Semerak", "Sidomukti", "Soneyan", "Tanjungrejo", "Tegalarum", "Tendas", "Tubanan", "Waturoyo"],
    "Juwana": ["Agungmulyo", "Bajomulyo", "Bakaran Kulon", "Bakaran Wetan", "Bendar", "Bringin", "Bumirejo", "Doropayung", "Dukutalit", "Gadingrejo", "Genengmulyo", "Growong Kidul", "Growong Lor", "Jepuro", "Karang", "Karangrejo", "Kauman", "Kebonsawahan", "Kedungpancing", "Ketip", "Kudukeras", "Langenharjo", "Margomulyo", "Mintomulyo", "Pajeksan", "Pekuwon", "Sejomulyo", "Tluwah", "Trimulyo"],
    "Pati": ["Blaru", "Bleber", "Dengkek", "Gajahmati", "Geritan", "Kalidoro", "Kutoharjo", "Mulyoharjo", "Mustokoharjo", "Ngarus", "Ngepungrejo", "Panjunan", "Parenggan", "Pati Kidul", "Pati Lor", "Pati Wetan", "Payang", "Plangitan", "Puri", "Purworejo", "Semampir", "Sidoharjo", "Sidokerto", "Sinoman", "Sugiharjo", "Tambaharjo", "Tambahsari", "Widorokandang", "Winong"],
    "Margorejo": ["Badegan", "Banjarsari", "Banyuurip", "Bumirejo", "Dadirejo", "Jambean Kidul", "Jimet", "Margorejo", "Metaraman", "Muktiharjo", "Ngawen", "Pegandan", "Penambuhan", "Sokokulon", "Sukobubuk", "Sukoharjo", "Tambaharjo", "Wangunrejo"],
    "Batangan": ["Batursari", "Bulumulyo", "Bumimulyo", "Gajahkumpul", "Gunungsari", "Jembangan", "Kedalon", "Ketitangwetan", "Klayusiwalan", "Kuniran", "Lengkong", "Mangunlegi", "Ngening", "Pecangaan", "Raci", "Sukoagung", "Tlogomojo", "Tompomulyo"],
    "Tayu": ["Bendokaton Kidul", "Bulungan", "Dororejo", "Jepat Kidul", "Jepat Lor", "Kalikalong", "Keboromo", "Kedungbang", "Kedungsari", "Luwang", "Margomulyo", "Pakis", "Pondowan", "Pundenrejo", "Purwokerto", "Sambiroto", "Sendangrejo", "Tayu Kulon", "Tayu Wetan", "Tendas", "Tunggulsari"],
    "Gunungwungkal": ["Bancak", "Gadu", "Gajihan", "Giling", "Gulangpungge", "Gunungwungkal", "Jembulwunut", "Jepalo", "Jrahi", "Ngetuk", "Perdopo", "Pesagen", "Sampok", "Sidomulyo", "Sumberejo"],
    "Cluwak": ["Bleber", "Bulakmojo", "Grogolsari", "Karangsari", "Medani", "Mojo", "Ngablak", "Ngawen", "Payak", "Plaosan", "Sentul", "Sirahan", "Sumur"],
    "Tlogowungu": ["Cabak", "Gunungsari", "Guwo", "Klumpit", "Lahar", "Purwosari", "Regaloh", "Sumbermulyo", "Suwatu", "Tajungsari", "Tamansari", "Tlogorejo", "Tlogosari", "Tlogowungu", "Wonorejo"],
    "Kayen": ["Beketel", "Boloagung", "Brati", "Durensawit", "Jatiroto", "Jimbaran", "Kayen", "Pasuruhan", "Pesagi", "Purwokerto", "Rogomulyo", "Slungkep", "Srikaton", "Sumbersari", "Sundoluhur", "Talun", "Trimulyo"],
    "Tambakromo": ["Angkatan Kidul", "Angkatan Lor", "Karangawen", "Karangmulyo", "Karangwono", "Keben", "Kedalingan", "Larangan", "Manggimulyo", "Mojomulyo", "Pakis", "Pojok", "Sinomwidodo", "Sitirejo", "Tambahagung", "Tambakromo", "Wukirsari", "Tanjungrejo"],
    "Pucakwangi": ["Bodeh", "Grogolsari", "Gunungpanti", "Karangrejo", "Karangwotan", "Kepohkencono", "Kletek", "Lumbungmas", "Mencon", "Mojoagung", "Pelemgede", "Plosorejo", "Pucakwangi", "Sitimulyo", "Sokopuluhan", "Tanjungsekar", "Tegalwero", "Terteg", "Triguno", "Wateshaji"],
    "Gabus": ["Babalan", "Banjarsari", "Bogotanjung", "Gabus", "Gebang", "Gempolsari", "Karaban", "Koripandriyo", "Kosekan", "Kuryokalangan", "Mintobasuki", "Mojolawaran", "Ngemplak Kidul", "Pantirejo", "Penanggungan", "Plumbungan", "Sambirejo", "Soko", "Sugihrejo", "Sunggingwarno", "Tambahmulyo", "Tanjang", "Tanjunganom", "Tlogoayu", "Wuwur"],
    "Sukolilo": ["Baleadi", "Baturejo", "Cengkalsewu", "Gadudero", "Kasiyan", "Kedumulyo", "Kedungwinong", "Kuwawur", "Pakem", "Porangparing", "Prawoto", "Sukolilo", "Sumbersoko", "Tompegunung", "Wegil", "Wotan"],
    "Gembong": ["Bageng", "Bermi", "Gembong", "Kedungbulus", "Ketanggan", "Klakahkasihan", "Plukaran", "Pohgading", "Semirejo", "Sitiluhur", "Wonosekar"],
    "Jaken": ["Aromanis", "Boto", "Kebonturi", "Lundo", "Manjang", "Mantingan", "Mojolampir", "Mojoluhur", "Ronggo", "Sidoluhur", "Sidomukti", "Srikaton", "Sriwedari", "Sumberagung", "Sumberarum", "Sumberejo", "Tegalarum", "Tlogorejo", "Trikoyo", "Sokopuluhan", "Sukorukun"],
    "Jakenan": ["Bungasrejo", "Dukuhmulyo", "Glonggong", "Jakenan", "Jatisari", "Kalimulyo", "Karanganyar", "Karangrejo Lor", "Kedungmulyo", "Mantingan Tengah", "Ngastorejo", "Plosojenar", "Puluhan Tengah", "Sembaturagung", "Sendangsoko", "Sidoarum", "Sidomulyo", "Sonorejo", "Tambahmulyo", "Tanjungsari", "Tlogorejo", "Tondokerto", "Tondomulyo"],
    "Winong": ["Blingijati", "Bringinwareng", "Bumiharjo", "Clekatakan", "Danyangmulyo", "Degolan", "Godo", "Gunungpanti", "Guyangan", "Karangkonang", "Karangsumber", "Kropak", "Kudur", "Mintorahayu", "Padangan", "Pagendisan", "Pekalongan", "Pohgading", "Pulorejo", "Sarimulyo", "Serutsadang", "Sugihan", "Sumbermulyo", "Tanggel", "Tawangrejo", "Tlogorejo", "Tlogosari", "Winong", "Wirun", "Kebowan"],
    "Dukuhseti": ["Alasdowo", "Bakalan", "Banyutowo", "Dukuhseti", "Dumpil", "Grogolan", "Kembang", "Kenanti", "Puncel", "Tegalombo", "Wedusan", "Ngagel"]
}

# ---------------------------------
# 3. KONFIGURASI HALAMAN STREAMLIT
# ---------------------------------
st.set_page_config(page_title="Database Ansor Banser", page_icon="🟢", layout="wide")

# ---------------------------------
# SISTEM LOGIN
# ---------------------------------
cookie_controller = CookieController()

cookie_logged_in = cookie_controller.get('logged_in')
cookie_nama_petugas = cookie_controller.get('nama_petugas')

if cookie_logged_in == "True" and st.session_state.get("logged_in") != True:
    st.session_state["logged_in"] = True
    st.session_state["nama_petugas"] = cookie_nama_petugas
    st.rerun()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["nama_petugas"] = ""

if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Database Banser X-7</h2>", unsafe_allow_html=True)
    
    col_log1, col_log2, col_log3 = st.columns([1, 1, 1])
    with col_log2:
        with st.form("login_form"):
            in_user = st.text_input("Username")
            in_pass = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Masuk", type="primary", use_container_width=True)
            
            if submit_login:
                if in_user in st.secrets["passwords"] and st.secrets["passwords"][in_user] == in_pass:
                    cookie_controller.set('logged_in', "True")
                    cookie_controller.set('nama_petugas', in_user)
                    st.session_state["logged_in"] = True
                    st.session_state["nama_petugas"] = in_user
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("⚠️ Username atau Password salah!")
    st.stop()

with st.sidebar:
    st.success(f"Masuk sebagai:\n**{st.session_state['nama_petugas']}**")
    if st.button("Keluar / Logout", use_container_width=True):
        cookie_controller.remove('logged_in')
        cookie_controller.remove('nama_petugas')
        st.session_state.clear() 
        time.sleep(0.5)
        st.rerun()

# ---------------------------------
# 4. TAMPILAN UTAMA APLIKASI
# ---------------------------------
col_logo, col_judul = st.columns([1, 11])
with col_logo:
    try:
        st.image("logo.png", width=80) 
    except:
        st.error("Logo belum ada") 
with col_judul:
    st.title("DATABASE BANSER X-7")
    st.markdown("Sistem penginputan dan manajemen data anggota Banser.")

tab1, tab2, tab3 = st.tabs(["📝 Form Penginputan", "🗃️ Database Anggota", "📊 Dashboard Statistik"])

# ---------------------------------
# TAB 1: FORM PENGINPUTAN
# ---------------------------------
with tab1:
    st.subheader("Data Anggota")
    
    if "sukses_simpan" in st.session_state and st.session_state["sukses_simpan"]:
        st.session_state["inp_nama"] = ""
        st.session_state["inp_tempat"] = ""
        st.session_state["inp_tanggal"] = datetime.date.today()
        st.session_state["inp_hp"] = ""
        st.session_state["inp_alamat"] = ""
        st.session_state["inp_kerja"] = ""
        st.session_state["inp_pendidikan"] = ""
        st.session_state["inp_kader"] = []
        st.session_state["inp_satkoryon"] = ""
        st.session_state["inp_satkorkel"] = ""
        st.session_state["inp_minat"] = []
        st.session_state["inp_bakat"] = []
        st.session_state["inp_grade"] = ""
        st.session_state["inp_status"] = ""
        
        # Hapus cache file uploader jika ada
        if "inp_foto" in st.session_state:
            del st.session_state["inp_foto"]
        
        if "inp_satkorkel_text" in st.session_state:
            del st.session_state["inp_satkorkel_text"]
            
        st.session_state["sukses_simpan"] = False 

    col1, col2 = st.columns(2)
    
    with col1:
        nama = st.text_input("1. Nama Lengkap *", placeholder="Masukkan nama sesuai KTP", key="inp_nama")
        tempat_lahir = st.text_input("2. Tempat Lahir *", key="inp_tempat")
        min_date = datetime.date(1950, 1, 1) 
        max_date = datetime.date.today()     
        tanggal_lahir = st.date_input("3. Tanggal Lahir *", min_value=min_date, max_value=max_date, format="DD/MM/YYYY", key="inp_tanggal")
        no_hp = st.text_input("4. Nomor HP/WhatsApp *", placeholder="Contoh: 08123456789", key="inp_hp")
        
    with col2:
        pekerjaan = st.text_input("6. Pekerjaan *", key="inp_kerja")
        pilihan_pendidikan = ["", "SD/MI", "SMP/MTS", "SMA/SMK/MA", "Diploma", "S1", "S2", "S3", "Tidak bersekolah"]
        pendidikan = st.selectbox("7. Pendidikan Terakhir *", pilihan_pendidikan, key="inp_pendidikan")
        alamat = st.text_area("5. Alamat Tinggal *", placeholder="Jalan, RT/RW, Desa/Kelurahan", key="inp_alamat")

    st.divider()
    st.subheader("Data Keorganisasian & Penilaian")
    col3, col4 = st.columns(2)
    
    with col3:
        pilihan_pengkaderan = ["Diklatsar", "Susbalan", "Susbapin", "Diklatsus", "Suspelat", "Belum pernah"]
        pengkaderan_list = st.multiselect("8. Jenjang Pengkaderan *", pilihan_pengkaderan, key="inp_kader")
        
        pilihan_satkoryon = ["", "Batangan", "Cluwak", "Dukuhseti", "Gabus", "Gembong", "Gunungwungkal", "Jaken", "Jakenan", "Juwana", "Kayen", "Margorejo", "Margoyoso", "Pati", "Pucakwangi", "Sukolilo", "Tambakromo", "Tayu", "Tlogowungu", "Trangkil", "Wedarijaksa", "Winong"]
        satkoryon = st.selectbox("9. Satkoryon *", pilihan_satkoryon, key="inp_satkoryon")
        
        if satkoryon in data_desa:
            satkorkel = st.selectbox("10. Satkorkel (Tingkat Desa/Kelurahan) *", data_desa[satkoryon], key="inp_satkorkel")
        else:
            satkorkel = st.text_input("10. Satkorkel (Tingkat Desa/Kelurahan) *", key="inp_satkorkel_text")
            
        pilihan_minat = [
            "Kaligrafi", "Fotografi", "Videografi", "Desain grafis", "Seni lukis", 
            "Seni musik", "Karya sastra", "Seni pertunjukan", "Seni budaya", 
            "Desain animasi", "Desain interior", "Pendidikan", "Kajian Islam", 
            "Elektronika", "Otomotif", "Pengolahan data", "Pemrograman", 
            "Artificial Intelligence", "Digital marketing", "Kegiatan sosial", 
            "Kepemudaan", "Kepemimpinan", "Advokasi masyarakat", "Kegiatan dakwah", 
            "Pemberdayaan UMKM", "Ekonomi bisnis", "Keuangan", "Kuliner", 
            "Olahraga berat", "Olahraga ringan", "Catur", "Game online", 
            "Kegiatan alam", "Kesehatan", "Lainnya"
        ]
        minat_list = st.multiselect("11. Minat *", pilihan_minat, key="inp_minat")
        
    with col4:
        pilihan_bakat = [
            "Konsep abstrak", "Pola dan angka", "Berfikir logis", "Berfikir kritis", 
            "Mengorganisasi team", "Analisis kuat", "Pengambilan keputusan", 
            "Penyelesaian konflik", "Publik speaking", "Kemampuan komunikasi", 
            "Kemampuan bernegosiasi", "Kemampuan beradaptasi", "Imajinasi visual", 
            "Bidang mekanik", "Sistem komputer", "Bidang perlistrikan", 
            "Bidang perdagangan", "Bidang pertukangan", "Bidang kesehatan", 
            "Memasak", "Menjahit", "Mengemudi", "Bidang administrasi", 
            "Bidang Perikanan", "Bidang Peternakan", "Bidang Pertanian", 
            "Bidang Perizinan", "Lainnya"
        ]
        bakat_list = st.multiselect("12. Bakat *", pilihan_bakat, key="inp_bakat")
        
        pilihan_grade = ["", "A (Excellent)", "B (Good)", "C (Average)", "D (Below)", "F (Failure)"]
        grade = st.selectbox("13. Grade Anggota *", pilihan_grade, key="inp_grade")
        
        status = st.selectbox("14. Status Keanggotaan *", ["", "Aktif", "Tidak Aktif", "Pindah Domisili", "Lulus"], key="inp_status")
        
        foto_upload = st.file_uploader("15. Pas Foto Anggota * (Maks 5MB, otomatis dikompres)", type=['jpg', 'jpeg', 'png'], key="inp_foto")

    st.markdown("**Catatan: Semua kolom dengan tanda (*) wajib diisi.**")
    
    if st.button("Simpan Data Anggota", type="primary"):
        # Validasi memastikan foto juga terisi
        if nama and tempat_lahir and tanggal_lahir and no_hp and pekerjaan and pendidikan and alamat and pengkaderan_list and satkoryon and satkorkel and minat_list and bakat_list and grade and status and foto_upload:
            
            pengkaderan_str = ", ".join(pengkaderan_list)
            minat_str = ", ".join(minat_list) 
            bakat_str = ", ".join(bakat_list) 
            waktu_input = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            with st.spinner("Memproses foto dan menyimpan data ke awan... Mohon tunggu."):
                try:
                    # 1. Kompresi Foto
                    compressed_foto = compress_image(foto_upload)
                    
                    # 2. Buat nama file unik (Format: Nama_NoHP.jpg)
                    nama_file = f"{nama.replace(' ', '_')}_{no_hp}.jpg"
                    
                    # 3. Unggah ke Google Drive dan dapatkan tautan
                    url_foto = upload_to_drive(compressed_foto, nama_file, FOLDER_ID)
                    
                    # 4. Siapkan data baris untuk Google Sheets
                    data_baru = (
                        nama, tempat_lahir, str(tanggal_lahir), no_hp, 
                        alamat, pekerjaan, pendidikan, 
                        pengkaderan_str, satkoryon, satkorkel, 
                        minat_str, bakat_str, grade, status, 
                        url_foto, # Link foto dari Google Drive ditaruh di kolom ini
                        waktu_input, st.session_state["nama_petugas"]
                    )
                    
                    # 5. Kirim ke Google Sheets
                    insert_data(data_baru)
                    
                    st.success(f"✅ Data dan Foto atas nama **{nama}** berhasil disimpan!")
                    time.sleep(2)
                    st.session_state["sukses_simpan"] = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"⚠️ Terjadi kesalahan sistem: {e}")
                    
        else:
            st.error("⚠️ Mohon lengkapi seluruh form pendaftaran dan pastikan Anda telah mengunggah pas foto.")

# ---------------------------------
# TAB 2: TAMPILAN DATABASE
# ---------------------------------
with tab2:
    st.subheader("Daftar Anggota Terdaftar")
    df_anggota = get_all_data()
    
    if not df_anggota.empty:
        col_met1, col_met2 = st.columns(2)
        col_met1.metric("Total Anggota Terdaftar", len(df_anggota))
        col_met2.metric("Anggota Aktif", len(df_anggota[df_anggota['status_keanggotaan'] == 'Aktif']))
        
        df_tampil = df_anggota.copy()
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_tampil.to_excel(writer, index=False, sheet_name='Data Anggota')
            
        st.download_button(
            label="📥 Unduh Data ke Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"Database_Banser_X7_{datetime.date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        # Menampilkan tabel data (Khusus Streamlit versi baru, link bisa diklik)
        st.dataframe(
            df_tampil, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "foto_anggota": st.column_config.LinkColumn("Link Foto")
            }
        )
    else:
        st.info("Belum ada data anggota yang terdaftar di Google Sheets.")

# ---------------------------------
# TAB 3: DASHBOARD STATISTIK
# ---------------------------------
with tab3:
    st.subheader("Visualisasi Data Anggota")
    if not df_anggota.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**1. Distribusi Anggota per Satkoryon**")
            satkoryon_count = df_anggota['satkoryon'].value_counts().reset_index()
            satkoryon_count.columns = ['Satkoryon', 'Jumlah']
            chart_satkoryon = alt.Chart(satkoryon_count).mark_bar(color='#118b44').encode(
                x=alt.X('Jumlah:Q', title='Jumlah Anggota'),
                y=alt.Y('Satkoryon:N', sort='-x', title='Satkoryon'),
                tooltip=['Satkoryon', 'Jumlah']
            ).properties(height=350)
            st.altair_chart(chart_satkoryon, use_container_width=True)

        with col_chart2:
            st.markdown("**2. Persentase Status Keanggotaan**")
            status_count = df_anggota['status_keanggotaan'].value_counts().reset_index()
            status_count.columns = ['Status', 'Jumlah']
            chart_status = alt.Chart(status_count).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Jumlah", type="quantitative"),
                color=alt.Color(field="Status", type="nominal", scale=alt.Scale(scheme='set2')),
                tooltip=['Status', 'Jumlah']
            ).properties(height=350)
            st.altair_chart(chart_status, use_container_width=True)

        st.divider()
        col_chart3, col_chart4 = st.columns(2)
        
        with col_chart3:
            st.markdown("**3. Latar Belakang Pendidikan**")
            pendidikan_count = df_anggota['pendidikan_terakhir'].replace("", "Belum Diisi").value_counts().reset_index()
            pendidikan_count.columns = ['Pendidikan', 'Jumlah']
            chart_pendidikan = alt.Chart(pendidikan_count).mark_bar(color='#20b2aa').encode(
                x=alt.X('Pendidikan:N', sort='-y', title='Pendidikan Terakhir', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Jumlah:Q', title='Jumlah Anggota'),
                tooltip=['Pendidikan', 'Jumlah']
            ).properties(height=300)
            st.altair_chart(chart_pendidikan, use_container_width=True)

        with col_chart4:
            st.markdown("**4. Jenjang Pengkaderan**")
            semua_kader = df_anggota['tingkat_pengkaderan'].dropna().astype(str).str.split(', ').explode()
            kader_count = semua_kader[semua_kader != ""].value_counts().reset_index()
            kader_count.columns = ['Pengkaderan', 'Jumlah']
            chart_kader = alt.Chart(kader_count).mark_bar(color='#f28e2b').encode(
                x=alt.X('Pengkaderan:N', sort='-y', title='Jenjang', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Jumlah:Q', title='Jumlah'),
                tooltip=['Pengkaderan', 'Jumlah']
            ).properties(height=300)
            st.altair_chart(chart_kader, use_container_width=True)

        st.divider()
        st.markdown("**5. Peta Minat Anggota**")
        if 'minat' in df_anggota.columns:
            semua_minat = df_anggota['minat'].dropna().astype(str).str.split(', ').explode()
            minat_count = semua_minat[semua_minat != ""].value_counts().reset_index()
            minat_count.columns = ['Minat', 'Jumlah']
            chart_minat = alt.Chart(minat_count).mark_bar(color='#4e79a7').encode(
                x=alt.X('Jumlah:Q', title='Jumlah Peminat'),
                y=alt.Y('Minat:N', sort='-x', title='Kategori Minat'),
                tooltip=['Minat', 'Jumlah']
            ).properties(height=400)
            st.altair_chart(chart_minat, use_container_width=True)

    else:
        st.info("Visualisasi akan muncul setelah ada minimal satu data anggota yang diinput di Google Sheets.")
