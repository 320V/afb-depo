from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import F
import json
from .models import Agac
from stok.models import Product

@login_required
def agac_listesi(request):
    agaclar = Agac.objects.all().order_by('-olusturma_tarihi')
    return render(request, 'agac/agac_listesi.html', {'agaclar': agaclar})

@login_required
def agac_olustur(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Form verilerini doğrula
            if not data.get('ad'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ağaç adı gerekli'
                }, status=400)
            
            # Ürünleri doğrula
            if not data.get('urunler'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'En az bir ürün eklemelisiniz'
                }, status=400)
            
            # Ürün miktarlarını kontrol et
            for urun in data['urunler']:
                if urun.get('miktar', 0) <= 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Ürün miktarı 0\'dan büyük olmalı'
                    }, status=400)
                
                # Ürünün varlığını kontrol et
                try:
                    Product.objects.get(id=urun['urun_id'])
                except Product.DoesNotExist:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'ID: {urun["urun_id"]} olan ürün bulunamadı'
                    }, status=404)
            
            # Yeni ağaç oluştur
            agac = Agac.objects.create(
                ad=data['ad'],
                aciklama=data.get('aciklama', ''),
                urunler=data['urunler'],
                olusturan=request.user,
                son_guncelleyen=request.user
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Ağaç başarıyla oluşturuldu',
                'redirect': '/agac/'
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Geçersiz JSON verisi'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    # GET isteği için ürün listesini hazırla
    urunler = Product.objects.values('id', 'isim', 'adet', 'urun_kodu').order_by('urun_kodu')
    return render(request, 'agac/agac_olustur.html', {
        'urunler': urunler
    })

@login_required
@require_http_methods(['GET'])
def uretilebilir_adet(request, agac_id):
    """
    Bir ağaçtan üretilebilecek maksimum adet sayısını hesaplar.
    """
    try:
        agac = get_object_or_404(Agac, kod=agac_id)
        min_adet = float('inf')  # Sonsuz başlangıç değeri
        
        for urun in agac.urunler:
            try:
                stok_urun = Product.objects.get(id=urun['urun_id'])
                if stok_urun.adet < urun['miktar']:
                    # Eğer stokta yeterli ürün yoksa, üretilemez (0)
                    return JsonResponse({'adet': 0})
                
                # Her ürün için üretilebilecek maksimum adedi hesapla
                urun_max_adet = stok_urun.adet // urun['miktar']
                min_adet = min(min_adet, urun_max_adet)
                
            except Product.DoesNotExist:
                return JsonResponse({'adet': 0})
        
        # Eğer hiç ürün yoksa veya min_adet hala sonsuzsa
        if min_adet == float('inf'):
            min_adet = 0
            
        return JsonResponse({'adet': min_adet})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def update_agac_urunu(request, agac_id):
    """
    Ürün ağacındaki bir ürünün miktarını gerçek zamanlı olarak günceller.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Geçersiz istek metodu'}, status=405)

    try:
        agac = get_object_or_404(Agac, kod=agac_id)
        data = json.loads(request.body)
        urun_id = data.get('urun_id')
        miktar = data.get('miktar')

        if urun_id is None:
            return JsonResponse({'status': 'error', 'message': 'Ürün ID gerekli'}, status=400)

        # Ürünün stokta var olduğunu kontrol et
        try:
            Product.objects.get(id=urun_id)
        except Product.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Ürün bulunamadı'}, status=404)

        # Ağaçtaki ürünleri güncelle
        urunler = agac.urunler
        
        if miktar is None:  # Ürün silme işlemi
            urunler = [u for u in urunler if u['urun_id'] != urun_id]
        else:  # Ürün ekleme veya güncelleme işlemi
            urun_var = False
            for urun in urunler:
                if urun['urun_id'] == urun_id:
                    urun['miktar'] = miktar
                    urun_var = True
                    break
            
            if not urun_var:
                urunler.append({'urun_id': urun_id, 'miktar': miktar})

        # Ağacı güncelle ve kaydet
        agac.urunler = urunler
        agac.son_guncelleyen = request.user
        agac.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Ürün başarıyla güncellendi'
        })

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Geçersiz JSON verisi'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500) 