# -*- coding: utf-8 -*-
import functools
import operator
import os
import re
try:
    import simplejson as json
except ImportError:
    import json

from mole.template import jinja2_template as render_template
from mole import request,response as Response,redirect, abort
from mole.mole import url as url_for
from utils import flash

from mocrud.filters import FilterMapping, FilterForm, FilterModelConverter
from mocrud.forms import BaseModelConverter, ChosenAjaxSelectWidget, LimitedModelSelectField
from mocrud.serializer import Serializer
from mocrud.utils import get_next, PaginatedQuery, path_to_models, slugify
#from mocrud.auth import Auth

from peewee import BooleanField, DateTimeField, ForeignKeyField, DateField, TextField
#from werkzeug import Headers
from wtforms import fields, widgets
from ormfields import ModelSelectField, ModelSelectMultipleField, ModelHiddenField
from ormform import model_form


current_dir = os.path.dirname(__file__)

method_dic = { "index": u"查看", "add": u"新增", "edit": u"更新", "delete": u"删除", "export": u"导出"}

class AdminModelConverter(BaseModelConverter):
    def __init__(self, model_admin, additional=None):
        super(AdminModelConverter, self).__init__(additional)
        self.model_admin = model_admin

    def handle_foreign_key(self, model, field, **kwargs):
        if field.null:
            kwargs['allow_blank'] = True

        if field.name in (self.model_admin.foreign_key_lookups or ()):
            form_field = ModelHiddenField(model=field.rel_model, **kwargs)
        else:
            form_field = ModelSelectField(model=field.rel_model, **kwargs)
        return field.name, form_field


class AdminFilterModelConverter(FilterModelConverter):
    def __init__(self, model_admin, additional=None):
        super(AdminFilterModelConverter, self).__init__(additional)
        self.model_admin = model_admin

    def handle_foreign_key(self, model, field, **kwargs):
        if field.name in (self.model_admin.foreign_key_lookups or ()):
            data_source = url_for(self.model_admin.get_url_name('ajax_list'))
            widget = ChosenAjaxSelectWidget(data_source, field.name)
            form_field = LimitedModelSelectField(model=field.rel_model, widget=widget, **kwargs)
        else:
            form_field = ModelSelectField(model=field.rel_model, **kwargs)
        return field.name, form_field


class ModelAdmin(object):
    """
    ModelAdmin provides create/edit/delete functionality for a peewee Model.
    """
    paginate_by = 20
    filter_paginate_by = 15

    # columns to display in the list index - can be field names or callables on
    # a model instance, though in the latter case they will not be sortable
    columns = None
    show_all_columns = True
    add_column_display = {}

    # exclude certian fields from being exposed as filters -- for related fields
    # use "__" notation, e.g. user__password
    filter_exclude = None
    filter_fields = None

    # form parameters, lists of fields
    exclude = None
    fields = None
    
    method_exclude = [] #'add', 'delete', 'edit', 'export'
    
    ops = []
    
    show_nav = True
    
    count = 0
    
    context = {}

    form_converter = AdminModelConverter

    # foreign_key_field --> related field to search on, e.g. {'user': 'username'}
    foreign_key_lookups = None

    # delete behavior
    delete_collect_objects = True
    delete_recursive = True

    filter_mapping = FilterMapping
    filter_converter = AdminFilterModelConverter
    
    menu_grup = '_default_grup'
    visible = True
    icon_class = 'icon-th-list'
    menu_index = 0
    
    verbose_name = None

    # templates, to override see get_template_overrides()
    base_templates = {
        'index': 'admin/models/index.html',
        'add': 'admin/models/add.html',
        'edit': 'admin/models/edit.html',
        'delete': 'admin/models/delete.html',
        'export': 'admin/models/export.html',
    }

    def __init__(self, admin, model_grup,  model):
        self.admin = admin
        self.model_grup = model_grup
        self.model = model
        self.db = model._meta.database
        self.pk = self.model._meta.primary_key

        self.templates = dict(self.base_templates)
        self.templates.update(self.get_template_overrides())
        
        self.model_op = []
        self.object_op = []
        for op_class in self.ops:
            self.register_op(op_class)

    def get_template_overrides(self):
        '''
        定义crud的基础模板
        '''
        return {}

    def get_url_name(self, name):
        return '%s.%s_%s' % (
            self.admin.blueprint.name,
            self.get_admin_name(),
            name,
        )
        
    def get_menu_key(self):
        return self.get_url_name("index")

    def get_filter_form(self):
        return FilterForm(
            self.model,
            self.filter_converter(self),
            self.filter_mapping(),
            self.filter_fields,
            self.filter_exclude,
        )

    def process_filters(self, query):
        filter_form = self.get_filter_form()
        form, query, cleaned = filter_form.process_request(query)
        return form, query, cleaned, filter_form._field_tree

    def get_form(self, adding=False, exclude=[]):
        allow_pk = adding and not self.model._meta.auto_increment
        m_exclude = exclude and  [ e for e in self.exclude] + exclude or self.exclude
        return model_form(self.model,
            allow_pk=allow_pk,
            only=self.fields,
            exclude=m_exclude,
            converter=self.form_converter(self),
        )

    def get_add_form(self):
        return self.get_form(adding=True)

    def get_edit_form(self, instance, exclude=[]):
        return self.get_form(adding=False, exclude = exclude)

    def get_query(self):
        return self.model.select()

    def get_object(self, pk):
        return self.get_query().where(self.pk==pk).get()
    
    def register_op(self, op_class):
        inherit_flag = None
        if hasattr(op_class,'__bases__'):
            if len(op_class.__bases__)>0:
                m_base = op_class.__bases__[0]
                if m_base.__name__ in ('ModelOp','ObjectOp'):
                    inherit_flag = m_base.__name__
                else:
                    if len(m_base.__bases__)>0:
                        if m_base.__bases__[0].__name__ in ('ModelOp','ObjectOp'):
                            inherit_flag = m_base.__bases__[0].__name__
        if inherit_flag:
            op_object = op_class(self)
            if inherit_flag == 'ModelOp':
                self.model_op.append(op_object)
            if inherit_flag == 'ObjectOp':
                self.object_op.append(op_object)

    def get_urls(self):
        if not self.method_exclude:
            m_list =  [
                ('/', self.index),
                ('/add/', self.add),
                ('/delete/', self.delete),
                ('/export/', self.export),
                ('/:pk/', self.edit),
                ('/_ajax/', self.ajax_list),
            ]
        else:
            m_list = [
                    ('/', self.index),
                    ('/_ajax/', self.ajax_list),
                ]
            if 'add' not in self.method_exclude:m_list.append( ('/add/', self.add) )
            if 'delete' not in self.method_exclude:m_list.append( ('/delete/', self.delete) )
            if 'export' not in self.method_exclude:m_list.append( ('/export/', self.export) )
            if 'edit'  not in self.method_exclude:m_list.append( ('/:pk/', self.edit) )
        
        ops = self.model_op + self.object_op
        for op in ops:
            m_name = op.__class__.__name__
            m_list.append( ('/%s/'%m_name, op.hander) )
        return m_list

    def get_columns(self):
        return self.model._meta.get_field_names()
    
    def get_column_display(self, column_name):
        if self.add_column_display.has_key(column_name):
            return self.add_column_display[column_name]
        try:
            field = self.model._meta.fields[column_name]
        except KeyError:
            return self.admin.template_helper.fix_underscores(column_name)
        else:
            return field.verbose_name
    
    def get_primary_key(self):
        return self.model._meta.primary_key.name

    def column_is_sortable(self, col):
        return col in self.model._meta.fields

    def get_display_name(self):
        if self.verbose_name:
            return self.verbose_name
        else:
            return self.model.__name__
        
    def check_display(self,key):
        if key in self.method_exclude:
            return False
        if key=='index' and not self.visible:
            return False
        m_auth = self.admin.auth
        if not m_auth.Role:
            return True
        user = m_auth.get_logged_in_user()
        permkey = self.get_url_name(key)
        if user:
            return self.admin.check_user_permission(user, permkey)
        else:
            return False

    def get_admin_name(self):
        return slugify(self.model.__name__)

    def save_model(self, instance, form, adding=False):
        form.populate_obj(instance)
        instance.save(force_insert=adding)
        return instance

    def apply_ordering(self, query, ordering):
        if ordering:
            desc, column = ordering.startswith('-'), ordering.lstrip('-')
            if self.column_is_sortable(column):
                field = self.model._meta.fields[column]
                query = query.order_by(field.asc() if not desc else field.desc())
        return query

    def get_extra_context(self):
        u'''
        Model模型级公共Context
        '''
        m_dic = self.admin.template_helper.get_helper_context()
        m_dic['model_grup'] = self.model_grup
        m_dic['model_admins'] = self.admin.get_grup_admins(self.model_grup)
        m_dic['model_name'] = self.get_admin_name()
        m_dic['model_menu_key'] = self.get_menu_key()
        return m_dic

    def index(self):
        query = self.get_query()

        ordering = request.params.get('ordering') or ''
        query = self.apply_ordering(query, ordering)

        # process the filters from the request
        filter_form, query, cleaned, field_tree = self.process_filters(query)

        # create a paginated query out of our filtered results
        pq = PaginatedQuery(query, self.paginate_by)

        if request.method == 'POST':
            id_list = ','.join(request.forms.getall('id'))
            return redirect(url_for(self.get_url_name(request.forms['action']), id=id_list))
#            if request.forms['action'] == 'delete':
#                return redirect(url_for(self.get_url_name('delete'), id=id_list))
#            else:
#                return redirect(url_for(self.get_url_name('export'), id=id_list))

        return render_template(self.templates['index'],
            model_admin=self,
            query=pq,
            ordering=ordering,
            filter_form=filter_form,    #过滤查询表单
            field_tree=field_tree,  #下拉过滤器
            active_filters=cleaned, #当前活动过滤项
            **self.get_extra_context()
        )

    def dispatch_save_redirect(self, instance):
        if 'save' in request.forms:
            return redirect(url_for(self.get_url_name('index')))
        elif 'save_add' in request.forms:
            return redirect(url_for(self.get_url_name('add')))
        else:
            return redirect(
                url_for(self.get_url_name('edit'), pk=instance.get_id())
            )

    def add(self):
        Form = self.get_add_form()
        instance = self.model()

        if request.method == 'POST':
            form = Form(request.forms)
            if form.validate():
                instance = self.save_model(instance, form, True)
                flash('New %s saved successfully' % self.get_display_name(), 'success')
                return self.dispatch_save_redirect(instance)
        else:
            form = Form()

        return render_template(self.templates['add'],
            model_admin=self,
            form=form,
            instance=instance,
            **self.get_extra_context()
        )

    def edit(self, pk):
        try:
            instance = self.get_object(pk)
        except self.model.DoesNotExist:
            return abort(404)

        Form = self.get_edit_form(instance)

        if request.method == 'POST':
            form = Form(request.forms, obj=instance)
            if form.validate():
                self.save_model(instance, form, False)
                flash('Changes to %s saved successfully' % self.get_display_name(), 'success')
                return self.dispatch_save_redirect(instance)
        else:
            form = Form(obj=instance)

        return render_template(self.templates['edit'],
            model_admin=self,
            instance=instance,
            form=form,
            **self.get_extra_context()
        )

    def collect_objects(self, obj):
        deps = obj.dependencies()
        objects = []

        for query, fk in obj.dependencies():
            if not fk.null:
                sq = fk.model_class.select().where(query)
                collected = [rel_obj for rel_obj in sq.execute().iterator()]
                if collected:
                    objects.append((0, fk.model_class, collected))

        return sorted(objects, key=lambda i: (i[0], i[1].__name__))

    def delete(self):
        if request.method == 'GET':
            id_list = request.params.get('id')
            id_list = id_list.split(',')
            id_list = [int(e) for e in id_list if e]
        else:
            id_list = request.forms.getall('id')
        query = self.model.select().where(self.pk << id_list)

        if request.method == 'GET':
            collected = {}
            if self.delete_collect_objects:
                for obj in query:
                    collected[obj.get_id()] = self.collect_objects(obj)

        elif request.method == 'POST':
            count = query.count()
            for obj in query:
                obj.delete_instance(recursive=self.delete_recursive)

            flash('Successfully deleted %s %ss' % (count, self.get_display_name()), 'success')
            return redirect(url_for(self.get_url_name('index')))

        return render_template(self.templates['delete'], **dict(
            model_admin=self,
            query=query,
            collected=collected,
            **self.get_extra_context()
        ))

    def collect_related_fields(self, model, accum, path, seen=None):
        seen = seen or set()
        path_str = '__'.join(path)
        for field in model._meta.get_fields():
            if isinstance(field, ForeignKeyField) and field not in seen:
                seen.add(field)
                self.collect_related_fields(field.rel_model, accum, path + [field.name], seen)
            elif model != self.model:
                accum.setdefault((model, path_str), [])
                accum[(model, path_str)].append(field)

        return accum

    def export(self):
        query = self.get_query()

        ordering = request.params.get('ordering') or ''
        query = self.apply_ordering(query, ordering)

        # process the filters from the request
        filter_form, query, cleaned, field_tree = self.process_filters(query)
        related = self.collect_related_fields(self.model, {}, [])

        # check for raw id
        id_list = request.params.getall('id')
        id_list = [int(e) for e in id_list if e]
        if id_list:
            query = query.where(self.pk << id_list)

        if request.method == 'POST':
            raw_fields = request.forms.getall('fields')
            export = Export(query, related, raw_fields)
            return export.json_response('export-%s.json' % self.get_admin_name())

        return render_template(self.templates['export'],
            model_admin=self,
            model=query.model_class,
            query=query,
            filter_form=filter_form,
            field_tree=field_tree,
            active_filters=cleaned,
            related_fields=related,
            sql=query.sql(),
            **self.get_extra_context()
        )

    def ajax_list(self):
        field = request.params.get('field')
        prev_page = 0
        next_page = 0

        try:
            models = path_to_models(self.model, field)
        except AttributeError:
            data = []
        else:
            rel_model = models.pop()
            rel_field = rel_model._meta.fields[self.foreign_key_lookups[field]]
            query = rel_model.select().order_by(rel_field)
            query_string = request.params.get('query')
            if query_string:
                query = query.where(rel_field ** ('%%%s%%' % query_string))

            pq = PaginatedQuery(query, self.filter_paginate_by)
            current_page = pq.get_page()
            if current_page > 1:
                prev_page = current_page - 1
            if current_page < pq.get_pages():
                next_page = current_page + 1

            data = [
                {'id': obj.get_id(), 'repr': unicode(obj)} \
                    for obj in pq.get_list()
            ]
        Response.headers['mimetype'] = 'application/json'
        return {'prev_page': prev_page, 'next_page': next_page, 'object_list': data}
#        return Response(json_data, mimetype='application/json')


class AdminPanel(object):
    verbose_name = None
    template_name = 'admin/panels/default.html'

    def __init__(self, admin, title):
        self.admin = admin
        self.title = title

    def dashboard_url(self):
        return url_for('%s.index' % (self.admin.blueprint.name))

    def get_urls(self):
        return ()

    def get_url_name(self, name):
        return '%s.panel_%s_%s' % (
            self.admin.blueprint.name,
            self.title,
            name,
        )

    def get_template_name(self):
        return self.template_name

    def get_context(self):
        return {}

    def render(self):
        return render_template(self.get_template_name(), panel=self, **self.get_context())


class AdminTemplateHelper(object):
    
    def __init__(self, admin):
        self.admin = admin  # 指针回路
        self.app = self.admin.app

    def get_model_field(self, model, field):
        u'''获取字段值'''
        if field.find('.')<0:
            attr = getattr(model, field)
            if model._meta.fields.has_key(field):
                m_fields = model._meta.fields
                if m_fields[field].choices:
                    m_dict = dict(m_fields[field].choices)
                    attr = m_dict.get(attr,attr)
        else:
            field_list = field.split('.')
            attr = getattr(model, field_list[0])
            attr = getattr(attr, field_list[1])
            field = field.replace('.', '_')
        if type(attr)==bool:attr=attr and u'是' or u'否'
        if hasattr( self.admin.get_admin_for(model.__class__), 'ps_'+field):attr = getattr( self.admin.get_admin_for(model.__class__), 'ps_'+field)(model)
        if attr==None:attr=''
        if callable(attr):
            return attr()
        return attr
 
    def get_form_field(self, form, field_name):
        return getattr(form, field_name)

    def fix_underscores(self, s):
        return s.replace('_', ' ').title()

    def update_querystring(self, querystring, key, val):
        if not querystring:
            return '%s=%s' % (key, val)
        else:
            querystring = re.sub('%s(?:[^&]+)?&?' % key, '', querystring).rstrip('&')
            return ('%s&%s=%s' % (querystring, key, val)).lstrip('&')

    def get_verbose_name(self, model, column_name):
        try:
            field = model._meta.fields[column_name]
        except KeyError:
            return self.fix_underscores(column_name)
        else:
            return field.verbose_name

    def get_model_admins(self):
        from mocrud import conf
        if conf:
            from mosys.sys_view import get_app_nemus
        else:
            get_app_nemus = None
        return {'branding': self.admin.branding, 
                'apps': conf and conf.apps_list or None,
                'apps_dict': conf and dict(conf.apps_list),
                'get_app_nemus':get_app_nemus
                }
    
    def get_helper_context(self):
        u'''
        Apps站点级公共Context
        '''
        return self.get_model_admins()

    def get_admin_url(self, obj):
        model_admin = self.admin.get_admin_for(type(obj))
        if model_admin:
            return url_for(model_admin.get_url_name('edit'), pk=obj.get_id())

    def get_model_name(self, model_class):
        model_admin = self.admin.get_admin_for(model_class)
        if model_admin:
            return model_admin.get_display_name()
        return model_class.__name__

    def apply_prefix(self, field_name, prefix_accum, field_prefix, rel_prefix='fr_', rel_sep='-'):
        accum = []
        for prefix in prefix_accum:
            accum.append('%s%s' % (rel_prefix, prefix))
        accum.append('%s%s' % (field_prefix, field_name))
        return rel_sep.join(accum)

    def prepare_environment(self):
#        self.app.template_context_processors[None].append(self.get_model_admins)
        from jinja2.defaults import DEFAULT_NAMESPACE,DEFAULT_FILTERS
        from filters import _tojson_filter
        from utils import get_flashed_messages
        DEFAULT_NAMESPACE_n = {}
        DEFAULT_NAMESPACE_n['get_model_field'] = self.get_model_field
        DEFAULT_NAMESPACE_n['get_form_field'] = self.get_form_field
        DEFAULT_NAMESPACE_n['get_verbose_name'] = self.get_verbose_name
        DEFAULT_FILTERS['fix_underscores'] = self.fix_underscores
        DEFAULT_FILTERS['tojson'] = _tojson_filter
        DEFAULT_NAMESPACE_n['request'] = request
        DEFAULT_NAMESPACE_n['update_querystring'] = self.update_querystring
        DEFAULT_NAMESPACE_n['get_admin_url'] = self.get_admin_url
        DEFAULT_NAMESPACE_n['get_model_name'] = self.get_model_name
        DEFAULT_NAMESPACE_n['get_flashed_messages'] = get_flashed_messages
        from mole.sessions import get_current_session
        DEFAULT_NAMESPACE_n['get_session'] = get_current_session
        DEFAULT_FILTERS['apply_prefix'] = self.apply_prefix
        DEFAULT_NAMESPACE.update(DEFAULT_NAMESPACE_n)

class Admin(object):
    def __init__(self, app, auth, template_helper=AdminTemplateHelper,
                 prefix='/admin', name='admin', branding=''):
        self.app = app
        self.auth = auth

        self._admin_models = {}
        self._registry = {}
        self._panels = {}
        self._pages = {}
        
        self.perms = []

        self.blueprint = self.app#self.get_blueprint(name)
        self.blueprint.name = 'admin'
        self.url_prefix = prefix

        self.template_helper = template_helper(self)
        self.template_helper.prepare_environment()

        self.branding = branding

    def auth_required(self, func, perm_key=None):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if self.auth.autogc:
                with self.auth.db:
                    if  self.auth.check:
                        user = self.auth.get_logged_in_user()
            
                        if not user:
                            login_url = url_for('auth.login', next=get_next())
                            return redirect(login_url)
            
                        if not self.check_user_permission(user, perm_key):
                            return abort(403)
            
                        return func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
            else:
                if  self.auth.check:
                    user = self.auth.get_logged_in_user()
        
                    if not user:
                        login_url = url_for('auth.login', next=get_next())
                        return redirect(login_url)
        
                    if not self.check_user_permission(user, perm_key):
                        return abort(403)
        
                    return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
        return inner

    def check_user_permission(self, user, perm_key=None):
        if user.admin:
            return True
        elif perm_key:
            return perm_key in user.get_perm_list()
        else:
            return True
        
    def get_op_permkey(self, madmin, callback):
        return madmin.get_url_name(callback.__name__!='hander' and callback.__name__ or callback.im_class.__name__)
    
    def get_page_permkey(self, page):
        return '%s.page_%s' % (self.blueprint.name, page.__class__.__name__)

    def get_urls(self):
        return (
            ('/', self.auth_required(self.index)),
            ('/database', self.table_desc),
        )

    def __contains__(self, item):
        return item in self._registry

    def __getitem__(self, item):
        return self._registry[item]

    def register(self, model_grup, model, admin_class=ModelAdmin):
        model_admin = admin_class(self, model_grup, model)
        admin_name = model_admin.get_admin_name()   #没有被使用

        self._registry[model] = model_admin

    def unregister(self, model):
        del(self._registry[model])

    def register_panel(self, title, panel):
        panel_instance = panel(self, title)
        self._panels[title] = panel_instance
        
    def register_page(self, page, name=None):
        page_instance = page(self)
        m_name  = name or page.__name__
        self._pages[m_name] = page_instance
        
    def get_pages(self):
        return self._pages.values()
    
    def get_perms(self):
        return self.perms

    def unregister_panel(self, title):
        del(self._panels[title])

    def get_admin_for(self, model):
        return self._registry.get(model)

    def get_model_admins(self):
        return sorted(self._registry.values(), key=lambda o: o.get_admin_name())
    
    def get_grup_admins(self,grup_name):
        return [ e for e in self._registry.values() if e.model_grup==grup_name]

    def get_panels(self):
        return sorted(self._panels.values(), key=lambda o: o.title)

    def index(self):
        u'''
        总控制面板视图
        '''
        return render_template('admin/index.html',
            model_admins=self.get_model_admins(),
            panels=self.get_panels(),
            **self.template_helper.get_helper_context()
        )
        
    def table_desc(self):
        u'''
        数据库表结构视图
        '''
        return render_template('admin/table_desc.html',
            model_admins=self.get_model_admins(),
            **self.template_helper.get_helper_context()
        )

    def get_blueprint(self, blueprint_name):
        return None
#        return Blueprint(
#            blueprint_name,
#            __name__,
#            static_folder=os.path.join(current_dir, 'static'),
#            template_folder=os.path.join(current_dir, 'templates'),
#        )

    def register_blueprint(self, **kwargs):
        self.app.register_blueprint(
            self.blueprint,
            url_prefix=self.url_prefix,
            **kwargs
        )

    def configure_routes(self):
        for url, callback in self.get_urls():
            self.blueprint.route('%s%s'%(self.url_prefix, url), 
                                 name= '%s.%s' %(self.blueprint.name,callback.__name__),
                                 method=['GET', 'POST'])(callback)

        for model_admin in self._registry.values():
            admin_name = model_admin.get_admin_name()
            for url, callback in model_admin.get_urls():
                full_url = '%s/%s%s' % (self.url_prefix,admin_name, url)
                m_key = model_admin.get_url_name(callback.__name__!='hander' and callback.__name__ or callback.im_class.__name__)#'admin.%s_%s' % (admin_name, callback.__name__),
                m_verbose = callback.__name__!='hander' and method_dic.get(callback.__name__,callback.__name__) or (callback.im_class.verbose_name or callback.im_class.__name__)
                group_verbose = model_admin.verbose_name or admin_name
                m_verbose = group_verbose + '-' + m_verbose
                self.perms.append( (m_key, group_verbose + '|' + m_verbose) )
                self.blueprint.route(
                    full_url,
                    name= m_key,
                    method=['GET', 'POST'],
                )(self.auth_required(callback, m_key))

        for panel in self._panels.values():
            for url, callback in panel.get_urls():
                full_url = '/%s%s' % (panel.title, url)
                self.blueprint.route(
                    full_url,
                    name='%s.panel_%s_%s' % (self.blueprint.name, panel.title, callback.__name__),
                    method=['GET', 'POST'],
                )(self.auth_required(callback))
        
        for page in self._pages.values():
            full_url = '%s/fp/%s/' % (self.url_prefix,page.__class__.__name__)
            m_key = self.get_page_permkey(page)#'%s.page_%s' % (self.blueprint.name, page.__class__.__name__)
            m_verbose = page.verbose_name or page.__class__.__name__
            self.perms.append( (m_key, m_verbose) )
            self.blueprint.route(
                full_url,
                name=m_key,
                method=['GET', 'POST'],
            )(self.auth_required(page.hander, m_key))

    def setup(self):
        self.configure_routes()
#        self.register_blueprint()

from mocrud import m_app
from mocrud.auth import auth
# 全局实例
admin = Admin(m_app, auth)

class Export(object):
    def __init__(self, query, related, fields):
        self.query = query
        self.related = related
        self.fields = fields

        self.alias_to_model = dict([(k[1], k[0]) for k in self.related.keys()])

    def prepare_query(self):
        clone = self.query.clone()

        select = []
        joined = set()

        def ensure_join(query, m, p):
            if m not in joined:
                if '__' not in p:
                    next_model = query.model_class
                else:
                    next, _ = p.rsplit('__', 1)
                    next_model = self.alias_to_model[next]
                    query = ensure_join(query, next_model, next)

                joined.add(m)
                return query.switch(next_model).join(m)
            else:
                return query

        for lookup in self.fields:
            # lookup may be something like "content" or "user__user_name"
            if '__' in lookup:
                path, column = lookup.rsplit('__', 1)
                model = self.alias_to_model[path]
                clone = ensure_join(clone, model, path)
            else:
                model = self.query.model_class
                column = lookup

            field = model._meta.fields[column]
            select.append(field)

        clone._select = select
        return clone

    def json_response(self, filename='export.json'):
        serializer = Serializer()
        prepared_query = self.prepare_query()
        field_dict = {}
        for field in prepared_query._select:
            field_dict.setdefault(field.model_class, [])
            field_dict[field.model_class].append(field.name)

        def generate():
            i = prepared_query.count()
            yield '[\n'
            for obj in prepared_query:
                i -= 1
                yield json.dumps(serializer.serialize_object(obj, field_dict))
                if i > 0:
                    yield ',\n'
            yield '\n]'
#        headers = Headers()
        Response.headers['Content-Type'] = 'application/javascript'
        Response.headers['Content-Disposition'] = 'attachment; filename=%s' % filename
        Response.headers['mimetype'] = 'text/javascript'
        return generate()
#        return Response(generate(), mimetype='text/javascript', headers=headers, direct_passthrough=True)
