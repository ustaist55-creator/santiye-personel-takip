import streamlit as st
import pandas as pd
import sqlite3
import datetime
import time

st.set_page_config(
    page_title="NEVZAT USTA - PERSONEL TAKİP SİSTEMİ",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Kurumsal Görsel Giydirme Paketi
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stSidebarUserContent"] { background-color: #1e293b; color: white; }
    div[data-testid="stSidebarUserContent"] h1, div[data-testid="stSidebarUserContent"] p { color: white !important; }
    .stButton>button { border-radius: 6px; font-weight: bold; }
    div[data-testid="stForm"] { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    h1, h2, h3 { color: #0f172a; font-family: 'Segoe UI', sans-serif; }
    </style>
""", unsafe_allow_html=True)

DB_YOLU = "santiye_veritabani.db"

def veritabanı_kur():
    conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
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
    conn.commit(); conn.close()

veritabanı_kur()
if "giris_basarili" not in st.session_state:
    st.session_state["giris_basarili"] = False
    st.session_state["rol"] = None
    st.session_state["santiye"] = None

if not st.session_state["giris_basarili"]:
    st.markdown("<h2 style='text-align: center;'>🏗️ NEVZAT USTA MERKEZİ PERSONEL TAKİP SİSTEMİ</h2>", unsafe_allow_html=True)
    with st.form("giris_formu"):
        kullanici_adi = st.text_input("Kullanıcı Adı")
        sifre = st.text_input("Şifre", type="password")
        if st.form_submit_button("SİSTEME GÜVENLİ GİRİŞ YAP", use_container_width=True):
            if kullanici_adi == "merkez1" and sifre == "merkez55":
                st.session_state["giris_basarili"] = True; st.session_state["rol"] = "merkez"; st.session_state["santiye"] = "MERKEZ GENEL"; st.rerun()
            elif kullanici_adi == "izleyici1" and sifre == "izle55":
                st.session_state["giris_basarili"] = True; st.session_state["rol"] = "izleyici"; st.session_state["santiye"] = "İZLEYİCİ GENEL"; st.rerun()
            elif sifre == "santiye55":
                subeler = ["CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"]
                if kullanici_adi in subeler:
                    st.session_state["giris_basarili"] = True; st.session_state["rol"] = "sube"; st.session_state["santiye"] = kullanici_adi; st.rerun()
                else: st.error("⚠️ Geçersiz Şantiye!")
            else: st.error("❌ Hatalı Giriş Bilgileri!")
    st.stop()

st.sidebar.markdown(f"### 👤 {st.session_state['santiye']}")
st.sidebar.markdown(f"**Yetki Grubu:** {str(st.session_state['rol']).upper()}")
if st.session_state["rol"] == "sube": menu_secim = st.sidebar.radio("MENÜ", ["Personel Giriş / Çıkış", "Aylık Puantaj Girişi"])
else: menu_secim = st.sidebar.radio("MENÜ", ["Merkez Yönetim Havuzu", "Merkez SGK Onay Masası"])

if st.sidebar.button("🚪 SİSTEMDEN ÇIKIS", use_container_width=True):
    st.session_state["giris_basarili"] = False; st.rerun()

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

st.markdown("### 📊 ŞANTİYE CANLI İSTATİSTİK PANELİ")
i_col1, i_col2, i_col3, i_col4 = st.columns(4)
with i_col1: st.metric("Toplam Aktif Çalışan", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]) if not df_canli.empty else 0)
with i_col2: st.metric("Toplam Ayrılan Personel", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK ÇIKIŞI YAPILDI"]) if not df_canli.empty else 0)
with i_col3: st.metric("Bugün Giriş Yapılan", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "GİRİŞ (BEKLEMEDE)"]) if not df_canli.empty else 0)
with i_col4: st.metric("Bugün Çıkış Yapılan", len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "ÇIKIŞ (BEKLEMEDE)"]) if not df_canli.empty else 0)
st.markdown("---")
if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
    st.markdown("### 📥 ŞANTİYE PERSONEL GİRİŞ / ÇIKIŞ İŞLEMLERİ")
    p_secim = st.radio("İşlem Tipi:", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], horizontal=True)
    
    if p_secim == "Sıfırdan Yeni Personel Ekle":
        with st.form("yeni_personel_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: p_ad = st.text_input("ADI SOYADI").upper()
            with col2: p_tc = st.text_input("TC KİMLİK NO", max_chars=11)
            with col3: p_birim = st.selectbox("BİRİMİ", ["BETONARME DEMİRCİSİ", "KALIPÇI", "DUVARCI", "SIVACI", "DÜZ İŞÇİ", "FORMAN", "MÜHENDİS", "MİMAR", "ŞEF", "BEKÇİ", "AŞÇI", "ELEKTRİKÇİ", "SIHHİ TESİSATÇI"])
            col4, col5, col6 = st.columns(3)
            with col4: p_dogum = st.text_input("DOĞUM TARİHİ", placeholder="Örn: 01/01/1980")
            with col5: p_is_giris = st.text_input("İŞE GİRİŞ TARİHİ", placeholder="Örn: 15/05/2026")
            with col6: p_calisma = st.selectbox("ÇALIŞMA DURUMU", ["NORMAL", "EMEKLİ", "TAŞERON", "YABANCI UYRUKLU"])
            col7, col8, col9 = st.columns(3)
            with col7: p_is_cikis = st.text_input("İŞTEN ÇIKIŞ TARİHİ", value="-")
            with col8: p_durum = st.selectbox("DURUMU", ["GİRİŞ (BEKLEMEDE)"])
            with col9: p_cikis_gun = st.text_input("ÇIKIS GÜN SAYISI", value="-")
            p_firma = st.text_input("FİRMA BİLGİSİ", value="NEVZAT USTA").upper()
            
            if st.form_submit_button("💾 VERİYİ OTOMATİK VERİTABANINA İŞLE", use_container_width=True):
                if not p_ad or not p_tc: st.error("⚠️ İsim ve TC zorunludur!")
                else:
                    conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                    cursor.execute("SELECT MAX(sira_no) FROM personel"); row_val = cursor.fetchone()[0]
                    sira_no = int(row_val) + 1 if row_val is not None else 1
                    cursor.execute("INSERT INTO personel VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (sira_no, st.session_state["santiye"], p_ad, p_tc, p_birim, p_dogum, p_is_giris, p_calisma, p_is_cikis, p_durum, p_cikis_gun, p_firma))
                    conn.commit(); conn.close(); st.success("✔️ Başarıyla listeye eklendi!"); time.sleep(0.5); st.rerun()

    elif p_secim == "Var Olan Personeli Güncelle / Çıkış Yap":
        df_sube_aktif = df_goster.copy() if not df_goster.empty else pd.DataFrame()
        if df_sube_aktif.empty: st.info("💡 Güncellenecek personel bulunmuyor.")
        else:
            p_listesi = df_sube_aktif.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
            secilen_p_str = st.selectbox("Personel Seçin", p_listesi)
            secilen_sira = int(str(secilen_p_str).split(" | ")[0].replace("Sıra No: ", ""))
            p_bilgi = df_sube_aktif[df_sube_aktif["Sıra No"] == secilen_sira].iloc[0]
            with st.form("guncelleme_form"):
                g_durum = st.selectbox("Yeni Durum", ["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)", "SGK GİRİŞİ YAPILDI", "SGK ÇIKIŞI YAPILDI"])
                g_cikis_tarihi = st.text_input("İşten Çıkış Tarihi", value=str(p_bilgi["İşten Çıkış Tarihi"]))
                g_cikis_gun = st.text_input("Çıkış Gün Sayısı", value=str(p_bilgi["Çıkış Gün Sayısı"]))
                if st.form_submit_button("🔄 GÜNCELLE", use_container_width=True):
                    conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                    cursor.execute("UPDATE personel SET durum=?, isten_cikis_tarihi=?, cikis_gun_sayisi=? WHERE sira_no=?", (g_durum, g_cikis_tarihi, g_cikis_gun, secilen_sira))
                    conn.commit(); conn.close(); st.success("✔️ Güncellendi!"); time.sleep(0.5); st.rerun()
elif st.session_state["rol"] == "merkez" and menu_secim == "Merkez SGK Onay Masası":
    st.markdown("### 🎯 MERKEZ RESMİ SGK ONAY MASASI")
    df_onay_bekleyen = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_canli.empty else pd.DataFrame()
    
    if df_onay_bekleyen.empty: st.success("🎉 Onay bekleyen kayıt bulunmuyor.")
    else:
        st.warning(f"🚨 Toplam {len(df_onay_bekleyen)} işlem onay bekliyor!")
        st.dataframe(df_onay_bekleyen, use_container_width=True, hide_index=True)
        
        # TAM İSTEDİĞİN GİBİ: KRALIN RESMİ E-BİLDİRGE ADRESİ
        st.markdown("""
            <a href="https://sgk.gov.tr" target="_blank" style="text-decoration: none;">
                <div style="background-color: #D32F2F; color: white; text-align: center; padding: 15px; border-radius: 10px; font-weight: bold; font-size: 18px; margin-bottom: 25px; cursor: pointer;">
                    🚀 RESMİ SGK SİTESİNE GİT VE İŞLEMİ YAP (E-BİLDİRGE EKRANI)
                </div>
            </a>
        """, unsafe_allow_html=True)
        
        p_onay_listesi = df_onay_bekleyen.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Giriş/Çıkış Durumu']})", axis=1).tolist()
        secilen_onay_p = st.selectbox("İşlemi Tamamlanan Personeli Seçin", p_onay_listesi)
        o_sira = int(str(secilen_onay_p).split(" | ")[0].replace("Sıra No: ", ""))
        
        o_col1, o_col2 = st.columns(2)
        with o_col1:
            if st.button("👍 SGK GİRİŞİNİ ONAYLA", use_container_width=True):
                conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                cursor.execute("UPDATE personel SET durum = 'SGK GİRİŞİ YAPILDI' WHERE sira_no = ?", (o_sira,))
                conn.commit(); conn.close(); st.success("Giriş Onaylandı!"); time.sleep(0.5); st.rerun()
        with o_col2:
            if st.button("👎 SGK ÇIKIŞINI ONAYLA", use_container_width=True):
                conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                cursor.execute("UPDATE personel SET durum = 'SGK ÇIKIŞI YAPILDI' WHERE sira_no = ?", (o_sira,))
                conn.commit(); conn.close(); st.success("Çıkış Onaylandı!"); time.sleep(0.5); st.rerun()
if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
    st.markdown("##### 📋 ŞANTİYENİZDEKİ CANLI PERSONEL HAVUZU")
    if not df_goster.empty:
        st.dataframe(df_goster.sort_values(by="Sıra No").style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
        r_col1, r_col2 = st.columns(2)
        with r_col1: st.download_button(label="📥 EXCEL RAPORU YAP", data=kurumsal_rapor_uret(df_goster), file_name="santiye_rapor.csv", mime="text/csv", use_container_width=True)
        with r_col2:
            if st.button("🖨️ PDF YAZDIR", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    df_sube_sil = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_goster.empty else pd.DataFrame()
    if not df_sube_sil.empty:
        st.markdown("---")
        sec_sil = st.selectbox("Silinecek Personel", df_sube_sil.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist(), key="sb_sil")
        if st.button("❌ BEKLEYEN KARTI LİSTEDEN SİL", use_container_width=True):
            s_sira = int(str(sec_sil).split(" | ")[0].replace("Sıra No: ", ""))
            conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor(); cursor.execute("DELETE FROM personel WHERE sira_no = ?", (s_sira,)); conn.commit(); conn.close(); st.rerun()

elif st.session_state["rol"] == "sube" and menu_secim == "Aylık Puantaj Girişi":
    st.markdown("### 📅 ŞANTİYE AYLIK PUANTAJ GİRİŞ EKRANI")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        df_p_aktif = df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"] if not df_goster.empty else pd.DataFrame()
        if df_p_aktif.empty: st.warning("⚠️ Aktif çalışan bulunamadı!")
        else:
            with st.form("puantaj_form", clear_on_submit=True):
                secilen_p = st.selectbox("Personel", df_p_aktif.apply(lambda r: f"{r['Adı Soyadı']} ({r['TC Kimlik No']})", axis=1).tolist())
                donem_ay = st.selectbox("Ay", ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
                calisilan_gun = st.number_input("Gün Sayısı", min_value=0, max_value=31, value=26)
                sefi_adi = st.text_input("Yetkili Şef")
                if st.form_submit_button("💾 PUANTAJI MERKEZE GÖNDER", use_container_width=True):
                    p_ad_parca = str(secilen_p).split(" (")[0]; p_tc_parca = str(secilen_p).split(" (")[1].replace(")", "").strip()
                    su_an = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                    cursor.execute("DELETE FROM puantaj WHERE tc_no = ? AND donem_ay = ? AND santiye = ?", (p_tc_parca, donem_ay, st.session_state["santiye"]))
                    cursor.execute("INSERT INTO puantaj (tarih_satir, santiye, personel_adi, tc_no, donem_ay, gun_sayisi, giren_sef) VALUES (?,?,?,?,?,?,?)", (su_an, str(st.session_state["santiye"]), p_ad_parca, p_tc_parca, donem_ay, int(calisilan_gun), sefi_adi.upper()))
                    conn.commit(); conn.close(); st.success("Puantaj İletildi!"); time.sleep(0.5); st.rerun()
    with col_p2:
        st.dataframe(df_p_goster.iloc[::-1] if not df_p_goster.empty else df_p_goster, use_container_width=True, hide_index=True)

elif st.session_state["rol"] in ["merkez", "izleyici"] and menu_secim == "Merkez Yönetim Havuzu":
    tab1, tab2 = st.tabs(["👥 CANLI MASTER HAVUZ", "📅 TOPLU PUANTAJLAR"])
    with tab1:
        f_santiye = st.selectbox("Şantiye Seçimi", ["HEPSİ", "CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"])
        df_m_filtre = df_canli.copy()
        if f_santiye != "HEPSİ": df_m_filtre = df_m_filtre[df_m_filtre["Şantiye Bilgisi"] == f_santiye]
        st.dataframe(df_m_filtre.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
        st.download_button(label="📥 MASTER EXCEL İNDİR (12 SÜTUN TAM)", data=kurumsal_rapor_uret(df_m_filtre), file_name="master.csv", mime="text/csv", use_container_width=True)
        if st.session_state["rol"] == "merkez" and not df_m_filtre.empty:
            m_sil = st.selectbox("MASTER VERİTABANINDAN KALICI SİL", df_m_filtre.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist())
            if st.button("🔥 SEÇİLİ PERSONELİ SİSTEMDEN TAMAMEN KAZI", use_container_width=True):
                m_sira = int(str(m_sil).split(" | ")[0].replace("Sıra No: ", ""))
                conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor(); cursor.execute("DELETE FROM personel WHERE sira_no = ?", (m_sira,)); conn.commit(); conn.close(); st.success("Kalıcı olarak silindi!"); time.sleep(0.5); st.rerun()
    with tab2: st.dataframe(df_puantaj_canli.iloc[::-1] if not df_puantaj_canli.empty else df_puantaj_canli, use_container_width=True, hide_index=True)










