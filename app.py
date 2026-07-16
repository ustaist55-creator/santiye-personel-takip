import streamlit as st
import pandas as pd
import datetime
import os
import io
import time
import sqlite3
import extra_streamlit_components as stx

# Sayfa Ayarları - Birebir Kurumsal Geniş Ekran
st.set_page_config(page_title="PERSONEL TAKİP", layout="wide")

st.markdown("""
<style>
    /* 🔒 GÜVENLİK VE MOBİL YAMASI */
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    [data-testid="stStatusWidget"], div[class^="viewerBadge"], div[class*="MainMenu"], iframe[title="st.iframe"] {
        display: none !important;
        visibility: hidden !important;
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
    div[data-testid="stMetric"] label { color: #64748B !important; font-weight: 600 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #0F172A !important; font-weight: bold !important; }
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

# 📡 OTOMATİK SQL VERİTABANI ALTYAPISI
DB_YOLU = "santiye_master_veri.db"

def sql_altyapi_kur():
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personel (
            sira_no INTEGER PRIMARY KEY, adi_soyadi TEXT, tc_no TEXT, dogum_tarihi TEXT,
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

sql_altyapi_kur()
def verileri_yukle_sql():
    conn = sqlite3.connect(DB_YOLU)
    df_p = pd.read_sql_query("SELECT sira_no as 'Sıra No', adi_soyadi as 'Adı Soyadı', tc_no as 'TC Kimlik No', dogum_tarihi as 'Doğum Tarihi', ise_giris as 'İşe Giriş Tarihi', isten_cikis as 'İşten Çıkış Tarihi', birimi as 'Birimi', santiye as 'Şantiye Bilgisi', firma as 'Firma Bilgisi', durum as 'Giriş/Çıkış Durumu', calisma_sekli as 'Çalışma Durumu', fark_gun as 'Çıkış Gün Sayısı' FROM personel", conn)
    df_pt = pd.read_sql_query("SELECT id as 'Kayıt ID', tarih_satir as 'Tarih_Saat', santiye as 'Şantiye', personel_adi as 'Personel_Adi', tc_no as 'TC_Kimlik', donem_ay as 'Dönem_Ay', gun_sayisi as 'Çalışılan_Gün_Sayısı', giren_sef as 'Giren_Sef' FROM puantaj", conn)
    conn.close()
    return df_p, df_pt

df_canli, df_puantaj_canli = verileri_yukle_sql()

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
    st.session_state["giris_yapildi"] = False
    st.session_state["kullanici"] = ""
    st.session_state["santiye"] = ""
    st.session_state["firma"] = ""
    st.session_state["rol"] = ""
try: saved_user = cookie_manager.get(cookie="saved_user")
except: saved_user = None

if saved_user and not st.session_state["giris_yapildi"]:
    if saved_user in KULLANICILAR:
        st.session_state["giris_yapildi"] = True
        st.session_state["kullanici"] = saved_user
        st.session_state["santiye"] = KULLANICILAR[saved_user]["santiye"]
        st.session_state["firma"] = KULLANICILAR[saved_user]["firma"]
        st.session_state["rol"] = KULLANICILAR[saved_user]["rol"]

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

def kurumsal_rapor_uret(df_data):
    return df_data.to_csv(index=False).encode('utf-8-sig')

if not st.session_state["giris_yapildi"]:
    st.write("")
    col_l1, col_l2, col_l3 = st.columns([1.2, 1, 1.2])
    with col_l2:
        st.markdown("<h3 style='text-align: center; color: #2B6CB0;'>🏛️ PERSONEL TAKİP</h3>", unsafe_allow_html=True)
        beni_hatirla_check = st.checkbox("Beni Hatırla")
        with st.form("login_form"):
            kullanici_adi = st.text_input("Kullanıcı Adı")
            sifre = st.text_input("Şifre", type="password")
            if st.form_submit_button("SİSTEME GÜVENLİ GİRİŞ YAP", use_container_width=True):
                if kullanici_adi in KULLANICILAR and KULLANICILAR[kullanici_adi]["sifre"] == sifre:
                    st.session_state["giris_yapildi"] = True
                    st.session_state["kullanici"] = kullanici_adi
                    st.session_state["santiye"] = KULLANICILAR[kullanici_adi]["santiye"]
                    st.session_state["firma"] = KULLANICILAR[kullanici_adi]["firma"]
                    st.session_state["rol"] = KULLANICILAR[kullanici_adi]["rol"]
                    if beni_hatirla_check:
                        try: cookie_manager.set("saved_user", kullanici_adi, max_age=datetime.timedelta(days=30))
                        except: pass
                    st.rerun()
                else: st.error("❌ Hatalı Giriş!")
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

    if st.session_state["rol"] == "sube":
        menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["Personel Giriş / Çıkış", "Aylık Puantaj Girişi"])
        df_goster = df_canli[df_canli["Şantiye Bilgisi"] == st.session_state["santiye"]] if not df_canli.empty else df_canli
        df_p_goster = df_puantaj_canli[df_puantaj_canli["Şantiye"] == st.session_state["santiye"]] if not df_puantaj_canli.empty else df_puantaj_canli
    else:
        menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["🏛️ Merkez Personel Takip", "📅 Aylık Puantajları İzle"])
        df_goster = df_canli.copy()
        df_p_goster = df_puantaj_canli.copy()

    bugun_str = datetime.date.today().strftime("%d.%m.%Y")
    df_bekleyen_sayi = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_canli.empty else pd.DataFrame()

    st.markdown("##### 📈 ŞANTİYE CANLI İSTATİSTİK PANELI")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Toplam Aktif Çalışan", len(df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]) if not df_goster.empty else 0)
    m2.metric("Toplam Ayrılan Personel", len(df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK ÇIKIŞI YAPILDI"]) if not df_goster.empty else 0)
    m3.metric("Bugün Girişi Yapılan", len(df_goster[(df_goster["İşe Giriş Tarihi"] == bugun_str) & (df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI")]) if not df_goster.empty else 0)
    m4.metric("Bugün Çıkışı Yapılan", len(df_goster[(df_goster["İşten Çıkış Tarihi"] == bugun_str) & (df_goster["Giriş/Çıkış Durumu"] == "SGK ÇIKIŞI YAPILDI")]) if not df_goster.empty else 0)

    if st.session_state["rol"] in ["merkez", "izleyici"] and not df_canli.empty:
        with st.expander("🏗️ Tüm Şantiyelerin Canlı Aktif Personel Dağılımı"):
            s_cols = st.columns(4)
            santiyeler_listesi = ["CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"]
            for idx, s_ad in enumerate(santiyeler_listesi):
                aktif_s = len(df_canli[(df_canli["Şantiye Bilgisi"] == s_ad) & (df_canli["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI")])
                s_cols[idx % 4].markdown(f"**{s_ad}:** `{aktif_s} Aktif`")
    st.markdown("---")
    if st.session_state["rol"] == "merkez" and menu_secim == "🏛️ Merkez Personel Takip":
        if not df_bekleyen_sayi.empty:
            with st.expander("🔔 ONAY BEKLEYEN HAREKETLER", expanded=True):
                bekleyen_listesi = df_bekleyen_sayi.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Şantiye Bilgisi']})", axis=1).tolist()
                secilen_islem_metni = st.selectbox("Onaylanacak Kartı Seçin", bekleyen_listesi)
                if secilen_islem_metni:
                    # 🎯 %100 KESİN MERKEZ ARINDIRMA MOTORU: split parçalamasından sonra güvenli string temizliği kilitlendi!
                    secilen_sira_no = int(str(secilen_islem_metni).replace("Sıra No: ", "").split(" | ").strip())
                    o1, o2 = st.columns(2)
                    with o1:
                        mevcut_bekleyen_durum = str(df_canli[df_canli["Sıra No"] == secilen_sira_no]["Giriş/Çıkış Durumu"].values).upper()
                        if "GİRİŞ" in mevcut_bekleyen_durum:
                            if st.button("✅ SGK GİRİŞİNE RESMİ ONAY VER"):
                                conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                                cursor.execute("UPDATE personel SET durum = 'SGK GİRİŞİ YAPILDI' WHERE sira_no = ?", (secilen_sira_no,))
                                conn.commit(); conn.close(); st.success("Giriş Onaylandı!"); time.sleep(0.5); st.rerun()
                        elif "ÇIKIŞ" in mevcut_bekleyen_durum:
                            if st.button("🚫 SGK ÇIKIŞINA RESMİ ONAY VER"):
                                conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                                cursor.execute("UPDATE personel SET durum = 'SGK ÇIKIŞI YAPILDI' WHERE sira_no = ?", (secilen_sira_no,))
                                conn.commit(); conn.close(); st.success("Çıkış Onaylandı!"); time.sleep(0.5); st.rerun()

    if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
        col_sol_form, col_sag_tablo = st.columns([1.2, 3])
        with col_sol_form:
            st.markdown("##### 📥 PERSONEL KART TANIMLAMA")
            islem_modu = st.radio("Mod", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], label_visibility="collapsed")
            varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris, varsayilan_cikis, varsayilan_sira, varsayilan_fark = "", "", "", "", "-", None, ""
            
            df_guncellenebilir_havuz = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)", "SGK GİRİŞİ YAPILDI"])] if not df_goster.empty else pd.DataFrame()
            if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and not df_guncellenebilir_havuz.empty:
                p_guncelle_listesi = df_guncellenebilir_havuz.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                secilen_g_p = st.selectbox("Personel Seçin", p_guncelle_listesi)
                if secilen_g_p:
                    g_sira_no = int(str(secilen_g_p).replace("Sıra No: ", "").split(" | ").strip())
                    p_satir = df_guncellenebilir_havuz[df_guncellenebilir_havuz["Sıra No"].astype(str) == str(g_sira_no)].iloc
                    varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris = str(p_satir["Adı Soyadı"]), str(p_satir["TC Kimlik No"]), str(p_satir["Doğum Tarihi"]), str(p_satir["İşe Giriş Tarihi"])
                    varsayilan_cikis, varsayilan_sira, varsayilan_fark = str(p_satir["İşten Çıkış Tarihi"]), g_sira_no, str(p_satir["Çıkış Gün Sayısı"])
            
            with st.form("excel_birebir_form", clear_on_submit=True):
                f_sub1, f_sub2 = st.columns(2)
                with f_sub1:
                    p_adi = st.text_input("ADI SOYADI", value=varsayilan_ad)
                    p_dogum = tarih_formatla(st.text_input("DOĞUM TARİHİ", value=varsayilan_dogum, placeholder="Örn: 01101986"))
                    p_isten_cikis = tarih_formatla(st.text_input("İŞTEN ÇIKIŞ TARİHİ", value=varsayilan_cikis))
                    p_durum = st.selectbox("DURUMU", ["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"], index=1 if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" else 0)
                with f_sub2:
                    p_tc = st.text_input("TC KİMLİK NO", max_chars=11, value=varsayilan_tc)
                    p_ise_giris = tarih_formatla(st.text_input("İŞE GİRİŞ TARİHİ", value=varsayilan_giris, placeholder="Örn: 15062026"))
                    p_birim = st.selectbox("BİRİMİ", YENI_BIRIMLER)
                    p_calisma = st.selectbox("ÇALIŞMA DURUMU", ["NORMAL", "EMEKLİ"])
                st.text_input("FİRMA BİLGİSİ", value=st.session_state["firma"], disabled=True)
                p_fark_gun_elle = st.text_input("ÇIKIŞ GÜN SAYISI", value=varsayilan_fark)
                
                if st.form_submit_button("💾 VERİYİ OTOMATİK VERİTABANINA İŞLE", use_container_width=True):
                    if p_adi.strip() != "" and p_tc.strip() != "":
                        conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                        if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and varsayilan_sira is not None:
                            cursor.execute("DELETE FROM personel WHERE sira_no = ?", (varsayilan_sira,))
                            sira_no = varsayilan_sira
                        else:
                            cursor.execute("SELECT MAX(sira_no) FROM personel")
                            row_val = cursor.fetchone()
                            sira_no = int(row_val) + 1 if row_val and row_val is not None and row_val != (None,) else 1
                        
                        cursor.execute("INSERT INTO personel VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (int(sira_no), p_adi.strip().upper(), str(p_tc.strip()), str(p_dogum), str(p_ise_giris), str(p_isten_cikis), str(p_birim), str(st.session_state["santiye"]), str(st.session_state["firma"]), str(p_durum), str(p_calisma), str(p_fark_gun_elle).upper()))
                        conn.commit(); conn.close(); st.success("✔️ Başarıyla işlendi!"); time.sleep(0.5); st.rerun()
        with col_sag_tablo:
            st.markdown("##### 📋 ŞANTİYENİZDEKİ CANLI PERSONEL HAVUZU")
            df_goster_sirali = df_goster.sort_values(by="Sıra No", ascending=True) if not df_goster.empty else df_goster
            if not df_goster_sirali.empty:
                st.dataframe(df_goster_sirali.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
                r_col1, r_col2 = st.columns(2)
                with r_col1: st.download_button(label="📥 BU LİSTEYİ EXCEL RAPORU YAP", data=kurumsal_rapor_uret(df_goster_sirali), file_name="santiye_personel_raporu.csv", mime="text/csv", use_container_width=True)
                with r_col2:
                    if st.button("🖨️ BU LİSTEYİ RESMİ PDF YAP / YAZDIR", use_container_width=True): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            else: st.info("💡 Kayıtlı personel bulunmuyor.")

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
                        p_ad_parca = str(secilen_p).split(" (").strip()
                        p_tc_parca = str(secilen_p).split(" (").replace(")", "").strip()
                        su_an_p = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                        cursor.execute("DELETE FROM puantaj WHERE tc_no = ? AND donem_ay = ? AND santiye = ?", (p_tc_parca, donem_ay, st.session_state["santiye"]))
                        cursor.execute("INSERT INTO puantaj (tarih_satir, santiye, personel_adi, tc_no, donem_ay, gun_sayisi, giren_sef) VALUES (?, ?, ?, ?, ?, ?, ?)", (su_an_p, str(st.session_state["santiye"]), str(p_ad_parca), str(p_tc_parca), str(donem_ay), int(calisilan_gun), sefi_adi.upper()))
                        conn.commit(); conn.close(); st.success("✔️ Puantaj Kilitlendi!"); time.sleep(0.5); st.rerun()
        with col_p2:
            st.dataframe(df_p_goster.iloc[::-1] if not df_p_goster.empty else df_p_goster, use_container_width=True, hide_index=True)
            if not df_p_goster.empty:
                p_silme_listesi = df_p_goster.apply(lambda r: f"ID: {r['Kayıt ID']} | {r['Personel_Adi']}", axis=1).tolist()
                secilen_p_sil_id = st.selectbox("Hatalı Kaydı Seçin", p_silme_listesi)
                if st.button("❌ SEÇİLİ PUANTAJI LİSTEDEN SİL", use_container_width=True):
                    sil_id = int(str(secilen_p_sil_id).replace("ID: ", "").split(" | ").strip())
                    conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                    cursor.execute("DELETE FROM puantaj WHERE id = ?", (sil_id,))
                    conn.commit(); conn.close(); st.success("Silindi!"); time.sleep(0.5); st.rerun()

    elif st.session_state["rol"] in ["merkez", "izleyici"]:
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
            if st.session_state["rol"] == "merkez" and not df_merkez_p_filtreli.empty:
                m_p_sil_list = df_merkez_p_filtreli.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                m_secilen_sil = st.selectbox("MASTER SİLME: Personel Seçin", m_p_sil_list)
                if st.button("🔥 SEÇİLİ PERSONELİ VERİTABANINA KALICI OLARAK SİL", use_container_width=True):
                    m_sil_sira = int(str(m_secilen_sil).replace("Sıra No: ", "").split(" | ").strip())
                    conn = sqlite3.connect(DB_YOLU); cursor = conn.cursor()
                    cursor.execute("DELETE FROM personel WHERE sira_no = ?", (m_sil_sira,))
                    conn.commit(); conn.close(); st.success("Silindi!"); time.sleep(0.5); st.rerun()
        with tab2:
            fp_col1, fp_col2 = st.columns(2)
            with fp_col1: secilen_fp_santiye = st.selectbox("Puantaj Şantiye Seçimi", ["HEPSİ", "CANİK", "GAZİETHEMPAŞA", "OFİS", "TEPECİK ABLOK", "POLATLI", "GİRESUN", "İSTANBUL", "MORFOLOJİ", "YAYLADERE", "MERKZE İŞYERİ-2", "KILIÇDEDE2"])
            with fp_col2: secilen_fp_ay = st.selectbox("Dönem Ay Seçimi", ["HEPSİ", "OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
            df_merkez_pt_filtreli = df_puantaj_canli.copy()
            if secilen_fp_santiye != "HEPSİ": df_merkez_pt_filtreli = df_merkez_pt_filtreli[df_merkez_pt_filtreli["Şantiye"] == secilen_fp_santiye]
            if secilen_fp_ay != "HEPSİ": df_merkez_pt_filtreli = df_merkez_pt_filtreli[df_merkez_pt_filtreli["Dönem_Ay"] == secilen_fp_ay]
            st.dataframe(df_merkez_pt_filtreli.iloc[::-1], use_container_width=True, hide_index=True)


