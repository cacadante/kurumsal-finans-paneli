import streamlit as st
import sqlite3
import pandas as pd
import hashlib

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return True
    return False

conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

# Tablolar
cursor.execute('CREATE TABLE IF NOT EXISTS kullanicilar (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_adi TEXT UNIQUE, sifre TEXT, rol TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS hesaplar (id INTEGER PRIMARY KEY AUTOINCREMENT, tur TEXT, isim TEXT, detay TEXT)')
cursor.execute('CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, tur TEXT, tutar REAL, departman TEXT, aciklama TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
cursor.execute('CREATE TABLE IF NOT EXISTS sistem_loglari (id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici TEXT, islem TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
conn.commit()

cursor.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = 'admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)", ('admin', make_hashes('123456'), 'Yönetici'))
    conn.commit()

st.set_page_config(page_title="Kurumsal Finans ve Cüzdan Yönetimi", page_icon="💼", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'role' not in st.session_state:
    st.session_state['role'] = ''

if not st.session_state['logged_in']:
    st.title("🔐 Kurumsal Panel Giriş Ekranı")
    with st.form("login_form"):
        k_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.form_submit_button("Giriş Yap"):
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
    col_baslik.title("🏢 Kurumsal Finans ve Cüzdan Yönetim Paneli")
    if col_cikis.button("🚪 Çıkış Yap"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.markdown(f"Aktif Kullanıcı: **{st.session_state['username']}** | Rol: `{st.session_state['role']}`")
    st.markdown("---")

    # Üst Sekmeler Sistemi (Asla kaybolmaz, her şey elinin altında)
    tab_listesi = ["🏠 Ana Sayfa", "💳 Cüzdanlar", "➕ İşlem Ekle", "📊 Geçmiş & Raporlar"]
    if st.session_state['role'] == 'Yönetici':
        tab_listesi.extend(["👥 Personel Yönetimi", "🛡️ Sistem Logları"])

    sekmeler = st.tabs(tab_listesi)

    with sekmeler[0]:
        st.subheader("Genel Finansal Özet")
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Yatırım'")
        t_yatirim = cursor.fetchone()[0] or 0.0
        cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Çekim'")
        t_cekim = cursor.fetchone()[0] or 0.0
        net = t_yatirim - t_cekim

        c1, c2, c3 = st.columns(3)
        c1.metric("🟢 Toplam Yatırım", f"{t_yatirim:,.2f} TL/USDT")
        c2.metric("🔴 Toplam Çekim", f"{t_cekim:,.2f} TL/USDT")
        c3.metric("💰 Net Kasa", f"{net:,.2f} TL/USDT")

        st.write("---")
        df_g = pd.read_sql_query("SELECT departman, SUM(tutar) as toplam FROM islemler GROUP BY departman", conn)
        if not df_g.empty:
            st.bar_chart(df_g.set_index('departman'))
        else:
            st.info("Grafik için henüz veri yok.")

    with sekmeler[1]:
        st.subheader("Şirket IBAN & Kripto Cüzdanlar")
        with st.form("h_form"):
            h_tur = st.selectbox("Tür", ["Banka IBAN", "Kripto Cüzdan"])
            isim = st.text_input("Borsa / Banka Adı")
            detay = st.text_input("IBAN / Cüzdan Adresi")
            if st.form_submit_button("Kaydet"):
                if isim and detay:
                    cursor.execute("INSERT INTO hesaplar (tur, isim, detay) VALUES (?, ?, ?)", (h_tur, isim, detay))
                    conn.commit()
                    st.success("Kaydedildi!")
        
        cursor.execute("SELECT tur, isim, detay FROM hesaplar")
        for h in cursor.fetchall():
            st.info(f"**[{h[0]}]** {h[1]} : `{h[2]}`")

    with sekmeler[2]:
        st.subheader("Yeni Yatırım / Çekim Talebi")
        with st.form("i_form"):
            i_tur = st.radio("İşlem Türü", ["Yatırım", "Çekim"])
            tutar = st.number_input("Tutar", min_value=0.0)
            dept = st.selectbox("Departman", ["Pazarlama", "Yazılım / Teknoloji", "Operasyon", "Likidite / Finans", "Yönetim"])
            notlar = st.text_area("Açıklama / Not")
            if st.form_submit_button("İşlemi Kaydet"):
                if tutar > 0:
                    cursor.execute("INSERT INTO islemler (kullanici, tur, tutar, departman, aciklama) VALUES (?, ?, ?, ?, ?)", 
                                   (st.session_state['username'], i_tur, tutar, dept, notlar))
                    conn.commit()
                    st.success("İşlem başarıyla eklendi!")

    with sekmeler[3]:
        st.subheader("Geçmiş İşlemler ve Excel Raporu")
        df = pd.read_sql_query("SELECT * FROM islemler ORDER BY id DESC", conn)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button("📥 Excel / CSV İndir", df.to_csv(index=False).encode('utf-8'), "rapor.csv", "text/csv")
        else:
            st.info("Kayıt bulunamadı.")

    if st.session_state['role'] == 'Yönetici':
        with sekmeler[4]:
            st.subheader("Personel Ekle")
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
                        st.error("Bu kullanıcı adı zaten var.")

            cursor.execute("SELECT kullanici_adi, rol FROM kullanicilar")
            for p in cursor.fetchall():
                st.markdown(f"👤 **{p[0]}** ({p[1]})")

        with sekmeler[5]:
            st.subheader("Sistem Logları")
            df_l = pd.read_sql_query("SELECT * FROM sistem_loglari ORDER BY id DESC", conn)
            st.dataframe(df_l, use_container_width=True)
