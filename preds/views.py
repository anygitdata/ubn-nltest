from django.shortcuts import render

from django.core.cache import cache
from django.http import JsonResponse



def get_content_eds_html(request):
    """Загрузка контента html """
    # from django.shortcuts import render_to_response

    sID = request.GET.get('file_tag')
    sID = sID[11:]  # btn-detail_eds_detail01
    sFile = '{}/{}.html'.format('preds/cont_tags', sID)

    # return render_to_response(sFile)
    return render(request, sFile)



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
    if request.method == 'GET':

        data = request.GET.get('file_tag')

        dc = dict(title="ED smart", cont=data, res="ok")

        return JsonResponse(dc, json_dumps_params=dict(ensure_ascii=False))

    return JsonResponse({'cont': 'Error url', 'res':'error'})


def greed(request):
    """Тестирование структуры greed for mobile device"""

    # return render(request, 'preds/test_grid.html')
    return render(request, 'preds/preds.html')

    # return render(request, 'preds/test_li.html')



def index(request):
    cache.set('item_navbar_active','item-navbar-mainapp')

    return render(request, 'preds/index.html')
