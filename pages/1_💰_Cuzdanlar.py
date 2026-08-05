import streamlit as st
import sqlite3

conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

st.title("💳 Şirket IBAN & Kripto Cüzdanlar")
st.markdown("---")

with st.form("hesap_ekle_form"):
    hesap_turu = st.selectbox("Hesap Türü", ["Banka IBAN", "Kripto Cüzdan (USDT - TRC20/ERC20)"])
    isim = st.text_input("Borsa / Banka Adı")
    detay = st.text_input("IBAN Numarası veya Cüzdan Adresi")
    kaydet_btn = st.form_submit_button("Cüzdanı / IBAN'ı Kaydet")
    
    if kaydet_btn:
        if isim and detay:
            cursor.execute("INSERT INTO hesaplar (tur, isim, detay) VALUES (?, ?, ?)", (hesap_turu, isim, detay))
            conn.commit()
            st.success("Hesap başarıyla eklendi!")
        else:
            st.error("Lütfen tüm alanları doldurun.")
            
st.write("---")
st.subheader("📋 Kayıtlı Kurumsal Hesaplar")
cursor.execute("SELECT id, tur, isim, detay FROM hesaplar")
hesaplar = cursor.fetchall()
if hesaplar:
    for h in hesaplar:
        st.info(f"**[{h[1]}]** — **{h[2]}** : ` {h[3]} `")
else:
    st.warning("Kayıtlı hesap bulunmuyor.")
