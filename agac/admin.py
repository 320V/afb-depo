from django.contrib import admin
from .models import Agac

@admin.register(Agac)
class AgacAdmin(admin.ModelAdmin):
    list_display = ('ad', 'olusturma_tarihi', 'guncelleme_tarihi', 'olusturan')
    search_fields = ('ad', 'aciklama')
    list_filter = ('olusturma_tarihi', 'guncelleme_tarihi', 'olusturan') 