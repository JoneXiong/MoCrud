# -*- coding: utf-8 -*-


from peewee import Model, SqliteDatabase

database = SqliteDatabase('./crud_example/example.db', check_same_thread=False, **{})
#database = PostgresqlDatabase('pbx', **{'user': 'mocrud'})
#database = MySQLDatabase('dc', **{'passwd': 'root', 'host': '127.0.0.1', 'user': 'root'})


class BaseModel(Model):
    class Meta:
        database = database