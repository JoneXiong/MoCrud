MoCrud
======

crud for Mole with peewee
libs 包含了 MoCrud依赖的包：mole、jinja2、peewee、wtforms

#### <i class="icon-file"></i> 概述
MoCrud是一个用于快速构建关系型数据库数据管理应用的Python Web应用框架，本身是一个 [Mole](https://github.com/JoneXiong/Mole) 应用，数据库交互使用了开源的轻量级Python ORM [peewee](https://github.com/coleifer/peewee)，web表单的生成采用简单易扩展的[wtforms](https://github.com/wtforms/wtforms)，搭配jinja2模块引擎，除此之外不依赖于其他三方库。

#### <i class="icon-pencil"></i> 特点

- 简洁灵活，部署方便，扩展性极强
- 快速开发，基本的crud功能自动产生，同时对其自定义也很方便容易
- 小巧的同时不失强大，基本具备Django Admin功能，而且极易做二次开发，上手较容易
- 模块化良好，使用时只需`import`，模板结构清晰，可直接继承或copy后修改
- 多种数据库的支持，继承peewee，可以支持MySQL、Sqlite、PostgreSQL等类型数据库

#### 项目地址
<https://github.com/JoneXiong/MoCrud>

#### <i class="icon-hdd"></i> 使用
```python
from mole import run
from mole.mole import default_app
from mole.sessions import SessionMiddleware

from mocrud.api import setup

import models
setup(models)

from mole import run
if __name__  == "__main__":
	app = SessionMiddleware(app=default_app(), cookie_key="you_key_xxxxx")
    run(app=app,host='0.0.0.0', port=8080)
```
其中models(包或.py)内的类即为我们定义ORM模型

项目已经包含一个demo应用`crud_example`,可以通过以下命令直接运行
```
$ python server.py
```


详细说明,请移步到 [MoCrud详细说明文档](/blog/2014/12/22/mocrud_detail.html)

#### <i class="icon-folder-open"></i> 案例
[bookM](http://git.oschina.net/jone/bookM) 一个小巧的企业内部图书订阅系统
