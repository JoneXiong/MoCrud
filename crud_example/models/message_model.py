# -*- coding: utf-8 -*-

import datetime

from mocrud.auth import BaseUser
from base_model import BaseModel as CrudModel
from mocrud.admin import ModelAdmin
from peewee import *

from user_model import User

class Message(CrudModel):
    u'''微博'''
    user = ForeignKeyField(User,verbose_name = u'用户')
    content = TextField(verbose_name=u'内容')
    pub_date = DateTimeField(default=datetime.datetime.now,verbose_name=u'提交时间')

    def __unicode__(self):
        return '%s: %s' % (self.user, self.content)
    
class MessageAdmin(ModelAdmin):
    verbose_name = u'微博'
    columns = ('user', 'content', 'pub_date',)
    foreign_key_lookups = {'user': 'username'}
    filter_fields = ('user', 'content', 'pub_date', 'user__username')
    
Message.Admin = MessageAdmin