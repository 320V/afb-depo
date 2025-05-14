from django.urls import path
from . import views

app_name = 'agac'

urlpatterns = [
    path('', views.agac_view, name='agac_listesi'),
] 