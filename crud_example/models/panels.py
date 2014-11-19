# -*- coding: utf-8 -*-
import datetime
from mole import request, redirect

from mocrud.admin import admin, AdminPanel
from mocrud.auth import auth
#from mocrud.filters import QueryFilter

from note_model import Note
from user_model import User
from message_model import Message


class NotePanel(AdminPanel):
    verbose_name = u'日志'
    template_name = 'notes_panel.html'

    def get_urls(self):
        return (
            ('/create/', self.create),
        )

    def create(self):
        if request.method == 'POST':
            if request.forms.get('message'):
                Note.create(
                    user=auth.get_logged_in_user(),
                    message=request.forms['message'],
                )
        next = request.forms.get('next') or self.dashboard_url()
        return redirect(next)

    def get_context(self):
        return {
            'note_list': Note.select().order_by(Note.created_date.desc()).paginate(1, 3)
        }

class UserStatsPanel(AdminPanel):
    verbose_name = u'用户统计'
    template_name = 'user_panel.html'

    def get_context(self):
        last_week = datetime.datetime.now() - datetime.timedelta(days=7)
        signups_this_week = User.select().where(User.join_date > last_week).count()
        messages_this_week = Message.select().where(Message.pub_date > last_week).count()
        return {
            'signups': signups_this_week,
            'messages': messages_this_week,
        }

#admin = Admin(app, auth)
#auth.register_admin(admin)
#admin.register(Relationship)
#admin.register(Note, NoteAdmin)

#from zk_models import Checkinout
#admin.register(Checkinout)

admin.register_panel('notes', NotePanel)
admin.register_panel('user_stats', UserStatsPanel)


