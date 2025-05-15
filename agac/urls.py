from django.urls import path
from . import views

app_name = 'agac'

urlpatterns = [
    path('liste/', views.agac_listesi, name='agac_listesi'),
    path('yeni/', views.agac_olustur, name='agac_olustur'),
    path('duzenle/<int:agac_id>/', views.agac_duzenle, name='agac_duzenle'),
    path('uretilebilir-adet/<int:agac_id>/', views.uretilebilir_adet, name='uretilebilir_adet'),
] 