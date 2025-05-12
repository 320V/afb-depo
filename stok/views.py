from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Product, UyariAyarlari

def table_view(request):
    products = Product.objects.all()
    uyari_ayarlari = UyariAyarlari.get_instance()
    
    return render(request, 'html/stok_listesi.html', {
        'products': products,
        'active_page': 'urun_listesi',
        'uyari_yuzdesi': uyari_ayarlari.uyari_yuzdesi / 100
    })

@csrf_exempt
@require_http_methods(["POST"])
def urun_cikis(request):
    try:
        data = json.loads(request.body)
        urunler = data.get('urunler', [])
        
        if not urunler:
            return JsonResponse({'success': False, 'error': 'Ürün listesi boş.'})
        
        for urun in urunler:
            try:
                # Ürün adı ve kodu ile eşleşen ilk ürünü bul
                product = Product.objects.filter(
                    isim=urun['urun_adi'],
                    urun_kodu=urun['urun_kodu']
                ).first()
                
                if not product:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Ürün adı "{urun["urun_adi"]}" ve kodu "{urun["urun_kodu"]}" olan ürün bulunamadı.'
                    })
                
                cikis_adet = int(urun['adet'])
                
                if product.adet < cikis_adet:
                    return JsonResponse({
                        'success': False, 
                        'error': f'{product.isim} ürünü için yeterli stok yok. Mevcut stok: {product.adet}'
                    })
                
                product.adet -= cikis_adet
                product.save()
                
            except ValueError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Geçersiz adet değeri.'
                })

        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Geçersiz JSON verisi.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})