import streamlit as st
import pandas as pd
import datetime
import os
import io
import time
import sqlite3  # Ebedi ve otomatik kilitli SQL veritabanı motoru
import extra_streamlit_components as stx

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
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div { color: #0F172A !important; background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important; border-radius: 6px !important; }
    .stButton>button { background: linear-gradient(135deg, #319795 0%, #2B6CB0 100%) !important; color: white !important; border-radius: 8px !important; border: none !important; font-weight: bold !important; transition: all 0.2s ease !important; }
    .stButton>button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 12px rgba(43, 108, 176, 0.3) !important; }
</style>
""", unsafe_allow_html=True)

# 📡 OTOMATİK SQL VERİTABANI BAĞLANTISI VE TABLO KURUMLARI
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
    df_pt = pd.read_sql_query("SELECT tarih_satir as 'Tarih_Saat', santiye as 'Şantiye', personel_adi as 'Personel_Adi', tc_no as 'TC_Kimlik', donem_ay as 'Dönem_Ay', gun_sayisi as 'Çalışılan_Gün_Sayısı', giren_sef as 'Giren_Sef' FROM puantaj", conn)
    conn.close()
    return df_p, df_pt

df_canli, df_puantaj_canli = verileri_yukle_sql()
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
        menu_secim = "Merkez Tracking"
        df_goster = df_canli.copy()
        df_p_goster = df_puantaj_canli.copy()

    df_bekleyen_sayi = df_canli[df_canli["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)"])] if not df_canli.empty else pd.DataFrame()
    if st.session_state["rol"] == "merkez":
        if not df_bekleyen_sayi.empty:
            with st.expander("🔔 ŞANTİYELERDEN GELEN ONAY BEKLEYEN HAREKETLER", expanded=True):
                bekleyen_listesi = df_bekleyen_sayi.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                secilen_islem_metni = st.selectbox("Onaylanacak Personel Kartını Seçin", bekleyen_listesi)
                if secilen_islem_metni:
                    secilen_sira_no = int(str(secilen_islem_metni).split("Sıra No: ").split(" |").strip())
                    o1, o2 = st.columns(2)
                    with o1:
                        if st.button("✅ HAREKETİ SİSTEME ONAYLA", use_container_width=True):
                            conn = sqlite3.connect(DB_YOLU)
                            cursor = conn.cursor()
                            cursor.execute("UPDATE personel SET durum = 'SGK GİRİŞİ YAPILDI' WHERE sira_no = ?", (secilen_sira_no,))
                            conn.commit()
                            conn.close()
                            st.success("İşlem SQL veritabanında otomatik onaylandı!")
                            time.sleep(0.5)
                            st.rerun()
                    with o2: st.info("Siz onay verdiğiniz an tüm şantiye ekranları canlı ortak güncellenir.")
                st.markdown("---")

    if st.session_state["rol"] == "sube" and menu_secim == "Personel Giriş / Çıkış":
        col_sol_form, col_sag_tablo = st.columns([1.2, 3])
        with col_sol_form:
            st.markdown("##### 📥 PERSONEL KART TANIMLAMA")
            islem_modu = st.radio("Mod", ["Sıfırdan Yeni Personel Ekle", "Var Olan Personeli Güncelle / Çıkış Yap"], label_visibility="collapsed")
            varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris, varsayilan_cikis, varsayilan_sira, varsayilan_fark = "", "", "", "", "-", None, ""
            
            df_guncellenebilir_havuz = df_goster[df_goster["Giriş/Çıkış Durumu"].isin(["GİRİŞ (BEKLEMEDE)", "ÇIKIŞ (BEKLEMEDE)", "SGK GİRİŞİ YAPILDI"])] if not df_goster.empty else pd.DataFrame()
            
            if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and not df_guncellenebilir_havuz.empty:
                p_guncelle_listesi = df_guncellenebilir_havuz.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                secilen_g_p = st.selectbox("İşlem Yapılacak Personeli Seçin", p_guncelle_listesi)
                if secilen_g_p:
                    g_sira_no = int(str(secilen_g_p).split("Sıra No: ").split(" |").strip())
                    p_satir = df_guncellenebilir_havuz[df_guncellenebilir_havuz["Sıra No"].astype(str) == str(g_sira_no)].iloc[0]
                    varsayilan_ad, varsayilan_tc, varsayilan_dogum, varsayilan_giris = str(p_satir["Adı Soyadı"]), str(p_satir["TC Kimlik No"]), str(p_satir["Doğum Tarihi"]), str(p_satir["İşe Giriş Tarihi"])
                    varsayilan_cikis = str(p_satir["İşten Çıkış Tarihi"]) if str(p_satir["İşten Çıkış Tarihi"]) != "-" else ""
                    varsayilan_sira = g_sira_no
                    varsayilan_fark = str(p_satir["Çıkış Gün Sayısı"]) if str(p_satir["Çıkış Gün Sayısı"]) != "-" else ""
            
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
                
                # 🎯 NET ÇÖZÜM: Kilit kaldırıldı! Çıkış gün sayısı artık şefin klavyeden elle özgürce doldurabileceği bir kutu!
                p_fark_gun_elle = st.text_input("ÇIKIŞ GÜN SAYISI", value=varsayilan_fark, placeholder="Örn: 15 Gün veya 26")
                if p_fark_gun_elle.strip() == "": p_fark_gun_elle = "-"
                
                if st.form_submit_button("💾 VERİYİ OTOMATİK VERİTABANINA İŞLE", use_container_width=True):
                    if p_adi.strip() != "" and p_tc.strip() != "":
                        conn = sqlite3.connect(DB_YOLU)
                        cursor = conn.cursor()
                        
                        if islem_modu == "Var Olan Personeli Güncelle / Çıkış Yap" and varsayilan_sira is not None:
                            cursor.execute("DELETE FROM personel WHERE sira_no = ?", (varsayilan_sira,))
                            sira_no = varsayilan_sira
                        else:
                            cursor.execute("SELECT MAX(sira_no) FROM personel")
                            max_val = cursor.fetchone()[0]
                            sira_no = int(max_val + 1) if max_val is not None else 1
                        
                        cursor.execute("""
                            INSERT INTO personel VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (int(sira_no), p_adi.strip().upper(), str(p_tc.strip()), str(p_dogum), str(p_ise_giris), str(p_isten_cikis), str(p_birim), str(st.session_state["santiye"]), p_firma.strip().upper(), str(p_durum), str(p_calisma), str(p_fark_gun_elle).upper()))
                        conn.commit()
                        conn.close()
                        
                        st.success("✔️ SQL Veritabanına saniyesinde otomatik işlendi!")
                        time.sleep(0.5)
                        st.rerun()
                    else: st.error("❌ İsim ve TC boş geçilemez!")
            
            if not df_goster.empty:
                st.markdown("---")
                p_silme_listesi_sube = df_goster.apply(lambda r: f"Sıra No: {r['Sıra No']} | {r['Adı Soyadı']}", axis=1).tolist()
                secilen_sil_p_sube = st.selectbox("Silmek İstediğiniz Personeli Seçin", p_silme_listesi_sube, key="sube_p_sil")
                if st.button("❌ SEÇİLİ PERSONELİ LİSTEDEN KALDIR", use_container_width=True):
                    s_sira = int(str(secilen_sil_p_sube).split("Sıra No: ").split(" |").strip())
                    conn = sqlite3.connect(DB_YOLU)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM personel WHERE sira_no = ?", (s_sira,))
                    conn.commit()
                    conn.close()
                    st.success("Personel kartı silindi!")
                    st.rerun()
        
        with col_sag_tablo:
            st.markdown("##### 📋 ŞANTİYENİZDEKİ CANLI PERSONEL HAVUZU")
            if not df_goster.empty:
                st.dataframe(df_goster.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
            else: st.info("💡 Şu an şantiyenize ait kayıtlı personel kartı bulunmuyor.")
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.download_button(label="📥 BU LİSTEYİ EXCEL RAPORU YAP", data=kurumsal_rapor_uret(df_goster), file_name="santiye_personel_raporu.csv", mime="text/csv", use_container_width=True)
            with r_col2:
                if st.button("🖨️ BU LİSTEYİ RESMİ PDF YAP / YAZDIR", use_container_width=True):
                    st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
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
                        
                        conn = sqlite3.connect(DB_YOLU)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM puantaj WHERE tc_no = ? AND donem_ay = ? AND santiye = ?", (p_tc_parca, donem_ay, st.session_state["santiye"]))
                        cursor.execute("INSERT INTO puantaj (tarih_satir, santiye, personel_adi, tc_no, donem_ay, gun_sayisi, giren_sef) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                       (su_an_p, str(st.session_state["santiye"]), str(p_ad_parca), str(p_tc_parca), str(donem_ay), int(calisilan_gun), sefi_adi.upper()))
                        conn.commit()
                        conn.close()
                        st.success("✔️ Puantaj SQL veritabanına otomatik kilitlendi!")
                        time.sleep(0.5)
                        st.rerun()

        with col_p2:
            st.markdown("##### 📋 Şantiyenizin Gönderdiği Puantaj Kayıtları")
            st.dataframe(df_p_goster.iloc[::-1] if not df_p_goster.empty else df_p_goster, use_container_width=True, hide_index=True)

    elif st.session_state["rol"] == "merkez":
        st.markdown("### 🖥️ GENEL MERKEZ YÖNETİCİ KONTROL KONSOLU")
        tab1, tab2, tab3 = st.tabs(["👥 CANLI PERSONEL HAVUZU", "📅 TOPLU ŞANTİYE PUANTAJLARI", "📊 STRATEJİK GRAFİK ANALİTİĞİ"])
        
        with tab1:
            st.dataframe(df_canli.style.map(renk_ayarla, subset=["Giriş/Çıkış Durumu"]), use_container_width=True, hide_index=True)
            st.download_button(label="📥 MASTER EXCEL RAPORU İNDİR", data=kurumsal_rapor_uret(df_canli), file_name="master_personel.csv", mime="text/csv", use_container_width=True)
            
        with tab2:
            st.dataframe(df_puantaj_canli.iloc[::-1] if not df_puantaj_canli.empty else df_puantaj_canli, use_container_width=True, hide_index=True)
            st.download_button(label="📥 MASTER PUANTAJ RAPORU İNDİR", data=kurumsal_rapor_uret(df_puantaj_canli), file_name="master_puantaj.csv", mime="text/csv", use_container_width=True)
            
        with tab3:
            if not df_canli.empty: st.bar_chart(df_canli["Şantiye Bilgisi"].value_counts())














