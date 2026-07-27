import streamlit as st
import pandas as pd
import datetime
import os
import io
import time
import sqlite3
import re
import extra_streamlit_components as stx

# Sayfa Ayarları - %100 Tam Ekran ve Sola-Sağa Sıfır Boşluk Nizamı
st.set_page_config(page_title="PERSONEL TAKİP", layout="wide")

st.markdown("""
<style>
    /* 🔒 GÜVENLİK VE MAKSİMUM GÖRÜNÜRLÜK YAMASI */
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stStatusWidget"], div[class^="viewerBadge"] {
        display: none !important;
        visibility: hidden !important;
    }
    /* 📺 MADDE 1: EKRANA TAM SIĞDIRMA VE GENİŞLİK CSS ZIRHI */
    .block-container {
        max-width: 100% !important;
        padding-left: 20px !important;
        padding-right: 20px !important;
        padding-top: 15px !important;
        padding-bottom: 15px !important;
    }
    /* 📱 TELEFON / MOBİL UYUM YAMASI */
    @media (max-width: 768px) {
        .stSidebar { min-width: 100% !important; max-width: 100% !important; }
        div[data-testid="stForm"] { padding: 15px !important; }
        .stDataframe { width: 100% !important; overflow-x: auto !important; }
    }
    .stApp { background-color: #F8FAFC; color: #1E293B !important; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        padding: 15px 20px !important;
        border-left: 5px solid #319795 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        padding: 25px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
    }
    label, p, span, h1, h2, h3, h4, h5, h6 { color: #0F172A !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div { color: #0F172A !important; background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 6px !important; }
    .stButton>button { background: linear-gradient(135deg, #319795 0%, #2B6CB0 100%) !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; transition: all 0.2s ease !important; }
    .stButton>button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 12px rgba(43, 108, 176, 0.3) !important; }
</style>
""", unsafe_allow_html=True)
DB_FILE = "santiye_personel.db"

def yerel_altyapi_kur():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personel (
            sira_no INTEGER PRIMARY KEY AUTOINCREMENT, adi_soyadi TEXT, tc_no TEXT, dogum_tarihi TEXT,
            ise_giris TEXT, isten_cikis TEXT, birimi TEXT, santiye TEXT, firma TEXT,
            durum TEXT, calisma_sekli TEXT, fark_gun TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS puantaj (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tarih_satir TEXT, santiye TEXT,
            personel_adi TEXT, tc_no TEXT, donem_ay TEXT, gun_sayisi INTEGER, giren_sef TEXT
        )
    """)
    conn.commit()
    conn.close()

yerel_altyapi_kur()

def verileri_yukle_yerel():
    conn = sqlite3.connect(DB_FILE)
    df_p = pd.read_sql_query("SELECT sira_no as \"Sıra No\", adi_soyadi as \"Adı Soyadı\", tc_no as \"TC Kimlik No\", dogum_tarihi as \"Doğum Tarihi\", ise_giris as \"İşe Giriş Tarihi\", isten_cikis as \"İşten Çıkış Tarihi\", birimi as \"Birimi\", santiye as \"Şantiye Bilgisi\", firma as \"Firma Bilgisi\", durum as \"Giriş/Çıkış Durumu\", calisma_sekli as \"Çalışma Durumu\", fark_gun as \"Çıkış Gün Sayısı\" FROM personel ORDER BY sira_no DESC", conn)
    df_pt = pd.read_sql_query("SELECT id as \"Kayıt ID\", tarih_satir as \"Tarih_Saat\", santiye as \"Şantiye\", personel_adi as \"Personel_Adi\", tc_no as \"TC_Kimlik\", donem_ay as \"Dönem_Ay\", gun_sayisi as \"Çalışılan_Gün_Sayısı\", giren_sef as \"Giren_Sef\" FROM puantaj ORDER BY id DESC", conn)
    conn.close()
    return df_p, df_pt

df_canli, df_puantaj_canli = verileri_yukle_yerel()
YENI_BIRIMLER = [
    "BETONARME DEMİRCİSİ", "İNŞAAT İŞÇİSİ", "KULE VİNÇ OPERATÖRÜ", "AHŞAP KALIPÇI",
    "İNŞAAT MÜHENDİSİ", "ŞANTİYE ŞEFİ", "MUHASABECİ", "MUHASEBE ELEMANI",
    "İSG UZMANI", "FORMEN", "BEDEN İŞÇİSİ", "DÜZ İŞÇİ", "YÖNETİCİ",
    "OFİS ELEMANI", "SEKRETER", "BÜRO MEMURU"
]

KULLANICILAR = {
    "canik": {"sifre": "5151", "santiye": "CANİK", "firma": "NEVZAT USTA", "rol": "sube"},
    "gaziethempaşa": {"sifre": "5252", "santiye": "GAZİETHEMPAŞA", "firma": "NEVZAT USTA", "rol": "sube"},
    "ofis": {"sifre": "5353", "santiye": "OFİS", "firma": "NEVZAT USTA", "rol": "sube"},
    "tepecika": {"sifre": "5454", "santiye": "TEPECİK ABLOK", "firma": "NEVZAT USTA", "rol": "sube"},
    "polatlı": {"sifre": "5555", "santiye": "POLATLI", "firma": "NEVZAT USTA", "rol": "sube"},
    "giresun": {"sifre": "5656", "santiye": "GİRESUN", "firma": "USTA KONUT", "rol": "sube"},
    "istanbul": {"sifre": "5757", "santiye": "İSTANBUL", "firma": "USTA KONUT", "rol": "sube"},
    "morfoloji": {"sifre": "5858", "santiye": "MORFOLOJİ", "firma": "USTA KONUT", "rol": "sube"},
    "yayladere": {"sifre": "5959", "santiye": "YAYLADERE", "firma": "USTA KONUT", "rol": "sube"},
    "merkezişyeri": {"sifre": "6060", "santiye": "MERKZE İŞYERİ-2", "firma": "USTA KONUT", "rol": "sube"},
    "kılıçdede": {"sifre": "6161", "santiye": "KILIÇDEDE2", "firma": "USTA KONUT", "rol": "sube"},
    "yönetici": {"sifre": "5050", "santiye": "HEPSİ", "firma": "HEPSİ", "rol": "izleyici"},
    "merkez": {"sifre": "2944", "santiye": "HEPSİ", "firma": "HEPSİ", "rol": "merkez"}
}

cookie_manager = stx.CookieManager()
if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False; st.session_state["kullanici"] = ""; st.session_state["santiye"] = ""; st.session_state["firma"] = ""; st.session_state["rol"] = ""
try: saved_user = cookie_manager.get(cookie="saved_user")
except: saved_user = None

if saved_user and not st.session_state["giris_yapildi"] and saved_user in KULLANICILAR:
    st.session_state["giris_yapildi"] = True; st.session_state["kullanici"] = saved_user
    st.session_state["santiye"] = KULLANICILAR[saved_user]["santiye"]
    st.session_state["firma"] = KULLANICILAR[saved_user]["firma"]; st.session_state["rol"] = KULLANICILAR[saved_user]["rol"]

def renk_ayarla(val):
    val_str = str(val).upper()
    if "BEKLEMEDE" in val_str: return "background-color: #FEF3C7; color: #92400E; font-weight: bold;"
    elif "GİRİŞİ YAPILDI" in val_str: return "background-color: #D1FAE5; color: #065F46; font-weight: bold;"
    elif "ÇIKIŞI YAPILDI" in val_str: return "background-color: #FEE2E2; color: #991B1B; font-weight: bold;"
    return ""

def tarih_formatla(metin):
    temiz = "".join([c for c in str(metin) if c.isdigit()])
    if len(metin) > 8: temiz = temiz[:8]
    if len(temiz) >= 5: return f"{temiz[:2]}.{temiz[2:4]}.{temiz[4:]}"
    elif len(temiz) >= 3: return f"{temiz[:2]}.{temiz[2:]}"
    return temiz

def excel_disa_aktar(df_data):
    if df_data.empty: return None
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_data.to_excel(writer, index=False, sheet_name='Personel Listesi')
    return output.getvalue()

if not st.session_state["giris_yapildi"]:
    col_l1, col_l2, col_l3 = st.columns([1.2, 1, 1.2])
    with col_l2:
        st.markdown("<h3 style='text-align: center; color: #2B6CB0;'>🏛️ PERSONEL TAKİP</h3>", unsafe_allow_html=True)
        beni_hatirla_check = st.checkbox("Beni Hatırla")
        with st.form("login_form"):
            kullanici_adi = st.text_input("Kullanıcı Adı"); sifre = st.text_input("Şifre", type="password")
            if st.form_submit_button("SİSTEME GÜVENLİ GİRİŞ YAP", use_container_width=True):
                if kullanici_adi in KULLANICILAR and KULLANICILAR[kullanici_adi]["sifre"] == sifre:
                    st.session_state["giris_yapildi"] = True; st.session_state["kullanici"] = kullanici_adi
                    st.session_state["santiye"] = KULLANICILAR[kullanici_adi]["santiye"]
                    st.session_state["firma"] = KULLANICILAR[kullanici_adi]["firma"]; st.session_state["rol"] = KULLANICILAR[kullanici_adi]["rol"]
                    if beni_hatirla_check:
                        try: cookie_manager.set("saved_user", kullanici_adi, max_age=datetime.timedelta(days=30))
                        except: pass
                    st.rerun()
                else: st.error("❌ Hatalı Giriş!")
    st.stop()
else:
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1: st.markdown(f"#### 💼 {st.session_state['santiye']} ŞANTİYESİ")
    with col_u2:
        if st.button("Canlı Verileri Yenile", use_container_width=True): st.rerun()
    with col_u3:
        if st.button("SİSTEMDEN GÜVENLİ ÇIKIŞ", use_container_width=True):
            st.session_state["giris_yapildi"] = False
            try: cookie_manager.delete("saved_user")
            except: pass
            st.rerun()

    if not df_canli.empty:
        bugun_str = datetime.datetime.now().strftime("%d.%m.%Y")
        df_metrik_havuz = df_canli[df_canli["Şantiye Bilgisi"] == st.session_state["santiye"]]
            
        if st.session_state["rol"] == "sube":
            m_aktif = len(df_metrik_havuz[df_metrik_havuz["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"])
            m_cikan = len(df_metrik_havuz[df_metrik_havuz["Giriş/Çıkış Durumu"] == "SGK ÇIKIŞI YAPILDI"])
            m_bugun_giren = len(df_metrik_havuz[(df_metrik_havuz["İşe Giriş Tarihi"] == bugun_str) & (df_metrik_havuz["Giriş/Çıkış Durumu"].str.contains("GİRİŞ", na=False))])
            m_bugun_cikan = len(df_metrik_havuz[(df_metrik_havuz["İşten Çıkış Tarihi"] == bugun_str) & (df_metrik_havuz["Giriş/Çıkış Durumu"].str.contains("ÇIKIŞ", na=False))])

            met1, met2, met3, met4 = st.columns(4)
            with met1: st.metric(label="🟢 AKTİF PERSONEL", value=m_aktif)
            with met2: st.metric(label="🔴 ÇIKAN PERSONEL", value=m_cikan)
            with met3: st.metric(label="⚡ BUGÜN GİREN", value=m_bugun_giren)
            with met4: st.metric(label="💥 BUGÜN ÇIKAN", value=m_bugun_cikan)
        else:
            m_merkez_aktif = len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"])
            m_merkez_cikan = len(df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK ÇIKIŞI YAPILDI"])
            m_merkez_bugun = len(df_canli[df_canli["İşe Giriş Tarihi"] == bugun_str])
            m_toplam_havuz = len(df_canli)

            met1, met2, met3, met4 = st.columns(4)
            with met1: st.metric(label="🏢 TOPLAM AKTİF ÇALIŞAN", value=m_merkez_aktif)
            with met2: st.metric(label="📉 TOPLAM ÇIKIŞ YAPAN", value=m_merkez_cikan)
            with met3: st.metric(label="🔥 BUGÜN TOPLAM GİRİŞ", value=m_merkez_bugun)
            with met4: st.metric(label="📋 MASTER HAVUZ MEVCUDU", value=m_toplam_havuz)
            
        st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state["rol"] == "sube":
        menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["Personel Giriş / Çıkış", "Aylık Puantaj Girişi"])
        df_goster = df_canli[df_canli["Şantiye Bilgisi"] == st.session_state["santiye"]] if not df_canli.empty else df_canli
        df_p_goster = df_puantaj_canli[df_puantaj_canli["Şantiye"] == st.session_state["santiye"]] if not df_puantaj_canli.empty else df_puantaj_canli
    else:
        menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["🏛️ Merkez Personel Takip", "📅 Aylık Puantajları İzle"])
        df_goster = df_canli.copy(); df_p_goster = df_puantaj_canli.copy()

    df_bekleyen_sayi = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_canli.empty else pd.DataFrame()

    if st.session_state["rol"] == "merkez" and menu_secim == "🏛️ Merkez Personel Takip" and not df_bekleyen_sayi.empty:
        with st.expander("🔔 ONAY BEKLEYEN HAREKETLER", expanded=True):
            bekleyen_listesi = df_bekleyen_sayi.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Şantiye Bilgisi']})", axis=1).tolist()
            secilen_islem_metni = st.selectbox("Onaylanacak Kartı Seçin", bekleyen_listesi)
            if secilen_islem_metni:
                metin_saf = str(secilen_islem_metni).split(" | ")
                secilen_sira_no = int(re.sub(r"[^\d]", "", metin_saf))
                
                st.markdown(f'<a href="https://sgk.gov.tr" target="_blank" style="text-decoration:none;"><div style="background-color:#D32F2F;color:white;padding:14px;border-radius:8px;text-align:center;font-weight:bold;margin-bottom:15px;font-size:16px;">🚀 RESMİ SGK SİTESİNE GİT VE İŞLEMİ YAP</div></a>', unsafe_allow_html=True)
                if st.button("✅ HAREKETİ RESMİ OLARAK ONAYLA", use_container_width=True):
                    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
                    cursor.execute("SELECT durum FROM personel WHERE sira_no = ?", (secilen_sira_no,))
                    mevcut_durum_row = cursor.fetchone()
                    mevcut_durum = mevcut_durum_row if mevcut_durum_row else "GİRİŞ"
                    yeni_durum = "SGK GİRİŞİ YAPILDI" if "GİRİŞ" in str(mevcut_durum).upper() else "SGK ÇIKIŞI YAPILDI"
                    cursor.execute("UPDATE personel SET durum = ? WHERE sira_no = ?", (yeni_durum, secilen_sira_no))
                    conn.commit(); conn.close(); st.success("Onay Tamamlandı!"); time.sleep(0.5); st.rerun()

    if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
        st.markdown("##### 📥 PERSONEL KART TANIMLAMA")
        islem_modu = st.radio("Mod", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], label_visibility="collapsed", horizontal=True)
        varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris, varsayilan_cikis, varsayilan_sira, varsayilan_fark = "", "", "", "", "-", None, ""
        
        df_guncellenebilir_havuz = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)", "SGK GİRİŞİ YAPILDI"])] if not df_goster.empty else pd.DataFrame()
        
        if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and not df_guncellenebilir_havuz.empty:
            p_guncelle_listesi = df_guncellenebilir_havuz.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
            secilen_g_p = st.selectbox("Personel Seçin", p_guncelle_listesi)
            if secilen_g_p:
                g_sira_no = int(str(secilen_g_p).split(" | ").replace("Sıra No: ", "").strip())
                filtered_df = df_guncellenebilir_havuz[df_guncellenebilir_havuz["Sıra No"] == g_sira_no]
                if not filtered_df.empty:
                    varsayilan_ad = str(filtered_df.iloc[0]["Adı Soyadı"])
                    varsayilan_tc = str(filtered_df.iloc[0]["TC Kimlik No"])
                    varsayilan_dogum = str(filtered_df.iloc[0]["Doğum Tarihi"])
                    varsayilan_giris = str(filtered_df.iloc[0]["İşe Giriş Tarihi"])
                    varsayilan_cikis = str(filtered_df.iloc[0]["İşten Çıkış Tarihi"])
                    varsayilan_sira = g_sira_no
                    varsayilan_fark = str(filtered_df.iloc[0]["Çıkış Gün Sayısı"])
        
        with st.form("excel_birebir_form", clear_on_submit=False):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                p_adi = st.text_input("ADI SOYADI", value=varsayilan_ad)
                p_dogum = tarih_formatla(st.text_input("DOĞUM TARIHI", value=varsayilan_dogum, placeholder="Örn: 01101986"))
            with f_col2:
                p_tc = st.text_input("TC KIMLIK NO", max_chars=11, value=varsayilan_tc)
                p_ise_giris = tarih_formatla(st.text_input("IŞE GIRIŞ TARIHI", value=varsayilan_giris, placeholder="Örn: 15062026"))
            with f_col3:
                p_birim = st.selectbox("BIRIMI", YENI_BIRIMLER)
                p_calisma = st.selectbox("ÇALIŞMA DURUMU", ["NORMAL", "EMEKLİ"])
            
            f_sub_col1, f_sub_col2, f_sub_col3 = st.columns(3)
            with f_sub_col1: p_isten_cikis = tarih_formatla(st.text_input("IŞTEN ÇIKIŞ TARIHI", value=varsayilan_cikis))
            with f_sub_col2: p_durum = st.selectbox("DURUMU", ["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"], index=1 if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" else 0)
            with f_sub_col3: p_fark_gun_elle = st.text_input("ÇIKIŞ GÜN SAYISI", value=varsayilan_fark)
            
            if st.form_submit_button("💾 VERİYI YEREL VERİTABANINA KALICI OLARAK İŞLE", use_container_width=True):
                if p_adi.strip() != "" and p_tc.strip() != "":
                    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
                    if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and varsayilan_sira is not None:
                        cursor.execute("DELETE FROM personel WHERE sira_no = ?", (varsayilan_sira,))
                    cursor.execute("INSERT INTO personel (adi_soyadi, tc_no, dogum_tarihi, ise_giris, isten_cikis, birimi, santiye, firma, durum, calisma_sekli, fark_gun) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (p_adi.strip().upper(), str(p_tc.strip()), str(p_dogum), str(p_ise_giris), str(p_isten_cikis), str(p_birim), str(st.session_state["santiye"]), str(st.session_state["firma"]), str(p_durum), str(p_calisma), str(p_fark_gun_elle).upper()))
                    conn.commit(); conn.close(); st.success("✔️ Kalıcı Olarak İşlendi!"); time.sleep(0.5); st.rerun()
        st.markdown("##### 📋 ŞANTİYENİZDEKİ CANLI PERSONEL HAVUZU")
        if not df_goster.empty:
            excel_dosyasi_sube = excel_disa_aktar(df_goster)
            if excel_dosyasi_sube:
                st.download_button(label="📥 CANLI PERSONEL LİSTESİNİ EXCEL OLARAK İNDİR", data=excel_dosyasi_sube, file_name=f"{st.session_state['santiye']}_personel_listesi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            try: st.dataframe(df_goster.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
            except: st.dataframe(df_goster.style.applymap(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)

        df_sube_silinebilir = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_goster.empty else pd.DataFrame()
        if not df_sube_silinebilir.empty:
            st.markdown("---")
            p_silme_listesi_sube = df_sube_silinebilir.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
            secilen_sil_p_sube = st.selectbox("Silmek İstediğiniz Personeli Seçin", p_silme_listesi_sube, key="sube_p_sil")
            if st.button("❌ SEÇİLİ PERSONELİ LİSTEDEN KALDIR", use_container_width=True):
                s_sira = int(str(secilen_sil_p_sube).split(" | ").replace("Sıra No: ", "").strip())
                conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
                cursor.execute("DELETE FROM personel WHERE sira_no = ?", (s_sira,))
                conn.commit(); conn.close(); st.success("Kayıt silindi!"); st.rerun()

    elif st.session_state["rol"] == "sube" and menu_secim == "Aylık Puantaj Girişi":
        st.markdown("### 📅 ŞANTİYE AYLIK PUANTAJ GİRİŞ EKRANI")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            df_puantaj_aktif = df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"] if not df_goster.empty else pd.DataFrame()
            if df_puantaj_aktif.empty: st.warning("⚠️ Onaylı aktif çalışan personel bulunmalıdır!")
            else:
                with st.form("puantaj_form", clear_on_submit=True):
                    p_secenekler = df_puantaj_aktif.apply(lambda r: f"{r['Adı Soyadı']} ({r['TC Kimlik No']})", axis=1).tolist()
                    secilen_p = st.selectbox("Personel Seçin", p_secenekler)
                    donem_ay = st.selectbox("Puantaj Dönemi", ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
                    calisilan_gun = st.number_input("Çalışılan Gün Sayısı", min_value=0, max_value=31, value=26)
                    sefi_adi = st.text_input("Giriş Yapan Yetkili")
                    if st.form_submit_button("💾 PUANTAJI MERKEZE GÖNDER", use_container_width=True):
                        p_str = str(secilen_p)
                        p_str_parts = p_str.split(" (")
                        p_ad_parca = p_str_parts[0].strip()
                        p_tc_parca = p_str_parts[1].replace(")", "").strip()
                        su_an_p = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
                        cursor.execute("DELETE FROM puantaj WHERE tc_no = ? AND donem_ay = ? AND santiye = ?", (p_tc_parca, donem_ay, st.session_state["santiye"]))
                        cursor.execute("INSERT INTO puantaj (tarih_satir, santiye, personel_adi, tc_no, donem_ay, gun_sayisi, giren_sef) VALUES (?, ?, ?, ?, ?, ?, ?)", (su_an_p, str(st.session_state["santiye"]), str(p_ad_parca), str(p_tc_parca), str(donem_ay), int(calisilan_gun), sefi_adi.upper()))
                        conn.commit(); conn.close(); st.success("✔️ Puantaj İşlendi!"); time.sleep(0.5); st.rerun()
        with col_p2:
            st.dataframe(df_p_goster, use_container_width=True, hide_index=True)
            if not df_p_goster.empty:
                p_silme_listesi = df_p_goster.apply(lambda r: f"ID: {r['Kayıt ID']} | {r['Personel_Adi']}", axis=1).tolist()
                secilen_p_sil_id = st.selectbox("Hatalı Kaydı Seçin", p_silme_listesi)
                if st.button("❌ SEÇİLİ PUANTAJI SİL", use_container_width=True):
                    sil_id = int(str(secilen_p_sil_id).split(" | ").replace("ID: ", "").strip())
                    conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
                    cursor.execute("DELETE FROM puantaj WHERE id = ?", (sil_id,))
                    conn.commit(); conn.close(); st.success("Silindi!"); time.sleep(0.5); st.rerun()
    elif st.session_state["rol"] in ["merkez", "izleyici"]:
        tab1, tab2 = st.tabs(["👥 CANLI MASTER PERSONEL HAVUZU", "📅 TOPLU ŞANTİYE PUANTAJLARI"])
        with tab1:
            # 🏢 MAVİ ÖZET PANEL: HANGİ ŞANTİYEDE KAÇ AKTİF PERSONEL VAR ANLIK ÖZET TABLOSU
            if not df_canli.empty:
                st.markdown("##### 🏛️ ŞANTİYE BAZLI AKTİF PERSONEL DAĞILIMI")
                df_santiye_aktifleri = df_canli[df_canli["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]
                if not df_santiye_aktifleri.empty:
                    df_dagilim = df_santiye_aktifleri.groupby("Şantiye Bilgisi").size().reset_index(name="Aktif Personel Sayısı")
                    df_dagilim.columns = ["Şantiye Adı", "Toplam Aktif Çalışan"]
                    st.dataframe(df_dagilim, use_container_width=True, hide_index=True)
                else:
                    st.info("💡 Şu an şantiyelerde resmi aktif çalışan bulunmamaktadır.")
                st.markdown("---")

            with st.expander("📥 EXCEL / CSV DOSYASINDAN TOPLU PERSONEL AKTARIMI (MERKEZ ÖZEL)"):
                st.info("💡 Sütunlar: 'Adı Soyadı', 'TC Kimlik No', 'Doğum Tarihi', 'İşe Giriş Tarihi', 'İşten Çıkış Tarihi', 'Birimi', 'Şantiye Bilgisi', 'Firma Bilgisi', 'Giriş/Çıkış Durumu', 'Çalışma Durumu', 'Çıkış Gün Sayısı'")
                yuklenen_dosya = st.file_uploader("Personel Excel Listesini Seçin", type=["xlsx", "xls", "csv"])
                if yuklenen_dosya is not None:
                    try:
                        # 🛠️ Codec hatasını tamamen yıkan çoklu otomatik şifreleme süzgeci
                        if yuklenen_dosya.name.endswith('.csv'):
                            try: df_toplu = pd.read_csv(yuklenen_dosya, sep=None, engine='python', dtype=str, encoding='utf-8')
                            except:
                                try: df_toplu = pd.read_csv(yuklenen_dosya, sep=None, engine='python', dtype=str, encoding='cp1254')
                                except: df_toplu = pd.read_csv(yuklenen_dosya, sep=None, engine='python', dtype=str, encoding='latin1')
                        else:
                            df_toplu = pd.read_excel(yuklenen_dosya, dtype=str)
                        
                        df_toplu.columns = df_toplu.columns.str.strip()
                        st.dataframe(df_toplu.head(5), use_container_width=True)
                        
                        if st.button("🚀 TÜM LİSTEYİ TAM EXCEL SIRASIYLA SİSTEME AKTAR", use_container_width=True):
                            conn = sqlite3.connect(DB_FILE); cursor = conn.cursor(); aktarilan = 0
                            
                            # Excel'deki orijinal nizam korunsun diye listeyi tersten (reverse) okuyarak işliyoruz kral!
                            df_toplu_ters = df_toplu.iloc[::-1]
                            
                            for _, r in df_toplu_ters.iterrows():
                                name_col = "Adı Soyadı" if "Adı Soyadı" in df_toplu.columns else df_toplu.columns[0]
                                tc_col = "TC Kimlik No" if "TC Kimlik No" in df_toplu.columns else df_toplu.columns[1]
                                
                                if pd.isna(r[name_col]) or pd.isna(r[tc_col]): continue
                                
                                cursor.execute("""
                                    INSERT INTO personel (adi_soyadi, tc_no, dogum_tarihi, ise_giris, isten_cikis, birimi, santiye, firma, durum, calisma_sekli, fark_gun) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    str(r.get("Adı Soyadı", r[name_col])).strip().upper(),
                                    str(r.get("TC Kimlik No", r[tc_col])).strip(),
                                    str(r.get("Doğum Tarihi", "-")),
                                    str(r.get("İşe Giriş Tarihi", "-")),
                                    str(r.get("İşten Çıkış Tarihi", "-")),
                                    str(r.get("Birimi", "DÜZ İŞÇİ")),
                                    str(r.get("Şantiye Bilgisi", "MERKEZ")),
                                    str(r.get("Firma Bilgisi", "NEVZAT USTA")),
                                    str(r.get("Giriş/Çıkış Durumu", "GİRİŞ (BEKLEMEDE)")),
                                    str(r.get("Çalışma Durumu", "NORMAL")),
                                    str(r.get("Çıkış Gün Sayısı", "-"))
                                ))
                                aktarilan += 1
                            conn.commit(); conn.close(); st.success(f"✔️ {aktarilan} Personel Tam Sırasıyla Kaydedildi!"); time.sleep(0.5); st.rerun()
                    except Exception as ex: st.error(f"❌ Hata: {ex}")

            f_col1, f_col2 = st.columns(2)
            with f_col1: secilen_f_santiye = st.selectbox("Şantiye Şube Seçimi", ["HEPSİ", "CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"])
            with f_col2: secilen_f_durum = st.selectbox("SGK Onay Durumu", ["HEPSİ", "SGK GİRİŞİ YAPILDI", "SGK ÇIKIŞI YAPILDI", "GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])
            
            # Değişkeni burada butonlardan hemen önce kuruyoruz kral
            df_merkez_p_filtreli = df_canli.copy()
            if secilen_f_santiye != "HEPSİ": df_merkez_p_filtreli = df_merkez_p_filtreli[df_merkez_p_filtreli["Şantiye Bilgisi"] == secilen_f_santiye]
            if secilen_f_durum != "HEPSİ": df_merkez_p_filtreli = df_merkez_p_filtreli[df_merkez_p_filtreli["Giriş/Çıkış Durumu"] == secilen_f_durum]
            
            # 🛠️ MERKEZ İÇİN CANLI LİSTE EXCEL İNDİRME BUTONU YERİ GÜVENLİĞE ALINDI
            if not df_merkez_p_filtreli.empty:
                excel_dosyasi_merkez = excel_disa_aktar(df_merkez_p_filtreli)
                if excel_dosyasi_merkez:
                    st.download_button(label="📥 CANLI MASTER LİSTEYİ EXCEL OLARAK İNDİR", data=excel_dosyasi_merkez, file_name="merkez_master_personel_listesi.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                
                try: st.dataframe(df_merkez_p_filtreli.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
                except: st.dataframe(df_merkez_p_filtreli.style.applymap(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
                
                if st.session_state["rol"] == "merkez":
                    m_p_sil_list = df_merkez_p_filtreli.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                    m_secilen_sil = st.selectbox("MASTER SİL: Personel Seçin", m_p_sil_list)
                    if st.button("🔥 SEÇİLİ PERSONELİ SİSTEMDEN KALICI OLARAK SİL", use_container_width=True):
                        m_sil_sira = int(str(m_secilen_sil).split(" | ").replace("Sıra No: ", "").strip())
                        conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
                        cursor.execute("DELETE FROM personel WHERE sira_no = ?", (m_sil_sira,))
                        conn.commit(); conn.close(); st.success("Sistemden tamamen temizlendi!"); time.sleep(0.5); st.rerun()
        with tab2:
            fp_col1, fp_col2 = st.columns(2)
            with fp_col1: secilen_fp_santiye = st.selectbox("Puantaj Şantiye Seçimi", ["HEPSİ", "CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"])
            with fp_col2: secilen_fp_ay = st.selectbox("Dönem Ay Seçimi", ["HEPSİ", "OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
            df_merkez_pt_filtreli = df_puantaj_canli.copy()
            if secilen_fp_santiye != "HEPSİ": df_merkez_pt_filtreli = df_merkez_pt_filtreli[df_merkez_pt_filtreli["Şantiye"] == secilen_fp_santiye]
            if secilen_fp_ay != "HEPSİ": df_merkez_pt_filtreli = df_merkez_pt_filtreli[df_merkez_pt_filtreli["Dönem_Ay"] == secilen_fp_ay]
            st.dataframe(df_merkez_pt_filtreli, use_container_width=True, hide_index=True)




















