import streamlit as st
import pandas as pd
import datetime
import os
import io
import extra_streamlit_components as stx  # Gerçek çerezli Beni Hatırla motoru

# Sayfa Ayarları - Birebir Kurumsal Geniş Ekran
st.set_page_config(page_title="PERSONEL TAKİP", layout="wide")

st.markdown("""
<style>
    /* 🔒 GÜVENLİK YAMASI: Sağ üstteki kedi, kalem, paylaş butonlarını tamamen uçurur */
    header, footer, .stDeployButton, [data-testid="stToolbar"], #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Ana Arka Plan - Temiz Kurumsal Beyaz / Açık Gri */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B !important;
    }
    /* Üst Özet Kartları Tasarımı - Soft Gölgeli */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        padding: 15px 20px !important;
        border-left: 5px solid #319795 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
    }
    div[data-testid="stMetric"] label {
        color: #64748B !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #0F172A !important;
        font-weight: bold !important;
    }
    /* Form Alanı Tasarımı */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        padding: 25px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
    }
    label, p, span, h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
    }
    
    /* "BENİ HATIRLA" YAZISININ KESİLMESİNİ ÖNLEYEN KESİN ÇÖZÜM CSS YAPISI */
    div[data-testid="stCheckbox"] {
        width: 100% !important;
        max-width: 300px !important;
        display: block !important;
    }
    div[data-testid="stCheckbox"] label {
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
    }
    div[data-testid="stCheckbox"] label p {
        color: #0F172A !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        overflow: visible !important;
        display: inline-block !important;
        width: 200px !important;
    }

    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 6px !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #319795 0%, #2B6CB0 100%) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 12px rgba(43, 108, 176, 0.3) !important;
    }
    .alert-bar {
        background: #FEF3C7;
        color: #92400E !important;
        border-left: 5px solid #D97706;
        padding: 12px;
        border-radius: 8px;
        font-weight: bold;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

VERI_DOSYASI = "santiye_personel_verileri_v2.csv"
PUANTAJ_DOSYASI = "santiye_puantaj_verileri.csv"

SUTUNLAR = [
    "Sıra No", "Adı Soyadı", "TC Kimlik No", "Doğum Tarihi", 
    "İşe Giriş Tarihi", "İşten Çıkış Tarihi", "Birimi", 
    "Şantiye Bilgisi", "Firma Bilgisi", "Giriş/Çıkış Durumu", "Çalışma Durumu", "Çıkış Gün Sayısı"
]

PUANTAJ_SUTUNLAR = ["Tarih_Saat", "Şantiye", "Personel_Adi", "TC_Kimlik", "Dönem_Ay", "Çalışılan_Gün_Sayısı", "Giren_Sef"]

if not os.path.exists(VERI_DOSYASI):
    df_init = pd.DataFrame(columns=SUTUNLAR)
    df_init.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")
else:
    df_check = pd.read_csv(VERI_DOSYASI, encoding="utf-8")
    if "Çıkış Gün Sayısı" not in df_check.columns:
        df_check["Çıkış Gün Sayısı"] = "-"
        df_check.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")

if not os.path.exists(PUANTAJ_DOSYASI):
    df_p_init = pd.DataFrame(columns=PUANTAJ_SUTUNLAR)
    df_p_init.to_csv(PUANTAJ_DOSYASI, index=False, encoding="utf-8")
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

try:
    saved_user = cookie_manager.get(cookie="saved_user")
except:
    saved_user = None

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
    if len(temiz) > 8: temiz = temiz[:8]
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
                        try:
                            cookie_manager.set("saved_user", kullanici_adi, max_age=datetime.timedelta(days=30))
                        except:
                            pass
                    st.rerun()
                else: st.error("❌ Kullanıcı adı veya şifre hatalı!")
else:
    col_u1, col_u2, col_u3 = st.columns(3)
    with col_u1:
        st.markdown(f"<h3 style='color: #2B6CB0; margin-top:0; font-family:sans-serif;'>💼 PERSONEL TAKİP | {st.session_state['santiye']}</h3>", unsafe_allow_html=True)
    with col_u2:
        if st.button("Canlı Verileri Yenile", use_container_width=True): st.rerun()
    with col_u3:
        if st.button("SİSTEMDEN GÜVENLİ ÇIKIŞ", use_container_width=True):
            st.session_state["giris_yapildi"] = False
            try:
                cookie_manager.delete("saved_user")
            except:
                pass
            st.rerun()

    df_canli = pd.read_csv(VERI_DOSYASI, encoding="utf-8")
    df_puantaj_canli = pd.read_csv(PUANTAJ_DOSYASI, encoding="utf-8")
    
    if st.session_state["rol"] == "sube":
        menu_secim = st.sidebar.radio("MENÜ SEÇENEKLERİ", ["Personel Giriş / Çıkış", "Aylık Puantaj Girişi"])
        df_goster = df_canli[df_canli["Şantiye Bilgisi"] == st.session_state["santiye"]]
        df_p_goster = df_puantaj_canli[df_puantaj_canli["Şantiye"] == st.session_state["santiye"]]
    else:
        menu_secim = "Merkez Tracking"
        df_goster = df_canli.copy()
        df_p_goster = df_puantaj_canli.copy()

    df_bekleyen_sayi = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])]
    if not df_bekleyen_sayi.empty and st.session_state["rol"] == "merkez":
        st.markdown(f"<div class='alert-bar'>🔔 BİLDİRİM: Şantiyelerden Onay Bekleyen {len(df_bekleyen_sayi)} Yeni Personel Hareketi Var!</div>", unsafe_allow_html=True)

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Onaylı Aktif Çalışan", len(df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]))
    m2.metric("Onay Bekleyen Hareketler", len(df_goster[df_goster["Giriş/Çıkış Durumu"].astype(str).str.contains("BEKLEMEDE", na=False)]))
    m3.metric("Toplam Kartlı Personel", len(df_goster))
    m4.metric("Toplam Puantaj Gün Sayısı", int(df_p_goster["Çalışılan_Gün_Sayısı"].sum()) if not df_p_goster.empty else 0)
    st.markdown("---")
    if st.session_state["rol"] == "merkez":
        if not df_bekleyen_sayi.empty:
            with st.expander("🔔 ŞANTİYELERDEN GELEN ONAY BEKLEYEN HAREKETLER", expanded=True):
                bekleyen_listesi = df_bekleyen_sayi.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Şantiye Bilgisi']} - {r['Giriş/Çıkış Durumu']})", axis=1).tolist()
                secilen_islem_metni = st.selectbox("Onaylanacak Personel Kartını Seçin", bekleyen_listesi)
                if secilen_islem_metni:
                    parca = secilen_islem_metni.split(" | ")
                    secilen_sira_no = int(parca[0].replace("Sıra No: ", "").strip())
                    mevcut_durum = df_canli[df_canli["Sıra No"] == secilen_sira_no]["Giriş/Çıkış Durumu"].values[0]
                    o1, o2 = st.columns(2)
                    with o1:
                        if mevcut_durum == "GİRİŞ (BEKLEMEDE)":
                            if st.button("✅ SGK GİRİŞİNE ONAY VER", use_container_width=True):
                                df_canli.loc[df_canli["Sıra No"] == secilen_sira_no, "Giriş/Çıkış Durumu"] = "SGK GİRİŞİ YAPILDI"
                                df_canli.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")
                                st.success("Durum başarıyla 'SGK GİRİŞİ YAPILDI' olarak güncellendi!")
                                st.rerun()
                        elif mevcut_durum == "ÇIKIŞ (BEKLEMEDE)":
                            if st.button("🚫 SGK ÇIKIŞINA ONAY VER", use_container_width=True):
                                df_canli.loc[df_canli["Sıra No"] == secilen_sira_no, "Giriş/Çıkış Durumu"] = "SGK ÇIKIŞI YAPILDI"
                                df_canli.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")
                                st.success("Durum başarıyla 'SGK ÇIKIŞI YAPILDI' olarak güncellendi!")
                                st.rerun()
                    with o2: st.info("Siz onay verdiğiniz an ilgili şantiyenin tablosu güncellenir.")
                st.markdown("---")

    if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
        col_sol_form, col_sag_tablo = st.columns([1.2, 3])
        with col_sol_form:
            st.markdown("##### 📥 PERSONEL KART TANIMLAMA")
            islem_modu = st.radio("Mod", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], label_visibility="collapsed")
            varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris, varsayilan_cikis, varsayilan_sira = "", "", "", "", "-", None
            
            df_guncellenebilir_havuz = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])]
            
            if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and not df_guncellenebilir_havuz.empty:
                p_guncelle_listesi = df_guncellenebilir_havuz.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Giriş/Çıkış Durumu']})", axis=1).tolist()
                secilen_g_p = st.selectbox("İşlem Yapılacak Personeli Seçin", p_guncelle_listesi)
                if secilen_g_p:
                    g_sira_no = int(secilen_g_p.split(" | ")[0].replace("Sıra No: ", "").strip())
                    p_satir = df_guncellenebilir_havuz[df_guncellenebilir_havuz["Sıra No"] == g_sira_no].iloc[0]
                    varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris = str(p_satir["Adı Soyadı"]), str(p_satir["TC Kimlik No"]), str(p_satir["Doğum Tarihi"]), str(p_satir["İşe Giriş Tarihi"])
                    varsayilan_cikis = str(p_satir["İşten Çıkış Tarihi"]) if str(p_satir["İşten Çıkış Tarihi"]) != "-" else ""
                    varsayilan_sira = g_sira_no
            elif islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and df_guncellenebilir_havuz.empty:
                st.info("💡 Güncellenebilecek personel bulunmuyor. Onaylı personeller şantiye tarafından değiştirilemez.")
            st.markdown("---")
            with st.form("excel_birebir_form", clear_on_submit=False):
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
                        if g_tarih > c_tarih:
                            tarih_hata_kontrol = True
                        else:
                            fark_gun = (c_tarih - g_tarih).days + 1
                            hesaplanan_gun_metni = f"{fark_gun} Gün"
                    except:
                        hesaplanan_gun_metni = "-"
                
                st.text_input("ÇIKIŞ GÜN SAYISI (Otomatik Hesaplanır)", value=hesaplanan_gun_metni, disabled=True)
                
                if st.form_submit_button("💾 VERİYİ SİSTEME İŞLE", use_container_width=True):
                    if tarih_hata_kontrol:
                        st.error("🛑 GÜVENLİK ENGELİ: İşe giriş tarihi, işten çıkış tarihinden sonra olamaz!")
                    elif p_adi.strip() != "" and p_tc.strip() != "":
                        if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and varsayilan_sira is not None:
                            df_canli = df_canli[df_canli["Sıra No"] != varsayilan_sira]
                            sira_no = varsayilan_sira
                        else: sira_no = int(df_canli["Sıra No"].max() + 1) if not df_canli.empty else 1
                        
                        yeni_personel = pd.DataFrame([{
                            "Sıra No": sira_no, "Adı Soyadı": p_adi.strip().upper(), "TC Kimlik No": p_tc.strip(),
                            "Doğum Tarihi": p_dogum, "İşe Giriş Tarihi": p_ise_giris, "İşten Çıkış Tarihi": p_isten_cikis,
                            "Birimi": p_birim, "Şantiye Bilgisi": st.session_state["santiye"], "Firma Bilgisi": p_firma.strip().upper(),
                            "Giriş/Çıkış Durumu": p_durum, "Çalışma Durumu": p_calisma, "Çıkış Gün Sayısı": hesaplanan_gun_metni
                        }])
                        df_canli = pd.concat([df_canli, yeni_personel]).sort_values(by="Sıra No")
                        df_canli.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")
                        st.success("✔️ İşlem başarıyla veritabanına işlendi!")
                        st.rerun()
                    else: st.error("❌ İsim ve TC boş geçilemez!")
            
            if not df_goster.empty:
                st.markdown("---")
                p_silme_listesi_sube = df_goster.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']} ({r['Giriş/Çıkış Durumu']})", axis=1).tolist()
                secilen_sil_p_sube = st.selectbox("Silmek İstediğiniz Personeli Seçin", p_silme_listesi_sube, key="sube_p_sil")
                if st.button("❌ SEÇİLİ PERSONELİ LİSTEDEN KALDIR", use_container_width=True):
                    s_sira = int(secilen_sil_p_sube.split(" | ")[0].replace("Sıra No: ", "").strip())
                    p_durumu_kontrol = df_canli[df_canli["Sıra No"] == s_sira]["Giriş/Çıkış Durumu"].values[0]
                    if "BEKLEMEDE" in str(p_durumu_kontrol).upper():
                        df_canli = df_canli[df_canli["Sıra No"] != s_sira]
                        df_canli.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")
                        st.success("Hatalı beklemedeki personel kartı silindi!")
                        st.rerun()
                    else: st.error("🛑 Onaylanmış personeli şantiyeler silsin istemiyoruz!")
        
        with col_sag_tablo:
            st.markdown("##### 📋 ŞANTİYENİZDEKİ PERSONEL HAVUZU")
            st.dataframe(df_goster.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
            csv_sube_p = kurumsal_rapor_uret(df_goster)
            st.download_button(label="📄 BU LİSTEYİ PDF / EXCEL RAPORU YAP", data=csv_sube_p, file_name="santiye_personel_raporu.csv", mime="text/csv", use_container_width=True)
    elif st.session_state["rol"] == "sube" and menu_secim == "Aylık Puantaj Girişi":
        st.markdown("### 📅 ŞANTİYE AYLIK PUANTAJ GİRİŞ EKRANI")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 📥 Yeni Puantaj Kaydı / Düzeltme Paneli")
            df_puantaj_aktif = df_goster[df_goster["Giriş/Çıkış Durumu"] == "SGK GİRİŞİ YAPILDI"]
            if df_puantaj_aktif.empty: st.warning("⚠️ Onaylı aktif çalışan personel bulunmalıdır!")
            else:
                with st.form("puantaj_form", clear_on_submit=True):
                    p_secenekler = df_puantaj_aktif.apply(lambda r: f"{r['Adı Soyadı']} ({r['TC Kimlik No']})", axis=1).tolist()
                    secilen_p = st.selectbox("Personel Seçin", p_secenekler)
                    donem_ay = st.selectbox("Puantaj Dönemi", ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
                    calisilan_gun = st.number_input("Çalışılan Gün Sayısı", min_value=0, max_value=31, value=26)
                    sefi_adi = st.text_input("Giriş Yapan Yetkili")
                    
                    if st.form_submit_button("💾 PUANTAJI MERKEZE GÖNDER", use_container_width=True):
                        # 🎯 GÜVENLİ VE ZIRHLI PARÇALAMA MOTORU ENTEGRE EDİLDİ
                        p_ad_parca = secilen_p.split("(")[0].strip()
                        p_tc_parca = secilen_p.split("(")[1].replace(")", "").strip()
                        su_an_p = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        df_puantaj_canli = df_puantaj_canli[~((df_puantaj_canli["TC_Kimlik"].astype(str) == str(p_tc_parca)) & (df_puantaj_canli["Dönem_Ay"] == donem_ay) & (df_puantaj_canli["Şantiye"] == st.session_state["santiye"]))]
                        yeni_puantaj = pd.DataFrame([{
                            "Tarih_Saat": su_an_p, "Şantiye": st.session_state["santiye"], "Personel_Adi": p_ad_parca, "TC_Kimlik": p_tc_parca,
                            "Dönem_Ay": donem_ay, "Çalışılan_Gün_Sayısı": int(calisilan_gun), "Giren_Sef": sefi_adi.upper()
                        }])
                        df_puantaj_canli = pd.concat([df_puantaj_canli, yeni_puantaj])
                        df_puantaj_canli.to_csv(PUANTAJ_DOSYASI, index=False, encoding="utf-8")
                        st.success("✔️ Puantaj başarıyla merkeze işlendi / güncellendi!")
                        st.rerun()
            
            if not df_p_goster.empty:
                st.markdown("---")
                silme_listesi = df_p_goster.apply(lambda r: f"{r['Tarih_Saat']} | {r['Personel_Adi']} ({r['Dönem_Ay']} - {r['Çalışılan_Gün_Sayısı']} Gün)", axis=1).tolist()
                secilen_sil_p = st.selectbox("Silmek İstediğiniz Kaydı Seçin", silme_listesi, key="sube_p_sil")
                if st.button("❌ SEÇİLİ PUANTAJI LİSTEDEN SİL", use_container_width=True):
                    sil_tarih = secilen_sil_p.split(" | ")[0].strip()
                    df_puantaj_canli = df_puantaj_canli[df_puantaj_canli["Tarih_Saat"] != sil_tarih]
                    df_puantaj_canli.to_csv(PUANTAJ_DOSYASI, index=False, encoding="utf-8")
                    st.success("Hatalı puantaj kaydı silindi!")
                    st.rerun()
        
        with col_p2:
            st.markdown("##### 📋 Şantiyenizin Gönderdiği Puantaj Kayıtları")
            st.dataframe(df_p_goster.iloc[::-1], use_container_width=True, hide_index=True)
            csv_sube_p_data = kurumsal_rapor_uret(df_p_goster)
            st.download_button(label="📄 PUANTAJ RAPORUNU DIŞARI RAPORLA (PDF UYUMLU)", data=csv_sube_p_data, file_name="santiye_puantaj_raporu.csv", mime="text/csv", use_container_width=True)

    elif st.session_state["rol"] == "merkez":
        st.markdown("### 🖥️ GENEL MERKEZ YÖNETİCİ KONTROL KONSOLU")
        
        # 🛡️ KALICI YEDEKLEME BUTONLARI: Sunucu uçsa bile tüm verileri bilgisayarına Excel yapar!
        y1, y2 = st.columns(2)
        with y1:
            st.download_button(label="📥 TÜM PERSONEL HAVUZUNU EXCEL YEDEĞİ OLARAK İNDİR", data=kurumsal_rapor_uret(df_canli), file_name=f"personel_havuzu_yedek_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        with y2:
            st.download_button(label="📥 TOPLU PUANTAJ LİSTESİNİ EXCEL YEDEĞİ OLARAK İNDİR", data=kurumsal_rapor_uret(df_puantaj_canli), file_name=f"puantaj_listesi_yedek_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
        
        st.markdown("---")
        tab1, tab2, tab3 = st.tabs(["👥 CANLI PERSONEL HAVUZU", "📅 TOPLU ŞANTİYE PUANTAJLARI", "📊 STRATEJİK GRAFİK ANALİTİĞİ"])
        
        with tab1:
            st.markdown("#### 🔍 Akıllı Filtreleme Paneli")
            arama_m = st.text_input("Personel Adı veya TC ile Havuzda Canlı Ara...").strip().upper()
            f1, f2 = st.columns(2)
            with f1: sec_santiye = st.multiselect("Şantiyeye Göre Süz", ["GİRESUN", "İSTANBUL", "MORFOLOJİ", "CANİK"])
            with f2: sec_durum = st.multiselect("SGK Onay Durumuna Göre Süz", df_canli["Giriş/Çıkış Durumu"].unique() if not df_canli.empty else [])
            
            df_m_goster = df_canli.copy()
            if arama_m: df_m_goster = df_m_goster[df_m_goster["Adı Soyadı"].str.contains(arama_m, na=False) | df_m_goster["TC Kimlik No"].astype(str).str.contains(arama_m, na=False)]
            if sec_santiye: df_m_goster = df_m_goster[df_m_goster["Şantiye Bilgisi"].isin(sec_santiye)]
            if sec_durum: df_m_goster = df_m_goster[df_m_goster["Giriş/Çıkış Durumu"].isin(sec_durum)]
            
            st.dataframe(df_m_goster.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
            
            if not df_canli.empty:
                st.markdown("---")
                m_p_silme_listesi = df_canli.apply(lambda r: f"Sıra No: {r['Sıra No']} | [{r['Şantiye Bilgisi']}] {r['Adı Soyadı']} ({r['Giriş/Çıkış Durumu']})", axis=1).tolist()
                secilen_m_sil_p = st.selectbox("Kalıcı Olarak Silinecek Personeli Seçin", m_p_silme_listesi, key="merkez_p_sil_kart")
                if st.button("❌ SEÇİLİ PERSONELİ VERİTABANINDAN TAMAMEN UÇUR", use_container_width=True):
                    m_s_sira = int(secilen_m_sil_p.split(" | ")[0].replace("Sıra No: ", "").strip())
                    df_canli = df_canli[df_canli["Sıra No"] != m_s_sira]
                    df_canli.to_csv(VERI_DOSYASI, index=False, encoding="utf-8")
                    st.success("Seçilen personel kartı merkez tam yetkisiyle uçuruldu!")
                    st.rerun()
                    
        with tab2:
            pf1, pf2 = st.columns(2)
            with pf1: p_sec_santiye = st.multiselect("Puantaj Şantiyesi Süz", ["GİRESUN", "İSTANBUL", "MORFOLOJİ", "CANİK"])
            with pf2: p_sec_ay = st.multiselect("Puantaj Ayı Süz", ["OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"])
            
            df_p_m_goster = df_puantaj_canli.copy()
            if p_sec_santiye: df_p_m_goster = df_p_m_goster[df_p_m_goster["Şantiye"].isin(p_sec_santiye)]
            if p_sec_ay: df_p_m_goster = df_p_m_goster[df_p_m_goster["Dönem_Ay"].isin(p_sec_ay)]
            
            st.dataframe(df_p_m_goster.iloc[::-1], use_container_width=True, hide_index=True)
            
            if not df_puantaj_canli.empty:
                st.markdown("---")
                m_silme_listesi = df_puantaj_canli.apply(lambda r: f"{r['Tarih_Saat']} | [{r['Şantiye']}] {r['Personel_Adi']} ({r['Dönem_Ay']} - {r['Çalışılan_Gün_Sayısı']} Gün)", axis=1).tolist()
                secilen_m_sil = st.selectbox("Silinecek Hatalı Puantajı Seçin", m_silme_listesi, key="merkez_p_sil_benzersiz")
                if st.button("❌ SEÇİLİ PUANTAJI VERİTABANINDAN KALICI OLARAK SİL", use_container_width=True):
                    m_sil_tarih = secilen_m_sil.split(" | ")[0].strip()
                    df_puantaj_canli = df_puantaj_canli[df_puantaj_canli["Tarih_Saat"] != m_sil_tarih]
                    df_puantaj_canli.to_csv(PUANTAJ_DOSYASI, index=False, encoding="utf-8")
                    st.success("Seçilen puantaj kaydı silindi!")
                    st.rerun()
                    
        with tab3:
            st.markdown("#### 📊 Şantiye Canlı Dağılım Grafikleri")
            if not df_canli.empty:
                santiye_counts = df_canli["Şantiye Bilgisi"].value_counts()
                st.bar_chart(santiye_counts)
            else:
                st.info("💡 Grafik çizilebilmesi için sistemde kayıtlı personel verisi bulunmalıdır.")
                
            st.markdown("---")
            st.markdown("<p style='text-align: center; color: #64748B; font-size: 11px;'>🤖 Personel Takip Sistemi | Güvenli Altyapı ve Kararlı Sürüm</p>", unsafe_allow_html=True)
