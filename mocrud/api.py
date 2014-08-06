# -*- coding: utf-8 -*-

from admin import ModelAdmin
from admin import admin
from auth import auth

def setup(app_models):
    for attr in dir(app_models):
        m=app_models.__getattribute__(attr)
        inherit_flag = False
        if hasattr(m,'__bases__'):
            if len(m.__bases__)>0:
                m_base = m.__bases__[0]
                if m_base.__name__ in ('CrudModel','BaseModel','Model'):
                    inherit_flag = True
                else:
                    if len(m_base.__bases__)>0:
                        if m_base.__bases__[0].__name__ in ('CrudModel','BaseModel','Model'):
                            inherit_flag = True
            
        if inherit_flag  and m.__name__ not in ['Model','CrudModel','BaseModel']:
            m_admin = None
            if hasattr(m,"Admin"):
                if issubclass(m.Admin, ModelAdmin):
                    m_admin = m.Admin
            if m_admin==None:
                m.Admin = m_admin = ModelAdmin
                admin.register('default',m)
            else:
                admin.register('default',m,m_admin)
    admin.setup()
    
def uncheck():
    auth.check = False
    
def create_tables():
    models = admin._registry
    for m in models:
        m.create_table(True)