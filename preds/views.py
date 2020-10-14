from django.shortcuts import render

from django.core.cache import cache


def index(request):
    cache.set('item_navbar_active','item-navbar-mainapp')

    return render(request, 'preds/index.html')
