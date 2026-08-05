import streamlit as st
import sqlite3
import hashlib

# Şifreleme fonksiyonu
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
        aciklama TEXT,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# Varsayılan Admin hesabı yoksa oluştur (Kullanıcı: admin, Şifre: 123456)
cursor.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = 'admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", 
                   ('admin', make_hashes('123456'), 'Yönetici'))
    conn.commit()

st.set_page_config(page_title="Kurumsal Finans ve Cüzdan Yönetimi", page_icon="💼", layout="wide")

# Oturum Yönetimi
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# Giriş Ekranı
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
                st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")
else:
    # Ana Panel Arayüzü
    st.sidebar.title(f"Hoş geldin, {st.session_state['username']}")
    st.sidebar.markdown(f"**Rol:** `{st.session_state['role']}`")
    st.sidebar.write("---")
    
    menu_secenekleri = ["🏠 Ana Sayfa & Özet", "💳 Şirket IBAN & Kripto Cüzdanlar", "➕ Yatırım / Çekim İşlemleri", "📊 Geçmiş İşlemler"]
    
    # Eğer yönetici ise personel ekleme menüsünü de ekle
    if st.session_state['role'] == 'Yönetici':
        menu_secenekleri.append("👥 Personel / Hesap Oluştur")
        
    menu = st.sidebar.selectbox("Menü", menu_secenekleri)
    
    if st.sidebar.button("Çıkış Yap"):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.rerun()

    if menu == "🏠 Ana Sayfa & Özet":
        st.title("🏢 Kurumsal Finans ve Cüzdan Yönetim Paneli")
        st.write("Sistem üzerinden tüm yatırımları, çekimleri ve kurumsal cüzdanları güvenli bir şekilde yönetebilirsiniz.")
        
        # İstatistikler için verileri çek
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Yatırım'")
        toplam_yatirim = cursor.fetchone()[0] or 0.0
        
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Çekim'")
        toplam_cekim = cursor.fetchone()[0] or 0.0
        
        net_durum = toplam_yatirim - toplam_cekim
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Toplam Yatırım", f"{toplam_yatirim:,.2f} TL/USDT")
        col2.metric("🔴 Toplam Çekim", f"{toplam_cekim:,.2f} TL/USDT")
        col3.metric("💰 Net Kasa / Bakiye", f"{net_durum:,.2f} TL/USDT")

    elif menu == "💳 Şirket IBAN & Kripto Cüzdanлар":
        st.subheader("💳 Kurumsal IBAN ve Kripto Cüzdan Yönetimi")
        
        with st.form("hesap_ekle_form"):
            hesap_turu = st.selectbox("Hesap Türü", ["Banka IBAN", "Kripto Cüzdan (USDT - TRC20/ERC20)"])
            isim = st.text_input("Borsa / Banka Adı (Örn: Binance USDT / Akbank Şirket)")
            detay = st.text_input("IBAN Numarası veya Cüzdan Adresi")
            kaydet_btn = st.form_submit_button("Cüzdanı / IBAN'ı Kaydet")
            
            if kaydet_btn:
                if isim and detay:
                    cursor.execute("INSERT INTO hesaplar (tur, isim, detay) VALUES (?, ?, ?)", (hesap_turu, isim, detay))
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
        
        with st.form("islem_form"):
            islem_turu = st.radio("İşlem Türünü Seçin", ["Yatırım", "Çekim"])
            tutar = st.number_input("İşlem Tutarı", min_value=0.0, step=100.0)
            aciklama = st.text_area("İşlem Açıklaması / Referans Kodu / Not")
            islem_yap_btn = st.form_submit_button("İşlemi Onayla ve Kaydet")
            
            if islem_yap_btn:
                if tutar > 0:
                    cursor.execute("INSERT INTO islemler (kullanici, tur, tutar, aciklama) VALUES (?, ?, ?, ?)", 
                                   (st.session_state['username'], islem_turu, tutar, aciklama))
                    conn.commit()
                    st.success(f"İşlem başarıyla kaydedildi! Tür: {islem_turu} | Tutar: {tutar}")
                else:
                    st.error("Lütfen 0'dan büyük bir tutar girin!")

    elif menu == "📊 Geçmiş İşlemler":
        st.subheader("📊 Tüm Yatırım ve Çekim Geçmişi Logları")
        
        cursor.execute("SELECT id, kullanici, tur, tutar, aciklama, tarih FROM islemler ORDER BY id DESC")
        veriler = cursor.fetchall()
        
        if veriler:
            for row in veriler:
                i_id, k_adi, tur, tutar, aciklama, tarih = row
                if tur == "Yatırım":
                    st.success(f"🟢 **{tur}** | Tutar: **{tutar:,.2f}** | Yapan: *{k_adi}* | Not: {aciklama} | Tarih: {tarih}")
                else:
                    st.error(f"🔴 **{tur}** | Tutar: **{tutar:,.2f}** | Yapan: *{k_adi}* | Not: {aciklama} | Tarih: {tarih}")
        else:
            st.info("Henüz geçmiş işlem kaydı bulunmuyor.")

    elif menu == "👥 Personel / Hesap Oluştur" and st.session_state['role'] == 'Yönetici':
        st.subheader("👥 Çalışanlar İçin Yeni Panel Hesabı Oluştur")
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
                        st.success(f"'{yeni_k_adi}' adlı kullanıcı başarıyla oluşturuldu!")
                    except:
                        st.error("Bu kullanıcı adı zaten sistemde mevcut, başka bir ad deneyin.")
                else:
                    st.error("Lütfen tüm alanları doldurun.")
                    
        st.write("---")
        st.subheader("📋 Mevcut Sistem Kullanıcıları")
        cursor.execute("SELECT id, kullanici_adi, rol FROM kullanicilar")
        Kisiler = cursor.fetchall()
        for k in Kisiler:
            st.write(- f"**{k[1]}** (Rol: `{k[2]}`)")
