from django.shortcuts import render
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)

# Create your views here.

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            # Debug log ekleyelim
            logger.debug(f"Request body: {request.body}")
            logger.debug(f"Content-Type: {request.headers.get('Content-Type')}")
            
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            logger.debug(f"Username: {username}")
            
            if not username or not password:
                return JsonResponse({
                    'success': False,
                    'message': 'Kullanıcı adı ve şifre gereklidir.'
                }, status=400)
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                # Kullanıcı izinlerini kontrol et
                permissions = {
                    'is_staff': user.is_staff,  # Admin paneline erişim izni
                    'is_superuser': user.is_superuser,  # Tam yetkili admin
                    'is_active': user.is_active,  # Hesap aktif mi
                }
                
                # Kullanıcının tüm izinlerini al
                user_permissions = list(user.get_all_permissions())
                
                # UserProfile bilgilerini al
                try:
                    profile = user.profile
                    title = profile.title
                except:
                    title = None
                
                return JsonResponse({
                    'success': True,
                    'message': 'Giriş başarılı',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': user.get_full_name(),
                        'title': title,
                        'permissions': permissions,
                        'all_permissions': user_permissions
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Geçersiz kullanıcı adı veya şifre'
                }, status=401)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Geçersiz JSON formatı'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Sadece POST istekleri kabul edilir'
    }, status=405)
