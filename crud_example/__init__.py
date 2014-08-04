﻿# -*- coding: utf-8 -*-

menus = (
         ('aboutEmp',u'菜单组一', 'grup_chat'),
         ('baseinfo',u'菜单组二', 'grup_chart'),
         ('reportEmp',u'菜单组二', 'grup_disc')
         )

####### Crud 初始化 #######
from mocrud.api import setup,uncheck
import models
setup(models)
uncheck()

####### 自定义视图 #########
import routes

from mole.const import TEMPLATE_PATH
TEMPLATE_PATH.append('./crud_example/templates/')