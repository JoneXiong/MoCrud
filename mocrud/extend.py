# -*- coding: utf-8 -*-

from mole.template import jinja2_template as render_template
from mole.mole import url as url_for
from wtforms import Form
from mole import request, redirect, abort
from utils import flash

class FormAction(Form):
    
    template = None
    OpForm = Form
    
    def init(self, form, request):
        pass
    
    def action(self, form, request):
        pass
    
    def hander(self):
        if request.method == 'POST':
            form = self.OpForm(request.forms)
            if form.validate():
                res =  self.action(form)
                if res:
                    return res
        else:
            form = self.OpForm()
            res = self.init(form)
            if res:
                return res
            
        return render_template(self.template, form=form)
        
class ModelOp(FormAction):
    
    verbose_name = None
    
    def __init__(self,model_admin):
        self.model_admin = model_admin
        self.instance = None
        
    def hander(self):
        self.instance = self.model_admin.model()

        if request.method == 'POST':
            form = self.OpForm(request.forms)
            if form.validate():
                res =  self.action(form, request)
                if res:
                    return res
        else:
            form = self.OpForm()
            res = self.init(form, request)
            if res:
                return res

        return render_template(self._get_template(),
            cur_op = self,
            model_admin=self.model_admin,
            form=form,
            instance=self.instance,
            **self.model_admin.get_extra_context()
        )
        
    def redirect(self):
        u'''
        默认的跳转
        '''
        return self.model_admin.dispatch_save_redirect(self.instance)
    
    def _get_template(self):
        if self.template:
            return self.template
        else:
            return 'admin/models/model_op.html'


class ObjectOp(FormAction):
    
    verbose_name = None
    only_id = False
    pk = None
    
    def __init__(self,model_admin):
        self.model_admin = model_admin
        self.instances = []
        
    def hander(self):
        if request.method == 'GET':
                id_list = request.params.get('id')
                id_list = id_list.split(',')
                id_list = [e for e in id_list if e]
        else:
            id_list = request.forms.getall('id')
        m_pk = self.pk and self.pk or 'pk'
        m_model = self.model_admin.model
        if self.pk:
            m_key = getattr(m_model,self.pk)
        else:
            m_key = self.model_admin.pk
        self.instances = self.only_id and id_list or m_model.select().where( m_key<< id_list)
        #if not self.instances:abort(404)

        if request.method == 'POST':
            form = self.OpForm(request.forms)
            if form.validate():
                res =  self.action(form, request)
                if res:
                    return res
        else:
            form = self.OpForm()
            res = self.init(form, request)
            if res:
                return res

        return render_template(self._get_template(),
            cur_op = self,
            model_admin=self.model_admin,
            form=form,
            instances=self.instances,
            **self.model_admin.get_extra_context()
        )
        
    def redirect(self):
        u'''
        默认的跳转
        '''
        return redirect(url_for(self.model_admin.get_url_name('index')))
    
    def _get_template(self):
        if self.template:
            return self.template
        else:
            return 'admin/models/object_op.html'