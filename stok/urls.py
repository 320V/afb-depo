from django.urls import path
from . import views

urlpatterns = [
    path('', views.table_view, name='stok_listesi'),
    path('urun-cikis/', views.urun_cikis, name='urun_cikis'),
    path('stok-dus/', views.stok_dus, name='stok_dus'),
]
