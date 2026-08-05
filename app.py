import streamlit as st
import sqlite3

# Veritabanı bağlantısı
conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

# Tabloları oluşturma (Hesaplar ve İşlemler)
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
        tur TEXT,
        tutar REAL,
        aciklama TEXT,
        tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

st.set_page_config(page_title="Kurumsal Finans Paneli", page_icon="💰", layout="centered")

st.title("🏢 Kurumsal Finans ve Cüzdan Yönetim Paneli")
st.write("---")

# Genişletilmiş Menü
menu = st.sidebar.selectbox("Menü", ["Hesap Ekle / Yönet", "İşlem Ekle (Yatırım/Çekim)", "Geçmiş İşlemler"])

if menu == "Hesap Ekle / Yönet":
    st.subheader("💳 Kurumsal IBAN veya Kripto Cüzdan Ekle")
    
    hesap_turu = st.selectbox("Hesap Türü", ["Banka IBAN", "Kripto Cüzdan (USDT vb.)"])
    isim = st.text_input("Hesap Sahibi / Borsası (Örn: Şirket Akbank / Binance)")
    detay = st.text_input("IBAN veya Cüzdan Adresi")
    
    if st.button("Hesabı Kaydet"):
        if isim and detay:
            cursor.execute("INSERT INTO hesaplar (tur, isim, detay) VALUES (?, ?, ?)", (hesap_turu, isim, detay))
            conn.commit()
            st.success(f"Başarıyla eklendi: {isim} ({hesap_turu})")
        else:
            st.error("Lütfen tüm alanları doldurun!")
            
    st.write("---")
    st.subheader("📋 Kayıtlı Hesaplar")
    cursor.execute("SELECT id, tur, isim, detay FROM hesaplar")
    hesaplar = cursor.fetchall()
    if hesaplar:
        for h in hesaplar:
            st.info(f"**{h[1]}** - {h[2]} : `+{h[3]}`")
    else:
        st.warning("Henüz kayıtlı hesap bulunmuyor.")

elif menu == "İşlem Ekle (Yatırım/Çekim)":
    st.subheader("➕ Yeni Finansal İşlem Ekle")
    
    islem_turu = st.radio("İşlem Türünü Seçin", ["Yatırım", "Çekim"])
    tutar = st.number_input("Tutar (TL / USDT vb.)", min_value=0.0, step=100.0)
    aciklama = st.text_area("Açıklama / Not")
    
    if st.button("İşlemi Kaydet"):
        if tutar > 0:
            cursor.execute("INSERT INTO islemler (tur, tutar, aciklama) VALUES (?, ?, ?)", (islem_turu, tutar, aciklama))
            conn.commit()
            st.success(f"Başarıyla kaydedildi! İşlem Türü: {islem_turu} | Tutar: {tutar}")
        else:
            st.error("Lütfen 0'dan büyük bir tutar girin!")

elif menu == "Geçmiş İşlemler":
    st.subheader("📊 Tüm Yatırım ve Çekim Geçmişi")
    
    cursor.execute("SELECT id, tur, tutar, aciklama, tarih FROM islemler ORDER BY id DESC")
    veriler = cursor.fetchall()
    
    if veriler:
        for row in veriler:
            islem_id, tur, tutar, aciklama, tarih = row
            if tur == "Yatırım":
                st.success(f"🟢 **{tur}** | Tutar: **{tutar}** | Not: {aciklama} | Tarih: {tarih}")
            else:
                st.error(f"🔴 **{tur}** | Tutar: **{tutar}** | Not: {aciklama} | Tarih: {tarih}")
    else:
        st.info("Henüz kayıtlı bir işlem bulunmuyor.")
