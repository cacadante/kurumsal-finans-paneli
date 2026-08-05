import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import secrets

# Sol menüyü ve çoklu sayfa görünümünü tamamen gizleyen CSS
st.set_page_config(page_title="Kurumsal Finans ve API Gateway", page_icon="💼", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    .main { background-color: #0b0f19; }
    .stMetric { background: linear-gradient(135deg, #1f2937 0%, #111827 100%); padding: 20px; border-radius: 12px; border: 1px solid #374151; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #111827; padding: 10px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f2937; border-radius: 6px; color: white; padding: 8px 16px; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: #2563eb !important; }
    </style>
""", unsafe_allow_html=True)

conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS kullanicilar (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_adi TEXT UNIQUE, sifre TEXT, rol TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS hesaplar (id INTEGER PRIMARY KEY AUTOINCREMENT, tur TEXT, isim TEXT, detay TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, tur TEXT, tutar REAL, departman TEXT, aciklama TEXT, dekont TEXT, durum TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
cursor.execute('CREATE TABLE IF NOT EXISTS sistem_loglari (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, islem TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
cursor.execute('CREATE TABLE IF NOT EXISTS api_anahtarlari (id INTEGER PRIMARY KEY AUTOINCREMENT, sirket_adi TEXT, api_key TEXT UNIQUE, webhook_url TEXT, gunluk_limit REAL, olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
conn.commit()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

cursor.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = 'admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", ('admin', make_hashes('123456'), 'Yönetici'))
    conn.commit()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

# GİRİŞ YAPILMAMIŞSA KESİNLİKLE İÇERİ GÖSTERME
if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("## 🔐 Kurumsal Panel Güvenli Giriş")
        st.write("Devam etmek için lütfen giriş yapın.")
        with st.form("login_form"):
            k_adi = st.text_input("Kullanıcı Adı")
            sifre = st.text_input("Şifre", type="password")
            if st.form_submit_button("Giriş Yap", use_container_width=True):
                cursor.execute("SELECT sifre, rol FROM kullanicilar WHERE kullanici_adi = ?", (k_adi,))
                user = cursor.fetchone()
                if user and check_hashes(sifre, user[0]):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = k_adi
                    st.session_state['role'] = user[1]
                    cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (k_adi, "Sisteme Giriş Yaptı"))
                    conn.commit()
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")
else:
    col_baslik, col_cikis = st.columns([8, 2])
    col_baslik.title("🏢 Kurumsal Finans & API Gateway")
    
    if col_cikis.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state['logged_in'] = False
        st.session_state['username'] = ''
        st.session_state['role'] = ''
        st.rerun()

    st.markdown(f"👤 Aktif Kullanıcı: **{st.session_state['username']}** &nbsp;|&nbsp; 🛡️ Rol: `{st.session_state['role']}`")
    st.markdown("---")

    if st.session_state['role'] == 'Yönetici':
        tab_listesi = ["🏠 Ana Sayfa", "💳 Cüzdanlar", "➕ Talep Oluştur", "🔔 Gelen Talepler & Onay", "📊 Geçmiş & Filtreler", "🔑 Partner API & Kotalar", "👥 Personel Yönetimi", "🛡️ Sistem Logları"]
    else:
        tab_listesi = ["🏠 Ana Sayfa", "💳 Cüzdanlar", "➕ Talep Oluştur", "📊 Geçmiş İşlemler"]

    sekmeler = st.tabs(tab_listesi)

    with sekmeler[0]:
        st.subheader("📊 Genel Finansal Özet (Onaylanan İşlemler)")
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Yatırım' AND durum = 'Onaylandı'")
        res_yat = cursor.fetchone()
        t_yatirim = res_yat[0] if res_yat and res_yat[0] is not None else 0.0
        
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Çekim' AND durum = 'Onaylandı'")
        res_cek = cursor.fetchone()
        t_cekim = res_cek[0] if res_cek and res_cek[0] is not None else 0.0
        
        net = t_yatirim - t_cekim

        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 Toplam Yatırım", f"{t_yatirim:,.2f} TL/USDT")
        c2.metric("🔴 Toplam Çekim", f"{t_cekim:,.2f} TL/USDT")
        c3.metric("💰 Net Kasa / Bakiye", f"{net:,.2f} TL/USDT")

    with sekmeler[1]:
        st.subheader("💳 Şirket IBAN & Kripto Cüzdan Yönetimi")
        with st.form("h_form"):
            h_tur = st.selectbox("Tür", ["Banka IBAN", "Kripto Cüzdan"])
            isim = st.text_input("Borsa / Banka Adı")
            detay = st.text_input("IBAN / Cüzdan Adresi")
            if st.form_submit_button("Cüzdanı / IBAN'ı Kaydet"):
                if isim and detay:
                    cursor.execute("INSERT INTO hesaplar (tur, isim, detay) VALUES (?, ?, ?)", (h_tur, isim, detay))
                    conn.commit()
                    st.success("Hesap başarıyla eklendi!")
        
        st.markdown("---")
        cursor.execute("SELECT tur, isim, detay FROM hesaplar")
        for h in cursor.fetchall():
            st.info(f"**[{h[0]}]** {h[1]} : `{h[2]}`")

    with sekmeler[2]:
        st.subheader("➕ Yeni Yatırım veya Çekim Talebi Gönder")
        with st.form("i_form"):
            i_tur = st.radio("İşlem Türü", ["Yatırım", "Çekim"], horizontal=True)
            tutar = st.number_input("Tutar", min_value=0.0)
            dept = st.selectbox("Departman", ["Pazarlama", "Yazılım / Teknoloji", "Operasyon", "Likidite / Finans", "Yönetim"])
            notlar = st.text_area("Açıklama / Not / Referans")
            dekont_dosya = st.file_uploader("Dekont / Fatura Yükle", type=["png", "jpg", "jpeg", "pdf"])
            
            if st.form_submit_button("Talebi Onaya Gönder"):
                if tutar > 0:
                    dosya_adi = dekont_dosya.name if dekont_dosya else "Dekont Yok"
                    cursor.execute("INSERT INTO islemler (kullanici, tur, tutar, departman, aciklama, dekont, durum) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                   (st.session_state['username'], i_tur, tutar, dept, notlar, dosya_adi, "Beklemede"))
                    conn.commit()
                    st.success("Talebiniz başarıyla yönetici onayına gönderildi!")

    if st.session_state['role'] == 'Yönetici':
        with sekmeler[3]:
            st.subheader("🔔 Kademeli Onay Merkezi (Maker-Checker)")
            cursor.execute("SELECT id, kullanici, tur, tutar, departman, aciklama, dekont, tarih, durum FROM islemler WHERE durum LIKE 'Beklemede%' ORDER BY id DESC")
            bekleyenler = cursor.fetchall()
            
            if bekleyenler:
                for b in bekleyenler:
                    b_id, b_kul, b_tur, b_tutar, b_dept, b_aciklama, b_dekont, b_tarih, b_durum = b
                    with st.container():
                        st.markdown(f"### 📌 Talep ID: #{b_id} | Şirket/Kullanıcı: **{b_kul}** | Tür: **{b_tur}**")
                        st.write(f"🏢 **Departman:** {b_dept} | 💵 **Tutar:** `{b_tutar:,.2f}` | 🕒 **Tarih:** {b_tarih}")
                        st.write(f"📝 **Not:** {b_aciklama}")
                        
                        col_onay, col_ret, _ = st.columns([1, 1, 4])
                        with col_onay:
                            if st.button("✅ Onayla", key=f"onay_{b_id}"):
                                cursor.execute("UPDATE islemler SET durum = 'Onaylandı' WHERE id = ?", (b_id,))
                                cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (st.session_state['username'], f"Talep Onaylandı (#{b_id})"))
                                conn.commit()
                                st.success(f"#{b_id} numaralı talep onaylandı!")
                                st.rerun()
                        with col_ret:
                            if st.button("❌ Reddet", key=f"ret_{b_id}"):
                                cursor.execute("UPDATE islemler SET durum = 'Reddedildi' WHERE id = ?", (b_id,))
                                cursor.execute("INSERT INTO sistem_loglari (kullanici, islem) VALUES (?, ?)", (st.session_state['username'], f"Talep Reddedildi (#{b_id})"))
                                conn.commit()
                                st.error(f"#{b_id} reddedildi.")
                                st.rerun()
                        st.markdown("---")
            else:
                st.info("Onay bekleyen talep bulunmuyor.")

        with sekmeler[4]:
            st.subheader("📊 Gelişmiş Filtreleme & Raporlar")
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                f_kul = st.text_input("Kullanıcı / Şirket Ara")
            with c_f2:
                f_tur = st.selectbox("İşlem Türü", ["Tümü", "Yatırım", "Çekim"])
            with c_f3:
                f_durum = st.selectbox("Durum", ["Tümü", "Onaylandı", "Beklemede", "Reddedildi"])
                
            sorgu = "SELECT id, kullanici, tur, tutar, departman, aciklama, dekont, durum, tarih FROM islemler WHERE 1=1"
            parametreler = []
            if f_kul:
                sorgu += " AND kullanici LIKE ?"
                parametreler.append(f"%{f_kul}%")
            if f_tur != "Tümü":
                sorgu += " AND tur = ?"
                parametreler.append(f_tur)
            if f_durum != "Tümü":
                sorgu += " AND durum LIKE ?"
                parametreler.append(f"%{f_durum}%")
                
            sorgu += " ORDER BY id DESC"
            df = pd.read_sql_query(sorgu, conn, params=parametreler)
            
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Excel / CSV İndir", df.to_csv(index=False).encode('utf-8'), "rapor.csv", "text/csv")
            else:
                st.info("Kayıt bulunamadı.")

        with sekmeler[5]:
            st.subheader("🔑 Partner API Anahtarları ve Kotalar")
            with st.form("api_form"):
                s_adi = st.text_input("Partner Şirket Adı")
                w_url = st.text_input("Webhook URL")
                g_limit = st.number_input("Günlük Limit (TL/USDT)", min_value=0.0, step=10000.0, value=100000.0)
                if st.form_submit_button("API Key Üret"):
                    if s_adi:
                        yeni_key = "pk_" + secrets.token_hex(16)
                        cursor.execute("INSERT INTO api_anahtarlari (sirket_adi, api_key, webhook_url, gunluk_limit) VALUES (?, ?, ?, ?)", (s_adi, yeni_key, w_url, g_limit))
                        conn.commit()
                        st.success(f"'{s_adi}' için API Key üretildi!")
                    else:
                        st.error("Şirket adı girin.")
                        
            st.markdown("---")
            cursor.execute("SELECT id, sirket_adi, api_key, webhook_url, gunluk_limit FROM api_anahtarlari")
            apiler = cursor.fetchall()
            if apiler:
                for api in apiler:
                    st.info(f"🏢 **{api[1]}** | Key: `{api[2]}` | Limit: `{api[4]:,.2f}`")
            else:
                st.warning("API anahtarı yok.")

        with sekmeler[6]:
            st.subheader("👥 Personel Yönetimi")
            with st.form("p_form"):
                pk = st.text_input("Kullanıcı Adı")
                ps = st.text_input("Şifre", type="password")
                pr = st.selectbox("Rol", ["Çalışan", "Yönetici"])
                if st.form_submit_button("Personel Aç"):
                    try:
                        cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", (pk, make_hashes(ps), pr))
                        conn.commit()
                        st.success("Personel eklendi!")
                    except:
                        st.error("Bu kullanıcı adı var.")

            st.markdown("---")
            cursor.execute("SELECT kullanici_adi, rol FROM kullanicilar")
            for p in cursor.fetchall():
                st.markdown(f"👤 **{p[0]}** ({p[1]})")

        with sekmeler[7]:
            st.subheader("🛡️ Sistem Logları ve Veritabanı Yedeği")
            with open("finance_panel.db", "rb") as db_file:
                st.download_button("💾 Veritabanını Yedekle (.db)", db_file, "finance_panel_yedek.db", "application/octet-stream")
            st.markdown("---")
            df_l = pd.read_sql_query("SELECT * FROM sistem_loglari ORDER BY id DESC", conn)
            st.dataframe(df_l, use_container_width=True)
    else:
        with sekmeler[3]:
            st.subheader("📊 Tüm İşlem Geçmişi")
            df = pd.read_sql_query("SELECT id, kullanici, tur, tutar, departman, aciklama, dekont, durum, tarih FROM islemler ORDER BY id DESC", conn)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.download_button("📥 Excel / CSV İndir", df.to_csv(index=False).encode('utf-8'), "rapor.csv", "text/csv")
            else:
                st.info("Kayıt bulunamadı.")
