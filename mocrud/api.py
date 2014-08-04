# -*- coding: utf-8 -*-

from admin import ModelAdmin
from admin import admin
from auth import auth

def setup(app_models):
    for attr in dir(app_models):
        m=app_models.__getattribute__(attr)
        if hasattr(m,'__bases__') and len(m.__bases__)>0 and m.__bases__[0].__name__ in ('CrudModel','BaseModel','Model') and m.__name__ not in ['Model','CrudModel','BaseModel']:
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