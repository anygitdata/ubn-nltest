from django import forms
from django.contrib.auth.models import User
from django.core import validators
from django.core.exceptions import ValidationError
import json
from django.db import transaction

from .models import AdvUser, SprStatus

from .serv_sprstatus import Com_proc_sprstatus
from .serv_advuser import Struct_default_AdvUser, Com_proc_advuser, POL, GET_MES, ID_COMMAND
from app import (ErrorRun_impl, getUser, getLogin_cl, getPassword_cl, 
                 get_valFromDict, Res_proc)
from app import PM_write_except_into_log as write_into_log, PM_run_raise as run_raise

from app.com_data.any_mixin import verify_exists_email,  verify_exists_email_ext 
from app.com_data.proc_send_email import send_simpl_email

from .modify_models import Modify_user, Modify_advuser
from .serv_typestatus import type_status_user


# Удаление начальных/конечных пробелов in dict
def clear_space(arg_dict:dict)->dict:
    """ Удаление начальных/конечных пробелов в элементах словаря """    
    res = arg_dict
    lst = ('email', 'parentuser', 'username', 'first_name', 'last_name','idcomp')
    for item in lst:
        if res.get(item):
            res[item] = res[item].strip()            

    return res


def upd_space_into_empty(arg_dict:dict)->dict:
    """ Преобразование значений None or '' -> empty """
    keys = arg_dict.keys();
    for key in keys:
        if arg_dict.get(key) is None or arg_dict.get(key) == '':
            arg_dict[key] = 'empty'
    return arg_dict


# Изменение password участников проекта
class UpdPassword_byHeadForm(forms.Form):
    """ Форма изменения пароля на уровне руководителя группы """

    password = forms.CharField(label='Введите пароль', max_length=50, widget=forms.PasswordInput())
    password2 = forms.CharField(label='Повторите пароль', max_length=50, widget=forms.PasswordInput())

    # Верификация паролей на уровне формы 
    def clean(self):
        from django.contrib.auth.hashers import check_password

        super().clean()
        errors = {}

        password = self.cleaned_data['password']
        password2 = self.cleaned_data['password2']        

        if password != password2:
            errors['password'] = ValidationError('Пароли не совпадают')
                    
        if errors:
            raise ValidationError(errors)


    def save(self, arg_session:dict)->Res_proc:
        """ Сохранение пароля пользователя проекта
      arg_session используется для значений upd_username """

        from django.contrib.auth.hashers import make_password
        from app.com_serv_dbase.serv_modf_profil import user_upd_psw

        res_save = Res_proc()

        try:
            cd_clean = self.cleaned_data

            user = getUser(arg_session['upd_username'])
            if user is None:
                run_raise('Логин не определен', showMes=True)
            
            #user.password = make_password(cd_clean['password'])

            type_status = type_status_user(user);
            statusID = type_status.statusID
            pswcl = None
            if type_status.levelperm >=30:
                pswcl = Com_proc_advuser.get_val_from_advData(user, 'pswcl')

            dc_sp = dict(
                username = user.username,
                password = make_password(cd_clean['password']),
                pswcl    = pswcl or 'empty',
                status_id   = statusID
                )

            res_proc = user_upd_psw(dc_sp);            
            res_save.mes = 'Пароль пользователя изменен'

            #user.save()
            #res_save.res = True

            res_save.mes = 'Пароль пользователя обновлен'

        except Exception as ex:
            res_save.error = ex

        return res_save


# Изменение пароля предназначено для пользователей
class UpdPsw_byUserForm(UpdPassword_byHeadForm):
    """ Форма изменения пароля самими пользователями """

    datapsw_base = forms.CharField(label='Начальный пароль', max_length=50, widget=forms.PasswordInput())    
        
    field_order = ['datapsw_base','password','password2']

    # верификация ввода пароля на уровне формы
    def clean(self):
        from django.contrib.auth.hashers import check_password

        super().clean()
        errors = {}

        password = self.cleaned_data['password']
        password2 = self.cleaned_data['password2']
        datapsw_base = self.cleaned_data['datapsw_base']

        password_encode = getUser(self.data_username).password

        if not check_password(datapsw_base, password_encode ) :  # Проверка ввода исходного пароля
            errors['datapsw_base'] = ValidationError('Введите правильный начальный пароль')

        if password != password2:
            errors['password'] = ValidationError('Пароли не совпадают')
                    
        if errors:
            raise ValidationError(errors)

    def save(self, arg_user:User)->Res_proc:
        """ Сохранение пароля пользователя проекта
      arg_user используется для значений password from User """

        from django.contrib.auth.hashers import make_password
        from app.com_serv_dbase.serv_modf_profil import user_upd_psw

        res_save = Res_proc()

        try:

            psw = self.cleaned_data['password']
            password = make_password(psw)
            
            user = getUser(arg_user)            
            status = Com_proc_sprstatus.getStatus_or_None(user);

            dc_sp = dict(
                username = user.username,
                password = password,
                pswcl    = psw,
                status_id   = status.pk
                )

            res_proc = user_upd_psw(dc_sp);            
            res_save.mes = 'Пароль пользователя изменен'

        except Exception as ex:
            res_save.error = ex

        return res_save


class UpdStatus_userForm(forms.Form):
    """ Верификация и сохранение изменений status_id """

    from collections import namedtuple

    status = forms.ModelChoiceField(label='Статус', 
                    widget=forms.Select(attrs={"class":"form-control"}),
                    empty_label='--- Выберите статус ---',
                    queryset = SprStatus.objects.order_by('levelperm').filter(levelperm__gt=10, levelperm__lt=100).exclude(status='proj-sadm') )

    limitcon30 = forms.IntegerField(label='Лимит подкл.', 
                    help_text='Лимит подключений',
                    required=False,  
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Лимит подключений"}))

    limitcon = forms.IntegerField(label='Лимит подкл.', 
                    help_text='Лимит подключений',
                    required=False,  
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Лимит подключений"}))

    limitcon40 = forms.IntegerField(label='Лимит подкл. рукГрупп', 
                    help_text='Лимит подключений',
                    required=False,  
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Лимит подкл. рукГрупп"}))

    limitcon70 = forms.IntegerField(label='Лимит подкл. супер-РукГр', 
                    help_text='Лимит подключений',
                    required=False,  
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Лимит супер-РукГр"}))


    # -------------- Блок локальных переменных ---------------
    # используются в процедуре clean(self)
    param_verf = namedtuple("param_verf", "user_head user_modf")
    
    #dc_param_verf = None инициализация из views form.dc_param_verf = form.param_verf(user_head=user_head.username, user_modf=dc_session['upd_username'])
    @property
    def PR_dc_param_verf(self):
        # Начальная инициализация из views 
        # form.param_verf(user_head=user_head.username, user_modf=dc_session['upd_username'])
        return self.dc_param_verf

    @property
    def PR_list_fields_status(self):
        """ используется в clear_data_status список используемых полей         
        для status.* 
        """
        return self.list_fields_status   

    def get_limit_used(self, arg_levelperm_sel:int):
        """ Используется для clean 
        Определяет разницу введенных значений по отношению к введенных в БД
        """

        from collections import namedtuple
        from app.models import spr_fields_models as fields
        import sys
        from .serv_sprstatus import Com_proc_sprstatus

        user_head = self.PR_dc_param_verf.user_head #  dc_cleaned['user_head']
        user_modf = self.PR_dc_param_verf.user_modf # dc_cleaned['user_modf']
        user = getUser(user_modf)

        dc_status = Com_proc_sprstatus.get_list_levelperm()
        dc_status = dc_status.res_list  # Список dict используемых status.levelperm 
        
        limit_max = sys.maxsize
        dc_cleaned = self.cleaned_data;

        # Локальный процедурный контент
        def loc_get_status(arg_level:int)->str:
            """ Локальная функция выборки значения из dc_status """

            res = [ item for item in dc_status if item['lvperm'] == arg_level][0]['status']
            
            return res;

        def loc_get_used_limit(arg_level:int)->int:
            """ Локальная функция обработки использованного лимита  """

            status_level = [ item for item in dc_status if item['lvperm'] == arg_level][0]['status']
            row = AdvUser.objects.filter(parentuser=user_head, 
                                    status=loc_get_status(arg_level)).exclude(pk=user)
            return row.count()

        # Конец блока локального процедурного контента 


        use_limit = namedtuple('use_limit', 
                        'used30 limit30 used40 limit40 used70 limit70', 
                        defaults=(0,0,0,0))

        res_limit = None

        status_head = type_status_user(user_head)
        levelperm_head = status_head.levelperm
        
        if arg_levelperm_sel == 40:
            if levelperm_head < 100:
                used30 = loc_get_used_limit(30) # row.count()
                limit30 = fields.get_limitcon40(40)
            else:
                used30 = 0
                limit30 = limit_max
                
            res_limit = use_limit(
                used30 = used30,
                limit30 = limit30
                )

        if arg_levelperm_sel == 70:
            if levelperm_head < 100:
                dc_limit70 = fields.get_limitcon70()     
                dc_limit70 = dc_limit70.res_dict
                
                used30 = loc_get_used_limit(30)
                used40 = loc_get_used_limit(40)
                used70 = loc_get_used_limit(70)
                limit30 = dc_limit70.get('limitcon') or 0
                limit40 = dc_limit70.get('limitcon40') or 0
                limit70 = dc_limit70.get('limitcon70') or 0

            else:
                used30 = used40 = used70 = 0
                limit30 = limit40 = limit70 = limit_max

            res_limit = use_limit(
                    used30= used30, 
                    limit30= limit30,
                    used40= used40, 
                    limit40= limit40,
                    used70= used70,
                    limit70= limit70
                    )
            

        return res_limit
    
    # ----------- Конец блока локальных переменных -------------

    
    # Проверка введенных данных на уровне формы
    def clean(self):
        
        import sys

        super().clean()
        errors = {}
    
        # используется в clear_data_status  self.PR_list_fields_status
        self.list_fields_status = []  

        dc_cleaned = self.cleaned_data;

        user_head = getUser(self.PR_dc_param_verf.user_head)
        user_modf = getUser(self.PR_dc_param_verf.user_modf)

        status_head = type_status_user(user_head)        
        status_user_base = type_status_user(user_modf)

        levelperm_user_base = status_user_base.levelperm
        levelperm_sel = dc_cleaned['status'].levelperm
        levelperm_head = status_head.levelperm

        if levelperm_sel > levelperm_head:
            errors['status'] = 'Статус больше допустимого'

        if levelperm_sel == 40: #верификация заполнения поля limitcon30
            if not dc_cleaned.get('limitcon30'):
                errors['limitcon30'] = 'Укажите кол-во подключений менеджеров'
            
        if levelperm_sel == 70: # Проверка прав 
            if not dc_cleaned.get('limitcon'):
                errors['limitcon'] = 'Укажите кол-во подключений менеджеров'
            if not dc_cleaned.get('limitcon40'):
                errors['limitcon40'] = 'Укажите кол-во подключений рукГрупп'

        # верификация резкого повышения/понижения levelperm
        num = 1
        dc_levelperm = {}
        for item in (20, 30, 40, 70) :
            dc = {item:num }
            dc_levelperm.update(dc)
            num += 1

        # Определение величины перехода levelperm относительно исходного значения
        div = dc_levelperm[levelperm_sel] - dc_levelperm[levelperm_user_base]
        if  abs(div) > 1:
            errors['status'] = 'Изменение статуса более чем на один порядок - отклонено'

        # верификация на уровне levelperm
        if not errors:
        
            if levelperm_sel > 30:  
                if levelperm_sel == 40:
                        
                    dc_limit_used40 = self.get_limit_used(40) 

                    # Верификация введенных значений limitcon для levelperm_sel=40
                    if dc_limit_used40.limit30 < (dc_limit_used40.used30 + dc_cleaned['limitcon30']) :
                        errors['limitcon30'] = 'Превышен лимит подключений'

                if levelperm_sel == 70:

                    # словарь типа nametuple используемых/назначенных лимитов
                    dc_limit_used70 = self.get_limit_used(70)  

                    # Верификация введенных значений limitcon для levelperm_sel = 70
                    if dc_limit_used70.limit30 < dc_limit_used70.used30 + dc_cleaned['limitcon']:
                        errors['limitcon'] = 'Превышен лимит подключений'

                    if dc_limit_used70.limit40 < dc_limit_used70.used40 + dc_cleaned['limitcon40'] :
                        errors['limitcon40'] = 'Превышен лимит подключений'

                    if dc_cleaned.get('limitcon70') and (dc_limit_used70.limit70 < (dc_limit_used70.used70 + dc_cleaned['limitcon70'])):
                            errors['limitcon70'] = 'Превышен лимит подключений'

        if errors:
            raise ValidationError(errors)


    def clear_data_status(self, arg_dict:dict):
        """ Удаление данных, связанных с status.* 
            обнуление данных js_struct and advData, входящих в структуру status.*
        """
        from app.models import spr_fields_models as fields

        if not self.PR_list_fields_status:
            # Заполнение self.list_fields_status
            row = fields.objects.filter(id_key=0)
            if row.exists():
                row_fields = row.first()
            else:
                run_raise('Сервер отклонил запрос', showMes=True)

            dc_fields = json.loads(row_fields.js_data)
            self.list_fields_status = dc_fields['fields']['status']

        for key in self.PR_list_fields_status:
            if arg_dict.get(key):
                del arg_dict[key]


    def save_status_into_db(self, arg_dict:dict, arg_user:User):
        """ Запись изменений status в БД увеличение статуса 
        или изменении структуры status.*
        """

        res_proc = Res_proc()

        try:

            rec = AdvUser.objects.get(pk=arg_user)

            js_struct = arg_dict['js_struct']
            status_id = arg_dict['status_id']

            advData = json.loads(rec.advData)  
            self.clear_data_status(advData)     # очистить от прежних значений status.*
        
            advData.update(js_struct)   # Обновление новыми значениями status.*

            advData.update(dict(
                status_id=status_id, 
                status=status_id))
            rec.status_id = status_id

            rec.js_struct = json.dumps(js_struct, ensure_ascii=False)
            rec.advData = json.dumps(advData, ensure_ascii=False)

            rec.save()            

            res_proc.res = True

        except Exception as ex:
            res_proc.error = ex

        return res_proc
    

    def save_status_resume_into_db(self, arg_dict:dict):
        """ Запись изменений статуса в БД при понижении статуса  """
        from app.com_serv_dbase.serv_modf_profil import sp_modf_data

        res_proc = Res_proc()
        try:
            res_sp = sp_modf_data(arg_dict, serv_proc='sp_user_upd_status_reduce')
            if not res_sp:
                res_proc.error = res_sp.error
                return res_proc

            res_proc.res_dict = res_sp.res_dict
            res_proc.res = True

        except Exception as ex:
            res_proc.error = ex        

        return res_proc      


    def save_data_status(self, arg_head, arg_session)->Res_proc:
        """ Процедура на уровне class -> сохранение изменений status_id/limitcon 
        вызывается из views.UpdStatus_user url:updpermuser
        """

        # Структура arg_session
        #lst_lvperm = lst_lvperm,
        #s_limit=s_limit,
        #upd_username=dc_datauser['username'],
        #upd_full_name=dc_datauser['full_name'],
        #upd_status=type_status.strIdent

        res_proc = Res_proc()

        try:

            dc_clean = self.cleaned_data;

            user_head = getUser(arg_head)
            user_modf = getUser(arg_session['upd_username'])
            status_head = type_status_user(user_head)
        
            levelperm_sel = dc_clean['status'].levelperm
            levelperm_head = status_head.levelperm
            levelperm_user_base = type_status_user(user_modf).levelperm

            # Предварительное заполнение dict for update model advUser
            status_id = dc_clean['status'].pk

            dc_servproc = dict(
                               user_modf=user_modf.username, 
                               status_id=status_id,
                               status = status_id
                               )

            js_struct = Com_proc_advuser.get_js_struct(user_modf)
            self.clear_data_status(js_struct)  # Удаление всех данных, связанных со status.*

            if levelperm_sel < 30:
                if js_struct.get('pswcl'):   del js_struct['pswcl']
                if js_struct.get('logincl'): del js_struct['logincl']


            # Блок подготовки данных для сохранения изменений в БД
            if levelperm_sel < levelperm_user_base: # Понижение привелигий

                user_head70 = Com_proc_advuser.get_head70_user(user_modf).username

                if levelperm_sel == 40:
                    js_struct['limitcon'] = dc_clean['limitcon30']
                    lst = [70,40]

                elif levelperm_sel in (20, 30):
                    if levelperm_sel == 30:
                        lst = [70,40,30]
                    else:
                        lst = [70,40,30,20,10]
                
                dc_servproc['js_struct'] = js_struct
                dc_servproc['lst'] = lst
                dc_servproc['user_head'] = user_head70 # рукГруппы на кого переводить структуру
                
                res_proc = self.save_status_resume_into_db(dc_servproc)

            # ---------- Конец контента обработки понижения статуса


            # блок обработки повышения статуса или только изменение параметров status.*
            if levelperm_sel > levelperm_user_base or levelperm_sel == levelperm_user_base :

                if levelperm_sel == 40:
                    js_struct['limitcon']= dc_clean['limitcon30']

                elif levelperm_sel == 70:
                    js_struct.update(dict(
                        limitcon=dc_clean['limitcon'],
                        limitcon40=dc_clean['limitcon40'],
                        limitcon70=dc_clean.get('limitcon70') or 0,
                        user_head = user_head.username   # рукГруппы проводивший изменения профиля
                        ))

                #dc_servproc['advData'] = advData
                dc_servproc['js_struct'] = js_struct                

                # Обновление данных через сервис django
                res_sp = self.save_status_into_db(dc_servproc, user_modf)
                if not res_sp:
                    res_proc.error = res_sp.error

                res_proc.res = True
                res_proc.res_dict = dict(mes='Обновлен статус', 
                                         data_mes=f'Статус {user_modf} обновлен ')
            

        except Exception as ex:
            res_proc.error = ex

        return res_proc



# используется для подтверждения перед удалением профиля
class AdvPanel_form(forms.Form):
    proj_memb  = forms.CharField(label='Логин менеджера', max_length=50, 
                    widget=forms.TextInput(
                        attrs={"class":"form-control", 
                               "placeholder":"Участник проекта",
                               "disabled" : "disabled"             
                               }) ) 


# Для руководителей проекта
# addprof_member
class AdvPanel_profForm(forms.Form):
    id_command = forms.ChoiceField(label='Метод обработки',                     
                    choices=ID_COMMAND,widget=forms.RadioSelect())
    proj_memb  = forms.CharField(label='Логин менеджера', max_length=50, 
                widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Участник проекта"}) ) 


class Templ_profForm(forms.Form):
    """ Общий шаблон Форм """

    # -------------- Поля формы для модели User ------------

    first_name = forms.CharField(label='Имя', max_length=50, 
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Имя"}) ) 
    last_name  = forms.CharField(label='Фамилия', max_length=50,
                    widget=forms.TextInput(attrs={"class":"form-control",  "placeholder":"Фамилия"}) )
    email      = forms.EmailField(label='Эл. почта', max_length=50, 
                    required=False,
                    widget=forms.TextInput(attrs={"class":"form-control",  "placeholder":"Адрес элПочты" }),
                    help_text='Обратная связь, восстановление пароля')

    # ------------ Поля формы для модели AdvUser ---------------

    phone       = forms.CharField(label='Телефон', max_length=15,
                    required=False,
                    help_text = 'Обратная связь',
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Телефон" }) )    
    idcomp      = forms.CharField(label='ID компании',
                    help_text='Для зарегистрированных клиентов',
                    required=False,
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"ID компании" } ))
    post        = forms.IntegerField(label='ПочтИндекс', 
                    help_text='Регион клиента',
                    required=False,  
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Почтовый индекс"}))    
    pol         = forms.ChoiceField(label='Пол', choices=POL,widget=forms.RadioSelect())
   
    ageGroup    = forms.IntegerField(label='Возраст',
                    required=False,
                    help_text = 'Важно, для отбора подаваемой информации!',
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Возраст" }) )  


    @classmethod
    def get_dict_conv_field(cls):
        """ Конвертрор используемых имен полей, отображаемые в html 
        --------------------------------------------------------
        Обработке подлежат только те поля, которые могут иметь значение 'Нет'

        return dict(namefield=КонвОбозначение)
        """

        res = dict(post='Индекс: Нет', idcomp='IDcomp: Нет', phone='Тел: Нет', email='email: Нет' )
        return res


    @classmethod
    def conv_dict_for_html(cls, arg_list):
        """ Сканирование и преобразование arg_dc по ключам совпадающим из Get_dict_conv_field()
        return convDict from arg_dc
        """

        dc_templ = cls.get_dict_conv_field()
        lst_modf = arg_list

        for item in lst_modf:
            for key in item.keys():

                if key in dc_templ and item[key].lower() == 'нет':
                    item[key] = dc_templ[key]

        s = json.dumps(lst_modf, ensure_ascii=False)
        return lst_modf


    @classmethod
    def com_modf_quest(cls, arg_head, arg_jsstruct=None, new_pswd=False)->dict:
        """ Обобщенная процедура обработки quest
        верификация/изменение 
        pswcl and logincl
        ---------------------------
        arg_head  используется для загрузки pswcl and logincl as default
        arg_user для загрузки js_struct 
        arg_user==None создается js_struct else loadFrom advuser_advuser.js_struct
        return js_struct
        """
        
        js_struct = dict()

        if arg_jsstruct:
            js_struct = arg_jsstruct
        
        if new_pswd:
            js_struct['pswcl'] = getPassword_cl()
            js_struct['logincl'] = getLogin_cl()

        else:
            user_head = getUser(arg_head)
        
            if Res_proc.FN_get_val_dict(js_struct, 'pswcl') is None:
                    js_struct_head = Com_proc_advuser.get_js_struct(user_head)
                    js_struct['pswcl'] = js_struct_head['pswcl']
            if Res_proc.FN_get_val_dict(js_struct, 'logincl') is None:
                    js_struct['logincl'] = getLogin_cl()



        return js_struct


    # dict описатель полей namefields -> descriptions используется в com_clean
    dc_descr_fields = None

    # список полей для верификации. Используется as default в com_clean
    lst_fields = ('first_name','last_name','email','phone','post','idcomp')

    @classmethod
    def get_descr_fields(cls)->dict:
        """ Возвращает объект dict dc_descr_fields """

        from collections import namedtuple

        if cls.dc_descr_fields is None:
            dc_descr_fields = dict(
                email='Эл. почта',
                phone='Телефон',
                idcomp='ID компании',
                post='Почт. индекс',
                ageGroup='Возр. группа',
                sendMes='Получать сообщ.',
                first_name='Имя',
                last_name='Фамилия'
                )

            cls.dc_descr_fields = dc_descr_fields

        return cls.dc_descr_fields


    @classmethod
    def com_clean(cls, arg_clean, arg_list=None)->dict:
        """ Общая процедура верификации 
        arg_clean dict self.cleaned_data
        arg_list  список полей для верификации
        return errors ={...}
        """

        errors = {}
        dc_descr = cls.get_descr_fields()   # Описатель полей nameField -> descr

        if arg_list is None: arg_list = cls.lst_fields

        for item in arg_list:
            if not arg_clean.get(item):
                errors[item] = f'Не заполнено поле {dc_descr[item]}'

        return errors


"""
Базовый класс для редактирования данных профиля
"""
class Base_profForm(Templ_profForm):
    """ Форма для клиентов  """

    sendMes     = forms.ChoiceField(label='Получать сообщ.', 
                    help_text = 'Интересная информация, восстановление пароля',
                    choices=GET_MES,
                    widget=forms.RadioSelect())

    def clean(self):
        
        super().clean()
        errors = {}
        
        dc_cleaned = self.cleaned_data;
        
        if not dc_cleaned.get('email') and not dc_cleaned.get('phone'):
            errors['phone'] = 'Введите email или телефон для обрСвязи'

        if not dc_cleaned.get('email') and dc_cleaned.get('sendMes'):
            self.cleaned_data['sendMes'] = 'false'

        if not dc_cleaned.get('phone'):
            del self.cleaned_data['phone']

        if errors:
            raise ValidationError(errors)  


    """
    Процедура создания шаблона dict для добавления qust-simp
    return res_proc.res_dict 
    """
    @classmethod
    def create_templDict_qust(cls, arg_user, arg_pswcl=None):        
        from .serv_sprstatus import Com_proc_sprstatus 

        res_proc = Res_proc()

        def run_raise(s_arg, showMes=None):
                s_err = 'advuser.forms.Base_profForm.create_templDict_quest'

                if showMes:            
                    raise ErrorRun_impl('verify##{0}'.format(s_arg))
                else:
                    raise ErrorRun_impl('{0} {1}'.format(s_err, s_arg))

        try:
            _username = ''
            _user = getUser(arg_user)
            if _user is None:
                _username = arg_user
            else:
                _username = _user.username

            logincl = getLogin_cl()
            pswcl = ''
            if arg_pswcl:
                pswcl = arg_pswcl
            else:
                res_pswcl = getPassword_cl()
                if res_pswcl: pswcl = res_pswcl
                else:
                    ErrorRun_impl('NotData##advuser.forms.Base_profForm.create_templDict_quest пароль не создан')

            _dict = dict( 
                        username = logincl,
                        first_name = 'Гость',
                        last_name ='сайта',
                        password = pswcl,
                        pswcl    = pswcl,
                        parentuser = _username,
                        status_id = Com_proc_sprstatus.get_status_qust_simp().pk,
                        sendMes = 'false',
                        pol = '-'
                        )

            res_proc.res_dict = _dict

        except Exception as ex:
            res_proc.error = ex

        return res_proc


    def save_add(self, arg_user:User)->Res_proc:
        """ Процедура обработки добавления профиля клиента """
        
        from django.contrib.auth.hashers import make_password        
        from app.com_serv_dbase.serv_modf_profil import serv_add_profil
        from app.models import spr_fields_models               

        res_proc = Res_proc()
        cd_dict = self.cleaned_data

        s_error = 'ValueError##advuser.form.Base_profilForm.save_add'

        try:
            parentuser = Com_proc_advuser.get_user_cons(arg_user)
            if parentuser is None:
                run_raise(s_error+' Консультант гостВхода не найден')

            status = Com_proc_sprstatus.get_status_by_levelperm(20)
            statusID = status.pk
            levelperm_sel = status.levelperm

            # Заполнение структуры js_struct 
            # from spr_fields_models.js_data where levelperm = levelperm_sel
            js_struct = spr_fields_models.get_js_struct(levelperm_sel)

            js_struct['pswcl'] = getPassword_cl()
            js_struct['idcomp'] = cd_dict.get('idcomp') or 'empty'

            cd_dict.update(
                    dict(
                            parentuser = parentuser.username,
                            password = make_password(js_struct['pswcl']),
                            username = getLogin_cl(),
                            status_id= statusID,
                            full_name= cd_dict['first_name'] + ' ' + cd_dict['last_name'],
                            js_struct = js_struct
                        ))

            cd_dict = clear_space(cd_dict)
            cd_dict = upd_space_into_empty(cd_dict)

            res_proc = serv_add_profil(cd_dict)

        except Exception as ex:
            res_proc.error = ex

        return res_proc


    def save_upd(self, arg_user:User, arg_parentuser)->Res_proc:
        """ Процедура обработки обновления профиля клиента """

        from app.com_serv_dbase.serv_modf_profil import serv_add_profil               
        from .serv_sprstatus import Com_proc_sprstatus

        try:
            
            res_proc = Res_proc()
            cd_dict = self.cleaned_data
            s_error = 'ValueError##advuser.form.Base_profilForm.save_upd'

            user_head = getUser(arg_parentuser)
            user = getUser(arg_user)
            js_struct = Com_proc_advuser.get_js_struct(user)
            js_struct = self.com_modf_quest(user_head, js_struct) # верификация pswcl and logincl

            cd_dict['js_struct'] = js_struct
            cd_dict['username'] = user.username
            
            cd_dict = clear_space(cd_dict)
            cd_dict = upd_space_into_empty(cd_dict)                        

            res_proc = serv_add_profil(cd_dict, serv_proc='sp_serv_upd_profil')
            
        except Exception as ex:
            res_proc.error = ex

        return res_proc
    

#************** Конец контента class Base_profForm  *****************


# ****************************************************************************

# Форма обновленияПрофиля для руководителя проекта или его субРуководители
class Modf_prof_byHeaderForm(Templ_profForm):    
    """ Для рукГрупп -> форма обновления профиля """

    ageGroup = forms.IntegerField(label='Возраст',
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Возраст" }) ) 
    
    field_order = ['first_name','last_name','email','phone','idcomp','post','pol','ageGroup']


    def clean(self):
        
        super().clean()
        errors = {}
        
        errors = self.com_clean(self.cleaned_data, ('idcomp','email','post','ageGroup','phone',))
        
        if self.cleaned_data['ageGroup'] > 150:
            errors['ageGroup'] = 'Значение больше допустимого'

        if errors:
            raise ValidationError(errors)        


    def save(self, arg_username, arg_parentuser): 
        """ Сохранение изменений профиля 
        arg_username для обработки профиля
        arg_parentuser для доступа к значению pswcl на уровне рукГруппы 
        """

        from app.com_serv_dbase.serv_modf_profil import serv_add_profil    

        res_proc = Res_proc();

        try:

            user = getUser(arg_username)
            if user is None:
                run_raise('Сбой обработки профиля: пользователь не определен' , showMes=True) 

            user_head = getUser(arg_parentuser)

            cd_dict = self.cleaned_data
            cd_dict['username'] = user.username

            js_struct = Com_proc_advuser.get_js_struct(user)            
            js_struct['idcomp'] = cd_dict['idcomp']  # верификация idcomp в clean()
            js_struct = self.com_modf_quest(user_head, js_struct) # верификация pswcl and logincl

            cd_dict['js_struct'] = js_struct

            # удаление пробелов. Для подстраховки 
            cd_dict = clear_space(cd_dict)
            cd_dict = upd_space_into_empty(cd_dict)

            res_proc = serv_add_profil(cd_dict, serv_proc='sp_serv_upd_profil')

        except Exception as ex:
            res_proc.error = ex;

        return res_proc
   
    
# *********** RegisterExt_profForm ***********

# Форма для редактирования профиля самими proj_member
# предназначена для участников проекта
# отличаетс от AddProf_memberForm набором полей
class Modf_prof_byuserForm(Templ_profForm):   
    """ Для пользователй проекта -> измПрофиля """
    ageGroup    = forms.IntegerField(label='Возраст',
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Возраст" }) ) 
    
    field_order = ['first_name','last_name','email','phone','idcomp','post','pol','ageGroup']


    def clean(self):
        
        super().clean()
        errors = {}
        
        # Централизованная верификация ввода 
        errors = self.com_clean(self.cleaned_data, ('email','post','ageGroup','phone',))


        if errors:
            raise ValidationError(errors)    

    def save(self, arg_user, arg_parentuser)->Res_proc:
        from app.com_serv_dbase.serv_modf_profil import serv_add_profil

        res_proc = Res_proc()
        cd_dict = self.cleaned_data
        s_error = 'ValueError##advuser.form.UpdProf_memberForm.save'

        try:

            user = getUser(arg_user)
            if user is None:
                run_raise(s_error + ' Пользователь не найден в БД')
            user_head = getUser(arg_parentuser)

            _advdata = Com_proc_advuser.get_advData(user)

            # Параметр, который не используется в форме, но обязателен
            cd_dict['sendMes'] = _advdata['sendMes']  
            
            js_struct = Com_proc_advuser.get_js_struct(user)
            js_struct['idcomp'] = cd_dict['idcomp'] # верификация а clean()
            js_struct = self.com_modf_quest(user_head, js_struct) # верификация pswcl and logincl


            # ----------- Подготовка dict for servProc ----------------
            cd_dict.update(
	            dict(username=user.username,                        			    
                        js_struct = js_struct
			            ))

            # удаление пробелов. Для подстраховки
            cd_dict = clear_space(cd_dict)
            cd_dict = upd_space_into_empty(cd_dict) # дополнительное преобразование

            # Запись профиля в БД by servProc
            res_proc = serv_add_profil(cd_dict, serv_proc='sp_serv_upd_profil')

                        
        except Exception as ex:
            res_proc.error = ex;

        return res_proc


# Добавление профиля участника проекта
# форма используется только proj_header or proj_subheader
class AddProf_memberForm(Modf_prof_byHeaderForm):
    """ Для руководителй групп -> создание профиля участников проекта """
    username    = forms.CharField(label='Логин менеджера', max_length=50, 
                    widget=forms.TextInput(attrs={"class":"form-control", "placeholder":"Логин"}) ) 

    password    = forms.CharField(label='Пароль', max_length=50, 
                    widget=forms.PasswordInput(attrs={"class":"form-control", "placeholder":"Пароль"}) ) 
    password1    = forms.CharField(label='Повт. пароль', max_length=50, 
                    widget=forms.PasswordInput(attrs={"class":"form-control", "placeholder":"Повторить"}) ) 
    status = forms.ModelChoiceField(label='Статус', 
                    widget=forms.Select(attrs={"class":"form-control"}),
                    empty_label='--- Выберите статус ---',
                    queryset = SprStatus.objects.order_by('levelperm').filter(levelperm__gt=10, levelperm__lt=100).exclude(status='proj-sadm') )


    field_order = ['username', 'password','password1', 'first_name','last_name', 'email', 'phone', 'idcomp', 'post','pol', 'ageGroup', 'status' ]


    def clean(self):
        
        super().clean()
        errors = {}
        self.errors_clean = None

        cd_dict = self.cleaned_data

        # верификация привилегий пользователя 
        user_head = self.user_head
        user_modf = getUser(cd_dict['username'])

        type_status_head = type_status_user(user_head)

        levelperm_head = type_status_head.levelperm
        levelperm_modf = cd_dict['status'].levelperm
        if (levelperm_head == 40 and levelperm_modf in (40, 70)) or (levelperm_modf == 70 and levelperm_head < 70) :
            self.errors_clean = 'Ошибка ввода данных: Статус больше допустимого'


        # Централизованная верификация ввода данных
        errors = Base_profForm.com_clean(cd_dict, ('email','post','ageGroup','phone',))

        user_modf = getUser(cd_dict['username'])
        if user_modf:
            errors['username'] = 'Повторный ввод логина'

        password = cd_dict['password']
        password1 = cd_dict['password1']

        if password != password1:
            errors['password'] = ValidationError('Пароли не совпадают')



        if errors:
            raise ValidationError(errors)

    # Создание нового профиля - участника проекта
    # использование сервПроцедуры 
    def save(self, arg_user):    
        """ Сохранение профиля пользователя на уровне рукГруппы """

        from django.contrib.auth.hashers import make_password        
        from app.com_serv_dbase.serv_modf_profil import serv_add_profil
        from app.models import spr_fields_models

        cd_dict = self.cleaned_data
        s_error = 'advuser.form.AddProf_memberForm.save'
        s_err   = 'verify##'

        res_proc = Res_proc();
        
        try:            
            
            if self.errors_clean:  # ошибка из процедуры clean()
                run_raise(self.errors_clean, showMes=True)

            user_head = getUser(arg_user)
            status_head = type_status_user(user_head)
            levelperm_head = status_head.levelperm

            levelperm_sel = cd_dict['status'].levelperm
            statusID = cd_dict['status'].pk

            del cd_dict['status']
            cd_dict['sendMes'] = 'true'

            if levelperm_sel == 20 :
                run_raise('Профиль клиента должен создавать пользователь гостВхода', showMes=True)

            if levelperm_head  < 40 or levelperm_sel > levelperm_head :
                run_raise(s_err + 'Нет прав на создание профиля', showMes=True)
            
            # Заполнение структуры js_struct 
            # from spr_fields_models.js_data where levelperm = levelperm_sel
            js_struct = spr_fields_models.get_js_struct(levelperm_sel)

            # Для рукГрупп создается новый набор свойств pswcl and logincl
            if levelperm_sel < 40:
                js_struct = self.com_modf_quest(user_head, js_struct) # Заполнение pswcl logincl
            else:
                # Заполнение pswcl logincl новыми значениями
                js_struct = self.com_modf_quest(user_head, js_struct, new_pswd=True) 
                

            js_struct['idcomp'] = cd_dict['idcomp']

            cd_dict.update(
                dict(
                   parentuser = user_head.username,
                   password = make_password(cd_dict['password']),
                   password_cl = make_password(js_struct['pswcl']),
                   full_name= cd_dict['first_name'] + ' ' + cd_dict['last_name'],
                   status_id= statusID,
                   js_struct=js_struct,
                   pswcl = js_struct['pswcl'],    # используется для инициализации questProfil
                   logincl = js_struct['logincl']
                    )
                )

            res_proc = serv_add_profil(cd_dict)

        except Exception as ex:
            res_proc.error = ex;

        return res_proc
        


# Форма контактов
class ContUser_extForm(forms.Form):
    username = forms.CharField(label='Имя', 
                               max_length=30,
                               widget=forms.TextInput(attrs={"class":"form-control border border-primary", 
                                                             "placeholder":"Имя"}))
    email = forms.EmailField(label='Эл. адрес',
                               max_length=50, 
                               widget=forms.EmailInput(attrs={"class":"form-control border border-primary",
                                                             "placeholder":"Email"} ))
    subject = forms.CharField(label='Тема сообщения', 
                               max_length=50, 
                               widget=forms.TextInput(attrs={"class":"form-control border border-primary",  
                                                             "placeholder":"Тема"}))
    mes = forms.CharField(label='Текст сообщения', 
                          widget=forms.Textarea(attrs={'rows':'2', 
                             "class":"md-textarea form-control border-0"
                                                       }))
