"""
Bu dosya örnek veri oluşturma kodunu içerir.
Sadece referans amaçlıdır ve doğrudan çalıştırılmamalıdır.
"""

from django.utils import timezone
from datetime import timedelta
import random
from .models import Product

def generate_sample_data():
    # Örnek veri listeleri
    urun_isimleri = ["Laptop", "Mouse", "Klavye", "Monitör", "Yazıcı", "Hoparlör", "Kulaklık", "Tablet", "Telefon", "Kamera"]
    markalar = ["Apple", "Samsung", "Logitech", "Dell", "HP", "Lenovo", "Asus", "Microsoft", "Sony", "Canon"]
    birimler = ["Adet", "Kutu", "Paket", "Set"]
    raf_numaralari = [f"{chr(65+i)}-{j:02d}" for i in range(5) for j in range(1, 11)]  # A-01'den E-10'a kadar

    # Son 30 gün içinde rastgele tarihler oluştur
    for i in range(50):
        # Rastgele gün (0-30 gün önce)
        random_days = random.randint(0, 30)
        random_hours = random.randint(0, 23)
        random_minutes = random.randint(0, 59)
        
        # Oluşturma tarihi ve saati
        olusturma_zamani = timezone.now() - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
        
        # Güncelleme tarihi ve saati (oluşturma zamanından sonra)
        guncelleme_zamani = olusturma_zamani + timedelta(hours=random.randint(1, 24))

        # Örnek veri oluşturma kodu
        Product.objects.create(
            isim=f"{random.choice(urun_isimleri)} {i+1}",
            urun_kodu=f"URUN-{i+1:03d}",
            aciklama=f"Bu ürün {random.choice(markalar)} markasına aittir.",
            adet=random.randint(1, 100),
            asgari_adet=random.randint(5, 20),
            birim=random.choice(birimler),
            raf_no=random.choice(raf_numaralari),
            marka=random.choice(markalar),
            olusturma_tarihi=olusturma_zamani.date(),
            olusturma_saat=olusturma_zamani.time(),
            guncelleme_tarihi=guncelleme_zamani.date(),
            guncelleme_saat=guncelleme_zamani.time()
        ) 