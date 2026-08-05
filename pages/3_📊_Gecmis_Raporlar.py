import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect('finance_panel.db', check_same_thread=False)

st.title("📊 Geçmiş İşlemler & Raporlar")
st.markdown("---")

df_islemler = pd.read_sql_query("SELECT id, kullanici, tur, tutar, departman, aciklama, tarih FROM islemler ORDER BY id DESC", conn)

if not df_islemler.empty:
    st.dataframe(df_islemler, use_container_width=True)
    
    csv_verisi = df_islemler.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Tabloyu CSV / Excel Olarak İndir",
        data=csv_verisi,
        file_name='kurumsal_finans_raporu.csv',
        mime='text/csv',
    )
else:
    st.info("Kayıtlı işlem bulunmuyor.")
