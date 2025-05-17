from django.contrib import admin
from .models import Product, UyariAyarlari, StockMovement, SystemSettings
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from sqlalchemy import create_engine
import pandas as pd
from datetime import datetime
from django import forms
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import qrcode
from io import BytesIO
from PIL import Image

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
    list_display = ('isim', 'urun_kodu', 'adet', 'asgari_adet', 'birim', 'urun_tipi', 'kasa_tipi', 'birim_fiyati')
    search_fields = ('isim', 'urun_kodu', 'muhasebe_kodu', 'tedarikci_kodu')
    list_filter = ('urun_tipi', 'kasa_tipi', 'marka')
    ordering = ('isim',)
    show_muhasebe_button = True  # Muhasebe Programından Ekle butonunu göster
    change_list_template = 'admin/stok/product/change_list.html'  # Özel template'i kullan

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('muhasebe-ekle/', self.admin_site.admin_view(self.muhasebe_ekle_view), name='muhasebe-ekle'),
            path('muhasebe-onay/', self.admin_site.admin_view(self.muhasebe_onay_view), name='muhasebe-onay'),
            path('toplu-qr-olustur/', self.admin_site.admin_view(self.toplu_qr_olustur_view), name='toplu-qr-olustur'),
        ]
        return custom_urls + urls

    def muhasebe_ekle_view(self, request):
        try:
            # Muhasebe programından veri çek
            stok_dict = get_stok_dict()
            
            # Mevcut ürünleri ve yeni ürünleri belirle
            mevcut_urunler = []
            yeni_urunler = []
            
            for stok_kodu, stok_adi in stok_dict.items():
                try:
                    urun = Product.objects.get(muhasebe_kodu=stok_kodu)
                    mevcut_urunler.append({
                        'urun_kodu': urun.urun_kodu,
                        'urun_adi': urun.isim,
                        'yeni_urun_adi': stok_adi,
                        'muhasebe_kodu': stok_kodu
                    })
                except Product.DoesNotExist:
                    yeni_urunler.append({
                        'urun_adi': stok_adi,
                        'muhasebe_kodu': stok_kodu
                    })
            
            # Session'a kaydet
                request.session['mevcut_urunler'] = mevcut_urunler
                request.session['yeni_urunler'] = yeni_urunler
            
            return render(request, 'admin/stok/product/muhasebe_onay.html', {
                'form': MuhasebeOnayForm(),
                'mevcut_urun_sayisi': len(mevcut_urunler),
                'yeni_urun_sayisi': len(yeni_urunler),
                'mevcut_urunler': mevcut_urunler[:10],  # İlk 10 ürünü göster
                'title': 'Muhasebe Ürün Güncelleme Onayı',
                'opts': self.model._meta,
            })
        except Exception as e:
            self.message_user(request, f"Muhasebe programına bağlanırken hata oluştu: {str(e)}", messages.ERROR)
            return redirect('admin:stok_product_changelist')

    def _mevcut_urunleri_guncelle(self, mevcut_urunler):
        for urun in mevcut_urunler:
            try:
                product = Product.objects.get(muhasebe_kodu=urun['muhasebe_kodu'])
                product.isim = urun['yeni_urun_adi']
                product.save()
            except Product.DoesNotExist:
                continue

    def _yeni_urunleri_ekle(self, yeni_urunler):
        for urun in yeni_urunler:
            Product.objects.create(
                isim=urun['urun_adi'],
                muhasebe_kodu=urun['muhasebe_kodu'],
                birim_fiyati=0  # Varsayılan değer
            )

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
                self.message_user(request, "Lütfen onay kutusunu işaretleyin.", messages.ERROR)
        
        mevcut_urunler = request.session.get('mevcut_urunler', [])
        yeni_urunler = request.session.get('yeni_urunler', [])
        
        context = {
            'form': MuhasebeOnayForm(),
            'mevcut_urun_sayisi': len(mevcut_urunler),
            'yeni_urun_sayisi': len(yeni_urunler),
            'mevcut_urunler': mevcut_urunler[:10],  # İlk 10 ürünü göster
            'title': 'Muhasebe Ürün Güncelleme Onayı',
            'opts': self.model._meta,
        }
        
        return render(request, 'admin/stok/product/muhasebe_onay.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_muhasebe_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

    def toplu_qr_olustur_view(self, request):
        if request.method == 'POST':
            qr_per_page = int(request.POST.get('qr_per_page', 10))
            products = Product.objects.all()
            
            # Create PDF
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # Calculate grid dimensions based on qr_per_page
            qr_size = 2 * cm  # QR code size
            margin = 1 * cm   # Page margin
            
            # Calculate optimal grid layout
            available_width = width - 2 * margin
            available_height = height - 2 * margin
            
            # Try to create a square-like grid
            cols = int((qr_per_page) ** 0.5)  # Square root for initial estimate
            rows = (qr_per_page + cols - 1) // cols  # Ceiling division
            
            # Adjust QR size to fit the page
            qr_size = min(
                available_width / cols,
                available_height / rows
            )
            
            # Generate QR codes
            qr = qrcode.QRCode(version=1, box_size=10, border=2) 
            current_page = 1
            current_row = 0
            current_col = 0
            qr_count = 0
            
            # Store QR code positions for later drawing grid lines
            qr_positions = []
            
            for product in products:
                # Generate QR code
                qr.clear()
                qr.add_data(product.urun_kodu)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Calculate position
                x = margin + current_col * qr_size
                y = height - margin - current_row * qr_size - qr_size
                
                # Store position for grid lines
                qr_positions.append((x, y, qr_size))
                
                # Save QR code to BytesIO
                qr_buffer = BytesIO()
                qr_img.save(qr_buffer, format='PNG')
                qr_buffer.seek(0)
                
                # Convert BytesIO to PIL Image
                img = Image.open(qr_buffer)
                
                # Draw QR code
                p.drawInlineImage(img, x, y, width=qr_size, height=qr_size)
                
                # Update position
                current_col += 1
                qr_count += 1
                
                if current_col >= cols:
                    current_col = 0
                    current_row += 1
                    if current_row >= rows or qr_count >= qr_per_page:
                        # Draw grid lines before showing new page
                        #self._draw_grid_lines(p, qr_positions, cols, rows, qr_size)
                        qr_positions = []  # Reset positions for new page
                        p.showPage()
                        current_page += 1
                        current_row = 0
                        qr_count = 0
            
            # Draw grid lines for the last page if there are any QR codes
            """if qr_positions:
                self._draw_grid_lines(p, qr_positions, cols, rows, qr_size)"""
            
            p.save()
            buffer.seek(0)
            
            # Create response
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="toplu_qr_kodlar.pdf"'
            return response
            
        # GET request - show form
        toplam_urun_sayisi = Product.objects.count()
        return render(request, 'admin/stok/product/toplu_qr_olustur.html', {
            'toplam_urun_sayisi': toplam_urun_sayisi,
        })

    def _draw_grid_lines(self, canvas, positions, cols, rows, qr_size):
        """Draw grid lines around QR codes"""
        if not positions:
            return
            
        # Get the first position to determine starting point
        start_x, start_y, _ = positions[0]
        
        # Set line properties
        canvas.setStrokeColorRGB(0.5, 0.5, 0.5)  # Darker gray color
        canvas.setLineWidth(0.2)  # Slightly thicker line
        
        # Draw vertical lines
        for i in range(cols + 1):
            x = start_x + (i * qr_size)
            canvas.line(x, start_y, x, start_y + (rows * qr_size))
        
        # Draw horizontal lines
        for i in range(rows + 1):
            y = start_y + (i * qr_size)
            canvas.line(start_x, y, start_x + (cols * qr_size), y)

@admin.register(UyariAyarlari)
class UyariAyarlariAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'urun_kodu', 'tedarikci_kodu', 'hareket_tipi', 'miktar', 'onceki_stok', 'sonraki_stok', 'islem_tarihi', 'kullanici', 'aciklama')
    list_filter = ('hareket_tipi', 'islem_tarihi', 'kullanici')
    search_fields = ('product__isim', 'product__urun_kodu', 'product__tedarikci_kodu', 'aciklama')
    ordering = ('-islem_tarihi',)
    readonly_fields = ('product', 'hareket_tipi', 'miktar', 'onceki_stok', 'sonraki_stok', 'islem_tarihi', 'kullanici', 'aciklama')

    def urun_kodu(self, obj):
        return obj.product.urun_kodu
    urun_kodu.short_description = 'Ürün Kodu'

    def tedarikci_kodu(self, obj):
        return obj.product.tedarikci_kodu or '-'
    tedarikci_kodu.short_description = 'Tedarikçi Kodu'

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    change_list_template = 'admin/system_settings_changelist.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('sifirla/', self.admin_site.admin_view(self.sifirla_view), name='sifirla_view'),
        ]
        return custom_urls + urls

    def sifirla_view(self, request):
        if request.method == 'POST':
            try:
                # İstatistikleri sıfırla
                StockMovement.objects.all().delete()
                
                # Son sıfırlama tarihini güncelle
                settings = SystemSettings.get_instance()
                settings.son_istatistik_sifirlama = timezone.now()
                settings.save()
                
                messages.success(request, 'İstatistikler başarıyla sıfırlandı.')
            except Exception as e:
                messages.error(request, f'Bir hata oluştu: {str(e)}')
            
            return redirect('admin:stok_systemsettings_changelist')
        
        return render(request, 'admin/sifirla_confirm.html')

    def has_add_permission(self, request):
            return False

    def has_delete_permission(self, request, obj=None):
        return False

