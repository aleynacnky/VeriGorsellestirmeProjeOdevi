import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def kart_olustur(parent, baslik, deger, row, col):
    frame = tk.Frame(parent, bg="#2B2D42")
    frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    lbl_baslik = tk.Label(
        frame,
        text=baslik,
        font=("Segoe UI", 10, "bold"),
        bg="#2B2D42",
        fg="#EDF2F4"
    )
    lbl_baslik.pack(padx=16, pady=(12, 4))

    lbl_deger = tk.Label(
        frame,
        text=deger,
        font=("Segoe UI", 12),
        bg="#2B2D42",
        fg="#8D99AE"
    )
    lbl_deger.pack(padx=16, pady=(0, 12))


def cizgi_grafik_olustur(parent, title, x, y, xlabel="", ylabel=""):
    fig = Figure(figsize=(5.6, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(x, y, marker="o")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.5)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


def bar_grafik_olustur(parent, title, x, y, xlabel="", ylabel=""):
    fig = Figure(figsize=(5.6, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    ax.bar(x, y)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, axis="y", linestyle="--", alpha=0.5)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


def pasta_grafik_olustur(parent, title, labels, sizes):
    fig = Figure(figsize=(5.0, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title(title)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    return canvas.get_tk_widget()


def market_penceresi_olustur(veri, dosya_yolu):
    pencere = tk.Toplevel()
    pencere.title("Market Satis Analiz Sistemi")
    pencere.geometry("1280x820")
    pencere.configure(bg="#1F1F2E")

    ana_canvas = tk.Canvas(pencere, bg="#1F1F2E", highlightthickness=0)
    scrollbar = ttk.Scrollbar(pencere, orient="vertical", command=ana_canvas.yview)
    kaydirilabilir_frame = tk.Frame(ana_canvas, bg="#1F1F2E")

    kaydirilabilir_frame.bind(
        "<Configure>",
        lambda e: ana_canvas.configure(scrollregion=ana_canvas.bbox("all"))
    )

    ana_canvas.create_window((0, 0), window=kaydirilabilir_frame, anchor="nw")
    ana_canvas.configure(yscrollcommand=scrollbar.set)

    ana_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def mouse_wheel(event):
        ana_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def shift_mouse_wheel(event):
        ana_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    ana_canvas.bind_all("<MouseWheel>", mouse_wheel)
    ana_canvas.bind_all("<Shift-MouseWheel>", shift_mouse_wheel)

    baslik = tk.Label(
        kaydirilabilir_frame,
        text="Market Satis Analiz Dashboard",
        font=("Segoe UI", 18, "bold"),
        bg="#1F1F2E",
        fg="white"
    )
    baslik.pack(pady=(16, 4))

    alt_baslik = tk.Label(
        kaydirilabilir_frame,
        text=f"Secilen dosya: {dosya_yolu}",
        font=("Segoe UI", 9),
        bg="#1F1F2E",
        fg="#BFC0C0"
    )
    alt_baslik.pack(pady=(0, 14))

    kart_frame = tk.Frame(kaydirilabilir_frame, bg="#1F1F2E")
    kart_frame.pack(fill="x", padx=20)

    for i in range(4):
        kart_frame.grid_columnconfigure(i, weight=1)

    kart_olustur(kart_frame, "Toplam Ciro", f"{veri['toplam_ciro']:.2f} TL", 0, 0)
    kart_olustur(kart_frame, "Toplam Satis Adedi", str(veri["toplam_satis_adedi"]), 0, 1)
    kart_olustur(kart_frame, "En Cok Satan Urun", veri["en_cok_satan_urun"], 0, 2)
    kart_olustur(kart_frame, "En Yogun Saat", f"{veri['en_yogun_saat']}:00", 0, 3)

    grafikler_frame = tk.Frame(kaydirilabilir_frame, bg="#1F1F2E")
    grafikler_frame.pack(fill="both", expand=True, padx=20, pady=15)

    for i in range(2):
        grafikler_frame.grid_columnconfigure(i, weight=1)

    en_cok_satan = veri["en_cok_satan_urunler"]
    g1 = bar_grafik_olustur(
        grafikler_frame,
        "En Cok Satan Urunler",
        list(en_cok_satan.index),
        list(en_cok_satan.values),
        "Urun",
        "Adet"
    )
    g1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    kategori_ciro = veri["kategori_bazli_ciro"]
    g2 = bar_grafik_olustur(
        grafikler_frame,
        "Kategori Bazli Ciro",
        list(kategori_ciro.index),
        list(kategori_ciro.values),
        "Kategori",
        "Ciro (TL)"
    )
    g2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

    gunluk_ciro = veri["gunluk_ciro"]
    g3 = cizgi_grafik_olustur(
        grafikler_frame,
        "Gunluk Toplam Ciro",
        [str(x) for x in gunluk_ciro.index],
        list(gunluk_ciro.values),
        "Tarih",
        "Ciro (TL)"
    )
    g3.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

    saatlik_yogunluk = veri["saatlik_satis_yogunlugu"]
    g4 = bar_grafik_olustur(
        grafikler_frame,
        "Saatlik Satis Yogunlugu",
        list(saatlik_yogunluk.index),
        list(saatlik_yogunluk.values),
        "Saat",
        "Ciro (TL)"
    )
    g4.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

    odeme_dagilimi = veri["odeme_turu_dagilimi"]
    g5 = pasta_grafik_olustur(
        grafikler_frame,
        "Odeme Turu Dagilimi",
        list(odeme_dagilimi.index),
        list(odeme_dagilimi.values)
    )
    g5.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    sube_ciro = veri["sube_bazli_ciro"]
    g6 = bar_grafik_olustur(
        grafikler_frame,
        "Sube Bazli Ciro",
        list(sube_ciro.index),
        list(sube_ciro.values),
        "Sube",
        "Ciro (TL)"
    )
    g6.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")