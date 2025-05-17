from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
import re

# Create your models here.

class Product(models.Model):
    URUN_TIPLERI = [
        ('hammadde', 'Hammadde'),
        ('yarimamul', 'Yarı Mamul'),
        ('mamul', 'Mamul'),
        ('sarf', 'Sarf Malzeme'),
    ]
    
    KASA_TIPLERI = [
        ('normal', 'Normal'),
        ('ozel', 'Özel'),
        ('kritik', 'Kritik'),
    ]

    isim = models.CharField(max_length=255, verbose_name="Ürün Adı", default="Yeni Ürün")
    urun_kodu = models.CharField(max_length=50, verbose_name="Ürün Kodu", unique=True, editable=False)
    muhasebe_kodu = models.CharField(max_length=50, verbose_name="Muhasebe Kodu", unique=True, default="MUH-001")
    tedarikci_kodu = models.CharField(max_length=50, verbose_name="Tedarikçi Kodu", blank=True, null=True, help_text="Tedarikçinin ürün için kullandığı kod (opsiyonel)")
    aciklama = models.TextField(verbose_name="Açıklama", blank=True, null=True, default="-")
    adet = models.IntegerField(verbose_name="Adet", default=0)
    asgari_adet = models.IntegerField(verbose_name="Asgari Adet", default=10)
    birim = models.CharField(max_length=20, verbose_name="Birim", default="Adet")
    raf_no = models.CharField(max_length=20, verbose_name="Raf No", default="A-01")
    marka = models.CharField(max_length=50, verbose_name="Marka", default="Umay")
    urun_tipi = models.CharField(max_length=20, verbose_name="Ürün Tipi", choices=URUN_TIPLERI, default='sarf')
    kasa_tipi = models.CharField(max_length=20, verbose_name="Kasa Tipi", choices=KASA_TIPLERI, default='normal')
    birim_fiyati = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Birim Fiyatı", default=0.00)
    olusturma_tarihi = models.DateField(verbose_name="Oluşturulma Tarihi", auto_now_add=True)
    olusturma_saat = models.TimeField(verbose_name="Oluşturma Saati", auto_now_add=True)
    guncelleme_tarihi = models.DateField(verbose_name="Güncellenme Tarihi", auto_now=True)
    guncelleme_saat = models.TimeField(verbose_name="Güncellenme Saati", auto_now=True)

    def __str__(self):
        return f"{self.isim} ({self.urun_kodu})"

    @classmethod
    def get_next_urun_kodu(cls):
        """
        Kullanılabilir bir sonraki ürün kodunu döndürür.
        Silinmiş kodları da tekrar kullanabilir.
        """
        # Tüm mevcut ürün kodlarını al
        existing_codes = set(cls.objects.values_list('urun_kodu', flat=True))
        
        # UMY- formatındaki kodları bul
        pattern = re.compile(r'UMY-(\d+)')
        used_numbers = set()
        
        for code in existing_codes:
            match = pattern.match(code)
            if match:
                used_numbers.add(int(match.group(1)))
        
        # Kullanılabilir ilk numarayı bul
        next_number = 1
        while next_number in used_numbers:
            next_number += 1
            
        return f"UMY-{next_number}"

    def save(self, *args, **kwargs):
        # Eğer ürün kodu boşsa veya UMY- formatında değilse, yeni kod ata
        if not self.urun_kodu or not self.urun_kodu.startswith('UMY-'):
            self.urun_kodu = self.get_next_urun_kodu()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ürün"
        verbose_name_plural = "Ürünler"
        ordering = ['-olusturma_tarihi', '-olusturma_saat']  # En son eklenen ürünler başta görünsün

class StockMovement(models.Model):
    HAREKET_TIPLERI = [
        ('giris', 'Giriş'),
        ('cikis', 'Çıkış'), 
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Ürün", related_name='stock_movements')
    hareket_tipi = models.CharField(max_length=10, verbose_name="Hareket Tipi", choices=HAREKET_TIPLERI)
    miktar = models.IntegerField(verbose_name="Miktar")
    onceki_stok = models.IntegerField(verbose_name="Önceki Stok")
    sonraki_stok = models.IntegerField(verbose_name="Sonraki Stok")
    aciklama = models.TextField(verbose_name="Açıklama", blank=True, null=True)
    islem_tarihi = models.DateTimeField(verbose_name="İşlem Tarihi", auto_now_add=True)
    kullanici = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name="İşlemi Yapan", null=True, blank=True)
    islem_yapan = models.CharField(max_length=255, verbose_name="İşlemi Yapan Kişi", null=True, blank=True)

    class Meta:
        verbose_name = "Stok Hareketi"
        verbose_name_plural = "Stok Hareketleri"
        ordering = ['-islem_tarihi']

    def __str__(self):
        return f"{self.product.isim} - {self.get_hareket_tipi_display()} ({self.miktar})"

class UyariAyarlari(models.Model):
    uyari_yuzdesi = models.IntegerField(
        verbose_name="Uyarı Yüzdesi",
        help_text="Asgari adetin yüzde kaçına düştüğünde sarı uyarı verileceği",
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    guncelleme_tarihi = models.DateTimeField(
        verbose_name="Güncelleme Tarihi",
        auto_now=True
    )

    class Meta:
        verbose_name = "Uyarı Ayarı"
        verbose_name_plural = "Uyarı Ayarları"

    def __str__(self):
        return f"Uyarı Yüzdesi: %{self.uyari_yuzdesi}"

    def save(self, *args, **kwargs):
        # Eğer başka kayıt varsa, onu sil
        if not self.pk and UyariAyarlari.objects.exists():
            UyariAyarlari.objects.all().delete()
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class StokYonetimi(models.Model):
    class Meta:
        permissions = [
            ("stok_mobil", "Stok Mobil Erişimi"),
        ]

class SystemSettings(models.Model):
    son_istatistik_sifirlama = models.DateTimeField(null=True, blank=True)
    son_yedekleme = models.DateTimeField(null=True, blank=True)
    sistem_durumu = models.CharField(max_length=20, default='aktif')
    bakim_modu = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_instance(cls):
        instance, created = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self):
        return f"Sistem Ayarları (Son Güncelleme: {self.updated_at})"
