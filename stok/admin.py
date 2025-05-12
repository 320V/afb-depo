from django.contrib import admin
from .models import Product, UyariAyarlari
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
from django import forms
from django.http import HttpResponseRedirect
from django.urls import reverse

class MuhasebeOnayForm(forms.Form):
    onay = forms.BooleanField(required=True, label="Var olan ürünlerin Muhasebe Kodu ve Ürün Adı bilgilerini güncellemek istiyor musunuz?")

def get_stok_dict(engine=None):
    """
    6.1. ile başlayan ürünlerin stok kodunu key, ürün adını value olarak döndüren dict döner.
    Eğer engine parametresi verilmezse, varsayılan bağlantı bilgileri kullanılır.
    """
    if engine is None:
        conn_str = "mssql+pyodbc://D00005:722@192.168.1.213/PrestoXL?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes"
        engine = create_engine(conn_str)
    query = """
    SELECT STOK_KODU, STOK_KISA_ADI
    FROM STOK
    WHERE STOK_KODU LIKE '6.1.%'
    """
    with engine.connect() as conn:
        df_stok = pd.read_sql(query, conn)
        stok_dict = {row['STOK_KODU']: row['STOK_KISA_ADI'] for _, row in df_stok.iterrows()}
    return stok_dict

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Listede gösterilecek alanlar
    list_display = ('isim', 'urun_kodu', 'muhasebe_kodu', 'tedarikci_kodu', 'marka', 'adet', 'asgari_adet', 'birim', 'raf_no', 'olusturma_tarihi', 'olusturma_saat', 'guncelleme_tarihi', 'guncelleme_saat')
    
    # Arama yapılabilecek alanlar
    search_fields = ('isim', 'urun_kodu', 'muhasebe_kodu', 'tedarikci_kodu', 'marka', 'raf_no')
    
    # Filtreleme seçenekleri
    list_filter = ('marka', 'birim', 'olusturma_tarihi', 'guncelleme_tarihi')
    
    # Sıralama seçenekleri
    ordering = ('-olusturma_tarihi', '-olusturma_saat')
    
    # Sayfa başına gösterilecek kayıt sayısı
    list_per_page = 20
    
    # Tarih bazlı hiyerarşik filtreleme
    date_hierarchy = 'olusturma_tarihi'
    
    # Düzenleme formunda gruplandırma
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('isim', 'muhasebe_kodu', 'tedarikci_kodu', 'aciklama', 'marka')
        }),
        ('Stok Bilgileri', {
            'fields': ('adet', 'asgari_adet', 'birim', 'raf_no')
        }),
        ('Tarih Bilgileri', {
            'fields': ('olusturma_tarihi', 'olusturma_saat', 'guncelleme_tarihi', 'guncelleme_saat'),
            'classes': ('collapse',)
        }),
    )
    
    # Sadece okunabilir alanlar
    readonly_fields = ('urun_kodu', 'olusturma_tarihi', 'olusturma_saat', 'guncelleme_tarihi', 'guncelleme_saat')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('muhasebe-ekle/', self.admin_site.admin_view(self.muhasebe_ekle_view), name='muhasebe-ekle'),
            path('muhasebe-onay/', self.admin_site.admin_view(self.muhasebe_onay_view), name='muhasebe-onay'),
        ]
        return custom_urls + urls

    def muhasebe_ekle_view(self, request):
        try:
            # Muhasebe programından verileri çek
            stok_dict = get_stok_dict()
            
            # Var olan ürünleri kontrol et
            mevcut_urunler = []
            yeni_urunler = []
            
            for stok_kodu, urun_adi in stok_dict.items():
                if Product.objects.filter(muhasebe_kodu=stok_kodu).exists():
                    mevcut_urunler.append({
                        'muhasebe_kodu': stok_kodu,
                        'urun_adi': urun_adi
                    })
                else:
                    yeni_urunler.append({
                        'muhasebe_kodu': stok_kodu,
                        'urun_adi': urun_adi
                    })
            
            # Eğer mevcut ürün varsa, onay sayfasına yönlendir
            if mevcut_urunler:
                request.session['mevcut_urunler'] = mevcut_urunler
                request.session['yeni_urunler'] = yeni_urunler
                return redirect('admin:muhasebe-onay')
            
            # Mevcut ürün yoksa direkt yeni ürünleri ekle
            self._yeni_urunleri_ekle(yeni_urunler)
            self.message_user(request, f"Toplam {len(yeni_urunler)} yeni ürün başarıyla eklendi.", messages.SUCCESS)
            
        except Exception as e:
            self.message_user(request, f"Hata oluştu: {str(e)}", messages.ERROR)
        
        return self.changelist_view(request)

    def muhasebe_onay_view(self, request):
        if request.method == 'POST':
            form = MuhasebeOnayForm(request.POST)
            if form.is_valid() and form.cleaned_data['onay']:
                try:
                    mevcut_urunler = request.session.get('mevcut_urunler', [])
                    yeni_urunler = request.session.get('yeni_urunler', [])
                    
                    # Mevcut ürünleri güncelle
                    self._mevcut_urunleri_guncelle(mevcut_urunler)
                    
                    # Yeni ürünleri ekle
                    self._yeni_urunleri_ekle(yeni_urunler)
                    
                    # Session'ı temizle
                    request.session.pop('mevcut_urunler', None)
                    request.session.pop('yeni_urunler', None)
                    
                    self.message_user(request, 
                        f"Toplam {len(mevcut_urunler)} ürün güncellendi ve {len(yeni_urunler)} yeni ürün eklendi.", 
                        messages.SUCCESS)
                    
                except Exception as e:
                    self.message_user(request, f"Hata oluştu: {str(e)}", messages.ERROR)
                
                return redirect('admin:stok_product_changelist')
        else:
            form = MuhasebeOnayForm()
        
        mevcut_urunler = request.session.get('mevcut_urunler', [])
        yeni_urunler = request.session.get('yeni_urunler', [])
        
        context = {
            'form': form,
            'mevcut_urun_sayisi': len(mevcut_urunler),
            'yeni_urun_sayisi': len(yeni_urunler),
            'mevcut_urunler': mevcut_urunler[:10],  # İlk 10 ürünü göster
            'title': 'Muhasebe Ürün Güncelleme Onayı',
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/stok/product/muhasebe_onay.html', context)

    def _mevcut_urunleri_guncelle(self, mevcut_urunler):
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()
        
        for urun in mevcut_urunler:
            Product.objects.filter(muhasebe_kodu=urun['muhasebe_kodu']).update(
                isim=urun['urun_adi'],
                guncelleme_tarihi=current_date,
                guncelleme_saat=current_time
            )

    def _yeni_urunleri_ekle(self, yeni_urunler):
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()
        
        for urun in yeni_urunler:
            Product.objects.create(
                muhasebe_kodu=urun['muhasebe_kodu'],
                isim=urun['urun_adi'],
                adet=0,
                asgari_adet=1,
                birim='ADET',
                marka='UMAY TECH',
                olusturma_tarihi=current_date,
                olusturma_saat=current_time,
                guncelleme_tarihi=current_date,
                guncelleme_saat=current_time
            )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_muhasebe_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(UyariAyarlari)
class UyariAyarlariAdmin(admin.ModelAdmin):
    list_display = ('uyari_yuzdesi', 'guncelleme_tarihi')
    readonly_fields = ('guncelleme_tarihi',)
    fieldsets = (
        ('Uyarı Ayarları', {
            'fields': ('uyari_yuzdesi', 'guncelleme_tarihi')
        }),
    )

    def has_add_permission(self, request):
        # Eğer zaten bir kayıt varsa, yeni eklemeye izin verme
        if UyariAyarlari.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Silme işlemine izin verme
        return False

