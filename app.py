import streamlit as st
import pandas as pd
import datetime
import time 
import io
import altair as alt
import json
import gspread
import requests
import base64
from streamlit_cookies_controller import CookieController
from PIL import Image
import uuid

# ---------------------------------
# 1. KONFIGURASI DATABASE
# ---------------------------------
@st.cache_resource
def init_connection():
    secrets_dict = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(secrets_dict)

client = init_connection()
SHEET_NAME = 'Database_Banser_X7' 
sheet = client.open(SHEET_NAME).sheet1

def insert_data(data):
    sheet.append_row(list(data))

def update_data(row_number, data):
    # Diperluas menjadi A hingga R (18 Kolom) karena ada tambahan "Satuan"
    cell_list = sheet.range(f'A{row_number}:R{row_number}')
    for i, val in enumerate(data):
        cell_list[i].value = val
    sheet.update_cells(cell_list)

def get_all_data():
    records = sheet.get_all_records()
    # Struktur 18 Kolom Baru
    columns_layout = [
        'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 'nomor_hp', 
        'alamat_tinggal', 'pekerjaan', 'pendidikan_terakhir', 
        'tingkat_pengkaderan', 'satkoryon', 'satkorkel', 'satuan',
        'minat', 'bakat', 'grade_anggota', 'status_keanggotaan', 
        'foto_anggota', 'waktu_input', 'admin'
    ]
    if not records:
        return pd.DataFrame(columns=columns_layout)
    df = pd.DataFrame(records)
    df.columns = columns_layout
    return df

# --- FUNGSI KOMPRESI & UPLOAD IMGBB ---
def compress_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((800, 800))
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=75, optimize=True)
    output.seek(0)
    return output

def upload_to_imgbb(file_stream):
    api_key = st.secrets["imgbb"]["api_key"]
    url = "https://api.imgbb.com/1/upload"
    payload = {
        "key": api_key,
        "image": base64.b64encode(file_stream.read()).decode('utf-8')
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json()["data"]["url"]
    else:
        raise Exception(f"Gagal mengunggah foto ke ImgBB: {response.text}")

# ---------------------------------
# 2. VARIABEL GLOBAL DAFTAR PILIHAN
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

pilihan_pendidikan = ["", "SD/MI", "SMP/MTS", "SMA/SMK/MA", "Diploma", "S1", "S2", "S3", "Tidak bersekolah"]
pilihan_pengkaderan = ["Diklatsar", "Susbalan", "Susbapin", "Diklatsus", "Suspelat", "Belum pernah"]
pilihan_satkoryon = ["", "Batangan", "Cluwak", "Dukuhseti", "Gabus", "Gembong", "Gunungwungkal", "Jaken", "Jakenan", "Juwana", "Kayen", "Margorejo", "Margoyoso", "Pati", "Pucakwangi", "Sukolilo", "Tambakromo", "Tayu", "Tlogowungu", "Trangkil", "Wedarijaksa", "Winong"]
pilihan_satuan = ["", "Regular Banser", "Banser Tanggap Bencana (Bagana)", "Banser Relawan Lalu Lintas (Balantas)", "Banser Husada (Basada)", "Banser Maritim (Baritim)", "Banser Protokoler", "Corp Provost Banser (CPB)"]
pilihan_minat = ["Kaligrafi", "Fotografi", "Videografi", "Desain grafis", "Seni lukis", "Seni musik", "Karya sastra", "Seni pertunjukan", "Seni budaya", "Desain animasi", "Desain interior", "Pendidikan", "Kajian Islam", "Kegiatan keagamaan", "Penertiban kendaraan", "Elektronika", "Otomotif", "Pengolahan data", "Pemrograman", "Artificial Intelligence", "Digital marketing", "Kegiatan sosial", "Kepemudaan", "Kepemimpinan", "Keprotokoleran", "Advokasi masyarakat", "Kegiatan dakwah", "Pemberdayaan UMKM", "Ekonomi bisnis", "Keuangan", "Kuliner", "Olahraga berat", "Olahraga ringan", "Catur", "Game online", "Instruktur senam", "Kegiatan alam", "Kebencanaan", "Kesehatan", "Lainnya"]
pilihan_bakat = ["Konsep abstrak", "Pola dan angka", "Berfikir logis", "Berfikir kritis", "Mengorganisasi team", "Analisis kuat", "Pengambilan keputusan", "Penyelesaian konflik", "Publik speaking", "Kemampuan komunikasi", "Kemampuan bernegosiasi", "Kemampuan beradaptasi", "Imajinasi visual", "Bidang mekanik", "Sistem komputer", "Bidang perlistrikan", "Bidang perdagangan", "Bidang pertukangan", "Bidang kesehatan", "Memasak", "Menjahit", "Mengemudi", "Bidang administrasi", "Bidang keamanan", "Bidang Perikanan", "Bidang Peternakan", "Bidang Pertanian", "Bidang Perizinan", "Lainnya"]
pilihan_grade = ["", "A (siap bertugas kapanpun di manapun)", "B (pasukan aktif)", "C (Pasukan masih istirahat)"]
pilihan_status = ["", "Aktif", "Tidak Aktif", "Pindah Domisili", "Lulus"]

def get_idx(val, lst):
    return lst.index(val) if val in lst else 0

# ---------------------------------
# 3. KONFIGURASI HALAMAN STREAMLIT
# ---------------------------------
st.set_page_config(page_title="Database Ansor Banser", page_icon="🟢", layout="wide")
# Sembunyikan elemen bawaan Streamlit
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = str(uuid.uuid4())
if "edit_uploader_key" not in st.session_state:
    st.session_state["edit_uploader_key"] = str(uuid.uuid4())

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

tab1, tab2, tab3, tab4 = st.tabs(["📝 Form Penginputan", "🗃️ Database Anggota", "📊 Dashboard Statistik", "✏️ Update Data"])

# ---------------------------------
# TAB 1: FORM PENGINPUTAN
# ---------------------------------
with tab1:
    st.subheader("Data Anggota Baru")
    
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
        st.session_state["inp_satuan"] = ""
        st.session_state["inp_minat"] = []
        st.session_state["inp_bakat"] = []
        st.session_state["inp_grade"] = ""
        st.session_state["inp_status"] = ""
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
        pendidikan = st.selectbox("7. Pendidikan Terakhir *", pilihan_pendidikan, key="inp_pendidikan")
        alamat = st.text_area("5. Alamat Tinggal *", placeholder="Jalan, RT/RW, Desa/Kelurahan", key="inp_alamat")

    st.divider()
    st.subheader("Data Keorganisasian & Penilaian")
    col3, col4 = st.columns(2)
    
    with col3:
        pengkaderan_list = st.multiselect("8. Jenjang Pengkaderan *", pilihan_pengkaderan, key="inp_kader")
        satkoryon = st.selectbox("9. Satkoryon *", pilihan_satkoryon, key="inp_satkoryon")
        if satkoryon in data_desa:
            satkorkel = st.selectbox("10. Satkorkel (Tingkat Desa/Kelurahan) *", data_desa[satkoryon], key="inp_satkorkel")
        else:
            satkorkel = st.text_input("10. Satkorkel (Tingkat Desa/Kelurahan) *", key="inp_satkorkel_text")
        
        # PENAMBAHAN INPUT SATUAN KHUSUS
        satuan = st.selectbox("11. Satuan Khusus *", pilihan_satuan, key="inp_satuan")
        
        minat_list = st.multiselect("12. Minat *", pilihan_minat, key="inp_minat")
        
    with col4:
        bakat_list = st.multiselect("13. Bakat *", pilihan_bakat, key="inp_bakat")
        grade = st.selectbox("14. Grade Anggota *", pilihan_grade, key="inp_grade")
        status = st.selectbox("15. Status Keanggotaan *", pilihan_status, key="inp_status")
        foto_upload = st.file_uploader("16. Pas Foto Anggota *", type=['jpg', 'jpeg', 'png'], key=st.session_state["uploader_key"])

    st.markdown("**Catatan: Semua kolom dengan tanda (*) wajib diisi.**")
    
    if st.button("Simpan Data Anggota", type="primary"):
        if nama and tempat_lahir and tanggal_lahir and no_hp and pekerjaan and pendidikan and alamat and pengkaderan_list and satkoryon and satkorkel and satuan and minat_list and bakat_list and grade and status and foto_upload:
            df_existing = get_all_data()
            
            clean_no_hp = str(no_hp).lstrip("0")
            existing_hps = df_existing['nomor_hp'].astype(str).str.lstrip("0").values
            
            if clean_no_hp in existing_hps:
                st.error(f"⚠️ Gagal! Nomor HP **{no_hp}** sudah terdaftar di dalam sistem.")
            else:
                pengkaderan_str = ", ".join(pengkaderan_list)
                minat_str = ", ".join(minat_list) 
                bakat_str = ", ".join(bakat_list) 
                
                hp_untuk_disimpan = f"'{no_hp}" 
                waktu_input = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
                
                with st.spinner("Mengunggah foto dan menyimpan data..."):
                    try:
                        compressed_foto = compress_image(foto_upload)
                        url_foto = upload_to_imgbb(compressed_foto)
                        # DISESUAIKAN MENJADI 18 VARIABEL (Disisipkan 'satuan')
                        data_baru = (
                            nama, tempat_lahir, str(tanggal_lahir), hp_untuk_disimpan, 
                            alamat, pekerjaan, pendidikan, pengkaderan_str, satkoryon, satkorkel, 
                            satuan, minat_str, bakat_str, grade, status, url_foto, 
                            waktu_input, st.session_state["nama_petugas"]
                        )
                        insert_data(data_baru)
                        
                        st.success(f"✅ Data atas nama **{nama}** berhasil disimpan!")
                        time.sleep(1.5)
                        st.session_state["uploader_key"] = str(uuid.uuid4())
                        st.session_state["sukses_simpan"] = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Terjadi kesalahan: {e}")
        else:
            st.error("⚠️ Mohon lengkapi form dan pastikan Anda telah mengunggah pas foto.")

# ---------------------------------
# TAB 2: TAMPILAN DATABASE & FILTER
# ---------------------------------
with tab2:
    st.subheader("Daftar Anggota Terdaftar")
    df_anggota = get_all_data()
    
    if not df_anggota.empty:
        st.markdown("🔍 **Pencarian & Filter Data**")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cari_nama = st.text_input("Cari Nama / HP:")
        with col_f2:
            filter_satkoryon = st.selectbox("Filter Satkoryon:", ["Semua"] + list(pilihan_satkoryon)[1:])
        with col_f3:
            if filter_satkoryon != "Semua" and filter_satkoryon in data_desa:
                filter_satkorkel = st.selectbox("Filter Satkorkel:", ["Semua"] + data_desa[filter_satkoryon])
            else:
                filter_satkorkel = st.selectbox("Filter Satkorkel:", ["Semua"])
        
        df_tampil = df_anggota.copy()
        
        if cari_nama:
            mask_nama = df_tampil['nama_lengkap'].astype(str).str.contains(cari_nama, case=False, na=False)
            mask_hp = df_tampil['nomor_hp'].astype(str).str.contains(cari_nama, case=False, na=False)
            df_tampil = df_tampil[mask_nama | mask_hp]
        if filter_satkoryon != "Semua":
            df_tampil = df_tampil[df_tampil['satkoryon'] == filter_satkoryon]
        if filter_satkorkel != "Semua":
            df_tampil = df_tampil[df_tampil['satkorkel'] == filter_satkorkel]
            
        st.divider()
        col_met1, col_met2 = st.columns(2)
        col_met1.metric("Total Data Ditampilkan", len(df_tampil))
        col_met2.metric("Anggota Aktif (Dari Filter)", len(df_tampil[df_tampil['status_keanggotaan'] == 'Aktif']))
        
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
        st.dataframe(df_tampil, use_container_width=True, hide_index=True, column_config={"foto_anggota": st.column_config.LinkColumn("Link Foto")})
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
            satkoryon_count = df_anggota['satkoryon'].value_counts().reset_index()
            satkoryon_count.columns = ['Satkoryon', 'Jumlah']
            chart_satkoryon = alt.Chart(satkoryon_count).mark_bar(color='#118b44').encode(
                x=alt.X('Jumlah:Q', title='Jumlah Anggota'),
                y=alt.Y('Satkoryon:N', sort='-x', title='Satkoryon'),
                tooltip=['Satkoryon', 'Jumlah']
            ).properties(title="Distribusi per Satkoryon", height=350)
            st.altair_chart(chart_satkoryon, use_container_width=True)

        with col_chart2:
            status_count = df_anggota['status_keanggotaan'].value_counts().reset_index()
            status_count.columns = ['Status', 'Jumlah']
            chart_status = alt.Chart(status_count).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Jumlah", type="quantitative"),
                color=alt.Color(field="Status", type="nominal", scale=alt.Scale(scheme='set2')),
                tooltip=['Status', 'Jumlah']
            ).properties(title="Persentase Status", height=350)
            st.altair_chart(chart_status, use_container_width=True)
            
        st.divider()
        col_chart3, col_chart4 = st.columns(2)
        with col_chart3:
            # Mengganti chart pendidikan dengan chart SATUAN KHUSUS agar lebih informatif
            if 'satuan' in df_anggota.columns:
                satuan_count = df_anggota['satuan'].replace("", "Belum Diisi").value_counts().reset_index()
                satuan_count.columns = ['Satuan', 'Jumlah']
                chart_satuan = alt.Chart(satuan_count).mark_bar(color='#e15759').encode(
                    x=alt.X('Satuan:N', sort='-y', title='Satuan Khusus', axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y('Jumlah:Q', title='Jumlah Anggota'),
                    tooltip=['Satuan', 'Jumlah']
                ).properties(title="Distribusi Satuan Khusus", height=300)
                st.altair_chart(chart_satuan, use_container_width=True)

        with col_chart4:
            semua_kader = df_anggota['tingkat_pengkaderan'].dropna().astype(str).str.split(', ').explode()
            kader_count = semua_kader[semua_kader != ""].value_counts().reset_index()
            kader_count.columns = ['Pengkaderan', 'Jumlah']
            chart_kader = alt.Chart(kader_count).mark_bar(color='#f28e2b').encode(
                x=alt.X('Pengkaderan:N', sort='-y', title='Jenjang', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Jumlah:Q', title='Jumlah'),
                tooltip=['Pengkaderan', 'Jumlah']
            ).properties(title="Jenjang Pengkaderan", height=300)
            st.altair_chart(chart_kader, use_container_width=True)

# ---------------------------------
# TAB 4: UPDATE DATA
# ---------------------------------
with tab4:
    st.subheader("Edit / Pembaruan Data Anggota")
    st.info("Ketikkan Nomor HP anggota untuk memanggil data lamanya. Anda dapat memperbaiki kesalahan ketik atau memperbarui status anggota di sini.")
    
    df_edit = get_all_data()
    edit_hp = st.text_input("🔍 Nomor HP Anggota yang ingin diedit:", placeholder="Contoh: 08123456789")
    
    if edit_hp:
        clean_input = str(edit_hp).lstrip("0")
        mask = df_edit['nomor_hp'].astype(str).str.lstrip("0") == clean_input
        matched_data = df_edit[mask]
        
        if matched_data.empty:
            st.warning(f"Data dengan Nomor HP {edit_hp} tidak ditemukan di dalam sistem.")
        else:
            idx = matched_data.index[0]
            row_number = idx + 2 
            
            c_nama = str(matched_data['nama_lengkap'].values[0])
            c_tempat = str(matched_data['tempat_lahir'].values[0])
            try:
                c_tanggal = datetime.datetime.strptime(str(matched_data['tanggal_lahir'].values[0]), "%Y-%m-%d").date()
            except:
                c_tanggal = datetime.date.today()
            c_alamat = str(matched_data['alamat_tinggal'].values[0])
            c_kerja = str(matched_data['pekerjaan'].values[0])
            c_pendidikan = str(matched_data['pendidikan_terakhir'].values[0])
            c_satkoryon = str(matched_data['satkoryon'].values[0])
            c_satkorkel = str(matched_data['satkorkel'].values[0])
            c_satuan = str(matched_data['satuan'].values[0])
            c_grade = str(matched_data['grade_anggota'].values[0])
            c_status = str(matched_data['status_keanggotaan'].values[0])
            c_foto_url = str(matched_data['foto_anggota'].values[0])
            
            hp_tampil = str(matched_data['nomor_hp'].values[0]).replace("'", "")
            if not hp_tampil.startswith("0"):
                hp_tampil = "0" + hp_tampil
            
            c_kader = [k.strip() for k in str(matched_data['tingkat_pengkaderan'].values[0]).split(', ') if k.strip() in pilihan_pengkaderan]
            c_minat = [m.strip() for m in str(matched_data['minat'].values[0]).split(', ') if m.strip() in pilihan_minat]
            c_bakat = [b.strip() for b in str(matched_data['bakat'].values[0]).split(', ') if b.strip() in pilihan_bakat]
            
            with st.form("form_edit_data"):
                st.markdown(f"**Mengedit Data: {c_nama}**")
                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    e_nama = st.text_input("1. Nama Lengkap", value=c_nama)
                    e_tempat = st.text_input("2. Tempat Lahir", value=c_tempat)
                    e_tanggal = st.date_input("3. Tanggal Lahir", value=c_tanggal, min_value=datetime.date(1950, 1, 1))
                    e_hp = st.text_input("4. Nomor HP (Kunci Data)", value=hp_tampil, disabled=True)
                    e_kerja = st.text_input("6. Pekerjaan", value=c_kerja)
                    e_pendidikan = st.selectbox("7. Pendidikan Terakhir", pilihan_pendidikan, index=get_idx(c_pendidikan, pilihan_pendidikan))
                with e_col2:
                    e_alamat = st.text_area("5. Alamat Tinggal", value=c_alamat)
                    e_kader = st.multiselect("8. Jenjang Pengkaderan", pilihan_pengkaderan, default=c_kader)
                    e_satkoryon = st.selectbox("9. Satkoryon", pilihan_satkoryon, index=get_idx(c_satkoryon, pilihan_satkoryon))
                    if e_satkoryon in data_desa:
                        e_satkorkel = st.selectbox("10. Satkorkel", data_desa[e_satkoryon], index=get_idx(c_satkorkel, data_desa[e_satkoryon]))
                    else:
                        e_satkorkel = st.text_input("10. Satkorkel", value=c_satkorkel)
                    e_satuan = st.selectbox("11. Satuan Khusus", pilihan_satuan, index=get_idx(c_satuan, pilihan_satuan))
                        
                st.divider()
                e_col3, e_col4 = st.columns(2)
                with e_col3:
                    e_minat = st.multiselect("12. Minat", pilihan_minat, default=c_minat)
                    e_bakat = st.multiselect("13. Bakat", pilihan_bakat, default=c_bakat)
                with e_col4:
                    e_grade = st.selectbox("14. Grade", pilihan_grade, index=get_idx(c_grade, pilihan_grade))
                    e_status = st.selectbox("15. Status", pilihan_status, index=get_idx(c_status, pilihan_status))
                    st.markdown(f"[Lihat Foto Saat Ini]({c_foto_url})")
                    e_foto = st.file_uploader("16. Ganti Foto (Kosongkan jika tidak ingin mengganti)", type=['jpg', 'jpeg', 'png'], key=st.session_state["edit_uploader_key"])

                submit_edit = st.form_submit_button("Simpan Perubahan Data", type="primary")
                
                if submit_edit:
                    with st.spinner("Memperbarui data ke database..."):
                        try:
                            final_foto_url = c_foto_url
                            if e_foto is not None:
                                compressed_new_foto = compress_image(e_foto)
                                final_foto_url = upload_to_imgbb(compressed_new_foto)
                                
                            hp_untuk_disimpan = f"'{hp_tampil}" 
                            waktu_update = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')
                            
                            # DISESUAIKAN MENJADI 18 VARIABEL
                            data_update = (
                                e_nama, e_tempat, str(e_tanggal), hp_untuk_disimpan, 
                                e_alamat, e_kerja, e_pendidikan, 
                                ", ".join(e_kader), e_satkoryon, e_satkorkel, e_satuan,
                                ", ".join(e_minat), ", ".join(e_bakat), e_grade, e_status, 
                                final_foto_url, waktu_update, st.session_state["nama_petugas"]
                            )
                            
                            update_data(row_number, data_update)
                            st.success("✅ Data berhasil diperbarui!")
                            time.sleep(1.5)
                            st.session_state["edit_uploader_key"] = str(uuid.uuid4())
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ Gagal memperbarui data: {e}")
