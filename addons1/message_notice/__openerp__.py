# -*- coding: utf-8 -*-
{
    'name': 'message notice',  # 模块名
    'description': '消息通知',  # 注释
    'author': 'ZWG',  # 作者
    'website': 'www.surveyerp.xicp.net:8072',  # 网站
    'category': 'other',  # 分类
    'version': '1.0',  # 版本号
    'depends': [
        'oa_workflow',
        'load_logs',
        'm2m_multi_selection',
        'ding_talk',
    ],  # 依赖
    'data': [
        'security/message_notice_security.xml',
        'security/ir.model.access.csv',

        'views/message_notice_view.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'auto_install': False,  # 是否自动安装
    'installable': True,  # 是否可安装
}
