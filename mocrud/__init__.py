# -*- coding: utf-8 -*-
'''
crud
'''
__version__ = "0.1"

import os

from mole.const import TEMPLATE_PATH
from mole.mole import default_app

cur = os.path.split(os.path.realpath(__file__))[0]
templates_path = os.path.join(cur,'templates')
TEMPLATE_PATH.append(templates_path)

try:
    import mosys
    conf = mosys.apps
except:
    conf = None
    
m_app = default_app()
if conf:
    if hasattr(conf,'app'):
        if conf.app:
            m_app = conf.app

from mole import static_file
static_path = os.path.join(cur,'static')
@m_app.route('/static_crud/:filename#.*#',name='admin.static')
def admin_static(filename):
    return static_file(filename, root=static_path)

#from db import Database
#from apps import crud_db_config
#db = Database(crud_db_config)