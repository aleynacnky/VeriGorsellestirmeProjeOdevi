import pandas as pd


def market_verisini_hazirla(dosya_yolu):
    df = pd.read_csv(dosya_yolu)

    gerekli = [
        "Tarih",
        "Saat",
        "Urun",
        "Kategori",
        "Adet",
        "Fiyat",
        "OdemeTuru",
        "Sube"
    ]

    eksik = [x for x in gerekli if x not in df.columns]

    if eksik:
        raise ValueError("Eksik sutunlar: " + ", ".join(eksik))

    df["Adet"] = pd.to_numeric(df["Adet"], errors="coerce")
    df["Fiyat"] = pd.to_numeric(df["Fiyat"], errors="coerce")

    df["ToplamTutar"] = df["Adet"] * df["Fiyat"]

    df["Tarih"] = pd.to_datetime(df["Tarih"])

    df["SaatNum"] = df["Saat"].astype(str).str[:2].astype(int)

    return {
        "toplam_ciro": df["ToplamTutar"].sum(),
        "toplam_satis_adedi": int(df["Adet"].sum()),
        "en_cok_satan_urun":
            df.groupby("Urun")["Adet"].sum().idxmax(),

        "en_yogun_saat":
            int(df.groupby("SaatNum")["ToplamTutar"].sum().idxmax()),

        "en_cok_satan_urunler":
            df.groupby("Urun")["Adet"].sum().sort_values(ascending=False).head(10),

        "kategori_bazli_ciro":
            df.groupby("Kategori")["ToplamTutar"].sum(),

        "gunluk_ciro":
            df.groupby(df["Tarih"].dt.date)["ToplamTutar"].sum(),

        "saatlik_satis_yogunlugu":
            df.groupby("SaatNum")["ToplamTutar"].sum(),

        "odeme_turu_dagilimi":
            df.groupby("OdemeTuru")["ToplamTutar"].sum(),

        "sube_bazli_ciro":
            df.groupby("Sube")["ToplamTutar"].sum(),
    }