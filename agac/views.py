from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from stok.models import Product
from .models import Agac
import json

def agac_view(request):
    """
    Ürün ağaçlarını görüntülemek için ana view fonksiyonu.
    """
    return render(request, 'html/agac_listesi.html', {
        'active_page': 'agac_listesi',
        'breadcrumb': {
            'title': 'Ürün Ağaçları',
            'subtitle': 'Ürün Ağaçlarını Görüntüle'
        }
    })

@login_required
def agac_listesi(request):
    agaclar = Agac.objects.all().order_by('-olusturma_tarihi')
    return render(request, 'agac/agac_listesi.html', {'agaclar': agaclar})

@login_required
def agac_duzenle(request, agac_id):
    agac = get_object_or_404(Agac, kod=agac_id)
    urunler = Product.objects.all()

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            agac.ad = data.get('ad')
            agac.aciklama = data.get('aciklama')
            agac.urunler = data.get('urunler', [])
            agac.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Ağaç başarıyla güncellendi',
                'redirect': '/agac/liste/'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return render(request, 'agac/agac_duzenle.html', {
        'agac': agac,
        'urunler': urunler
    })

@login_required
def uretilebilir_adet(request, agac_id):
    agac = get_object_or_404(Agac, kod=agac_id)
    min_uretilebilir = float('inf')
    
    for urun in agac.urunler:
        try:
            stok_urun = Product.objects.get(id=urun['urun_id'])
            gerekli_adet = urun['miktar']
            uretilebilir = stok_urun.adet // gerekli_adet
            min_uretilebilir = min(min_uretilebilir, uretilebilir)
        except Product.DoesNotExist:
            return JsonResponse({'adet': 0})
    
    if min_uretilebilir == float('inf'):
        return JsonResponse({'adet': 0})
    
    return JsonResponse({'adet': min_uretilebilir})

@login_required
def agac_olustur(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ad = data.get('ad')
            aciklama = data.get('aciklama')
            urunler = data.get('urunler', [])

            # Yeni ağaç oluştur
            agac = Agac.objects.create(
                ad=ad,
                aciklama=aciklama,
                urunler=urunler,
                olusturan=request.user
            )

            return JsonResponse({
                'status': 'success',
                'message': 'Ağaç başarıyla oluşturuldu',
                'redirect': '/agac/liste/'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    # GET isteği için ürünleri getir
    urunler = Product.objects.all()
    return render(request, 'agac/agac_olustur.html', {'urunler': urunler}) 