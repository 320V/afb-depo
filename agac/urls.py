from django.urls import path
from . import views

app_name = 'agac'

urlpatterns = [
    path('', views.agac_listesi, name='agac_listesi'),
    path('yeni/', views.agac_olustur, name='agac_olustur'),
    path('uretilebilir-adet/<int:agac_id>/', views.uretilebilir_adet, name='uretilebilir_adet'),
    path('update-urun/<int:agac_id>/', views.update_agac_urunu, name='update_agac_urunu'),
]