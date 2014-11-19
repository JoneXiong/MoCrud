# -*- coding: utf-8 -*-

import datetime

from mocrud.auth import BaseUser
from mocrud.db import CrudModel
from mocrud.admin import ModelAdmin
from peewee import *

from user_model import User

class Note(CrudModel):
    u'''日志'''
    user = ForeignKeyField(User,verbose_name=u'用户')
    message = TextField(verbose_name=u'内容')
    status = IntegerField(choices=((1, 'live'), (2, 'deleted')), null=True, verbose_name=u'状态')
    created_date = DateTimeField(default=datetime.datetime.now, verbose_name=u'创建时间')
    
class NoteAdmin(ModelAdmin):
    verbose_name = u'日志'
    columns = ('user', 'message', 'created_date',)
    exclude = ('created_date',)
    
Note.Admin = NoteAdmin