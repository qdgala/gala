# -*- coding: utf-8 -*-
{
    'name': 'load logs',  # 模块名
    'description': 'load logs',  # 注释
    'author': 'ZWG',  # 作者
    'website': 'www.surveyerp.xicp.net:8072',  # 网站
    'category': 'other',  # 分类
    'version': '1.0',  # 版本号
    'depends': [],  # 依赖
    'data': [
        'security/ir.model.access.csv',

        'views/load_logs_view.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'auto_install': False,  # 是否自动安装
    'installable': True,  # 是否可安装
}
