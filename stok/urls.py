from django.urls import path
from . import views

urlpatterns = [
    path('', views.table_view, name='stok_listesi'),
    path('urun-listesi/', views.urun_listesi, name='urun_listesi'),
    path('urun-cikis/', views.urun_cikis, name='urun_cikis'),
    path('stok-dus/', views.stok_dus, name='stok_dus'),
    path('stok-artis/', views.stok_artis, name='stok_artis'),
    path('<str:urun_id>/adet/', views.urun_adet_to_id, name='urun_adet_to_id'),
]
