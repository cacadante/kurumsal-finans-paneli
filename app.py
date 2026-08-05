import streamlit as st
import sqlite3

# Veritabanı bağlantısı ve tablo oluşturma
conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

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

menu = st.sidebar.selectbox("Menü", ["İşlem Ekle (Yatırım/Çekim)", "Geçmiş İşlemler"])

if menu == "İşlem Ekle (Yatırım/Çekim)":
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
