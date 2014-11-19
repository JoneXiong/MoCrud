# -*- coding: utf-8 -*-
import datetime

from mocrud.auth import BaseUser
from base_model import BaseModel as CrudModel
from mocrud.admin import ModelAdmin
from peewee import *
from mocrud.auth import auth

class User(CrudModel, BaseUser):
    u'''用户'''
    username = CharField()
    password = CharField()
    email = CharField()
    join_date = DateTimeField(default=datetime.datetime.now, verbose_name=u'加入时间')
    active = BooleanField(default=True)
    admin = BooleanField(default=False)

    def __unicode__(self):
        return self.username

    def following(self):
        u'''关注列表'''
        return User.select().join(
            Relationship, on=Relationship.to_user
        ).where(Relationship.from_user==self).order_by(User.username)

    def followers(self):
        u'''被关注列表'''
        return User.select().join(
            Relationship, on=Relationship.from_user
        ).where(Relationship.to_user==self).order_by(User.username)

    def is_following(self, user):
        u'''是否关注了某人'''
        return Relationship.select().where(
            Relationship.from_user==self,
            Relationship.to_user==user
        ).exists()

    def gravatar_url(self, size=80):
        u'''获取头像url'''
        return 'http://static.oschina.net/uploads/user/52/105889_100.jpg'
    
class UserAdmin(ModelAdmin):
    verbose_name = u'用户'
    columns = ('username', 'email', 'active', 'admin')

User.Admin = auth.get_model_admin(UserAdmin)
auth.User = User

class Relationship(CrudModel):
    u'''关注关系'''
    from_user = ForeignKeyField(User, related_name='relationships')
    to_user = ForeignKeyField(User, related_name='related_to')

    def __unicode__(self):
        return u'%s 关注 %s' % (self.from_user, self.to_user)
    
class RelationshipAdmin(ModelAdmin):
    verbose_name = u'关系'
    
Relationship.Admin = RelationshipAdmin
