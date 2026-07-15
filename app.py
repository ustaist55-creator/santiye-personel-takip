import streamlit as st
import pandas as pd
import datetime
import os
import io
import time
import extra_streamlit_components as stx
from streamlit_gsheets import GSheetsConnection

# Sayfa Ayarları - Birebir Kurumsal Geniş Ekran
st.set_page_config(page_title="PERSONEL TAKİP", layout="wide")

st.markdown("""
<style>
    /* 🔒 GÜVENLİK YAMASI: Sağ üstteki kedi, kalem, paylaş butonlarını tamamen uçurur */
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu {
        display: none !important;
        visibility: hidden !important;
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
    div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div { color: #0F172A !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div { color: #0F172A !important; background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 6px !important; }
    .stButton>button { background: linear-gradient(135deg, #319795 0%, #2B6CB0 100%) !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; transition: all 0.2s ease !important; }
    .stButton>button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 12px rgba(43, 108, 176, 0.3) !important; }
</style>
""", unsafe_allow_html=True)

# 📡 ORTAK VE ORJİNAL GOOGLE DRIVE HAVUZ BAĞLANTISI
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    try:
        st.cache_data.clear() # Her girişte Google Drive'daki en taze veriyi çeker
        df_p = conn.read(worksheet="Sayfa1", ttl=0).dropna(how="all")
        df_pt = conn.read(worksheet="Sayfa2", ttl=0).dropna(how="all")
        return df_p, df_pt
    except:
        df_p = pd.DataFrame(columns=["Sıra No", "Adı Soyadı", "TC Kimlik No", "Doğum Tarihi", "İşe Giriş Tarihi", "İşten Çıkış Tarihi", "Birimi", "Şantiye Bilgisi", "Firma Bilgisi", "Giriş/Çıkış Durumu", "Çalışma Durumu", "Çıkış Gün Sayısı"])
        df_pt = pd.DataFrame(columns=["Tarih_Saat", "Şantiye", "Personel_Adi", "TC_Kimlik", "Dönem_Ay", "Çalışılan_Gün_Sayısı", "Giren_Sef"])
        return df_p, df_pt

df_canli, df_puantaj_canli = verileri_yukle()

# 🔒 HIZLI VE KİLİTLENMEYEN TEK SATIR EKLEME (APPEND) MOTORU
def google_drive_tek_satir_ekle(worksheet_adi, yeni_satir_df):
    try:
        mevcut_df = conn.read(worksheet=worksheet_adi, ttl=0).dropna(how="all")
        guncel_df = pd.concat([mevcut_df, yeni_satir_df]).astype(str).replace("nan", "-").replace("None", "-")
        conn.update(worksheet=worksheet_adi, data=guncel_df)
        st.cache_data.clear()
        return True
    except:
        st.error("⚠️ Google Drive bağlantısı kurulamadı, lütfen butona tekrar basın.")
        return False
KULLANICILAR = {
    "istanbul": {"sifre": "5151", "santiye": "İSTANBUL", "rol": "sube"},
    "giresun": {"sifre": "5252", "santiye": "GİRESUN", "rol": "sube"},
    "morfoloji": {"sifre": "5353", "santiye": "MORFOLOJİ", "rol": "sube"},
    "canik": {"sifre": "5454", "santiye": "CANİK", "rol": "sube"},
    "merkez": {"sifre": "1234", "santiye": "HEPSİ", "rol": "merkez"}
}

cookie_manager = stx.CookieManager()

if "giris_yapildi" not in st.session_state:
    st.session_state["giris_yapildi"] = False
    st.session_state["kullanici"] = ""
    st.session_state["santiye"] = ""
    st.session_state["rol"] = ""

try: saved_user = cookie_manager.get(cookie="saved_user")
except: saved_user = None

if saved_user and not st.session_state["giris_yapildi"]:
    if saved_user in KULLANICILAR:
        st.session_state["giris_yapildi"] = True
        st.session_state["kullanici"] = saved_user
        st.session_state["santiye"] = KULLANICILAR[saved_user]["santiye"]
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
        st.markdown("<h3 style='text-align: center; color: #2B6CB0; margin-bottom: 5px;'>🏛️ PERSONEL TAKİP</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B; font-size:13px; margin-bottom:20px;'>Kullanıcı Giriş Paneli</p>", unsafe_allow_html=True)
        beni_hatirla_check = st.checkbox("Beni Hatırla")
        with st.form("login_form"):
            kullanici_adi = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı girin...")
            sifre = st.text_input("Şifre", type="password", placeholder="Şifrenizi girin...")
            if st.form_submit_button("SİSTEME GÜVENLİ GİRİŞ YAP", use_container_width=True):
                if kullanici_adi in KULLANICILAR and KULLANICILAR[kullanici_adi]["sifre"] == sifre:
                    st.session_state["giris_yapildi"] = True
                    st.session_state["kullanici"] = kullanici_adi
                    st.session_state["santiye"] = KULLANICILAR[kullanici_adi]["santiye"]
                    st.session_state["rol"] = KULLANICILAR[kullanici_adi]["rol"]
                    if beni_hatirla_check:
                        try: cookie_manager.set("saved_user", kullanici_adi, max_age=datetime.timedelta(days=30))
                        except: pass
                    st.rerun()
                else: st.error("❌ Kullanıcı adı veya şifre hatalı!")
else:
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        st.markdown(f"<h3 style='color: #2B6CB0; margin-top:0; font-family:sans-serif;'>💼 PERSONEL TAKİP | {st.session_state['santiye']}</h3>", unsafe_allow_html=True)
    with col_u2:
        if st.button("Canlı Verileri Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
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
        menu_secim = "Merkez Tracking"
        df_goster = df_canli.copy()
        df_p_goster = df_puantaj_canli.copy()

    df_bekleyen_sayi = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_canli.empty else pd.DataFrame()

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Onaylı Aktif Çalışan", len(df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]) if not df_goster.empty else 0)
    m2.metric("Onay Bekleyen Hareketler", len(df_goster[df_goster["Giriş/Çıkış Durumu"].astype(str).str.contains("BEKLEMEDE", na=False)]) if not df_goster.empty else 0)
    m3.metric("Toplam Kartlı Personel", len(df_goster) if not df_goster.empty else 0)
    m4.metric("Toplam Puantaj Gün Sayısı", int(df_p_goster["Çalışılan_Gün_Sayısı"].astype(float).sum()) if not df_p_goster.empty else 0)
    st.markdown("---")
    if st.session_state["rol"] == "merkez":
        if not df_bekleyen_sayi.empty:
            with st.expander("🔔 ŞANTİYELERDEN GELEN ONAY BEKLEYEN HAREKETLER", expanded=True):
                bekleyen_listesi = df_bekleyen_sayi.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                secilen_islem_metni = st.selectbox("Onaylanacak Personel Kartını Seçin", bekleyen_listesi)
                if secilen_islem_metni:
                    secilen_sira_no = secilen_islem_metni.split("Sıra No: ")[1].split(" |")[0].strip()
                    o1, o2 = st.columns(2)
                    with o1:
                        if st.button("✅ HAREKETİ GOOGLE DRIVE'DA ONAYLA", use_container_width=True):
                            df_canli.loc[df_canli["Sıra No"].astype(str) == str(secilen_sira_no), "Giriş/Çıkış Durumu"] = "SGK GİRİŞİ YAPILDI"
                            conn.update(worksheet="Sayfa1", data=df_canli)
                            st.cache_data.clear()
                            st.success("İşlem Google Drive'da kalıcı onaylandı!")
                            st.rerun()
                    with o2: st.info("Siz onay verdiğiniz an tüm şantiye ekranları anında ortak güncellenir.")
                st.markdown("---")

    if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
        col_sol_form, col_sag_tablo = st.columns([1.2, 3])
        with col_sol_form:
            st.markdown("##### 📥 PERSONEL KART TANIMLAMA")
            islem_modu = st.radio("Mod", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], label_visibility="collapsed")
            varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris, varsayilan_cikis, varsayilan_sira = "", "", "", "", "-", None
            
            df_guncellenebilir_havuz = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_goster.empty else pd.DataFrame()
            
            if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and not df_guncellenebilir_havuz.empty:
                p_guncelle_listesi = df_guncellenebilir_havuz.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                secilen_g_p = st.selectbox("İşlem Yapılacak Personeli Seçin", p_guncelle_listesi)
                if secilen_g_p:
                    g_sira_no = secilen_g_p.split("Sıra No: ")[1].split(" |")[0].strip()
                    p_satir = df_guncellenebilir_havuz[df_guncellenebilir_havuz["Sıra No"].astype(str) == str(g_sira_no)].iloc[0]
                    varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris = str(p_satir["Adı Soyadı"]), str(p_satir["TC Kimlik No"]), str(p_satir["Doğum Tarihi"]), str(p_satir["İşe Giriş Tarihi"])
                    varsayilan_cikis = str(p_satir["İşten Çıkış Tarihi"]) if str(p_satir["İşten Çıkış Tarihi"]) != "-" else ""
                    varsayilan_sira = g_sira_no
            
            # 🎯 NET ÇÖZÜM: clear_on_submit=True yapıldı, butona basıldığı an kutular bomboş temizlenir!
            with st.form("excel_birebir_form", clear_on_submit=True):
                f_sub1, f_sub2 = st.columns(2)
                with f_sub1:
                    p_adi = st.text_input("ADI SOYADI", value=varsayilan_ad)
                    p_dogum = tarih_formatla(st.text_input("DOĞUM TARİHİ", value=varsayilan_dogum, placeholder="Örn: 01101986"))
                    p_isten_cikis = tarih_formatla(st.text_input("İŞTEN ÇIKIŞ TARİHİ", value=varsayilan_cikis, placeholder="Çıkışta doldurun"))
                    if p_isten_cikis.strip() == "" or p_isten_cikis == ". .": p_isten_cikis = "-"
                    p_durum = st.selectbox("DURUMU", ["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"], index=1 if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" else 0)
                with f_sub2:
                    p_tc = st.text_input("TC KİMLİK NO", max_chars=11, value=varsayilan_tc)
                    p_ise_giris = tarih_formatla(st.text_input("İŞE GİRİŞ TARİHİ", value=varsayilan_giris, placeholder="Örn: 15062026"))
                    p_birim = st.selectbox("BİRİMİ", ["DEMİRCİ", "AHŞAP KALIPÇI", "KULE VİNÇ OPERATÖRÜ", "DÜZ İŞÇİ", "USTA", "KALIPÇI"])
                    p_calisma = st.selectbox("ÇALIŞMA DURUMU", ["NORMAL", "EMEKLİ"])
                p_firma = st.text_input("FİRMA BİLGİSİ", value="USTA KONUT")
                
                hesaplanan_gun_metni = "-"
                tarih_hata_kontrol = False
                if p_ise_giris and p_isten_cikis != "-":
                    try:
                        g_tarih = datetime.datetime.strptime(p_ise_giris, "%d.%m.%Y")
                        c_tarih = datetime.datetime.strptime(p_isten_cikis, "%d.%m.%Y")
                        if g_tarih > c_tarih: tarih_hata_kontrol = True
                        else: hesaplanan_gun_metni = f"{(c_tarih - g_tarih).days + 1} Gün"
                    except: hesaplanan_gun_metni = "-"
                
                st.text_input("ÇIKIŞ GÜN SAYISI (Otomatik)", value=hesaplanan_gun_metni, disabled=True, key="c_gun_otomatik_gosterge")
                
                if st.form_submit_button("💾 VERİYİ GOOGLE EXCEL'E İŞLE", use_container_width=True):
                    if p_adi.strip() != "" and p_tc.strip() != "":
                        if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and varsayilan_sira is not None:
                            df_canli = df_canli[df_canli["Sıra No"].astype(str) != str(varsayilan_sira)]
                            sira_no = varsayilan_sira
                        else: sira_no = int(df_canli["Sıra No"].astype(float).max() + 1) if not df_canli.empty else 1
                        
                        yeni_personel_row = pd.DataFrame([{
                            "Sıra No": int(sira_no), "Adı Soyadı": p_adi.strip().upper(), "TC Kimlik No": str(p_tc.strip()),
                            "Doğum Tarihi": str(p_dogum), "İşe Giriş Tarihi": str(p_ise_giris), "İşten Çıkış Tarihi": str(p_isten_cikis),
                            "Birimi": str(p_birim), "Şantiye Bilgisi": str(st.session_state["santiye"]), "Firma Bilgisi": p_firma.strip().upper(),
                            "Giriş/Çıkış Durumu": str(p_durum), "Çalışma Durumu": str(p_calisma), "Çıkış Gün Sayısı": str(hesaplanan_gun_metni)
                        }])
                        
                        # 📡 Google Drive'a kilitlenmeden anında ekler
                        if google_drive_tek_satir_ekle("Sayfa1", yeni_personel_row):
                            st.success("✔️ Google Excel'e kalıcı olarak işlendi ve form temizlendi!")
                            time.sleep(1)
                            st.rerun()
                    else: st.error("❌ İsim ve TC boş geçilemez!")
    elif st.session_state["rol"] == "sube" and menu_secim == "Aylık Puantaj Girişi":
        st.markdown("### 📅 ŞANTİYE AYLIK PUANTAJ GİRİŞ EKRANI")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 📥 Yeni Puantaj Kaydı / Düzeltme Paneli")
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
                        p_ad_parca = str(secilen_p).split(" (")[0].strip()
                        p_tc_parca = str(secilen_p).split(" (")[1].replace(")", "").strip()
                        su_an_p = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        if not df_puantaj_canli.empty:
                            df_puantaj_canli = df_puantaj_canli[~((df_puantaj_canli["TC_Kimlik"].astype(str) == str(p_tc_parca)) & (df_puantaj_canli["Dönem_Ay"] == donem_ay) & (df_puantaj_canli["Şantiye"] == st.session_state["santiye"]))]
                        
                        yeni_puantaj_row = pd.DataFrame([{
                            "Tarih_Saat": su_an_p, "Şantiye": str(st.session_state["santiye"]), "Personel_Adi": str(p_ad_parca), "TC_Kimlik": str(p_tc_parca),
                            "Dönem_Ay": str(donem_ay), "Çalışılan_Gün_Sayısı": int(calisilan_gun), "Giren_Sef": sefi_adi.upper()
                        }])
                        if google_drive_tek_satir_ekle("Sayfa2", yeni_puantaj_row):
                            st.success("✔️ Puantaj kalıcı olarak e-tabloza eklendi!")
                            time.sleep(1)
                            st.rerun()

        with col_p2:
            st.markdown("##### 📋 Şantiyenizin Gönderdiği Puantaj Kayıtları")
            st.dataframe(df_p_goster.iloc[::-1] if not df_p_goster.empty else df_p_goster, use_container_width=True, hide_index=True)

    elif st.session_state["rol"] == "merkez":
        st.markdown("### 🖥️ GENEL MERKEZ YÖNETİCİ KONTROL KONSOLU")
        tab1, tab2, tab3 = st.tabs(["👥 CANLI PERSONEL HAVUZU", "📅 TOPLU ŞANTİYE PUANTAJLARI", "📊 STRATEJİK GRAFİK ANALİTİĞİ"])
        
        with tab1:
            st.dataframe(df_canli, use_container_width=True, hide_index=True)
            st.download_button(label="📥 MASTER EXCEL RAPORU İNDİR", data=kurumsal_rapor_uret(df_canli), file_name="master_personel.csv", mime="text/csv", use_container_width=True)
            
        with tab2:
            st.dataframe(df_puantaj_canli.iloc[::-1] if not df_puantaj_canli.empty else df_puantaj_canli, use_container_width=True, hide_index=True)
            
        with tab3:
            if not df_canli.empty: st.bar_chart(df_canli["Şantiye Bilgisi"].value_counts())




