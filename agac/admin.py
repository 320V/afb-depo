from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.forms import ModelForm, ValidationError
from django.template.loader import render_to_string
from .models import Agac
from stok.models import Product

class AgacAdminForm(ModelForm):
    class Meta:
        model = Agac
        fields = '__all__'

    def clean_urunler(self):
        urunler = self.cleaned_data.get('urunler', [])
        if not urunler:
            raise ValidationError("En az bir ürün eklemelisiniz.")
        
        for urun in urunler:
            if not isinstance(urun.get('miktar'), int) or urun.get('miktar') < 0:
                raise ValidationError("Ağaç adedi 0'dan küçük olamaz.")
        
        return urunler

@admin.register(Agac)
class AgacAdmin(admin.ModelAdmin):
    form = AgacAdminForm
    list_display = ('ad', 'olusturma_tarihi', 'guncelleme_tarihi', 'olusturan', 'son_guncelleyen', 'agac_link')
    search_fields = ('ad', 'aciklama')
    list_filter = ('olusturma_tarihi', 'guncelleme_tarihi', 'olusturan', 'son_guncelleyen')
    readonly_fields = ('olusturan', 'olusturma_tarihi', 'olusturma_saat', 'son_guncelleyen', 'guncelleme_tarihi', 'formatted_urunler')
    exclude = ('urunler',)

    def agac_link(self, obj):
        url = reverse('admin:agac_agac_change', args=[obj.kod])
        return format_html('<a href="{}" class="button">Düzenle</a>', url)
    agac_link.short_description = 'İşlemler'

    def formatted_urunler(self, obj):
        if not obj.urunler:
            return "-"
        
        context = {
            'urunler': [],
            'all_products': Product.objects.values('id', 'isim', 'adet', 'urun_kodu')
        }
        
        for urun in obj.urunler:
            try:
                product = Product.objects.get(id=urun['urun_id'])
                context['urunler'].append({
                    'id': product.id,
                    'isim': product.isim,
                    'urun_kodu': product.urun_kodu,
                    'stok_adet': product.adet,
                    'agac_adet': urun['miktar']
                })
            except Product.DoesNotExist:
                continue

        return mark_safe(render_to_string('admin/agac/agac_urunler.html', context))

    formatted_urunler.short_description = "Ürünler"

    def save_model(self, request, obj, form, change):
        if not change:  # Yeni kayıt oluşturuluyorsa
            obj.olusturan = request.user
        obj.son_guncelleyen = request.user
        super().save_model(request, obj, form, change) 