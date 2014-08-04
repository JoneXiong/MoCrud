# -*- coding: utf-8 -*-
'''
crud
'''

__version__ = "0.1"

from mole.const import TEMPLATE_PATH
from mole.mole import default_app
TEMPLATE_PATH.append('./lib/mocrud/templates/')

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
@m_app.route('/static_crud/:filename#.*#',name='admin.static')
def admin_static(filename):
    return static_file(filename, root='./lib/mocrud/static')

#from db import Database
#from apps import crud_db_config
#db = Database(crud_db_config)