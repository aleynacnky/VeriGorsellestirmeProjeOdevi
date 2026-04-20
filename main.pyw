import pyperclip
from pynput import keyboard
import pyautogui
import tkinter as tk
from tkinter import messagebox, filedialog
import time
import threading
import requests
import queue
import os
import tempfile
import atexit

from market_analiz import market_verisini_hazirla
from gorsellestirme import market_penceresi_olustur


# --- AYARLAR ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_ADI = "gemma3:1b"  # Ana model (F8)
TEXT_MODEL_CANDIDATES = [
    MODEL_ADI,
    "gemma3:1b",
]

KISAYOL_METIN = keyboard.Key.f8   # Metin secimi icin kisayol
kilit_dosyasi = os.path.join(tempfile.gettempdir(), "ai_asistan_f8.lock")

# Global degiskenler
root = None
gui_queue = queue.Queue()
kisayol_basildi = False
market_analiz_acik = False
aktif_menu = None
islem_devam_ediyor = False

# --- AKILLI KONU TANIMA ICIN SOZLUKLER ---
KATEGORI_SOZLUGU = {
    "sut urunleri": ["sut urunleri", "süt ürünleri", "sut ve sut urunleri", "süt ve süt ürünleri", "dairy"],
    "kahvaltilik": ["kahvaltilik", "kahvaltılık", "kahvaltilik urunleri", "kahvalti urunleri"],
    "icecek": ["icecek", "içecek", "içecekler", "mesrubat", "meşrubat"],
    "atistirmalik": ["atistirmalik", "atıştırmalık", "atistirmaliklar", "cips", "biskuvi", "bisküvi", "cikolata", "çikolata"],
    "temizlik": ["temizlik", "temizlik urunleri", "deterjan", "hijyen"],
    "meyve sebze": ["meyve sebze", "meyve", "sebze", "manav"],
    "temel gida": ["temel gida", "bakliyat", "makarna", "pirinc", "pirinç", "un", "yag", "yağ", "seker", "şeker"],
}

URUN_SOZLUGU = {
    "yumurta": {"kategori": "kahvaltilik", "es_anlamlilar": ["yumurta", "yumurtalar", "organik yumurta"]},
    "sut": {"kategori": "sut urunleri", "es_anlamlilar": ["sut", "süt", "gunluk sut", "günlük süt"]},
    "peynir": {"kategori": "sut urunleri", "es_anlamlilar": ["peynir", "kasar", "kaşar", "beyaz peynir", "labne"]},
    "yogurt": {"kategori": "sut urunleri", "es_anlamlilar": ["yogurt", "yoğurt", "suzme yogurt", "süzme yoğurt"]},
    "tereyagi": {"kategori": "sut urunleri", "es_anlamlilar": ["tereyagi", "tereyağı"]},
    "ekmek": {"kategori": "kahvaltilik", "es_anlamlilar": ["ekmek", "tam bugday ekmegi", "tam buğday ekmeği"]},
    "zeytin": {"kategori": "kahvaltilik", "es_anlamlilar": ["zeytin", "siyah zeytin", "yesil zeytin", "yeşil zeytin"]},
    "cay": {"kategori": "icecek", "es_anlamlilar": ["cay", "çay"]},
    "kahve": {"kategori": "icecek", "es_anlamlilar": ["kahve", "filtre kahve", "turk kahvesi", "türk kahvesi"]},
    "cola": {"kategori": "icecek", "es_anlamlilar": ["kola", "cola", "coca cola"]},
    "ayran": {"kategori": "sut urunleri", "es_anlamlilar": ["ayran"]},
    "su": {"kategori": "icecek", "es_anlamlilar": ["su", "icme suyu", "içme suyu"]},
}


# --- MEVCUT MENU ISLEMLERI ---
ISLEMLER = {
    "📝 Gramer Düzelt": "Bu metni Türkçe yazım ve dil bilgisi kurallarına göre düzelt, resmi ve akıcı olsun. Sadece sonucu ver.",
    "🇬🇧 İngilizceye Çevir": "Bu metni İngilizceye çevir. Sadece çeviriyi ver.",
    "🇹🇷 Türkçeye Çevir": "Bu metni Türkçeye çevir. Sadece çeviriyi ver.",
    "📑 Özetle (Madde Madde)": "Bu metni analiz et ve en önemli noktaları madde madde özetle.",
    "💼 Daha Resmi Yap": "Bu metni kurumsal bir e-posta diline çevir, çok resmi olsun.",
    "🐍 Python Koduna Çevir": "Bu metindeki isteği yerine getiren bir Python kodu yaz. Sadece kodu ver.",
    "📧 Cevap Yaz (Mail)": "Bu gelen bir e-posta, buna kibar ve profesyonel bir cevap metni taslağı yaz.",
    "🎮 PS5 Oyun Skor + Acımasız Yorum": (
        "Secili metni bir PS5 oyunu adi olarak ele al. Asagidaki formatta Turkce cevap ver:\n"
        "1) Oyun: <ad>\n"
        "2) Topluluk Begeni Skorlari:\n"
        "- Metacritic User Score: <deger veya 'bilgi yok'>\n"
        "- OpenCritic / benzer elestirmen ortalamasi: <deger veya 'bilgi yok'>\n"
        "- Oyuncu yorumu ortalamasi (PS Store vb.): <deger veya 'bilgi yok'>\n"
        "3) Hukum: sadece 'IYI' veya 'KOTU'\n"
        "4) Acimasiz Yorum: 2-4 cumle, net ve sert.\n"
        "Kurallar: Kesin bilmedigin puani uydurma, onun yerine 'bilgi yok' yaz. "
        "Yorumu skorlarla tutarli kur."
    ),
}

EK_ISLEMLER = {
    "Urun/Kategori Ozeti": "urun_kategori_ozeti",
    "Satis Icgorusu Yaz": "satis_icgorusu",
    "Grafik Onerisi Ver": "grafik_onerisi",
    "Karsilastirma Sorulari Uret": "karsilastirma_sorulari",
    "Dashboard Fikri Ver": "dashboard_fikri",
    "Kampanya Fikri Ver": "kampanya_fikri",
    "Musteri Profili Yorumla": "musteri_profili",
}


def normalize_metin(metin):
    if not metin:
        return ""

    metin = metin.strip().lower()

    karakter_map = str.maketrans({
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    })
    metin = metin.translate(karakter_map)

    metin = " ".join(metin.split())
    return metin


def kuralli_konu_bul(metin):
    temiz_metin = normalize_metin(metin)

    if not temiz_metin:
        return {
            "uygun_mu": False,
            "tip": "alakasiz",
            "ana_konu": "",
            "kategori": "",
            "guven": 0.0,
        }

    # Once kategori kontrolu
    for kategori_adi, varyasyonlar in KATEGORI_SOZLUGU.items():
        norm_varyasyonlar = [normalize_metin(v) for v in varyasyonlar]
        if temiz_metin in norm_varyasyonlar:
            return {
                "uygun_mu": True,
                "tip": "kategori",
                "ana_konu": temiz_metin,
                "kategori": kategori_adi,
                "guven": 0.95,
            }

    # Sonra urun kontrolu
    for urun_adi, bilgi in URUN_SOZLUGU.items():
        varyasyonlar = [normalize_metin(v) for v in bilgi.get("es_anlamlilar", [])]
        if temiz_metin in varyasyonlar:
            return {
                "uygun_mu": True,
                "tip": "urun",
                "ana_konu": urun_adi,
                "kategori": bilgi.get("kategori", ""),
                "guven": 0.95,
            }

    # Parcali eslesme: ornegin "organik yumurta", "sade yogurt", "sut urunleri reyonu"
    for urun_adi, bilgi in URUN_SOZLUGU.items():
        varyasyonlar = [normalize_metin(v) for v in bilgi.get("es_anlamlilar", [])]
        if any(v in temiz_metin for v in varyasyonlar):
            return {
                "uygun_mu": True,
                "tip": "urun",
                "ana_konu": urun_adi,
                "kategori": bilgi.get("kategori", ""),
                "guven": 0.75,
            }

    for kategori_adi, varyasyonlar in KATEGORI_SOZLUGU.items():
        norm_varyasyonlar = [normalize_metin(v) for v in varyasyonlar]
        if any(v in temiz_metin for v in norm_varyasyonlar):
            return {
                "uygun_mu": True,
                "tip": "kategori",
                "ana_konu": temiz_metin,
                "kategori": kategori_adi,
                "guven": 0.75,
            }

    return {
        "uygun_mu": False,
        "tip": "alakasiz",
        "ana_konu": temiz_metin,
        "kategori": "",
        "guven": 0.10,
    }


def konu_analizi_yap(metin):
    """
    Ilk asamada kuralli sistem kullaniliyor.
    Ileride istenirse buraya LLM fallback eklenebilir.
    """
    return kuralli_konu_bul(metin)


def akilli_prompt_olustur(islem_tipi, secili_metin, analiz):
    tip = analiz.get("tip", "")
    ana_konu = analiz.get("ana_konu", secili_metin)
    kategori = analiz.get("kategori", "")

    baglam = (
        "Asagidaki ifade market / satis / urun-kategori analizi baglaminda degerlendirilecektir.\n"
        f"Secilen ifade: {secili_metin}\n"
        f"Tespit edilen tip: {tip}\n"
        f"Ana konu: {ana_konu}\n"
        f"Ilgili kategori: {kategori}\n\n"
    )

    if islem_tipi == "ozet":
        if tip == "urun":
            return (
                baglam +
                "Bu secili ifade bir urundur. "
                "Urunu kisa ve anlasilir sekilde tanit. "
                "Market satis analizi baglaminda neden onemli olabilecegini 4-6 cumleyle acikla. "
                "Sadece Turkce cevap ver."
            )
        else:
            return (
                baglam +
                "Bu secili ifade bir urun kategorisidir. "
                "Kategoriyi kisa ve anlasilir sekilde tanit. "
                "Bu kategoride hangi urun tiplerinin yer alabilecegini ve market analizi acisindan neden onemli oldugunu 4-6 cumleyle acikla. "
                "Sadece Turkce cevap ver."
            )

    if islem_tipi == "satis_icgorusu":
        if tip == "urun":
            return (
                baglam +
                "Bu secili ifade bir market urunudur. "
                "Bu urun icin muhtemel satis davranislarini, musteri ilgisini, fiyat hassasiyetini ve kampanya etkisini yorumla. "
                "3-5 maddelik icgoru uret. Uydurma sayisal veri verme."
            )
        else:
            return (
                baglam +
                "Bu secili ifade bir market urun kategorisidir. "
                "Bu kategori icin muhtemel satis davranislarini, musteri talebini, alt urun cesitliligini ve kampanya etkisini yorumla. "
                "3-5 maddelik icgoru uret. Uydurma sayisal veri verme."
            )

    if islem_tipi == "grafik_oneri":
        if tip == "urun":
            return (
                baglam +
                "Bu urun icin veri gorsellestirme odevi kapsaminda hangi grafiklerin uygun olacagini oner. "
                "Her oneride grafik turu, neyi gosterecegi ve neden uygun oldugu yazsin. "
                "En az 4 oneriyi madde madde ver."
            )
        else:
            return (
                baglam +
                "Bu kategori icin veri gorsellestirme odevi kapsaminda hangi grafiklerin uygun olacagini oner. "
                "Her oneride grafik turu, neyi gosterecegi ve neden uygun oldugu yazsin. "
                "En az 4 oneriyi madde madde ver."
            )

    if islem_tipi == "karsilastirma":
        if tip == "urun":
            return (
                baglam +
                "Bu urun icin veri analizi yaparken sorulabilecek karsilastirma sorulari uret. "
                "Ornegin fiyat, satis miktari, donemsellik, kampanya etkisi gibi boyutlari kullan. "
                "En az 6 soru uret."
            )
        else:
            return (
                baglam +
                "Bu kategori icin veri analizi yaparken sorulabilecek karsilastirma sorulari uret. "
                "Alt kategori, toplam satis, urun cesitliligi, donemsellik ve kampanya etkisi gibi boyutlari kullan. "
                "En az 6 soru uret."
            )

    if islem_tipi == "dashboard":
        if tip == "urun":
            return (
                baglam +
                "Bu urun icin dashboard tasarlaniyormus gibi dusun. "
                "Dashboard'da hangi KPI'lar, hangi kartlar ve hangi grafikler olmali, madde madde yaz. "
                "Veri gorsellestirme ogrencisi icin uygulanabilir olsun."
            )
        else:
            return (
                baglam +
                "Bu kategori icin dashboard tasarlaniyormus gibi dusun. "
                "Dashboard'da hangi KPI'lar, hangi kartlar ve hangi grafikler olmali, madde madde yaz. "
                "Veri gorsellestirme ogrencisi icin uygulanabilir olsun."
            )

    return baglam + "Secili metni market analizi baglaminda acikla."


def get_available_text_model():
    """Metin islemede kullanilabilir modeli secer."""
    preferred_models = []
    for model in TEXT_MODEL_CANDIDATES:
        if model and model not in preferred_models:
            preferred_models.append(model)

    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            return MODEL_ADI

        models = response.json().get("models", [])
        installed_lower = {m.get("name", "").lower(): m.get("name", "") for m in models}

        for candidate in preferred_models:
            candidate_lower = candidate.lower()
            if candidate_lower in installed_lower:
                return installed_lower[candidate_lower]

            candidate_base = candidate_lower.split(":")[0]
            for installed_name_lower, installed_name in installed_lower.items():
                if installed_name_lower.startswith(candidate_base + ":"):
                    return installed_name
    except Exception:
        pass

    return MODEL_ADI


def ollama_cevap_al(prompt):
    """Ollama API'den cevap al."""
    try:
        aktif_model = get_available_text_model()
        payload = {
            "model": aktif_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            },
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "").strip()

        err_msg = (
            f"Ollama API Hatasi: {response.status_code}\n"
            f"Model: {aktif_model}\n"
            f"Cevap: {response.text}"
        )
        print(f"HATA: {err_msg}")
        gui_queue.put((messagebox.showerror, ("API Hatasi", err_msg)))
        return None

    except requests.exceptions.ConnectionError:
        err_msg = (
            "Ollama'ya baglanilamadi.\n"
            "Programin calistigindan emin olun!\n"
            "(http://localhost:11434)"
        )
        print(f"HATA: {err_msg}")
        gui_queue.put((messagebox.showerror, ("Baglanti Hatasi", err_msg)))
        return None

    except Exception as e:
        err_msg = f"Beklenmeyen Hata: {e}"
        print(f"HATA: {err_msg}")
        gui_queue.put((messagebox.showerror, ("Hata", err_msg)))
        return None


def strip_code_fence(text):
    if not text:
        return text

    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = lines[1:] if lines else []
        while lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    return cleaned


def secili_metni_kopyala(max_deneme=4):
    sentinel = f"__AI_ASISTAN__{time.time_ns()}__"
    try:
        pyperclip.copy(sentinel)
    except Exception:
        pass

    for _ in range(max_deneme):
        pyautogui.hotkey("ctrl", "c")
        time.sleep(0.2)
        metin = pyperclip.paste()
        if metin and metin.strip() and metin != sentinel:
            return metin

    return ""


def pencere_modunda_gosterilsin_mi(komut_adi):
    return "PS5 Oyun Skor" in komut_adi


def sonuc_penceresi_goster(baslik, icerik):
    pencere = tk.Toplevel(root)
    pencere.title(baslik)
    pencere.geometry("780x520")
    pencere.minsize(520, 320)
    pencere.attributes("-topmost", True)

    frame = tk.Frame(pencere, bg="#1f1f1f")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    text_alani = tk.Text(
        frame,
        wrap="word",
        bg="#2b2b2b",
        fg="white",
        insertbackground="white",
        font=("Segoe UI", 10),
        padx=10,
        pady=10,
    )
    kaydirma = tk.Scrollbar(frame, command=text_alani.yview)
    text_alani.configure(yscrollcommand=kaydirma.set)

    text_alani.pack(side="left", fill="both", expand=True)
    kaydirma.pack(side="right", fill="y")

    text_alani.insert("1.0", icerik)
    text_alani.config(state="disabled")

    alt_frame = tk.Frame(pencere, bg="#1f1f1f")
    alt_frame.pack(fill="x", padx=10, pady=(0, 10))

    def panoya_kopyala():
        pyperclip.copy(icerik)

    tk.Button(
        alt_frame,
        text="Panoya Kopyala",
        command=panoya_kopyala,
        bg="#3d3d3d",
        fg="white",
        activebackground="#4d4d4d",
        activeforeground="white",
        relief="flat",
        padx=12,
        pady=6,
    ).pack(side="left")

    tk.Button(
        alt_frame,
        text="Kapat",
        command=pencere.destroy,
        bg="#3d3d3d",
        fg="white",
        activebackground="#4d4d4d",
        activeforeground="white",
        relief="flat",
        padx=12,
        pady=6,
    ).pack(side="right")

    pencere.focus_force()
    pencere.lift()

def genel_islem_yap(komut_adi, secili_metin):
    prompt_emri = ISLEMLER[komut_adi]
    full_prompt = f"{prompt_emri}\n\nMetin:\n{secili_metin}"

    print(f"Islem: {komut_adi}")
    print("Ollama ile isleniyor...")

    sonuc = ollama_cevap_al(full_prompt)
    if not sonuc:
        print("Sonuc alinamadi.")
        return

    sonuc = strip_code_fence(sonuc)

    if pencere_modunda_gosterilsin_mi(komut_adi):
        gui_queue.put((sonuc_penceresi_goster, (komut_adi, sonuc)))
        print("Sonuc ayri pencerede gosterildi.")
        return

    pyperclip.copy(sonuc)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    print("Islem tamamlandi.")


def ek_islem_yap(komut_adi, secili_metin):
    analiz = kuralli_konu_bul(secili_metin)

    if not analiz.get("uygun_mu", False):
        gui_queue.put((
            messagebox.showwarning,
            (
                "Gecersiz Konu",
                "Secilen metin urun veya kategori olarak taninamadi.\n\n"
                "Ornek:\n"
                "- yumurta\n"
                "- sut\n"
                "- yogurt\n"
                "- sut urunleri\n"
                "- icecek"
            )
        ))
        return

    islem_tipi = EK_ISLEMLER[komut_adi]

    if islem_tipi == "urun_kategori_ozeti":
        prompt = f"""
Secilen ifade market urunu veya kategorisidir: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bunu veri gorsellestirme odevi baglaminda acikla.
Kisa, net ve Turkce yaz.
"""
    elif islem_tipi == "satis_icgorusu":
        prompt = f"""
Secilen ifade: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bu konu icin satis icgoruleri yaz.
3-5 madde olsun.
Uydurma sayisal veri verme.
"""
    elif islem_tipi == "grafik_onerisi":
        prompt = f"""
Secilen ifade: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bu konu icin veri gorsellestirme odevi kapsaminda uygun grafik onerileri ver.
En az 4 madde yaz.
Her maddede grafik tipi ve neden uygun oldugu olsun.
"""
    elif islem_tipi == "karsilastirma_sorulari":
        prompt = f"""
Secilen ifade: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bu konu icin analizde sorulabilecek karsilastirma sorulari uret.
En az 6 soru ver.
"""
    elif islem_tipi == "dashboard_fikri":
        prompt = f"""
Secilen ifade: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bu konu icin bir dashboard tasarlaniyormus gibi dusun.
Hangi kartlar, KPI'lar ve grafikler olmali, madde madde yaz.
"""
    elif islem_tipi == "kampanya_fikri":
        prompt = f"""
Secilen ifade: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bu urun veya kategori icin kampanya fikirleri ver.
Musteri ilgisi ve satis artisi acisindan yorumla.
"""
    elif islem_tipi == "musteri_profili":
        prompt = f"""
Secilen ifade: {secili_metin}
Tip: {analiz['tip']}
Kategori: {analiz['kategori']}

Bu urun veya kategoriye ilgi gosteren muhtemel musteri profilini yorumla.
Kisa ve analitik yaz.
"""
    else:
        return

    sonuc = ollama_cevap_al(prompt)
    if not sonuc:
        return

    sonuc = strip_code_fence(sonuc)
    gui_queue.put((sonuc_penceresi_goster, (komut_adi, sonuc)))


def islemi_yap(komut_adi, secili_metin):
    global islem_devam_ediyor

    if islem_devam_ediyor:
        print("Zaten bir islem calisiyor, yeni istek yok sayildi.")
        return

    islem_devam_ediyor = True

    try:
        if komut_adi in EK_ISLEMLER:
            ek_islem_yap(komut_adi, secili_metin)
        else:
            genel_islem_yap(komut_adi, secili_metin)
    finally:
        islem_devam_ediyor = False

def yukleniyor_penceresi_goster():
    pencere = tk.Toplevel(root)
    pencere.title("Market Analizi")
    pencere.geometry("360x130")
    pencere.resizable(False, False)
    pencere.attributes("-topmost", True)
    pencere.configure(bg="#1A1A2E")
    pencere.update_idletasks()

    x = (pencere.winfo_screenwidth() // 2) - 180
    y = (pencere.winfo_screenheight() // 2) - 65
    pencere.geometry(f"360x130+{x}+{y}")

    tk.Label(
        pencere,
        text="Market satis verileri analiz ediliyor...",
        font=("Segoe UI", 10, "bold"),
        bg="#1A1A2E",
        fg="#EAEAEA",
    ).pack(pady=(22, 8))

    tk.Label(
        pencere,
        text="Grafikler hazirlaniyor, lutfen bekleyin.",
        font=("Segoe UI", 9),
        bg="#1A1A2E",
        fg="#9E9E9E",
    ).pack()

    pencere.update()
    return pencere


def market_analizi_baslat():
    global market_analiz_acik

    if market_analiz_acik:
        return

    market_analiz_acik = True

    dosya_yolu = filedialog.askopenfilename(
        title="Market satis CSV dosyasini secin",
        filetypes=[("CSV Dosyalari", "*.csv")]
    )

    if not dosya_yolu:
        market_analiz_acik = False
        return

    yukleniyor_ref = [None]

    def yukleniyor_ac():
        yukleniyor_ref[0] = yukleniyor_penceresi_goster()

    gui_queue.put((yukleniyor_ac, ()))

    def arka_plan():
        global market_analiz_acik
        time.sleep(0.2)
        print(f"Secilen dosya: {dosya_yolu}")

        try:
            veri = market_verisini_hazirla(dosya_yolu)

            def kapat_ve_goster():
                global market_analiz_acik

                if yukleniyor_ref[0]:
                    try:
                        yukleniyor_ref[0].destroy()
                    except Exception:
                        pass

                market_penceresi_olustur(veri, dosya_yolu)
                market_analiz_acik = False

            gui_queue.put((kapat_ve_goster, ()))

        except Exception as e:
            hata_mesaji = str(e)

            def hata_goster():
                global market_analiz_acik

                if yukleniyor_ref[0]:
                    try:
                        yukleniyor_ref[0].destroy()
                    except Exception:
                        pass

                messagebox.showerror(
                    "Hata",
                    f"Market verisi analiz edilirken hata olustu:\n\n{hata_mesaji}"
                )
                market_analiz_acik = False

            gui_queue.put((hata_goster, ()))

    threading.Thread(target=arka_plan, daemon=True).start()

def menu_goster():
    """Metni kopyalar ve tek bir popup menu gosterir."""
    global aktif_menu

    secili_metin = secili_metni_kopyala()

    if not secili_metin or not secili_metin.strip():
        gui_queue.put(
            (
                messagebox.showwarning,
                (
                    "Secim Bulunamadi",
                    "Lutfen once metin secin, sonra F8 ile menuyu acin.",
                ),
            )
        )
        return

    if aktif_menu is not None:
        try:
            aktif_menu.unpost()
            aktif_menu.destroy()
        except Exception:
            pass
        aktif_menu = None

    menu = tk.Menu(
        root,
        tearoff=0,
        bg="#2b2b2b",
        fg="white",
        activebackground="#4a4a4a",
        activeforeground="white",
        font=("Segoe UI", 10),
        relief="flat",
        borderwidth=1,
    )

    aktif_menu = menu

    def komut_olustur(komut_adi, secilen_metin):
        def komut_calistir():
            global aktif_menu

            try:
                if aktif_menu is not None:
                    aktif_menu.unpost()
                    aktif_menu.destroy()
            except Exception:
                pass
            aktif_menu = None

            islemi_yap(komut_adi, secilen_metin)

        return komut_calistir

    for baslik in ISLEMLER.keys():
        menu.add_command(
            label=baslik,
            command=komut_olustur(baslik, secili_metin)
        )

    menu.add_separator()

    for baslik in EK_ISLEMLER.keys():
        menu.add_command(
            label=baslik,
            command=komut_olustur(baslik, secili_metin)
        )

    menu.add_separator()
    menu.add_command(
        label="Market Satis Analizi Ac",
        command=market_analizi_baslat
    )

    menu.add_separator()
    menu.add_command(
        label="Iptal",
        command=lambda: None
    )

    try:
        x, y = pyautogui.position()
        menu.tk_popup(x, y)
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass

def process_queue():
    """Kuyruktaki GUI islemlerini ana thread'de calistirir."""
    try:
        while True:
            try:
                task = gui_queue.get_nowait()
            except queue.Empty:
                break

            func, args = task
            func(*args)
    finally:
        if root:
            root.after(100, process_queue)

def on_release(key):
    global kisayol_basildi
    try:
        if key == KISAYOL_METIN:
            kisayol_basildi = False
    except AttributeError:
        pass

def on_press(key):
    global kisayol_basildi

    try:
        if key == KISAYOL_METIN and not kisayol_basildi:
            kisayol_basildi = True
            print("F8 algilandi")
            gui_queue.put((menu_goster, ()))
    except AttributeError:
        pass

def kilidi_sil():
    try:
        if os.path.exists(kilit_dosyasi):
            os.remove(kilit_dosyasi)
    except Exception:
        pass


if __name__ == "__main__":
    if os.path.exists(kilit_dosyasi):
        print("Program zaten calisiyor. Once eski pencereyi kapatin.")
        raise SystemExit

    with open(kilit_dosyasi, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    atexit.register(kilidi_sil)

    print("=" * 60)
    print("AI Asistan - Metin Isleme + Market Satis Analizi")
    print("=" * 60)

    aktif_text_model = get_available_text_model()
    print(f"Metin Isleme (F8): {aktif_text_model}")
    print("Kullanim:")
    print("   F8 - Metin sec ve AI islemleri yap")
    print("   Yeni market odakli secenekler de menude yer alir")
    print("Programi kapatmak icin bu pencereyi kapatin veya Ctrl+C yapin.")
    print("=" * 60)

    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if test_response.status_code == 200:
            print("Ollama baglantisi basarili.")
        else:
            print("Ollama'ya baglanilamadi, servisi kontrol edin.")
    except Exception:
        print("Ollama calismiyor olabilir. 'ollama serve' ile baslatin.")

    print()

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    root = tk.Tk()
    root.withdraw()
    root.after(100, process_queue)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Kapatiliyor...")