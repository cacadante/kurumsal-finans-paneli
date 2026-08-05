import streamlit as st
import sqlite3

conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

st.title("➕ Yatırım / Çekim İşlemleri")
st.markdown("---")

with st.form("islem_form"):
    islem_turu = st.radio("İşlem Türünü Seçin", ["Yatırım", "Çekim"])
    tutar = st.number_input("İşlem Tutarı", min_value=0.0, step=100.0)
    departman = st.selectbox("İlgili Departman", ["Pazarlama", "Yazılım / Teknoloji", "Operasyon", "Likidite / Finans", "Yönetim"])
    aciklama = st.text_area("İşlem Açıklaması / Referans")
    islem_yap_btn = st.form_submit_button("İşlemi Onayla ve Kaydet")
    
    if islem_yap_btn:
        if tutar > 0:
            cursor.execute("INSERT INTO islemler (kullanici, tur, tutar, departman, aciklama) VALUES (?, ?, ?, ?, ?)", 
                           ("admin", islem_turu, tutar, departman, aciklama))
            conn.commit()
            st.success(f"İşlem başarıyla kaydedildi! Tür: {islem_turu} | Tutar: {tutar}")
        else:
            st.error("Lütfen 0'dan büyük bir tutar girin!")
