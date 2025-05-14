from django.shortcuts import render

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