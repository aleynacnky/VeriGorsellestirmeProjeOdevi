# 📊 AI Destekli Veri Görselleştirme ve Market Analiz Sistemi

## 📌 Genel Bakış

Bu proje, veri görselleştirme dersine ait temel bir uygulamanın geliştirilmiş ve genişletilmiş bir versiyonudur. Amaç, klasik veri görselleştirme yaklaşımını daha akıllı, etkileşimli ve bağlama duyarlı hale getirmektir.

Proje kapsamında kullanıcı, herhangi bir metni seçerek F8 tuşu aracılığıyla sistemle etkileşime geçebilir. Sistem bu metni analiz eder, bağlamını belirler ve buna uygun analiz, yorum ve görselleştirme önerileri üretir.

Bu proje geliştirilirken özellikle **kurulabilirlik, taşınabilirlik ve tekrar üretilebilirlik (reproducibility)** dikkate alınmıştır. Bu nedenle sistemin çalışabilmesi için gerekli olan tüm bağımlılıklar ve kurulum adımları README içerisinde **"Gereksinimler & Kurulum" başlığı altında açık ve detaylı şekilde sunulmuştur**.

Bu yönüyle proje yalnızca bir uygulama değil, aynı zamanda **kolay kurulabilir ve yeniden üretilebilir bir yazılım çözümü** olarak tasarlanmıştır.

---

## 🎯 Projenin Amacı

Bu projenin temel amacı, veri görselleştirme sürecini daha verimli, yönlendirici ve akıllı hale getirmektir.

Klasik veri görselleştirme sürecinde kullanıcı:
- veriyi analiz eder
- uygun grafik tipini seçer
- yorum üretir

Bu projede ise sistem:

- Kullanıcıdan gelen girdiyi analiz eder  
- Girdinin bağlamını belirler (ürün / kategori / alakasız)  
- Bu bağlama göre analiz ve öneri üretir  
- Kullanıcıya doğrudan uygulanabilir çıktılar sunar  

Bu yaklaşım sayesinde proje, yalnızca veri sunan bir yapıdan çıkarak **karar destek sistemi** haline getirilmiştir.

---

## 🧠 Sistem Özellikleri

### 🔹 Metin Tabanlı Etkileşim (F8 Menü Sistemi)

Kullanıcı herhangi bir uygulamada metin seçer ve `F8` tuşuna basarak sistemle etkileşime geçebilir.

Sunulan işlemler:

- Gramer düzeltme  
- Çeviri (TR / EN)  
- Özetleme  
- Resmileştirme  
- Python kodu üretimi  
- Mail cevabı yazma  

---

### 🔹 Bağlam Analizi (Ürün / Kategori Tespiti)

Sistem, seçilen metni analiz ederek aşağıdaki sınıflardan birine yerleştirir:

- Ürün (örneğin: "yumurta")  
- Kategori (örneğin: "süt ürünleri")  
- Alakasız metin (örneğin: "merhaba")  

Bu yapı sayesinde sistem yalnızca anlamlı girdiler üzerinde çalışır ve daha doğru sonuçlar üretir.

---

### 🔹 Market Odaklı AI Analizi

Ürün veya kategori tespit edildiğinde:

- Satış içgörüsü  
- Grafik önerileri  
- Dashboard fikirleri  
- Kampanya önerileri  
- Müşteri analizi  

gibi çıktılar üretilir.

---

### 🔹 Veri Görselleştirme

CSV veri seti üzerinden:

- veri analizi yapılır  
- grafikler oluşturulur  
- görselleştirme sağlanır  

---

## ⚙️ Gereksinimler & Kurulum

Bu bölüm, projenin farklı bilgisayarlarda sorunsuz şekilde çalıştırılabilmesi için gerekli olan yazılım bileşenlerini, bağımlılıkları ve kurulum adımlarını ayrıntılı olarak açıklamaktadır. Proje, hem genel amaçlı metin işleme işlemlerini hem de market satış verisi odaklı yapay zekâ destekli analizleri bir arada sunduğu için, kurulum sürecinde hem Python ortamının hem de yerel LLM servisinin doğru biçimde hazırlanması gerekir. Proje ayrıca F8 kısayolu ile çalışan masaüstü etkileşimine, yerel panoya erişime, pencere tabanlı arayüze ve CSV seçimi üzerinden veri analizine dayanmaktadır. Bu nedenle kurulum yalnızca “paket yüklemekten” ibaret değildir; aynı zamanda çalışma ortamının doğru hazırlanmasını da içerir.

### 🔧 Sistem Gereksinimleri

Projeyi çalıştırmak için aşağıdaki temel gereksinimlerin sağlanması gerekir:

#### 1. Python 3.10 veya üzeri
Proje Python ile yazılmıştır ve ana uygulama main.pyw dosyası üzerinden çalışır. Kod içinde hem standart kütüphaneler hem de üçüncü taraf paketler kullanılmaktadır. Bu nedenle güncel bir Python sürümü önerilir. tkinter, threading, queue, time, os, tempfile ve atexit gibi modüller Python standart kütüphanesinden gelirken; pyperclip, pynput, pyautogui ve requests dış bağımlılıklardır.

#### 2. Ollama
Proje, metin üretimi ve analiz işlemleri için yerel olarak çalışan bir Ollama servisine bağlanır. Kodda API adresi http://localhost:11434/api/generate olarak tanımlanmıştır. Bu da Ollama servisinin yerel makinede açık olması gerektiği anlamına gelir. Ayrıca varsayılan model gemma3:1b olarak ayarlanmıştır.

#### 3. Yerel model
Kodda varsayılan aday model listesinde gemma3:1b yer almaktadır. Program, önce mevcut modelleri kontrol eder ve uygun bir modeli seçmeye çalışır. Bu nedenle sistemde en azından bu modelin kurulu olması gerekir.

#### 4. Windows ortamı önerilir
Proje F8 global kısayolu, pano işlemleri, fare konumu üzerinden popup menü açılması ve .bat ile başlatma gibi kullanım alışkanlıklarına göre tasarlanmıştır. Teknik olarak bazı parçalar farklı sistemlerde de çalışabilir, ancak mevcut kullanım biçimi Windows üzerinde daha uygundur. pyautogui, pynput ve pano erişimi gibi bileşenler burada kritik rol oynar.

#### 5. Proje dosya yapısı eksiksiz olmalıdır
Ana dosya tek başına yeterli değildir. main.pyw, yerel modül olarak market_analiz içinden market_verisini_hazirla ve gorsellestirme içinden market_penceresi_olustur fonksiyonlarını içe aktarır. Yani bu iki dosyanın da proje klasöründe bulunması gerekir. Aksi halde program açılışta import hatası verir.

#### 6. CSV veriyle çalışma için veri dosyası
Market analizi özelliği, kullanıcıdan bir .csv dosyası seçmesini ister. Bu nedenle market analizi modülünü kullanmak için uygun formatta bir CSV dosyasına ihtiyaç vardır. Kod içinde dosya seçim penceresi yalnızca CSV uzantılı dosyaları kabul edecek şekilde ayarlanmıştır.

---

### 🖱️ Kullanım İçin Ek Gereksinimler

Bu proje klasik bir terminal uygulaması gibi değil; masaüstü etkileşimine dayalıdır. Bu yüzden kurulumdan sonra şu kullanım koşullarını da bilmek gerekir:

#### 1. F8 kısayolu aktif olmalı
Kodda kısayol tuşu keyboard.Key.f8 olarak tanımlanmıştır. F8’e basıldığında program seçili metni panodan okumaya çalışır ve popup menü açar.

#### 2. Metin seçimi yapılmış olmalı
Program, seçili metni Ctrl+C ile kopyalamaya çalışır. Eğer kullanıcı önceden bir metin seçmemişse, uyarı mesajı verir. Bu yüzden F8 kullanımı “önce metin seç, sonra F8’e bas” mantığına dayanır.

#### 3. Market analizi için CSV seçilmelidir
Menüden market analizi açıldığında kullanıcıdan bir CSV dosyası seçmesi beklenir. Geçerli veri olmadan bu modül çalışmaz.

---

### 🧪 Kurulumdan Sonra Test Etme

Kurulumu tamamladıktan sonra hızlı kontrol için şunları test et:

1. Terminalde programı başlat.  
2. Ollama servisinin açık olduğundan emin ol.  
3. Basit bir metin yaz: yumurta  
4. Bu metni seç.  
5. F8 tuşuna bas.  
6. Menü açılıyorsa temel sistem çalışıyor demektir.  
7. Menüden bir AI işlemi seç.  
8. Market modülü için ayrıca bir CSV dosyası seçerek görselleştirme akışını kontrol et.  

Bu test akışı, hem metin işleme sistemini hem de market analizi akışını doğrulamak için yeterlidir.

## 🧩 Sistem Mimarisi

```mermaid
flowchart TD

A[Metin Secimi] --> B[F8 Tusuna Basilir]
B --> C[Metin Kopyalanir]
C --> D[Metin Analizi]

D -->|Urun/Kategori| E[Market AI Islemleri]
D -->|Genel Metin| F[Standart AI Islemleri]
D -->|Alakasiz| G[Uyari Ver]

E --> H[Prompt Olustur]
F --> H

H --> I[Ollama Modeli]
I --> J[Sonuc Uret]

J --> K[Popup veya Metne Yaz]

E --> L[Grafik Onerisi]
E --> M[Dashboard Fikri]
E --> N[Satis Icgorusu]

O[CSV Veri] --> P[Market Analizi]
P --> Q[Grafik Gosterimi]