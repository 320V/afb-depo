from django.urls import path
from . import views

app_name = 'accounts'
 
urlpatterns = [
    path('api/login/', views.login_api, name='login_api'),
] 