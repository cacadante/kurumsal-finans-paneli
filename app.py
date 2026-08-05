import streamlit as st
import sqlite3
import pandas as pd

conn = sqlite3.connect('finance_panel.db', check_same_thread=False)
cursor = conn.cursor()

# Tabloları garanti olması için ana sayfada da oluşturuyoruz
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
conn.commit()

st.set_page_config(page_title="Kurumsal Finans Paneli", page_icon="💼", layout="wide")

st.title("🏢 Kurumsal Finans ve Cüzdan Yönetim Paneli")
st.markdown("---")
st.write("Sistem üzerinden tüm yatırımları, çekimleri ve kurumsal cüzdanları yönetebilirsiniz.")

cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Yatırım'")
toplam_yatirim = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(tutar) FROM islemler WHERE tur = 'Çekim'")
toplam_cekim = cursor.fetchone()[0] or 0.0

net_durum = toplam_yatirim - toplam_cekim

col1, col2, col3 = st.columns(3)
col1.metric("🟢 Toplam Yatırım", f"{toplam_yatirim:,.2f} TL/USDT")
col2.metric("🔴 Toplam Çekim", f"{toplam_cekim:,.2f} TL/USDT")
col3.metric("💰 Net Kasa / Bakiye", f"{net_durum:,.2f} TL/USDT")

st.write("---")
st.subheader("📈 Departman Bazlı Dağılım Grafiği")
df_grafik = pd.read_sql_query("SELECT departman, SUM(tutar) as toplam FROM islemler GROUP BY departman", conn)
if not df_grafik.empty:
    st.bar_chart(df_grafik.set_index('departman'))
else:
    st.info("Grafik için henüz veri bulunmuyor.")
