import streamlit as st
import pandas as pd
import sqlite3
import datetime
import time

# Sayfa Genişlik ve Başlık Ayarları (Orijinal Başlık Sabitlendi)
st.set_page_config(
    page_title="PERSONEL TAKİP SİSTEMİ",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Şantiye Temasına Uygun Kurumsal CSS Tasarımı
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stSidebarUserContent"] { background-color: #1e293b; color: white; }
    div[data-testid="stSidebarUserContent"] h1, div[data-testid="stSidebarUserContent"] p { color: white !important; }
    .stButton>button { border-radius: 6px; font-weight: bold; }
    div[data-testid="stForm"] { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    h1, h2, h3, h4, h5 { color: #0f172a; font-family: 'Segoe UI', sans-serif; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

DB_YOLU = "santiye_veritabani.db"

# Veritabanı Tablolarını Sıfırdan Güvenli Oluşturma Fonksiyonu
def veritabanı_kur():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personel (
            sira_no INTEGER PRIMARY KEY,
            santiye TEXT,
            adi_soyadi TEXT,
            tc_no TEXT,
            birimi TEXT,
            dogum_tarihi TEXT,
            ise_giris_tarihi TEXT,
            calisma_durumu TEXT,
            isten_cikis_tarihi TEXT,
            durum TEXT,
            cikis_gun_sayisi TEXT,
            firma_bilgisi TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS puantaj (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih_satir TEXT,
            santiye TEXT,
            personel_adi TEXT,
            tc_no TEXT,
            donem_ay TEXT,
            gun_sayisi INTEGER,
            giren_sef TEXT
        )
    """)
    conn.commit()
    conn.close()

veritabanı_kur()
# Oturum Değişkenlerinin Tanımlanması
if "giris_basarili" not in st.session_state:
    st.session_state["giris_basarili"] = False
    st.session_state["rol"] = None
    st.session_state["santiye"] = None

# Giriş Yapılmadıysa Karşılama Ekranı Aç (Orijinal Başlık Sabitlendi)
if not st.session_state["giris_basarili"]:
    st.markdown("<h2 style='text-align: center;'>🏗️ PERSONEL TAKİP SİSTEMİ</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Lütfen şantiye veya merkez giriş bilgilerinizi yazınız</p>", unsafe_allow_html=True)
    
    with st.form("giris_formu"):
        kullanici_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.form_submit_button("SİSTEME GÜVENLİ GİRİŞ YAP", use_container_width=True):
            if kullanici_adi == "merkez1" and sifre == "merkez55":
                st.session_state["giris_basarili"] = True
                st.session_state["rol"] = "merkez"
                st.session_state["santiye"] = "MERKEZ GENEL"
                st.rerun()
            elif kullanici_adi == "izleyici1" and sifre == "izle55":
                st.session_state["giris_basarili"] = True
                st.session_state["rol"] = "izleyici"
                st.session_state["santiye"] = "İZLEYİCİ GENEL"
                st.rerun()
            elif sifre == "santiye55":
                subeler = ["CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"]
                if kullanici_adi in subeler:
                    st.session_state["giris_basarili"] = True
                    st.session_state["rol"] = "sube"
                    st.session_state["santiye"] = kullanici_adi
                    st.rerun()
                else:
                    st.error("⚠️ Geçersiz Şantiye Kullanıcı Adı!")
            else:
                st.error("❌ Hatalı Giriş Bilgileri!")
    st.stop()

# Sol Panel (Sidebar) Menü Yapılandırması
st.sidebar.markdown(f"### 👤 {st.session_state['santiye']}")
st.sidebar.markdown(f"**Yetki Seviyesi:** {str(st.session_state['rol']).upper()}")

if st.session_state["rol"] == "sube":
    menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["Personel Giriş / Çıkış", "Aylık Puantaj Girişi"])
else:
    menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["Merkez Yönetim Havuzu", "Merkez SGK Onay Masası"])

st.sidebar.markdown("---")
if st.sidebar.button("🚪 SİSTEMDEN GÜVENLİ ÇIKIS", use_container_width=True):
    st.session_state["giris_basarili"] = False
    st.session_state["rol"] = None
    st.session_state["santiye"] = None
    st.rerun()

# SQL Canlı Veri Okuma Motorları
conn = sqlite3.connect(DB_YOLU)
df_canli = pd.read_sql_query("SELECT sira_no as 'Sıra No', santiye as 'Şantiye Bilgisi', adi_soyadi as 'Adı Soyadı', tc_no as 'TC Kimlik No', birimi as 'Birimi', dogum_tarihi as 'Doğum Tarihi', ise_giris_tarihi as 'İşe Giriş Tarihi', calisma_durumu as 'Çalışma Durumu', isten_cikis_tarihi as 'İşten Çıkış Tarihi', durum as 'Giriş/Çıkış Durumu', cikis_gun_sayisi as 'Çıkış Gün Sayısı', firma_bilgisi as 'Firma Bilgisi' FROM personel", conn)
df_puantaj_canli = pd.read_sql_query("SELECT id as 'Kayıt ID', tarih_satir as 'Kayıt Tarihi', santiye as 'Şantiye', personel_adi as 'Personel_Adi', tc_no as 'TC_No', donem_ay as 'Dönem_Ay', gun_sayisi as 'Gün_Sayısı', giren_sef as 'Giriş_Yapan_Yetkili' FROM puantaj", conn)
conn.close()

df_goster = df_canli[df_canli["Şantiye Bilgisi"] == st.session_state["santiye"]] if not df_canli.empty else df_canli
df_p_goster = df_puantaj_canli[df_puantaj_canli["Şantiye"] == st.session_state["santiye"]] if not df_puantaj_canli.empty else df_puantaj_canli

def renk_ayarla(val):
    if val == "SGK GİRİŞİ YAPILDI": return "background-color: #d1fae5; color: #065f46; font-weight: bold;"
    elif val == "SGK ÇIKIŞI YAPILDI": return "background-color: #fee2e2; color: #991b1b; font-weight: bold;"
    elif val == "GİRİŞ (BEKLEMEDE)": return "background-color: #fef3c7; color: #92400e; font-weight: bold;"
    elif val == "ÇIKIŞ (BEKLEMEDE)": return "background-color: #ffedd5; color: #9a3412; font-weight: bold;"
    return ""

def kurumsal_rapor_uret(df):
    if df.empty: return b""
    return df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")

# Üst Bilgi Sayaç Kartları
st.markdown("### 📊 ŞANTİYE CANLI İSTATİSTİK PANELİ")
i_col1, i_col2, i_col3, i_col4 = st.columns(4)
with i_col1: st.metric("Toplam Aktif Çalışan", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]) if not df_canli.empty else 0)
with i_col2: st.metric("Toplam Ayrılan Personel", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK ÇIKIŞI YAPILDI"]) if not df_canli.empty else 0)
with i_col3: st.metric("Bugün Giriş Yapılan (Bekleyen)", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "GİRİŞ (BEKLEMEDE)"]) if not df_canli.empty else 0)
with i_col4: st.metric("Bugün Çıkış Yapılan (Bekleyen)", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "ÇIKIŞ (BEKLEMEDE)"]) if not df_canli.empty else 0)
st.markdown("---")
if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
    st.markdown("### 📥 ŞANTİYE PERSONEL GİRİŞ / ÇIKIŞ İŞLEMLERİ")
    p_secim = st.radio("İşlem Tipi Seçin:", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], horizontal=True)
    
    if p_secim == "Sıfırdan Yeni Personel Ekle":
        with st.form("yeni_personel_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: p_ad = st.text_input("ADI SOYADI").upper()
            with col2: p_tc = st.text_input("TC KİMLİK NO", max_chars=11)
            with col3: p_birim = st.selectbox("BİRİMİ", ["BETONARME DEMİRCİSİ", "KALIPÇI", "DUVARCI", "SIVACI", "DÜZ İŞÇİ", "FORMAN", "MÜHENDİS", "MİMAR", "ŞEF", "BEKÇİ", "AŞÇI", "ELEKTRİKÇİ", "SIHHİ TESİSATÇI"])
            
            col4, col5, col6 = st.columns(3)
            with col4: p_dogum = st.text_input("DOĞUM TARİHİ", placeholder="Örn: 01/01/1986")
            with col5: p_is_giris = st.text_input("İŞE GİRİŞ TARİHİ", placeholder="Örn: 15/05/2026")
            with col6: p_calisma = st.selectbox("ÇALIŞMA DURUMU", ["NORMAL", "EMEKLİ", "TAŞERON", "YABANCI UYRUKLU"])
            
            col7, col8, col9 = st.columns(3)
            with col7: p_is_cikis = st.text_input("İŞTEN ÇIKIŞ TARİHİ", value="-")
            with col8: p_durum = st.selectbox("DURUMU", ["GİRİŞ (BEKLEMEDE)"])
            with col9: p_cikis_gun = st.text_input("ÇIKIS GÜN SAYISI", value="-")
            
            p_firma = st.text_input("FİRMA BİLGİSİ", value="NEVZAT USTA").upper()
            
            if st.form_submit_button("💾 VERİYİ OTOMATİK VERİTABANINA İŞLE", use_container_width=True):
                if not p_ad or not p_tc:
                    st.error("⚠️ Adı Soyadı ve TC Kimlik No alanları zorunludur!")
                else:
                    conn = sqlite3.connect(DB_YOLU)
                    cursor = conn.cursor()
                    cursor.execute("SELECT MAX(sira_no) FROM personel")
                    row_val = cursor.fetchone()
                    
                    # Boş veritabanında patlamayı önleyen hatasız akıllı sıra no üretici
                    if row_val[0] is not None:
                        sira_no = int(row_val[0]) + 1
                    else:
                        sira_no = 1
                    
                    cursor.execute("""
                        INSERT INTO personel (sira_no, santiye, adi_soyadi, tc_no, birimi, dogum_tarihi, ise_giris_tarihi, calisma_durumu, isten_cikis_tarihi, durum, cikis_gun_sayisi, firma_bilgisi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (sira_no, st.session_state["santiye"], p_ad, p_tc, p_birim, p_dogum, p_is_giris, p_calisma, p_is_cikis, p_durum, p_cikis_gun, p_firma))
                    conn.commit()
                    conn.close()
                    st.success(f"✔️ {p_ad} başarıyla bekleme listesine eklendi!")
                    time.sleep(0.5)
                    st.rerun()

    elif p_secim == "Var Olan Personeli Güncelle / Çıkış Yap":
        df_sube_aktif = df_goster.copy() if not df_goster.empty else pd.DataFrame()
        if df_sube_aktif.empty:
            st.info("💡 Şantiyenizde güncellenecek herhangi bir personel bulunmuyor.")
        else:
            p_listesi = df_sube_aktif.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Giriş/Çıkış Durumu']})", axis=1).tolist()
            secilen_p_str = st.selectbox("Güncellenecek Personeli Seçin", p_listesi)
            
            # Dilimleme ve ayıklama işlemlerinin çökmesini önleyen güvenli metin ayırıcı
            secilen_sira = int(str(secilen_p_str).split(" | ")[0].replace("Sıra No: ", "").strip())
            p_bilgi = df_sube_aktif[df_sube_aktif["Sıra No"] == secilen_sira].iloc[0]
            
            with st.form("guncelleme_form"):
                st.markdown(f"**Seçilen Çalışan:** {p_bilgi['Adı Soyadı']} | **Mevcut Durum:** {p_bilgi['Giriş/Çıkış Durumu']}")
                g_durum = st.selectbox("Yeni Giriş/Çıkış Durumu", ["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)", "SGK GİRİŞİ YAPILDI", "SGK ÇIKIŞI YAPILDI"])
                g_cikis_tarihi = st.text_input("İşten Çıkış Tarihi (Çıkış Veriliyorsa)", value=str(p_bilgi["İşten Çıkış Tarihi"]))
                g_cikis_gun = st.text_input("Çıkış Gün Sayısı", value=str(p_bilgi["Çıkış Gün Sayısı"]))
                
                if st.form_submit_button("🔄 PERSONEL KARTINI GÜNCELLE", use_container_width=True):
                    conn = sqlite3.connect(DB_YOLU)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE personel 
                        SET durum = ?, isten_cikis_tarihi = ?, cikis_gun_sayisi = ?
                        WHERE sira_no = ?
                    """, (g_durum, g_cikis_tarihi, g_cikis_gun, secilen_sira))
                    conn.commit()
                    conn.close()
                    st.success("✔️ Personel kartı başarıyla güncellendi!")
                    time.sleep(0.5)
                    st.rerun()
elif st.session_state["rol"] == "merkez" and menu_secim == "Merkez SGK Onay Masası":
    st.markdown("### 🎯 MERKEZ RESMİ SGK ONAY MASASI")
    df_onay_bekleyen = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_canli.empty else pd.DataFrame()
    
    if df_onay_bekleyen.empty:
        st.success("🎉 Harika! SGK onayı bekleyen hiçbir personel kaydı bulunmuyor.")
    else:
        st.warning(f"🚨 Şu anda şantiyelerden gelen ve onay bekleyen toplam {len(df_onay_bekleyen)} işlem var!")
        st.dataframe(df_onay_bekleyen, use_container_width=True, hide_index=True)
        
        # Nokta Atışı Eklenen Resmi e-Bildirge Giriş Bağlantı İstasyonu
        st.markdown("""
            <a href="https://sgk.gov.tr" target="_blank" style="text-decoration: none;">
                <div style="background-color: #D32F2F; color: white; text-align: center; padding: 16px; border-radius: 10px; font-weight: bold; font-size: 18px; margin-bottom: 25px; cursor: pointer; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                    🚀 RESMİ SGK SİTESİNE GİT VE İŞLEMİ YAP (E-BİLDİRGE EKRANI)
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        p_onay_listesi = df_onay_bekleyen.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Şantiye Bilgisi']} | {r['Adı Soyadı']} ({r['Giriş/Çıkış Durumu']})", axis=1).tolist()
        secilen_onay_p = st.selectbox("SGK Bildirimi Tamamlanan Personeli Seçin", p_onay_listesi)
        
        o_sira = int(str(secilen_onay_p).split(" | ")[0].replace("Sıra No: ", "").strip())
        p_onay_bilgi = df_onay_bekleyen[df_onay_bekleyen["Sıra No"] == o_sira].iloc[0]
        
        o_col1, o_col2 = st.columns(2)
        with o_col1:
            if st.button("👍 SGK GİRİŞİNİ ONAYLA VE LİSTEYE KİLİTLE", use_container_width=True):
                conn = sqlite3.connect(DB_YOLU)
                cursor = conn.cursor()
                cursor.execute("UPDATE personel SET durum = 'SGK GİRİŞİ YAPILDI' WHERE sira_no = ?", (o_sira,))
                conn.commit()
                conn.close()
                st.success(f"✔️ {p_onay_bilgi['Adı Soyadı']} Girişi Onaylandı!")
                time.sleep(0.5)
                st.rerun()
        with o_col2:
            if st.button("👎 SGK ÇIKIŞINI ONAYLA VE ARŞİVE GÖNDER", use_container_width=True):
                conn = sqlite3.connect(DB_YOLU)
                cursor = conn.cursor()
                cursor.execute("UPDATE personel SET durum = 'SGK ÇIKIŞI YAPILDI' WHERE sira_no = ?", (o_sira,))
                conn.commit()
                conn.close()
                st.success(f"✔️ {p_onay_bilgi['Adı Soyadı']} Çıkışı Onaylandı!")
                time.sleep(0.5)
                st.rerun()
if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
    st.markdown("##### 📋 ŞANTİYENİZDEKİ CANLI PERSONEL HAVUZU")
    df_goster_sirali = df_goster.sort_values(by="Sıra No", ascending=True) if not df_goster.empty else df_goster
    if not df_goster_sirali.empty:
        st.dataframe(df_goster_sirali.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
        r_col1, r_col2 = st.columns(2)
        with r_col1: st.download_button(label="📥 BU LİSTEYİ EXCEL RAPORU YAP (12 SÜTUN TAM)", data=kurumsal_rapor_uret(df_goster_sirali), file_name="santiye_personel_raporu.csv", mime="text/csv", use_container_width=True)
        with r_col2:
            if st.button("🖨️ BU LİSTEYİ RESMİ PDF YAP / YAZDIR", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    else: 
        st.info("💡 Kayıtlı personel bulunmuyor.")

    df_sube_silinebilir = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_goster.empty else pd.DataFrame()
    if not df_sube_silinebilir.empty:
        st.markdown("---")
        p_silme_listesi_sube = df_sube_silinebilir.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
        secilen_sil_p_sube = st.selectbox("Silmek İstediğiniz Personeli Seçin", p_silme_listesi_sube, key="sube_p_sil")
        if st.button("❌ SEÇİLİ PERSONELİ LİSTEDEN KALDIR", use_container_width=True):
            s_sira = int(str(secilen_sil_p_sube).split(" | ")[0].replace("Sıra No: ", "").strip())
            conn = sqlite3.connect(DB_YOLU)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM personel WHERE sira_no = ?", (s_sira,))
            conn.commit()
            conn.close()
            st.success("Beklemedeki personel kartı silindi!")
            st.rerun()

elif st.session_state["rol"] == "sube" and menu_secim == "Aylık Puantaj Girişi":
    st.markdown("### 📅 ŞANTİYE AYLIK PUANTAJ GİRİŞ EKRANI")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        df_puantaj_aktif = df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"] if not df_goster.empty else pd.DataFrame()
        if df_puantaj_aktif.empty: 
            st.warning("⚠️ Onaylı aktif çalışan personel bulunmalıdır!")
        else:
            with st.form("puantaj_form", clear_on_submit=True):
                p_secenekler = df_puantaj_aktif.apply(lambda r: f"{r['Adı Soyadı']} ({r['TC Kimlik No']})", axis=1).tolist()
                secilen_p = st.selectbox("Personel Seçin", p_secenekler)
                donem_ay = st.selectbox("Puantaj Dönemi", ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
                calisilan_gun = st.number_input("Çalışılan Gün Sayısı", min_value=0, max_value=31, value=26)
                sefi_adi = st.text_input("Giriş Yapan Yetkili")
                
                if st.form_submit_button("💾 PUANTAJI MERKEZE GÖNDER", use_container_width=True):
                    p_ad_parca = str(secilen_p).split(" (")[0].strip()
                    p_tc_parca = str(secilen_p).split(" (")[1].replace(")", "").strip()
                    su_an_p = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = sqlite3.connect(DB_YOLU)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM puantaj WHERE tc_no = ? AND donem_ay = ? AND santiye = ?", (p_tc_parca, donem_ay, st.session_state["santiye"]))
                    cursor.execute("INSERT INTO puantaj (tarih_satir, santiye, personel_adi, tc_no, donem_ay, gun_sayisi, giren_sef) VALUES (?, ?, ?, ?, ?, ?, ?)", (su_an_p, str(st.session_state["santiye"]), str(p_ad_parca), str(p_tc_parca), str(donem_ay), int(calisilan_gun), sefi_adi.upper()))
                    conn.commit()
                    conn.close()
                    st.success("✔️ Puantaj Kilitlendi!")
                    time.sleep(0.5)
                    st.rerun()
    with col_p2:
        st.dataframe(df_p_goster.iloc[::-1] if not df_p_goster.empty else df_p_goster, use_container_width=True, hide_index=True)
        if not df_p_goster.empty:
            p_silme_listesi = df_p_goster.apply(lambda r: f"ID: {r['Kayıt ID']} | {r['Personel_Adi']}", axis=1).tolist()
            secilen_p_sil_id = st.selectbox("Hatalı Kaydı Seçin", p_silme_listesi)
            if st.button("❌ SEÇİLİ PUANTAJI LİSTEDEN SİL", use_container_width=True):
                sil_id = int(str(secilen_p_sil_id).split(" | ")[0].replace("ID: ", "").strip())
                conn = sqlite3.connect(DB_YOLU)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM puantaj WHERE id = ?", (sil_id,))
                conn.commit()
                conn.close()
                st.success("Silindi!")
                time.sleep(0.5)
                st.rerun()

elif st.session_state["rol"] in ["merkez", "izleyici"] and menu_secim == "Merkez Yönetim Havuzu":
    tab1, tab2 = st.tabs(["👥 CANLI MASTER PERSONEL HAVUZU", "📅 TOPLU ŞANTİYE PUANTAJLARI"])
    with tab1:
        f_col1, f_col2 = st.columns(2)
        with f_col1: secilen_f_santiye = st.selectbox("Şantiye Şube Seçimi", ["HEPSİ", "CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"])
        with f_col2: secilen_f_durum = st.selectbox("SGK Onay Durumu", ["HEPSİ", "SGK GİRİŞİ YAPILDI", "SGK ÇIKIŞI YAPILDI", "GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])
        df_merkez_p_filtreli = df_canli.copy()
        if secilen_f_santiye != "HEPSİ": df_merkez_p_filtreli = df_merkez_p_filtreli[df_merkez_p_filtreli["Şantiye Bilgisi"] == secilen_f_santiye]
        if secilen_f_durum != "HEPSİ": df_merkez_p_filtreli = df_merkez_p_filtreli[df_merkez_p_filtreli["Giriş/Çıkış Durumu"] == secilen_f_durum]
        df_merkez_p_filtreli = df_merkez_p_filtreli.sort_values(by="Sıra No", ascending=True) if not df_merkez_p_filtreli.empty else df_merkez_p_filtreli
        st.dataframe(df_merkez_p_filtreli.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
        st.download_button(label="📥 MASTER EXCEL RAPORU İNDİR (12 SÜTUN TAM)", data=kurumsal_rapor_uret(df_merkez_p_filtreli), file_name="master_personel.csv", mime="text/csv", use_container_width=True)
        
        if st.session_state["rol"] == "merkez" and not df_merkez_p_filtreli.empty:
            m_p_sil_list = df_merkez_p_filtreli.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
            m_secilen_sil = st.selectbox("MASTER SİLME: Personel Seçin", m_p_sil_list)
            if st.button("🔥 SEÇİLİ PERSONELİ VERİTABANINA KALICI OLARAK SİL", use_container_width=True):
                m_sil_sira = int(str(m_secilen_sil).split(" | ")[0].replace("Sıra No: ", "").strip())
                conn = sqlite3.connect(DB_YOLU)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM personel WHERE sira_no = ?", (m_sil_sira,))
                conn.commit()
                conn.close()
                st.success("Silindi!")
                time.sleep(0.5)
                st.rerun()
    with tab2:
        fp_col1, fp_col2 = st.columns(2)
        with fp_col1: secilen_fp_santiye = st.selectbox("Puantaj Şantiye Seçimi", ["HEPSİ", "CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"])
        with fp_col2: secilen_fp_ay = st.selectbox("Dönem Ay Seçimi", ["HEPSİ", "OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
        df_merkez_pt_filtreli = df_puantaj_canli.copy()
        if secilen_fp_santiye != "HE5Sİ": df_merkez_pt_filtreli = df_merkez_pt_filtreli[df_merkez_pt_filtreli["Şantiye"] == secilen_fp_santiye]
        if secilen_fp_ay != "HEPSİ": df_merkez_pt_filtreli = df_merkez_pt_filtreli[df_merkez_pt_filtreli["Dönem_Ay"] == secilen_fp_ay]
        st.dataframe(df_merkez_pt_filtreli.iloc[::-1], use_container_width=True, hide_index=True)











