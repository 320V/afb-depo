from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Agac(models.Model):
    kod = models.AutoField(primary_key=True)  # Otomatik artan kod
    ad = models.CharField(max_length=100)
    aciklama = models.TextField(blank=True, null=True)
    urunler = models.JSONField()  # Ürün adları ve adetleri JSON olarak saklanacak
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    olusturan = models.ForeignKey(User, on_delete=models.CASCADE)
    olusturma_saat = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.kod} - {self.ad}" 