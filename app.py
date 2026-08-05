import sqlite3
import streamlit as st
import hashlib
import datetime
import pandas as pd
import re
import io

st.set_page_config(page_title="Kurumsal Finans & Kripto Yönetim Merkezi", page_icon="💎", layout="wide")

# Şık Kurumsal Tasarım ve Canlı Renkler (CSS)
st.markdown("""
    <style>
    .kpi-card {
        background-color: #1e2530;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #2d3748;
        text-align: center;
    }
    .kpi-title {
        font-size: 14px;
        color: #a0aec0;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: bold;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('finance_panel.db')
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bank_name TEXT,
            account_holder TEXT,
            iban TEXT,
            added_by TEXT,
            status TEXT DEFAULT 'Onay Bekliyor'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS crypto_wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            coin_name TEXT,
            network TEXT,
            wallet_address TEXT,
            wallet_owner TEXT,
            added_by TEXT,
            status TEXT DEFAULT 'Onay Bekliyor'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp TEXT
        )
    ''')
    
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hash_password("1234")
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                  ("admin", hashed_pw, "Super Admin"))
    
    conn.commit()
    conn.close()

init_db()

def log_action(username, action):
    conn = sqlite3.connect('finance_panel.db')
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO audit_logs (username, action, timestamp) VALUES (?, ?, ?)", (username, action, now))
    conn.commit()
    conn.close()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.session_state['role'] = ""

if not st.session_state['logged_in']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("## 🔐 Kurumsal Panel Girişi")
            st.write("Devam etmek için lütfen giriş yapın.")
            
            login_user = st.text_input("Kullanıcı Adı")
            login_pass = st.text_input("Şifre", type="password")
            
            if st.button("Giriş Yap", use_container_width=True):
                conn = sqlite3.connect('finance_panel.db')
                c = conn.cursor()
                c.execute("SELECT password, role FROM users WHERE username = ?", (login_user,))
                user_data = c.fetchone()
                conn.close()
                
                if user_data and user_data[0] == hash_password(login_pass):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = login_user
                    st.session_state['role'] = user_data[1]
                    log_action(login_user, "Sisteme giriş yaptı.")
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
    st.stop()

st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.markdown(f"**Rol:** `{st.session_state['role']}`")
st.sidebar.markdown("---")

nav_options = ["💳 Banka Hesapları", "🪙 Kripto Cüzdanları", "📊 İstatistikler & Raporlar"]
if st.session_state['role'] == "Super Admin":
    nav_options.extend(["👥 Kullanıcı Yönetimi", "📜 İşlem Logları"])

menu = st.sidebar.radio("Navigasyon", nav_options)

if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    log_action(st.session_state['username'], "Sistemden çıkış yaptı.")
    st.session_state['logged_in'] = False
    st.rerun()

# ---------------------------------------------------------
# 1. BÖLÜM: BANKA HESAPLARI (Toplu Yükleme + Doğrulama + Toast)
# ---------------------------------------------------------
if menu == "💳 Banka Hesapları":
    st.title("💳 Kurumsal IBAN & Finans Paneli")
    st.write("Onaylı banka hesaplarını yönetin, toplu Excel yükleyin ve filtreleyin.")
    st.markdown("---")

    conn = sqlite3.connect('finance_panel.db')
    df_banks = pd.read_sql("SELECT * FROM bank_accounts", conn)
    conn.close()

    total_banks = len(df_banks)
    pending_banks = len(df_banks[df_banks['status'] == 'Onay Bekliyor']) if total_banks > 0 else 0
    approved_banks = len(df_banks[df_banks['status'] == 'Onaylı']) if total_banks > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Toplam Hesap</div><div class="kpi-value">{total_banks}</div></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Onaylı Hesaplar</div><div class="kpi-value">🟢 {approved_banks}</div></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Onay Bekleyen</div><div class="kpi-value">🟡 {pending_banks}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not df_banks.empty:
        csv_data = df_banks.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Banka Listesini Excel / CSV Olarak İndir",
            data=csv_data,
            file_name="banka_hesaplari.csv",
            mime="text/csv",
        )

    if st.session_state['role'] != "İzleyici":
        tab_add1, tab_add2 = st.tabs(["➕ Tekli Hesap Ekle", "📂 Toplu Excel / CSV Yükle"])
        
        with tab_add1:
            with st.form("iban_form", clear_on_submit=True):
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    bank_name = st.selectbox("Banka", ["Akbank", "Türkiye İş Bankası", "VakıfBank", "Enpara", "Papara", "Ziraat Bankası", "Garanti BBVA", "Diğer"])
                with col_f2:
                    account_holder = st.text_input("Ad Soyad (Hesap Sahibi)")
                with col_f3:
                    iban = st.text_input("IBAN", placeholder="TR000000000000000000000000")
                
                submitted = st.form_submit_button("💾 Hesabı Kaydet", use_container_width=True)
                
                if submitted:
                    if bank_name and account_holder and iban:
                        clean_iban = iban.replace(" ", "").upper()
                        # Regex IBAN Doğrulama (TR ve toplam 26 karakter olmalı)
                        if not re.match(r'^TR\d{24}$', clean_iban):
                            st.error("⚠️ Hatalı IBAN formatı! Türkiye IBAN'ları 'TR' ile başlamalı ve toplam 26 karakter olmalıdır.")
                        else:
                            initial_status = "Onaylı" if st.session_state['role'] == "Super Admin" else "Onay Bekliyor"
                            
                            conn = sqlite3.connect('finance_panel.db')
                            c = conn.cursor()
                            c.execute("INSERT INTO bank_accounts (bank_name, account_holder, iban, added_by, status) VALUES (?, ?, ?, ?, ?)", 
                                      (bank_name, account_holder.upper(), clean_iban, st.session_state['username'], initial_status))
                            conn.commit()
                            conn.close()
                            
                            log_action(st.session_state['username'], f"{bank_name} için yeni IBAN ekledi ({initial_status}).")
                            st.success(f"Hesap eklendi! Durum: {initial_status}")
                            st.rerun()
                    else:
                        st.warning("Lütfen tüm alanları doldurun.")

        with tab_add2:
            st.write("Örnek Sütun Adları: `bank_name`, `account_holder`, `iban` içeren bir CSV dosyası yükleyerek yüzlerce hesabı tek tıkla sisteme aktarabilirsiniz.")
            uploaded_file = st.file_uploader("CSV Dosyası Seçin", type=["csv"])
            if uploaded_file is not None:
                try:
                    df_upload = pd.read_csv(uploaded_file)
                    required_cols = {'bank_name', 'account_holder', 'iban'}
                    if required_cols.issubset(df_upload.columns):
                        if st.button("🚀 Toplu Verileri Veritabanına Aktar"):
                            conn = sqlite3.connect('finance_panel.db')
                            c = conn.cursor()
                            count = 0
                            for _, row in df_upload.iterrows():
                                b_name = str(row['bank_name'])
                                holder = str(row['account_holder']).upper()
                                b_iban = str(row['iban']).replace(" ", "").upper()
                                
                                if re.match(r'^TR\d{24}$', b_iban):
                                    c.execute("INSERT INTO bank_accounts (bank_name, account_holder, iban, added_by, status) VALUES (?, ?, ?, ?, ?)", 
                                              (b_name, holder, b_iban, st.session_state['username'], "Onaylı"))
                                    count += 1
                            conn.commit()
                            conn.close()
                            log_action(st.session_state['username'], f"Toplu Excel/CSV üzerinden {count} adet banka hesabı yükledi.")
                            st.success(f"Başarıyla {count} adet hesap içeri aktarıldı!")
                            st.rerun()
                    else:
                        st.error("CSV dosyasının sütun adları 'bank_name', 'account_holder', 'iban' olmalıdır!")
                except Exception as e:
                    st.error(f"Dosya okunurken hata oluştu: {e}")

    st.markdown("### 📋 Banka Hesapları Listesi")
    
    col_s1, col_s2 = st.columns([2, 1])
    with col_s1:
        search_query = st.text_input("🔍 Ara (İsim veya IBAN içinde ara)", placeholder="Ad soyad veya IBAN yazın...")
    with col_s2:
        bank_filter = st.selectbox("🏦 Bankaya Göre Filtrele", ["Tümü", "Akbank", "Türkiye İş Bankası", "VakıfBank", "Enpara", "Papara", "Ziraat Bankası", "Garanti BBVA", "Diğer"])

    filtered_accounts = []
    for index, row in df_banks.iterrows():
        acc_id, b_name, holder, b_iban, added_by, status = row['id'], row['bank_name'], row['account_holder'], row['iban'], row['added_by'], row['status']
        if bank_filter != "Tümü" and b_name != bank_filter:
            continue
        if search_query:
            query = search_query.lower()
            if query not in holder.lower() and query not in b_iban.lower():
                continue
        filtered_accounts.append(row)

    if filtered_accounts:
        for i in range(0, len(filtered_accounts), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(filtered_accounts):
                    row = filtered_accounts[i + j]
                    acc_id, b_name, holder, b_iban, added_by, status = row['id'], row['bank_name'], row['account_holder'], row['iban'], row['added_by'], row['status']
                    with cols[j]:
                        with st.container(border=True):
                            badge = "🟢 Onaylı" if status == "Onaylı" else "🟡 Onay Bekliyor"
                            st.markdown(f"#### 🏦 {b_name}  &nbsp;&nbsp; `{badge}`")
                            st.markdown(f"👤 **{holder}**")
                            st.code(b_iban, language="text")
                            
                            # Toast Bildirim Tetikleyicisi
                            if st.button("📋 IBAN'ı Kopyala", key=f"copy_iban_{acc_id}", use_container_width=True):
                                st.toast(f"Panoya Kopyalandı: {b_iban}", icon="✅")
                                
                            st.caption(f"Ekleyen: {added_by}")
                            
                            c_b1, c_b2 = st.columns(2)
                            if status == "Onay Bekliyor" and st.session_state['role'] == "Super Admin":
                                with c_b1:
                                    if st.button("✅ Onayla", key=f"approve_bank_{acc_id}", use_container_width=True):
                                        conn = sqlite3.connect('finance_panel.db')
                                        c = conn.cursor()
                                        c.execute("UPDATE bank_accounts SET status = 'Onaylı' WHERE id = ?", (acc_id,))
                                        conn.commit()
                                        conn.close()
                                        log_action(st.session_state['username'], f"{b_name} hesabını onayladı.")
                                        st.success("Hesap onaylandı!")
                                        st.rerun()
                            
                            if st.session_state['role'] == "Super Admin":
                                with c_b2:
                                    if st.button("🗑️ Sil", key=f"del_bank_{acc_id}", use_container_width=True):
                                        conn = sqlite3.connect('finance_panel.db')
                                        c = conn.cursor()
                                        c.execute("DELETE FROM bank_accounts WHERE id = ?", (acc_id,))
                                        conn.commit()
                                        conn.close()
                                        log_action(st.session_state['username'], f"{b_name} hesabını sildi.")
                                        st.success("Silindi!")
                                        st.rerun()
    else:
        st.info("📭 Aradığınız kriterlere uygun banka hesabı bulunamadı.")

# ---------------------------------------------------------
# 2. BÖLÜM: KRİPTO CÜZDANLARI (Toplu Yükleme + Toast)
# ---------------------------------------------------------
elif menu == "🪙 Kripto Cüzdanları":
    st.title("🪙 Kripto Cüzdan Yönetimi")
    st.write("USDT, BTC, ETH gibi cüzdan adreslerini yönetin ve toplu yükleyin.")
    st.markdown("---")

    conn = sqlite3.connect('finance_panel.db')
    df_crypto = pd.read_sql("SELECT * FROM crypto_wallets", conn)
    conn.close()

    total_crypto = len(df_crypto)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Toplam Cüzdan</div><div class="kpi-value">{total_crypto}</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not df_crypto.empty:
        csv_crypto = df_crypto.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Kripto Listesini Excel / CSV Olarak İndir",
            data=csv_crypto,
            file_name="kripto_cuzdanlari.csv",
            mime="text/csv",
        )

    if st.session_state['role'] != "İzleyici":
        tab_c1, tab_c2 = st.tabs(["➕ Tekli Cüzdan Ekle", "📂 Toplu CSV Yükle"])
        
        with tab_c1:
            with st.form("crypto_form", clear_on_submit=True):
                col_cr1, col_cr2 = st.columns(2)
                with col_cr1:
                    coin_name = st.selectbox("Coin / Varlık", ["USDT", "USDC", "BTC", "ETH", "TRX", "SOL", "Diğer"])
                    network = st.selectbox("Ağ (Network)", ["TRC20", "ERC20", "BEP20", "Bitcoin Network", "Solana", "Diğer"])
                with col_cr2:
                    wallet_owner = st.text_input("Cüzdan Sahibi / Not")
                    wallet_address = st.text_input("Cüzdan Adresi", placeholder="Cüzdan adresini buraya yapıştırın...")
                
                crypto_submitted = st.form_submit_button("💾 Cüzdanı Kaydet", use_container_width=True)
                
                if crypto_submitted:
                    if coin_name and network and wallet_address:
                        clean_address = wallet_address.strip()
                        initial_status = "Onaylı" if st.session_state['role'] == "Super Admin" else "Onay Bekliyor"
                        
                        conn = sqlite3.connect('finance_panel.db')
                        c = conn.cursor()
                        c.execute("INSERT INTO crypto_wallets (coin_name, network, wallet_address, wallet_owner, added_by, status) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (coin_name, network, clean_address, wallet_owner.upper(), st.session_state['username'], initial_status))
                        conn.commit()
                        conn.close()
                        
                        log_action(st.session_state['username'], f"{coin_name} ({network}) cüzdanı ekledi.")
                        st.success("Kripto cüzdanı başarıyla eklendi!")
                        st.rerun()
                    else:
                        st.warning("Lütfen zorunlu alanları doldurun.")

        with tab_c2:
            st.write("Sütun adları `coin_name`, `network`, `wallet_address`, `wallet_owner` olan CSV dosyanızı yükleyebilirsiniz.")
            up_crypto = st.file_uploader("Kripto CSV Seçin", type=["csv"], key="c_up")
            if up_crypto is not None:
                try:
                    df_cup = pd.read_csv(up_crypto)
                    if {'coin_name', 'network', 'wallet_address', 'wallet_owner'}.issubset(df_cup.columns):
                        if st.button("🚀 Kriptoları Toplu Aktar"):
                            conn = sqlite3.connect('finance_panel.db')
                            c = conn.cursor()
                            ccount = 0
                            for _, r in df_cup.iterrows():
                                c.execute("INSERT INTO crypto_wallets (coin_name, network, wallet_address, wallet_owner, added_by, status) VALUES (?, ?, ?, ?, ?, ?)", 
                                          (str(r['coin_name']), str(r['network']), str(r['wallet_address']).strip(), str(r['wallet_owner']).upper(), st.session_state['username'], "Onaylı"))
                                ccount += 1
                            conn.commit()
                            conn.close()
                            log_action(st.session_state['username'], f"Toplu olarak {ccount} kripto cüzdanı ekledi.")
                            st.success(f"{ccount} adet cüzdan aktarıldı!")
                            st.rerun()
                    else:
                        st.error("CSV sütunları eşleşmiyor!")
                except Exception as e:
                    st.error(f"Hata: {e}")

    st.markdown("### 📋 Kripto Cüzdanları Listesi")
    
    if not df_crypto.empty:
        for index, row in df_crypto.iterrows():
            c_id, coin, net, address, owner, added_by, status = row['id'], row['coin_name'], row['network'], row['wallet_address'], row['wallet_owner'], row['added_by'], row['status']
            with st.container(border=True):
                badge = "🟢 Onaylı" if status == "Onaylı" else "🟡 Onay Bekliyor"
                st.markdown(f"#### 🪙 {coin} &nbsp;&nbsp; `Ağ: {net}` &nbsp;&nbsp; `{badge}`")
                st.markdown(f"👤 **Sahip:** {owner}")
                st.code(address, language="text")
                
                if st.button("📋 Adresi Kopyala", key=f"copy_crypto_{c_id}", use_container_width=True):
                    st.toast(f"Panoya Kopyalandı: {address}", icon="✅")
                    
                st.caption(f"Ekleyen: {added_by}")
                
                if st.session_state['role'] == "Super Admin":
                    if st.button("🗑️ Cüzdanı Sil", key=f"del_crypto_{c_id}"):
                        conn = sqlite3.connect('finance_panel.db')
                        c = conn.cursor()
                        c.execute("DELETE FROM crypto_wallets WHERE id = ?", (c_id,))
                        conn.commit()
                        conn.close()
                        log_action(st.session_state['username'], f"{coin} cüzdanını sildi.")
                        st.success("Silindi!")
                        st.rerun()
    else:
        st.info("📭 Henüz eklenmiş bir kripto cüzdanı bulunmuyor.")

# ---------------------------------------------------------
# 3. BÖLÜM: İSTATİSTİKLER VE GRAFİKLER (YENİ EKLENTİ)
# ---------------------------------------------------------
elif menu == "📊 İstatistikler & Raporlar":
    st.title("📊 Detaylı İstatistikler ve Grafikler")
    st.write("Sistemdeki banka ve kripto dağılımlarının görsel analizi.")
    st.markdown("---")

    conn = sqlite3.connect('finance_panel.db')
    df_b = pd.read_sql("SELECT bank_name FROM bank_accounts", conn)
    df_c = pd.read_sql("SELECT coin_name FROM crypto_wallets", conn)
    conn.close()

    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("🏦 Bankalara Göre Hesap Dağılımı")
        if not df_b.empty:
            bank_counts = df_b['bank_name'].value_counts()
            st.bar_chart(bank_counts)
        else:
            st.info("Yeterli banka verisi yok.")

    with col_g2:
        st.subheader("🪙 Kripto Varlık Dağılımı")
        if not df_c.empty:
            coin_counts = df_c['coin_name'].value_counts()
            st.bar_chart(coin_counts)
        else:
            st.info("Yeterli kripto verisi yok.")

# ---------------------------------------------------------
# 4. BÖLÜM: KULLANICI YÖNETİMİ
# ---------------------------------------------------------
elif menu == "👥 Kullanıcı Yönetimi":
    st.title("👥 Kullanıcı & Rol Yönetimi")
    st.write("Operatör, İzleyici veya Super Admin rolleri tanımlayın.")
    st.markdown("---")

    with st.form("new_user_form", clear_on_submit=True):
        st.subheader("➕ Yeni Personel / Kullanıcı Ekle")
        col_u1, col_u2, col_u3 = st.columns(3)
        with col_u1:
            new_username = st.text_input("Kullanıcı Adı")
        with col_u2:
            new_password = st.text_input("Şifre", type="password")
        with col_u3:
            new_role = st.selectbox("Yetki Rolü", ["Operatör", "İzleyici", "Super Admin"])
        
        user_submitted = st.form_submit_button("Kullanıcıyı Kaydet", use_container_width=True)
        
        if user_submitted:
            if new_username and new_password:
                try:
                    conn = sqlite3.connect('finance_panel.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                              (new_username, hash_password(new_password), new_role))
                    conn.commit()
                    conn.close()
                    log_action(st.session_state['username'], f"Yeni kullanıcı oluşturdu: {new_username} ({new_role})")
                    st.success(f"'{new_username}' başarıyla oluşturuldu!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Bu kullanıcı adı zaten alınmış!")
            else:
                st.warning("Lütfen kullanıcı adı ve şifre girin.")

    st.markdown("### 📋 Mevcut Kullanıcılar")
    conn = sqlite3.connect('finance_panel.db')
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users")
    users = c.fetchall()
    conn.close()

    for u in users:
        uid, uname, urole = u
        col_info1, col_info2, col_info3 = st.columns([2, 2, 1])
        with col_info1:
            st.text(f"👤 {uname}")
        with col_info2:
            st.text(f"🔑 {urole}")
        with col_info3:
            if uname != "admin":
                if st.button("Sil", key=f"del_user_{uid}"):
                    conn = sqlite3.connect('finance_panel.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM users WHERE id = ?", (uid,))
                    conn.commit()
                    conn.close()
                    log_action(st.session_state['username'], f"Kullanıcıyı sildi: {uname}")
                    st.success("Kullanıcı silindi!")
                    st.rerun()

# ---------------------------------------------------------
# 5. BÖLÜM: İŞLEM LOGLARI
# ---------------------------------------------------------
elif menu == "📜 İşlem Logları":
    st.title("📜 Sistem Aktivite Logları")
    st.write("Kullanıcıların gerçekleştirdiği tüm işlemlerin geçmişi.")
    st.markdown("---")

    conn = sqlite3.connect('finance_panel.db')
    c = conn.cursor()
    c.execute("SELECT username, action, timestamp FROM audit_logs ORDER BY id DESC")
    logs = c.fetchall()
    conn.close()

    if logs:
        for log in logs:
            uname, action, timestamp = log
            st.markdown(f"`{timestamp}` | **{uname}**: {action}")
    else:
        st.info("Henüz kayıtlı bir işlem logu bulunmuyor.")
