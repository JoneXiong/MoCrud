# coding = utf-8
from mole import route
from mole import request
from mole import response
from mole import redirect
from mole.template import jinja2_template

@route('/',name='homepage')
def homepage():
    from mocrud.admin import admin
    return jinja2_template('admin/model_grup.html',
        panels=admin.get_panels(),
        model_grup = 'default',
        model_admins=admin.get_grup_admins('default'),
        **admin.template_helper.get_helper_context()
    )