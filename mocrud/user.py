# -*- coding: utf-8 -*-
import datetime

from peewee import *

from mocrud.admin import ModelAdmin, admin
from mocrud import db
from mocrud.utils import get_next, make_password, check_password

class UserBase(db.CrudModel):
    id = PrimaryKeyField()
    username = CharField(unique=True, db_column='name', verbose_name=u'用户名')
    password = CharField(verbose_name=u'密码')
    
    email = CharField(null=True,verbose_name=u'Email')
    active = BooleanField(default=True)
    admin = BooleanField(default=False, verbose_name=u'是否管理员')
    
    nickname = CharField(null=True, verbose_name=u'昵称')
    last_login = DateTimeField(null=True, verbose_name=u'最后登录时间')
    locked = BooleanField(default=False, verbose_name=u'是否已锁')
    deleted = BooleanField(default=False, verbose_name=u'是否已删')
    note = CharField(null=True, verbose_name=u'备注信息')
    
    ctime = DateTimeField(default=datetime.datetime.now, verbose_name=u'创建时间')
    
    def __unicode__(self):
        return self.username
    
    def get_perm_list(self):
        roles = self.rel_roles
        m_list = []
        for r in roles:
            m_r = r.role
            if m_r.perms_core:
                m_list = m_list + m_r.perms_core.split(',')
        return m_list
    
    def set_password(self, password):
        self.password = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password)
    
class UserAdmin(ModelAdmin):
    verbose_name = u'登录用户'
    menu_grup = 'group_system'
    menu_index = 1
    columns = ('username', 'active', 'admin', 'note')
    
    def save_model(self, instance, form, adding=False):
        orig_password = instance.password
    
        user = super(UserAdmin, self).save_model(instance, form, adding)
    
        if orig_password != form.password.data:
            user.set_password(form.password.data)
            user.save()
    
        return user
    
class PermissionBase(db.CrudModel):
    name = CharField(null=True, verbose_name=u'关键字')
    description = CharField(null=True, verbose_name=u'描述')
    props = CharField(null=True)
    ctime = DateTimeField(default=datetime.datetime.now,verbose_name=u'创建时间')
    
class PermissionAdmin(ModelAdmin):
    verbose_name = u'权限'
    menu_grup = 'group_system'
    menu_index = 4
    method_exclude = ('delete')
    columns = ('name', 'description')
    
class RoleBase(db.CrudModel):
    name = CharField(null=True, verbose_name=u'关键字')
    role_name = CharField(verbose_name=u'角色名')
    perms_core = CharField(null=True, choices='get_perms_choices', spliter=',', verbose_name=u'权限')
    perms_other = CharField(null=True, verbose_name=u'其他权限')
    reserve = CharField(null=True, verbose_name=u'保留字段')
    ctime = DateTimeField(default=datetime.datetime.now,verbose_name=u'创建时间')
    
    def __unicode__(self):
        return self.role_name
    
    @staticmethod
    def get_perms_choices():
        return admin.get_perms()
    
class RoleAdmin(ModelAdmin):
    verbose_name = u'角色'
    menu_grup = 'group_system'
    menu_index = 2
    exclude = ('name', 'perms_other', 'reserve', 'ctime')
    columns = ('role_name', 'ctime')
    
class RolePermBase(db.CrudModel):
    u'''角色权限'''
    role = ForeignKeyField(RoleBase, verbose_name = u'角色', db_column='role_id', related_name='rel_perms')
    perm = ForeignKeyField(PermissionBase, verbose_name = u'权限', db_column='perm_id', related_name='rel_roles')
    ctime = DateTimeField(default=datetime.datetime.now,verbose_name=u'创建时间')
    
class RolePermAdmin(ModelAdmin):
    verbose_name = u'角色权限'
    menu_grup = 'group_system'
    menu_index = 5
    
class UserRoleBase(db.CrudModel):
    u'''用户角色'''
    user = ForeignKeyField(UserBase, verbose_name = u'用户', db_column='user_id', related_name='rel_roles')
    role = ForeignKeyField(RoleBase, verbose_name = u'角色', db_column='role_id', related_name='rel_users')
    ctime = DateTimeField(default=datetime.datetime.now,verbose_name=u'创建时间')

class UserRoleAdmin(ModelAdmin):
    verbose_name = u'用户角色'
    menu_grup = 'group_system'
    menu_index = 3