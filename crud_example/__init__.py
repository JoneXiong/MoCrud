# -*- coding: utf-8 -*-

####### Crud 初始化 #######
from mocrud.api import setup,uncheck
import models
setup(models)
uncheck()

####### 自定义视图 #########
import routes

from mole.const import TEMPLATE_PATH
TEMPLATE_PATH.append('./crud_example/templates/')