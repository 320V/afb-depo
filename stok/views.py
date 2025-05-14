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
    """
    Web arayüzündeki popup üzerinden ürün adı ve kodu seçilerek stoktan düşme yapan ve 
    toplu çıkış işlemi gerçekleştiren bir fonksiyondur.
    """
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
                    urun_kodu=urun['urun_kodu'].upper()
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

@csrf_exempt
@require_http_methods(["POST"])
def stok_artis(request):
    """
    Web arayüzündeki popup üzerinden ürün adı ve kodu seçilerek stoktan artış yapan ve 
    toplu artış işlemi gerçekleştiren bir fonksiyondur.
    """
    try:
        data = json.loads(request.body)
        urunler = data.get('urunler', [])
        
        if not urunler:
            return JsonResponse({
                'success': False,
                'error': 'Ürün listesi boş.'
            })
        
        sonuclar = []
        hata = None
        
        for urun in urunler:
            try:
                urun_kodu = urun.get('urun_kodu')
                adet = urun.get('adet')
                
                if not urun_kodu or not adet:
                    hata = 'Ürün kodu ve adet bilgisi gereklidir.'
                    break
                
                try:
                    adet = int(adet)
                    if adet <= 0:
                        hata = 'Adet değeri pozitif bir sayı olmalıdır.'
                        break
                except ValueError:
                    hata = 'Geçersiz adet değeri.'
                    break
                
                # Ürünü bul
                product = Product.objects.filter(urun_kodu=urun_kodu).first()
                
                if not product:
                    hata = f'Ürün kodu "{urun_kodu}" olan ürün bulunamadı.'
                    break
                
                # Stok artışı
                product.adet += adet
                product.save()
                
                sonuclar.append({
                    'urun_kodu': urun_kodu,
                    'urun_adi': product.isim,
                    'artirilan_adet': adet,
                    'yeni_stok': product.adet
                })
                
            except Exception as e:
                hata = str(e)
                break
        
        if hata:
            return JsonResponse({
                'success': False,
                'error': hata
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Toplam {len(sonuclar)} ürüne stok eklendi.',
            'sonuclar': sonuclar
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Geçersiz JSON verisi.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def stok_dus(request):
    """
    Ürün koduna göre stoktan düşme yapan ve her ürün için ayrı ayrı sonuç bilgisi döndüren bir API endpoint'tir.
    """
    try:
        data = json.loads(request.body)
        urunler = data.get('urunler', [])
        
        if not urunler:
            return JsonResponse({
                'success': False,
                'error': 'Ürün listesi boş.'
            })
        
        sonuclar = []
        hata = None
        
        for urun in urunler:
            try:
                urun_kodu = urun.get('urun_kodu')
                adet = urun.get('adet')
                
                if not urun_kodu or not adet:
                    hata = 'Ürün kodu ve adet bilgisi gereklidir.'
                    break
                
                try:
                    adet = int(adet)
                    if adet <= 0:
                        hata = 'Adet değeri pozitif bir sayı olmalıdır.'
                        break
                except ValueError:
                    hata = 'Geçersiz adet değeri.'
                    break
                
                # Ürünü bul
                product = Product.objects.filter(urun_kodu=urun_kodu).first()
                
                if not product:
                    hata = f'Ürün kodu "{urun_kodu}" olan ürün bulunamadı.'
                    break
                
                # Stok kontrolü
                if product.adet < adet:
                    hata = f'{product.isim} ürünü için yeterli stok yok. Mevcut stok: {product.adet}'
                    break
                
                # Stoktan düş
                product.adet -= adet
                product.save()
                
                sonuclar.append({
                    'urun_kodu': urun_kodu,
                    'urun_adi': product.isim,
                    'dusulen_adet': adet,
                    'kalan_stok': product.adet
                })
                
            except Exception as e:
                hata = str(e)
                break
        
        if hata:
            return JsonResponse({
                'success': False,
                'error': hata
            })
        
        return JsonResponse({
            'success': True,
            'message': f'Toplam {len(sonuclar)} üründen stok düşüldü.',
            'sonuclar': sonuclar
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Geçersiz JSON verisi.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def urun_adet_to_id(request, urun_id):
    try:
        # Tüm ürünlerin kodlarını listele
        tum_urunler = Product.objects.all()
        print("\n=== Mevcut Ürün Kodları ===")
        for urun in tum_urunler:
            print(f"Ürün Kodu: {urun.urun_kodu}")
        print("==========================\n")
        
        # Gelen urun_id'yi göster
        print(f"İstenen Ürün Kodu: {urun_id}")
        
        # Ürünü ID'ye göre bul
        product = Product.objects.filter(urun_kodu=urun_id).first()
        
        if not product:
            return JsonResponse({
                'success': False,
                'error': f'Ürün kodu "{urun_id}" olan ürün bulunamadı.'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'urun': {
                'id': product.id,
                'isim': product.isim,
                'urun_kodu': product.urun_kodu,
                'adet': product.adet
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def urun_listesi(request):
    """
    Tüm ürünlerin listesini ve uyarı yüzdesini JSON formatında döndüren API endpoint'i.
    """
    try:
        # Tüm ürünleri al
        products = Product.objects.all()
        uyari_ayarlari = UyariAyarlari.get_instance()
        
        # Ürünleri JSON formatına dönüştür
        urunler = []
        for product in products:
            urunler.append({
                'id': product.id,
                'isim': product.isim,
                'urun_kodu': product.urun_kodu,
                'adet': product.adet,
                'birim': product.birim if hasattr(product, 'birim') else None,
                'kategori': product.kategori if hasattr(product, 'kategori') else None
            })
        
        return JsonResponse({
            'success': True,
            'urunler': urunler,
            'uyari_yuzdesi': uyari_ayarlari.uyari_yuzdesi / 100
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)