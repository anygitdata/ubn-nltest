from django.shortcuts import render

from django.core.cache import cache
from django.http import JsonResponse


def get_content_eds(request):
    """Ajax  обработчик <script> ...</script> from  base_layout.html.
    Обработка специальных сообщений через модальноеОкно в браузере
    key in dict for session:  system_send_mes
        Структура request.session['system_send_mes']:
            dict(title='Сессия', mes=s_mes, res='exists')
            res='exists' - идентификатор для отображения в диалоговом окне
            title='Сессия' заголовок сообщения
            mes=s_mes      строка сообщения
    url:  contenteds
    name: contenteds
    """
    1
    dc = dict(title="ED smart", cont="Контент продукции ED", res="ok")

    return JsonResponse(dc, json_dumps_params=dict(ensure_ascii=False))


def greed(request):
    """Тестирование структуры greed for mobile device"""

    # return render(request, 'preds/temp/test_grid.html')
    return render(request, 'preds/test_grid.html')
    # return render(request, 'preds/test_li.html')



def index(request):
    cache.set('item_navbar_active','item-navbar-mainapp')

    return render(request, 'preds/index.html')
