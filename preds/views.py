from django.shortcuts import render

from django.core.cache import cache



def greed(request):
    """Тестирование структуры greed for mobile device"""
    return render(request, 'preds/test_grid.html')
    # return render(request, 'preds/test_li.html')



def index(request):
    cache.set('item_navbar_active','item-navbar-mainapp')

    return render(request, 'preds/index.html')
