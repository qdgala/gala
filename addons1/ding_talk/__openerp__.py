# -*- coding: utf-8 -*-
{
    'name': 'ding talk',  # 模块名
    'description': 'ding talk',  # 注释
    'author': 'ZWG',  # 作者
    'website': 'www.surveyerp.xicp.net:8072',  # 网站
    'category': 'other',  # 分类
    'version': '1.0',  # 版本号
    'depends': [
        'hr',
    ],  # 依赖
    'data': [
        'views/hr_employee.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'auto_install': False,  # 是否自动安装
    'installable': True,  # 是否可安装
}
