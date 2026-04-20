import pyperclip
from pynput import keyboard
import pyautogui
import tkinter as tk
from tkinter import messagebox, filedialog
import time
import threading
import requests
import queue

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


# Global değişkenler
root = None
gui_queue = queue.Queue()
kisayol_basildi = False
market_analiz_acik = False


# --- MENÜ SEÇENEKLERİ VE PROMPT'LAR ---
ISLEMLER = {
    "📝 Gramer Düzelt": "Bu metni Türkçe yazım ve dil bilgisi kurallarına göre düzelt, resmi ve akıcı olsun. Sadece sonucu ver.",
    "🇬🇧 İngilizceye Çevir": "Bu metni İngilizceye çevir. Sadece çeviriyi ver.",
    "🇹🇷 Türkçeye Çevir": "Bu metni Türkçeye çevir. Sadece çeviriyi ver.",
    "📑 Özetle (Madde Madde)": "Bu metni analiz et ve en önemli noktaları madde madde özetle.",
    "💼 Daha Resmi Yap": "Bu metni kurumsal bir e-posta diline çevir, çok resmi olsun.",
    "🐍 Python Koduna Çevir": "Bu metindeki isteği yerine getiren bir Python kodu yaz. Sadece kodu ver.",
    "📧 Cevap Yaz (Mail)": "Bu gelen bir e-posta, buna kibar ve profesyonel bir cevap metni taslağı yaz.",
    "🎮 PS5 Oyun Skor + Acımasız Yorum": (
        "Seçili metni bir PS5 oyunu adı olarak ele al. Aşağıdaki formatta Türkçe cevap ver:\n"
        "1) Oyun: <ad>\n"
        "2) Topluluk Beğeni Skorları:\n"
        "- Metacritic User Score: <değer veya 'bilgi yok'>\n"
        "- OpenCritic / benzer eleştirmen ortalaması: <değer veya 'bilgi yok'>\n"
        "- Oyuncu yorumu ortalaması (PS Store vb.): <değer veya 'bilgi yok'>\n"
        "3) Hüküm: sadece 'IYI' veya 'KOTU'\n"
        "4) Acımasız Yorum: 2-4 cümle, net ve sert.\n"
        "Kurallar: Kesin bilmediğin puanı uydurma, onun yerine 'bilgi yok' yaz. "
        "Yorumu skorlarla tutarlı kur."
    ),
}


def get_available_text_model():
    """Metin işlemede kullanılabilir modeli seçer."""
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
        print(f"❌ {err_msg}")
        gui_queue.put((messagebox.showerror, ("API Hatasi", err_msg)))
        return None

    except requests.exceptions.ConnectionError:
        err_msg = (
            "Ollama'ya baglanilamadi.\n"
            "Programin calistigindan emin olun!\n"
            "(http://localhost:11434)"
        )
        print(f"❌ {err_msg}")
        gui_queue.put((messagebox.showerror, ("Baglanti Hatasi", err_msg)))
        return None

    except Exception as e:
        err_msg = f"Beklenmeyen Hata: {e}"
        print(f"❌ {err_msg}")
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


def islemi_yap(komut_adi, secili_metin):
    prompt_emri = ISLEMLER[komut_adi]
    full_prompt = f"{prompt_emri}:\n\n'{secili_metin}'"

    print(f"🤖 Islem: {komut_adi}")
    print("⏳ Ollama ile isleniyor...")

    sonuc = ollama_cevap_al(full_prompt)
    if not sonuc:
        print("❌ Sonuc alinamadi.")
        return

    sonuc = strip_code_fence(sonuc)
    if sonuc.startswith("'") and sonuc.endswith("'"):
        sonuc = sonuc[1:-1]

    if pencere_modunda_gosterilsin_mi(komut_adi):
        gui_queue.put((sonuc_penceresi_goster, (komut_adi, sonuc)))
        print("✅ Sonuc ayri pencerede gosterildi.")
        return

    time.sleep(0.2)
    pyperclip.copy(sonuc)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    print("✅ Islem tamamlandi!")


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
        print(f"📁 Secilen dosya: {dosya_yolu}")

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


def process_queue():
    """Kuyruktaki GUI işlemlerini ana thread'de çalıştırır."""
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


def menu_goster():
    """Metni kopyalar ve menüyü gösterir (ana thread)."""
    secili_metin = secili_metni_kopyala()
    if not secili_metin.strip():
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

    menu = tk.Menu(
        root,
        tearoff=0,
        bg="#2b2b2b",
        fg="white",
        activebackground="#4a4a4a",
        activeforeground="white",
        font=("Segoe UI", 10),
    )

    def komut_olustur(k_adi, s_metin):
        def komut_calistir():
            threading.Thread(
                target=islemi_yap,
                args=(k_adi, s_metin),
                daemon=True
            ).start()
        return komut_calistir

    for baslik in ISLEMLER.keys():
        menu.add_command(label=baslik, command=komut_olustur(baslik, secili_metin))

    menu.add_separator()
    menu.add_command(label="📊 Market Satis Analizi Ac", command=market_analizi_baslat)
    menu.add_separator()
    menu.add_command(label="❌ Iptal", command=lambda: None)

    try:
        x, y = pyautogui.position()
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


def on_press(key):
    global kisayol_basildi
    try:
        print(f"Basilan tus: {key}")

        if key == KISAYOL_METIN and not kisayol_basildi:
            print("F8 algilandi")
            kisayol_basildi = True
            gui_queue.put((menu_goster, ()))

    except AttributeError:
        pass


def on_release(key):
    global kisayol_basildi
    try:
        if key == KISAYOL_METIN:
            kisayol_basildi = False
    except AttributeError:
        pass

if __name__ == "__main__":
    print("=" * 60)
    print("🤖 AI Asistan - Metin Isleme + Market Satis Analizi")
    print("=" * 60)

    aktif_text_model = get_available_text_model()
    print(f"📦 Metin Isleme (F8): {aktif_text_model}")
    print()
    print("🔧 Kullanim:")
    print("   F8 - Metin sec ve AI islemleri yap")
    print()
    print("⚠️ Programi kapatmak icin bu pencereyi kapatin veya Ctrl+C yapin.")
    print("=" * 60)

    try:
        test_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if test_response.status_code == 200:
            print("✅ Ollama baglantisi basarili!")
        else:
            print("⚠️ Ollama'ya baglanilamadi, servisi kontrol edin!")
    except Exception:
        print("⚠️ Ollama calismiyor olabilir! 'ollama serve' ile baslatin.")

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