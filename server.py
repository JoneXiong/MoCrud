# -*- coding: utf-8 -*-
##################### 系统环境设置 #######################
def set_lib_path():
    import sys
    import os
    sys.path.append('./libs')
set_lib_path()

import mocrud
import crud_example


from mole.mole import default_app
#加入SessionMiddleware 中间件
from mole.sessions import SessionMiddleware
app = SessionMiddleware(app=default_app(), cookie_key="457rxK8ytkKiqkfqwfoiQS@kaJSFOo8h",no_datastore=True)


#运行服务
from mole import run
if __name__  == "__main__":
    run(app=app,host='0.0.0.0', port=8081)