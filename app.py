import streamlit as st
import pandas as pd
import datetime
import time 
import io
import altair as alt
import json
import gspread

# ---------------------------------
# 1. KONFIGURASI DATABASE (GOOGLE SHEETS VIA SECRETS)
# ---------------------------------
@st.cache_resource
def init_connection():
    # Membaca data rahasia dari brankas Streamlit Cloud
    secrets_dict = dict(st.secrets["gcp_service_account"])
    return gspread.service_account_from_dict(secrets_dict)

client = init_connection()
SHEET_NAME = 'Database_Banser_X7' 
sheet = client.open(SHEET_NAME).sheet1

def insert_data(data):
    # Menambahkan data sebagai baris baru di Excel online
    sheet.append_row(list(data))

def get_all_data():
    # Mengambil semua baris data
    records = sheet.get_all_records()
    
    # Jika Google Sheets hanya berisi header (belum ada data)
    if not records:
        return pd.DataFrame(columns=[
            'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 'nomor_hp', 
            'alamat_tinggal', 'pekerjaan', 'pendidikan_terakhir', 
            'tingkat_pengkaderan', 'satkoryon', 'satkorkel', 
            'minat_bakat', 'status_keanggotaan', 'waktu_input'
        ])
        
    df = pd.DataFrame(records)
    
    # Memaksa nama kolom agar seragam dengan sistem sebelumnya untuk grafik
    df.columns = [
        'nama_lengkap', 'tempat_lahir', 'tanggal_lahir', 'nomor_hp', 
        'alamat_tinggal', 'pekerjaan', 'pendidikan_terakhir', 
        'tingkat_pengkaderan', 'satkoryon', 'satkorkel', 
        'minat_bakat', 'status_keanggotaan', 'waktu_input'
    ]
    return df

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
# 4. TAB 1: FORM PENGINPUTAN
# ---------------------------------
with tab1:
    st.subheader("Data Anggota")
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
    st.subheader("Data Keorganisasian")
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
        
    with col4:
        status = st.selectbox("12. Status Keanggotaan *", ["", "Aktif", "Tidak Aktif", "Pindah Domisili", "Lulus"], key="inp_status")
        pilihan_minat = ["Olahraga", "Musik", "Seni Rupa", "Menulis", "Matematika", "Bahasa", "Sejarah & Budaya", "Teknologi", "Kuliner", "Mekanik", "Petualangan", "Kegiatan Sosial", "Keagamaan", "Dunia Digital", "Game", "Lainnya_"]
        minat_bakat_list = st.multiselect("11. Minat & Bakat *", pilihan_minat, key="inp_minat")

    st.markdown("**Catatan: Semua kolom dengan tanda (*) wajib diisi.**")
    
    if st.button("Simpan Data Anggota", type="primary"):
        if nama and tempat_lahir and tanggal_lahir and no_hp and pekerjaan and pendidikan and alamat and pengkaderan_list and satkoryon and satkorkel and status and minat_bakat_list:
            
            # Persiapan data untuk Google Sheets
            pengkaderan_str = ", ".join(pengkaderan_list)
            minat_bakat_str = ", ".join(minat_bakat_list) 
            waktu_input = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Format data persis mengikuti urutan kolom di Google Sheets Anda
            data_baru = (
                nama, tempat_lahir, str(tanggal_lahir), no_hp, 
                alamat, pekerjaan, pendidikan, 
                pengkaderan_str, satkoryon, satkorkel, 
                minat_bakat_str, status, waktu_input
            )
            
            with st.spinner("Menyimpan ke awan..."):
                insert_data(data_baru)
            
            st.success(f"✅ Data atas nama **{nama}** berhasil disimpan ke Google Sheets!")
            time.sleep(1.5)
            st.session_state.clear()
            st.rerun()
        else:
            st.error("⚠️ Mohon lengkapi seluruh form pendaftaran. Pastikan tidak ada kolom yang terlewat.")

# ---------------------------------
# 5. TAB 2: TAMPILAN DATABASE
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
        st.dataframe(df_tampil, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data anggota yang terdaftar di Google Sheets.")

# ---------------------------------
# 6. TAB 3: DASHBOARD STATISTIK
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
        st.markdown("**5. Peta Minat & Bakat Anggota**")
        semua_minat = df_anggota['minat_bakat'].dropna().astype(str).str.split(', ').explode()
        minat_count = semua_minat[semua_minat != ""].value_counts().reset_index()
        minat_count.columns = ['Minat & Bakat', 'Jumlah']
        chart_minat = alt.Chart(minat_count).mark_bar(color='#4e79a7').encode(
            x=alt.X('Jumlah:Q', title='Jumlah Peminat'),
            y=alt.Y('Minat & Bakat:N', sort='-x', title='Kategori Minat'),
            tooltip=['Minat & Bakat', 'Jumlah']
        ).properties(height=400)
        st.altair_chart(chart_minat, use_container_width=True)

    else:
        st.info("Visualisasi akan muncul setelah ada minimal satu data anggota yang diinput di Google Sheets.")
