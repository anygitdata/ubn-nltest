
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.contrib.auth.decorators import login_required

from app import getUser

from .forms import (Base_profForm, AddProf_memberForm, AdvPanel_profForm,
                    Modf_prof_byHeaderForm, Modf_prof_byuserForm,
                    UpdPassword_byHeadForm, UpdPsw_byUserForm, UpdStatus_userForm )

from .serv_advuser import Com_proc_advuser
from .serv_typestatus import type_status_user
# import json


def modf_data_dict(arg_dc:dict)->dict:
    """ Сброс значений empty or ''  into None """
    dc_res = arg_dc
    for key in dc_res.keys():
        val = dc_res.get(key)
        if val == 'empty' or val == '':
            dc_res[key] = None

    return dc_res


# Контроллеры перенаправления на редактирование
# Перенаправление сообщения на страницу empty
# используется для верификации или отсутствия данных
def redirect_empty(arg_title=None, arg_mes=None):
    """ Перенаправление по url emptyext
    arg_title  заголовок на странице default None -> Сообщение сервера
    arg_mes    текстовое сообщение   default None -> Сервер отклонил обработку
    """

    cache.delete('item_navbar_active')  # Обнуление кэша идентификатора id set JS active links

    cache.set('emptyext', dict( title=arg_title or 'Сообщение сервера' , mes=arg_mes or 'Сервер отклонил обработку' ) )
    return redirect('emptyext')


# url  /advuser/modpanelprof
# Административная панель
@login_required
def AdvPanel_prof(request):
    from .serv_typestatus import type_status_user

    cache.set('item_navbar_active','item-navbar-admpanel')

    """Настройки на уровне рукГруппы закрыты.
    РукПроекта не готово к полному сопровождению"""
    return redirect('listprof_lvl30', page=1)


    user = request.user
    type_status = type_status_user(user)

    if type_status.levelperm < 40:
        return redirect_empty(arg_title='Нет прав', arg_mes='Нет прав на обработку профиля участника проекта')


    if request.method == 'POST':

        form = AdvPanel_profForm(request.POST)
        if form.is_valid():

            proj_memb = form.cleaned_data['proj_memb']
            id_command = int(form.cleaned_data['id_command'])
            if id_command == 1:  # изменить профиль

                cache.set('Modf_prof_byheader', proj_memb)
                return redirect('updprofiluser')
            elif id_command == 2: # изменение пароля

                cache.set('UpdPassword_user', proj_memb) # передает данные для username
                return redirect('updpswuser')

            else: # Изменение status
                cache.set('UpdStatus_user', proj_memb)
                return redirect('updpermuser')
    else:

        if not cache.has_key('AdvPanel_prof'):
            form = AdvPanel_profForm()
        else:
            proj_memb = cache.get('AdvPanel_prof')
            dc_init = dict(proj_memb=proj_memb)
            form = AdvPanel_profForm(initial=dc_init)

        return render(request,'advuser/header_panel.html', dict(form=form, error=None))


@login_required
def UpdStatus_user(request):
    """Контроллер обраотки изменений status_id.
    Изменения осуществляются только рукГрупп
    url: updpermuser"""


    # JS set adctive links не настроено !!!
    # в нужном месте установить код
    # cache.set('item_navbar_active','item-navbar-admpanel') # JS set active links


    def return_render(arg_form:UpdStatus_userForm, arg_dc:dict):
        """Локальная процедура для запуска render.
        arg_form: UpdStatus_userForm
        arg_dc: dc_session = request.session['UpdStatus_user']
        return render with cont form and dc_session """

        cont = dict(form=arg_form)
        cont.update(arg_dc)

        return render(request,'advuser/upd_status_user.html', cont)


    if not cache.has_key('UpdStatus_user'):
        return redirect_empty(arg_title='Сервер отклонил обработку', arg_mes='Параметры запроса устарели')

    user = cache.get('UpdStatus_user')
    user = getUser(user)
    if user is None:
        cache.delete('UpdStatus_user')
        return redirect_empty(arg_title='Сервер отклонил обработку', arg_mes='Нет данных по логину')


    if request.method == 'POST':
        form = UpdStatus_userForm(request.POST)
        dc_session = request.session['UpdStatus_user']

        # изициализация локальных полей для процедуры clear()
        user_head = getUser(request.user.username)

        form.dc_param_verf = form.param_verf(user_head=user_head.username,
                                        user_modf=dc_session['upd_username'])

        if form.is_valid():
            user = request.user
            res_save = form.save_data_status(user, dc_session)

            if res_save:
                mes = res_save.res_dict['data_mes']
                dict_cache = dict(username=dc_session['upd_username'], mes=mes)
                cache.set('Success_register_user', dict_cache)
                del request.session['UpdStatus_user']

                return redirect('ver_profil')  # переход на view Success_register_user

            else:
                return return_render(form, dc_session)

        else:  # сообщения из процедуры clean()
            return return_render(form, dc_session)


    else: # Обработка запроса GET

        from .serv_sprstatus import Com_proc_sprstatus

        from app.models import spr_fields_models
        import json

        type_status = type_status_user(user)
        levelperm_user = type_status.levelperm

        user_master = getUser( request.user)
        type_status_master = type_status_user(user_master)

        # Блок верификации
        if 1 < 2 :
            if type_status_master.levelperm < 40 or type_status_master.levelperm <= levelperm_user:
                return redirect_empty(arg_title='Сервер отклонил обработку', arg_mes='Нет прав на обработку')

            if levelperm_user < 30:
                return redirect_empty(arg_title='Сервер отклонил обработку', arg_mes='Статус клиента не меняется')

            if levelperm_user == 100 :
                return redirect_empty(arg_title='Сервер отклонил обработку', arg_mes='Статус руководителя проекта постоянный')

            parentuser = Com_proc_advuser.get_parentuser_02(user)
            if parentuser.username != user_master.username:
                return redirect_empty(arg_title='Сервер отклонил обработку', arg_mes='Руководитель группы может изменять профиль только своей структуры')


        # Конец блока верификации

        # Значение as default for levelperm== 40 кол-во менеджеров
        limitcon30 = spr_fields_models.get_limitcon40(40)

        # значение поля advuser.js_struct
        dc_jsstruct = Com_proc_advuser.get_js_struct(user)

        # значения app_spr_fields_models.js_data
        dc_limit70 = spr_fields_models.get_limitcon70()
        dc_limit70 = dc_limit70.res_dict

        # инициализация переменных status.* для user_modf
        res_dict = dict()
        if levelperm_user == 40:   # если уровень доступа был 40
            res_dict['limitcon30'] = dc_jsstruct.get('limitcon') or 0
            res_dict.update(dc_limit70 ) # значения default for levelperm=70

        if levelperm_user == 70:  # если уровень доступа был 70 -> максНабор данных
            res_dict.update(dict(
                                limitcon    = dc_jsstruct.get('limitcon') or 0 ,
                                limitcon40  = dc_jsstruct.get('limitcon40') or 0,
                                limitcon70  = dc_jsstruct.get('limitcon70') or 0,
                                limitcon30  = limitcon30   # default for levelperm=40
                                 ))

        lst_lvperm = Com_proc_sprstatus.get_list_levelperm().res_list
        res_dict.update( dict(lvperm=lst_lvperm ) )
        s_limit = json.dumps(res_dict, ensure_ascii=True)

        dc_datauser = Com_proc_advuser.get_advData(user)
        dc_session = dict( lst_lvperm = lst_lvperm,
                       s_limit=s_limit,
                       upd_username=dc_datauser['username'],
                       upd_full_name=dc_datauser['full_name'],
                       upd_status=type_status.strIdent
            )

        request.session['UpdStatus_user'] = dc_session

        # инициализация limitcon30,  limitcon,limitcon40,limitcon70
        # через upd_status_user_01.js после загрузки контента html
        dc_initial = dict(status=type_status.statusID)
        form = UpdStatus_userForm(initial=dc_initial)

        return return_render(form, dc_session)


@login_required
def UpdPassword_user(request):
    """ Контроллер изменения пароля участника проекта
    url:updpswuser
    """

    from .serv_typestatus import type_status_user
    from .serv_sprstatus import Com_proc_sprstatus

    user = request.user
    type_status = type_status_user(user)

    if not type_status:
        return redirect_empty(arg_title='Статус',
                              arg_mes='Сервер остановил обработку: статус не определен ')


    if type_status.levelperm < 40 :
        return redirect_empty(arg_title='Нет прав',
                              arg_mes='Нет прав на создание профиля участника проекта')

    cache.set('item_navbar_active','item-navbar-profile')   #JS set adctive link


    if request.method == 'POST':
        form = UpdPassword_byHeadForm(request.POST)
        dc_session = request.session['UpdPassword_user']

        if form.is_valid():

            res_save = form.save(dc_session)

            if res_save:

                dict_cache = dict(username=dc_session['upd_username'], mes=res_save.mes)
                cache.set('Success_register_user', dict_cache)
                del request.session['UpdPassword_user']

                return redirect('ver_profil')  # переход на view Success_register_user

            else:
                # возврат формы на доработку и отображение сообщений об ошибках
                dc_cont = dict(form=form)
                dc_cont.update(dc_session)
                dc_cont.update(error=res_save.error )

            return render(request, 'advuser/upd_password_user.html', dc_cont)


        else: # возврат формы на доработку

            dc_cont = dict(form=form)  # отображение ошибок, выявленных на уровне валидации form
            dc_cont.update(dc_session)

            return render(request, 'advuser/upd_password_user.html', dc_cont)

    else:   # Обработка GET

        if not cache.has_key('UpdPassword_user'):
            return redirect_empty(arg_mes='Данные устарели')

        upd_username = cache.get('UpdPassword_user')
        cache.delete('UpdPassword_user')

        dc_cont = Com_proc_advuser.get_advData(upd_username)
        if dc_cont is None:
            return redirect_empty(arg_title='Нет данных',
                                  arg_mes='Сервер остановил обработку: нет данных для обработки ')


        form = UpdPassword_byHeadForm()
        kwargs=dict(username=upd_username)
        status = Com_proc_sprstatus.getStatus_or_None(**kwargs)

        dc_session = dict(
                       title='Изменение пароля пользователя проекта',
                       username_header=user.username,
                       full_name=user.get_full_name(),
                       statusInfo=type_status.strIdent,
                       upd_username=dc_cont['username'],
                       upd_full_name=dc_cont['full_name'],
                       upd_status=status.strIdent
            )

        request.session['UpdPassword_user'] = dc_session  # перенос данных из cache into session

        res_cont = dict(form=form)
        res_cont.update(dc_session)

        return render(request, 'advuser/upd_password_user.html', res_cont)


# Изменение пароля самими пользователями
# url: updpswbyUser
@login_required
def UpdPsw_byUser(request):
    """ Изменение пароля самими пользователями """

    from .serv_typestatus import type_status_user

    user = getUser(request.user)

    cache.set('item_navbar_active','item-navbar-profile')   #JS set adctive link

    if request.method == 'POST':

        form = UpdPsw_byUserForm(request.POST)
        form.data_username = user.username
        dc_session = request.session['UpdPsw_byUser']

        if form.is_valid():

            res_save = form.save(user)

            if res_save:

                dict_cache = dict(username=user.username, mes=res_save.mes)
                cache.set('Success_register_user', dict_cache)
                del request.session['UpdPsw_byUser']

                return redirect('ver_profil')  # переход на view Success_register_user

            else:
                # возврат формы на доработку и отображение сообщений об ошибках
                dc_cont = dict(form=form)
                dc_cont.update(dc_session)
                dc_cont.update(error=res_save.error )

            return render(request, 'advuser/upd_password_by_user.html', dc_cont)


        else: # возврат формы на доработку

            dc_cont = dict(form=form)  # отображение ошибок, выявленных на уровне валидации form
            dc_cont.update(dc_session)

            return render(request, 'advuser/upd_password_by_user.html', dc_cont)


    else:   # Обработка GET запроса

        type_status = type_status_user(user)
        dc_cont = Com_proc_advuser.get_advData(user)

        dc_session = dict(
                       title='Изменение пароля пользователя проекта',
                       upd_username=dc_cont['username'],
                       upd_full_name=dc_cont['full_name'],
                       upd_status=type_status.strIdent
            )

        request.session['UpdPsw_byUser'] = dc_session

        dc_init = dict(dataupd=user.username)
        form = UpdPsw_byUserForm(initial=dc_init)

        res_cont = dict(form=form)
        res_cont.update(dc_session)

        return render (request, 'advuser/upd_password_by_user.html' , res_cont)


@login_required
def AddProf_member(request):
    """Для рукГрупп -> создание профиля участников проекта."""


    # JS set adctive links не настроено !!!
    # в нужном месте установить код
    # cache.set('item_navbar_active','item-navbar-admpanel') # JS set active links


    from .serv_typestatus import type_status_user

    user = request.user
    type_status = type_status_user(user)

    if not type_status:
        return redirect_empty(arg_title='Статус', arg_mes='Сервер остановил обработку: статус не определен ')


    if type_status.levelperm < 40 :
        return redirect_empty(arg_title='Нет прав', arg_mes='Нет прав на создание профиля участника проекта')


    parentuser = Com_proc_advuser.get_user_cons(user)
    if parentuser is None:
        if user.is_superuser:
            parentuser = user
        else:
            return redirect_empty(arg_title='Сообщение сервера', arg_mes='Наставник не определен')


    cache.set('item_navbar_active','item-navbar-admpanel')

    if request.method == 'POST':
        form = AddProf_memberForm(request.POST)
        form.user_head = user

        if form.is_valid():
            res_save = form.save(user)

            if res_save:
                dict_cache = dict(username=res_save.any_str, mes=res_save.mes)
                cache.set('Success_register_user', dict_cache)

                return redirect('ver_profil')

            else:
                return render(request, 'advuser/regUser_ext.html', dict(
                            res=False,
                            parentuser=parentuser.username,
                            error=res_save.error,
                            title='Редактор профиля',
                            form=form
                            ))

        else:
            return render(request, 'advuser/regUser_ext.html', dict(
                            res=False,
                            parentuser=parentuser.username,
                            error='Ошибка/и заполнения полей формы',
                            title='Создание профиля',
                            form=form
                            ))

    else:

        # Загрузить данные из внешнего файла
        # используется при тестировании ввода
        #
        #from app import loadJSON_file_modf
        #dict_js = loadJSON_file_modf('advuser/arg_RegisterIns_profForm_member')
        #form = AddProf_memberForm(initial=dict_js)

        form = AddProf_memberForm()

        return render(request, 'advuser/regUser_ext.html', dict(
                            parentuser=parentuser.username,
                            res=True,
                            error='',
                            title='Создание профиля',
                            form=form
                            ))

# конец контроллеров адмПанели


def com_proc_render(arg_dc_cach:dict):
    """Общая процедура render.

    arg_dc_cach содержит ВСЕ параметры для обработки  return render
    ВСЕ параметры передаются через cach
    ---------------------------------------------------------------
    Структура arg_dc_cach:
        request  arg request from procViews
        dc_cont  dict контент
        str_html строка шаблона *.html
        str_err  строка ошибки вводится в arg_dict_cach
    """

    dc_cont = arg_dc_cach['dc_cont']
    request = arg_dc_cach['request']

    str_html = dc_cont['str_html']
    dc_err = arg_dc_cach.get('dc_err', None)

    del dc_cont['str_html']

    if dc_err is not None:
        dc_cont.update(dc_err)

    return render(request, str_html, dc_cont)


def Modf_prof_byheader(request):
    """Для рукГрупп -> изменение профиля участников проекта.

    url: updprofiluser
    name: updprofiluser
    Вместо RegisterExt_profForm"""


    # JS set adctive links не настроено !!!
    # в нужном месте установить код
    # cache.set('item_navbar_active','item-navbar-admpanel') # JS set active links



    from .modify_models import get_dictData_init_Form
    from .serv_advuser import Com_proc_advuser

    arg_dc_cach = dict(request = request)

    if request.method == 'POST':
        form = Modf_prof_byHeaderForm(request.POST)

        if 'Modf_prof_byheader' in request.session:
            dc_session  = request.session['Modf_prof_byheader']
            username    = dc_session['username_modf']
            parentuser  = dc_session['parentuser']

            dc_session['form'] = form
            arg_dc_cach['dc_cont'] = dc_session

        else:
            return redirect_empty(arg_title='Отказ сервера обработки запроса',
                arg_mes='Данные устарели: пользователь не определен' )


        if form.is_valid():

            res_save = form.save(username, parentuser)
            if res_save:

                #Success_register_user заполнение cache
                dict_cache = dict(username=username, mes=res_save.mes)

                cache.set('Success_register_user', dict_cache)
                del request.session['Modf_prof_byheader']

                return redirect('ver_profil')  # переход на view Success_register_user

            else:
                arg_dc_cach.update(dict(
                        dc_err=dict(error=res_save.error) ))
                return  com_proc_render(arg_dc_cach)

        else:
            arg_dc_cach.update(dict(
                dc_err=dict(error='Проверьте введенные данные') ))
            return  com_proc_render(arg_dc_cach)


    else:  # GET запрос
        try:
            # cache инициализируется из AdvPanel_prof
            if not cache.has_key('Modf_prof_byheader'):
                return redirect_empty(arg_title='Отказ сервера обработки запроса',
                    arg_mes='Данные устарели: пользователь не определен')

            parentuser = request.user
            username = cache.get('Modf_prof_byheader')

            cache.delete('Modf_prof_byheader')

            res_verify = Com_proc_advuser.verify_yourHead(username, parentuser)
            if not res_verify:
                if res_verify.mes: # сообщение для отображения
                    return redirect_empty(res_verify.mes)
                else:
                    return redirect_empty(arg_title='Отказ сервера обработки запроса', arg_mes='Процедура обработки остановлена на сервере')

            # Выполняется проверка привилегий parentuser
            dict_param = get_dictData_init_Form(parentuser.pk, username)
            if dict_param:

                # Словарь параметров создается один раз и помещается в session
                # Обработка POST: настройки считываются из dict from session
                dc_session = dict(
                    str_html = 'advuser/regUser_ext.html',
                    parentuser=parentuser.username,
                    username_modf = username,
                    res=False,
                    #error='',
                    title='Редактор профиля',
                    form=None
                    )

                request.session['Modf_prof_byheader'] = dc_session

                dc_cont = dc_session.copy()

                dict_initial = dict_param.res_dict
                dict_initial = modf_data_dict(dict_initial)  # сброс значений '' or 'empty'

                form = Modf_prof_byHeaderForm(initial=dict_initial)

                dc_cont.update(dict(form=form, res=True))

                # dict для обобщенной процедуры com_proc_render
                arg_dc_cach.update(dict(
                                dc_err=dict(error=''),
                                dc_cont=dc_cont
                                ))

                return com_proc_render(arg_dc_cach)

            else:
                return  redirect_empty(arg_title='Отказ сервера обработки запроса', arg_mes=dict_param.error)

        except Exception as ex:
            return redirect_empty()


"""
Изменение профиля самими участниками проекта proj_member
"""
@login_required
def Modf_prof_byuser(request):
    """ Изменение профиля самими участниками проекта """

    user = request.user
    parentuser = Com_proc_advuser.get_user_cons(user)
    if parentuser is None:
        return redirect_empty(arg_mes='Сервер отклонил обработку: наставник не определен' )

    cache.set('item_navbar_active','item-navbar-profile')

    if request.method == "POST":
        form = Modf_prof_byuserForm(request.POST)
        if form.is_valid():
            res_save = form.save(user.username, parentuser)
            if res_save:

                #Success_register_user заполнение cache
                dict_cache = dict(username=user.username, mes=res_save.mes)

                cache.set('Success_register_user', dict_cache)

                return redirect('ver_profil')  # переход на view Success_register_user

            else:
                return render(request, 'advuser/regUser_ext.html', dict(
                            parentuser=parentuser.username,
                            res=False,
                            error=res_save.error,
                            title='Редактор профиля',
                            form=form
                            ))

        else:
            return render(request, 'advuser/regUser_ext.html', dict(
                            parentuser=parentuser.username,
                            res=False,
                            error='Проверьте введенные данные',
                            title='Редактор профиля',
                            form=form
                            ))
    else:
        try:

            dict_param = dict()

            if not Com_proc_advuser.get_advData_user(user, dict_param) :
                return redirect_empty(
                        arg_title='Отказ сервера',
                        arg_mes='Нет данных для обработки' )

            dict_param = modf_data_dict(dict_param)  # сброс значений '' or 'empty'
            form = Modf_prof_byuserForm(initial=dict_param)

            dc_cont = dict(
                            parentuser=parentuser.username,
                            res=True,
                            title='Редактор профиля',
                            form=form
                            )

            return render(request, 'advuser/regUser_ext.html', dc_cont)

        except Exception as ex:
            return redirect_empty()


"""Контроллер обр-ки запроса на создание профиля гостевогоВхода.

url: /advuser/addprofquestins   /advuser/addprofquestupd
"""
@login_required
def AddProf_quest(request):
    """ Добавление/изм профиля клиента """

    from .serv_advuser import type_status_user, Com_proc_advuser


    user = request.user
    parentuser = Com_proc_advuser.get_user_cons(user)
    if parentuser is None:
        return redirect_empty(arg_mes='Наставник не определен')


    cache.set('item_navbar_active','item-navbar-profile')

    if request.method == 'POST':

        form = Base_profForm(request.POST)

        # dict по умолчанию для сообщений об ошибках
        dc_cont_err = dict(
            res=False,
            parentuser=parentuser.username,
            error= 'Сервер отклонил обработку. Проверьте введенные данные',
            title='Создание профиля',
            form=form
            )

        if form.is_valid():
            user = getUser(request.user)

            res_save = form.save_add(user)
            if res_save:  # успешное обновление

                #Success_register_user заполнение cache
                dict_cache = dict(username=res_save.any_str, mes=res_save.mes)
                cache.set('Success_register_user', dict_cache)

                return redirect('ver_profil')

            else:  # ошибка обработки
                dc_cont_err.update(dict(error=res_save.error))
                return render(request, 'advuser/regUser_ext.html', dc_cont_err)


        return render(request, 'advuser/regUser_ext.html', dc_cont_err )

    else:   # Обработка создания профиля клиента
        type_status = type_status_user(user)
        if not type_status:
            return redirect_empty(arg_title='Статус', arg_mes='Нет данных статуса')

        if type_status.levelperm == 10:

            form = Base_profForm()

            return render(request, 'advuser/regUser_ext.html', dict(
                                parentuser=parentuser.username,
                                res=True,
                                error='',
                                title='Создание профиля',
                                form=form
                                ))
        else:
            return redirect_empty(arg_mes='Нет прав. Только для гостевого входа')


def UpdProf_quest(request):
    """ Изменение профиля клиента самим пользователем """

    from .serv_advuser import type_status_user, Com_proc_advuser


    user = request.user
    parentuser = Com_proc_advuser.get_user_cons(user)
    if parentuser is None:
        return redirect_empty(arg_mes='Наставник не определен')


    if request.method == 'POST':

        form = Base_profForm(request.POST)
        if form.is_valid():
            user = getUser(request.user)

            res_save = form.save_upd(user, parentuser)
            if res_save:  # успешное обновление

                #Success_register_user заполнение cache
                dict_cache = dict(username=res_save.any_str, mes=res_save.mes)
                cache.set('Success_register_user', dict_cache)

                return redirect('ver_profil')

            else:  # ошибка обработки
                return render(request, 'advuser/regUser_ext.html', dict(
                            res=False,
                            parentuser=parentuser.username,
                            error= res_save.error,
                            title='Обновление профиля',
                            form=form
                            ))

        else:  # Не прошла валидация данных
            return render(request, 'advuser/regUser_ext.html', dict(
                            res=False,
                            parentuser=parentuser.username,
                            error='Ошибка заполнения полей формы',
                            title= 'Обновление профиля' ,
                            form=form
                            ))

    else:
        # Проверка, кто делает запрос
        type_status = type_status_user(user)
        if not type_status:
            return redirect_empty(arg_title='Статус', arg_mes='Нет данных статуса')

        from .modify_models import get_dictData_init_Form_regQuest

        if not (type_status.levelperm == 20):
            return redirect_empty(arg_mes='Только для зарегистрированных клиентов')

        dict_param = dict()

        if not Com_proc_advuser.get_advData_user(user, dict_param) :
            return redirect_empty(
                    arg_title='Отказ сервера',
                    arg_mes='Нет данных для обработки' )

        dict_param = modf_data_dict(dict_param) # сброс значений '' or 'empty'
        form = Base_profForm(initial=dict_param)

        return render(request, 'advuser/regUser_ext.html', dict(
                        parentuser=parentuser.username,
                        res=True,
                        title='Редактор профиля',
                        form=form
                        ))


"""
Используется для отображения результатов регистрации клиента на сайте
url: ver_profil/
"""
@login_required
def Success_register_user(request):
    """ Подтверждение успешной регистрации
    Изменений профиля
    изменений levelperm status.*
    """

    if 'Success_register_user' not in cache:
        return redirect('/')  # На случай, если делается попытка перезапуска

    dict_cache = cache.get('Success_register_user')
    user = dict_cache.get('username')
    mes  = dict_cache.get('mes')

    cache.delete('Success_register_user')

    prof = Com_proc_advuser.get_profil_user(user)
    if prof:
        cont = prof.res_dict
        cont.update(dict(mes=mes))
        return render(request, 'advuser/prof_conf_modf.html', cont)
    else:
        return redirect_empty(arg_title='Профиль')


def Table_profils_lev30(request, page):
    """ View для отображения списка профилей в таблФорме
    Предназначена для менеджеров
    url: advuser/listprof_lvl30/<str:page>/
    """

    from .modify_models import get_list_prof_memb
    # from advuser.serv_typestatus import type_status_user
    # from .forms import Templ_profForm

    user = request.user
    # type_status = type_status_user(user)

    res_data_prof = get_list_prof_memb(user, arg_list='10,20,30', num_rows=5, sel_page=page)
    if res_data_prof is None:
        redirect_empty('Нет данных для просмотра')

    res_list = res_data_prof.res_list
    if res_list is None:
        return redirect_empty(arg_title='Сообщение сервера', arg_mes='Нет данных построения списка')

    dc_page = res_data_prof.res_dict


    num_pages = []
    num = 1
    while num <= dc_page['num_pages']:
        num_pages.append(num)
        num +=1

    cont = dict(
        rows=res_list, dc_page=dc_page, num_pages=num_pages, filter=filter)

    cache.set('item_navbar_active','item-navbar-admpanel')

    return render(request, 'advuser/prof_table_format_short_ext.html', cont)



@login_required
def List_profils(request, page, filter):
    """List_profils.

    url:  listprofils
    name: listprofils
    ------------------------
    Табличная форма показа менеджеров"""

    from .modify_models import get_list_prof_memb
    from advuser.serv_typestatus import type_status_user


    return redirect('listprof_lvl30', page=page)

    # Полный сервис управления временно не доступен
    # из-за неподготовленности рукПроекта


    user = request.user
    type_status = type_status_user(user)
    if type_status.levelperm < 40:
        return redirect_empty(arg_title='Уровень прав', arg_mes='Нет прав на просмотр данных')

    filter_sp = filter.replace('-',',')


    # изменение 24.07.2020  использование пагинатора
    res_data_prof = get_list_prof_memb(user, arg_list=filter_sp, num_rows=5, sel_page=page)
    if res_data_prof is None:
        redirect_empty('Нет данных для просмотра')

    res_list = res_data_prof.res_list
    if res_list is None:
        return redirect_empty(arg_title='Сообщение сервера', arg_mes='Нет данных построения списка')

    dc_page = res_data_prof.res_dict
    num_pages = []
    num = 1
    while num <= dc_page['num_pages']:
        num_pages.append(num)
        num +=1

    cont = dict(
        rows=res_list, dc_page=dc_page, num_pages=num_pages, filter=filter)

    return render(request, 'advuser/prof_table_format.html', cont)
    #return render(request, 'advuser/prof_table_format_short_ext.html', cont)



@login_required
def Index(request):
    # from .serv_typestatus import type_status_user

    return render(request, 'advuser/index.html')


# url из nltest.urls
# # path('profile/', Profile, name='profile' ),
@login_required
def Profile(request):
    from .serv_advuser import Com_proc_advuser

    prof = Com_proc_advuser.get_profil_user(request.user)
    if prof:

        cache.set('item_navbar_active','item-navbar-profile')

        if prof.res_obj.levelperm == 10:
            cont = dict(prof=prof.res_dict['prof'])

            return render(request,'advuser/prof_quest.html', cont )

        else:
            return render(request, 'advuser/profile_user.html', prof.res_dict)

    else:
        idmes = empty_mes.CreateEMPTY_mes(prof.error, 'Отказ сервера')
        return redirect('empty', mes=idmes)


def Redir_upd_prof_listProf(request, mes):
    """Перенаправление на редактирование профиля из списка.
    url: updmesdata<str:mes>  name:updmesdata
    """

    user = request.user

    parentuser = Com_proc_advuser.get_user_cons(mes)
    if parentuser is None:
        return redirect_empty(arg_mes='Наставник не определен')

    if user.username != parentuser.username:
        return redirect_empty(arg_title='Права редактирования', arg_mes='Нет прав на редактирование профиля')

    cache.set('AdvPanel_prof', mes)

    return redirect ('modpanelprof')    # перенаправление на AdvPanel_prof


"""
Перенаправление
    для доступа к редактированию профиля пользователя
"""
@login_required
def Redir_updprof(request):
    """ Перенаправление на редактПрофиля самими участниками проекта """

    from .serv_advuser import type_status_user

    user = request.user
    type_status = type_status_user(user)

    if type_status.levelperm == 10:
        return redirect('addprofquest')

    elif type_status.levelperm == 20:
        return redirect('updprofquest')

    else:
        # Обновление профиля участниками проекта
        cache.set('Upd_prof_member', user.username)
        return redirect('modf_prof_byuser')
