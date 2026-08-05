import streamlit as st
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

# Veritabanı bağlantısı
conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

# Tabloları oluşturma
cursor.execute('''
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT UNIQUE,
        sifre TEXT,
        rol TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS hesaplar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tur TEXT,
        isim TEXT,
        detay TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS islemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici TEXT,
        tur TEXT,
        tutar REAL,
        departman TEXT,
        aciklama TEXT,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS sistem_loglari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici TEXT,
        islem TEXT,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Varsayılan Admin hesabı yoksa oluştur
cursor.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = 'admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", 
                   ('admin', make_hashes('123456'), 'Yönetici'))
    conn.commit()

st.set_page_config(page_title="Kurumsal Finans ve Cüzdan Yönetimi", page_icon="💼", layout="wide")

# Özel CSS Tasarımı
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

if not st.session_state['logged_in']:
    st.title("🔐 Kurumsal Panel Giriş Ekranı")
    st.write("Lütfen sistemdeki kullanıcı adınız ve şifrenizle giriş yapın.")
    
    with st.form("login_form"):
        k_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        submit = st.form_submit_button("Giriş Yap")
        
        if submit:
            cursor.execute("SELECT sifre, rol FROM kullanicilar WHERE kullanici_adi = ?", (k_adi,))
            user = cursor.fetchone()
            if user and check_hashes(sifre, user[0]):
                st.session_state['logged_in'] = True
                st.session_state['username'] = k_adi
                st.session_state['role'] = user[1]
                
                # Giriş logu kaydet
                cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (k_adi, "Sisteme Giriş Yaptı"))
                conn.commit()
                
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")
else:
    st.sidebar.title(f"Hoş geldin, {st.session_state['username']}")
    st.sidebar.markdown(f"**Rol:** `{st.session_state['role']}`")
    st.sidebar.write("---")
    
    menu_secenekleri = [
        "🏠 Ana Sayfa & Özet", 
        "💳 Şirket IBAN & Kripto Cüzdanlar", 
        "➕ Yatırım / Çekim İşlemleri", 
        "📊 Geçmiş İşlemler & Raporlar"
    ]
    
    if st.session_state['role'] == 'Yönetici':
        menu_secenekleri.append("👥 Personel / Hesap Oluştur")
        menu_secenekleri.append("🛡️ Sistem Logları (Audit)")
        
    menu = st.sidebar.radio("📌 Menü Seçenekleri", menu_secenekleri)
    
    st.sidebar.write("---")
    if st.sidebar.button("🚪 Çıkış Yap"):
        cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (st.session_state['username'], "Sistemden Çıkış Yaptı"))
        conn.commit()
        
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.rerun()

    if menu == "🏠 Ana Sayfa & Özet":
        st.title("🏢 Kurumsal Finans ve Cüzdan Yönetim Paneli")
        st.markdown("---")
        st.write("Sistem üzerinden tüm yatırımları, çekimleri, departman bazlı hareketleri ve kurumsal cüzdanları yönetebilirsiniz.")
        
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Yatırım'")
        toplam_yatirim = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Çekim'")
        toplam_cekim = cursor.fetchone()[0] or 0.0
        
        net_durum = toplam_yatirim - toplam_cekim
        
        st.write("")
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Toplam Yatırım", f"{toplam_yatirim:,.2f} TL/USDT")
        col2.metric("🔴 Toplam Çekim", f"{toplam_cekim:,.2f} TL/USDT")
        col3.metric("💰 Net Kasa / Bakiye", f"{net_durum:,.2f} TL/USDT")
        
        st.write("---")
        st.subheader("📈 Departman Bazlı Dağılım Grafiği")
        
        # Grafik için verileri çek
        df_grafik = pd.read_sql_query("SELECT departman, SUM(tutar) as toplam FROM islemler GROUP BY departman", conn)
        if not df_grafik.empty:
            st.bar_chart(df_grafik.set_index('departman'))
        else:
            st.info("Grafik oluşturulabilmesi için henüz kayıtlı işlem bulunmuyor.")

    elif menu == "💳 Şirket IBAN & Kripto Cüzdanlar":
        st.subheader("💳 Kurumsal IBAN ve Kripto Cüzdan Yönetimi")
        st.markdown("---")
        
        with st.form("hesap_ekle_form"):
            hesap_turu = st.selectbox("Hesap Türü", ["Banka IBAN", "Kripto Cüzdan (USDT - TRC20/ERC20)"])
            isim = st.text_input("Borsa / Banka Adı (Örn: Binance USDT / Akbank Şirket)")
            detay = st.text_input("IBAN Numarası veya Cüzdan Adresi")
            kaydet_btn = st.form_submit_button("Cüzdanı / IBAN'ı Kaydet")
            
            if kaydet_btn:
                if isim and detay:
                    cursor.execute("INSERT INTO hesaplar (tur, isim, detay) VALUES (?, ?, ?)", (hesap_turu, isim, detay))
                    conn.commit()
                    cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (st.session_state['username'], f"Hesap Eklendi: {isim}"))
                    conn.commit()
                    st.success("Hesap başarıyla eklendi!")
                else:
                    st.error("Lütfen tüm alanları eksiksiz doldurun.")
                    
        st.write("---")
        st.subheader("📋 Kayıtlı Kurumsal Hesaplar Listesi")
        cursor.execute("SELECT id, tur, isim, detay FROM hesaplar")
        hesaplar = cursor.fetchall()
        if hesaplar:
            for h in hesaplar:
                st.info(f"**[{h[1]}]** — **{h[2]}** : ` {h[3]} `")
        else:
            st.warning("Henüz kayıtlı bir kurumsal hesap bulunmuyor.")

    elif menu == "➕ Yatırım / Çekim İşlemleri":
        st.subheader("➕ Yeni Yatırım veya Çekim Talebi Girişi")
        st.markdown("---")
        
        with st.form("islem_form"):
            islem_turu = st.radio("İşlem Türünü Seçin", ["Yatırım", "Çekim"])
            tutar = st.number_input("İşlem Tutarı", min_value=0.0, step=100.0)
            departman = st.selectbox("İlgili Departman", ["Pazarlama", "Yazılım / Teknoloji", "Operasyon", "Likidite / Finans", "Yönetim"])
            aciklama = st.text_area("İşlem Açıklaması / Referans Kodu / Not")
            islem_yap_btn = st.form_submit_button("İşlemi Onayla ve Kaydet")
            
            if islem_yap_btn:
                if tutar > 0:
                    cursor.execute("INSERT INTO islemler (kullanici, tur, tutar, departman, aciklama) VALUES (?, ?, ?, ?, ?)", 
                                   (st.session_state['username'], islem_turu, tutar, departman, aciklama))
                    conn.commit()
                    cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (st.session_state['username'], f"{islem_turu} Yapıldı: {tutar} TL ({departman})"))
                    conn.commit()
                    st.success(f"İşlem başarıyla kaydedildi! Tür: {islem_turu} | Tutar: {tutar} | Departman: {departman}")
                else:
                    st.error("Lütfen 0'dan büyük bir tutar girin!")

    elif menu == "📊 Geçmiş İşlemler & Raporlar":
        st.subheader("📊 Tüm Geçmiş İşlemler ve Excel Raporlama")
        st.markdown("---")
        
        # Filtreleme Seçenekleri
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtre_tur = st.selectbox("İşlem Türüne Göre Filtrele", ["Tümü", "Yatırım", "Çekim"])
        with col_f2:
            filtre_dept = st.selectbox("Departmana Göre Filtrele", ["Tümü", "Pazarlama", "Yazılım / Teknoloji", "Operasyon", "Likidite / Finans", "Yönetim"])
            
        sorgu = "SELECT id, kullanici, tur, tutar, departman, aciklama, tarih FROM islemler WHERE 1=1"
        parametreler = []
        
        if filtre_tur != "Tümü":
            sorgu += " AND tur = ?"
            parametreler.append(filtre_tur)
        if filtre_dept != "Tümü":
            sorgu += " AND departman = ?"
            parametreler.append(filtre_dept)
            
        sorgu += " ORDER BY id DESC"
        
        df_islemler = pd.read_sql_query(sorgu, conn, params=parametreler)
        
        if not df_islemler.empty:
            st.dataframe(df_islemler, use_container_width=True)
            
            # Excel İndirme Butonu
            csv_verisi = df_islemler.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Tabloyu CSV / Excel Olarak İndir",
                data=csv_verisi,
                file_name='kurumsal_finans_raporu.csv',
                mime='text/csv',
            )
        else:
            st.info("Seçilen kriterlere uygun işlem kaydı bulunmuyor.")

    elif menu == "👥 Personel / Hesap Oluştur" and st.session_state['role'] == 'Yönetici':
        st.subheader("👥 Çalışanlar İçin Yeni Panel Hesabı Oluştur")
        st.markdown("---")
        st.write("Çalışanların kendi kullanıcı adı ve şifreleriyle sisteme giriş yapıp işlem yapabilmesi için buradan hesap açabilirsiniz.")
        
        with st.form("personel_form"):
            yeni_k_adi = st.text_input("Personel Kullanıcı Adı")
            yeni_sifre = st.text_input("Personel Şifresi", type="password")
            rol_secim = st.selectbox("Personel Rolü", ["Çalışan", "Yönetici"])
            personel_olustur_btn = st.form_submit_button("Personel Hesabı Oluştur")
            
            if personel_olustur_btn:
                if yeni_k_adi and yeni_sifre:
                    try:
                        cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", 
                                       (yeni_k_adi, make_hashes(yeni_sifre), rol_secim))
                        conn.commit()
                        cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (st.session_state['username'], f"Personel Hesabı Açıldı: {yeni_k_adi}"))
                        conn.commit()
                        st.success(f"'{yeni_k_adi}' adlı kullanıcı başarıyla oluşturuldu!")
                    except:
                        st.error("Bu kullanıcı adı zaten sistemde mevcut, başka bir ad deneyin.")
                else:
                    st.error("Lütfen tüm alanları doldurun.")
                    
        st.write("---")
        st.subheader("📋 Mevcut Sistem Kullanıcıları")
        cursor.execute("SELECT id, kullanici_adi, rol FROM kullanicilar")
        kisiler = cursor.fetchall()
        for k in kisiler:
            st.markdown(f"👤 **{k[1]}** (Rol: `{k[2]}`)")

    elif menu == "🛡️ Sistem Logları (Audit)" and st.session_state['role'] == 'Yönetici':
        st.subheader("🛡️ Sistem Güvenlik ve Aktivite Logları")
        st.markdown("---")
        st.write("Sistemdeki tüm kullanıcı hareketleri, giriş çıkışlar ve işlem kayıtları aşağıda tutulmaktadır.")
        
        df_loglar = pd.read_sql_query("SELECT id, kullanici, islem, tarih FROM sistem_loglari ORDER BY id DESC", conn)
        if not df_loglar.empty:
            st.dataframe(df_loglar, use_container_width=True)
        else:
            st.info("Henüz sistem logu bulunmuyor.")
