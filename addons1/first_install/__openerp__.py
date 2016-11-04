# -*- coding: utf-8 -*-
{
    'name': 'first install',  # 模块名
    'description': '自动安装全部模块',  # 注释
    'author': 'ZWG',  # 作者
    'website': 'www.surveyerp.xicp.net:8072',  # 网站
    'category': 'other',  # 分类
    'version': '1.0',  # 版本号
    'depends': [
        'account_accountant',
        'sale',
        'purchase',
        'purchase_hb',
        'l10n_cn_small_business',

        'oa_workflow',
        'message_notice',
        'hd_quote',

    ],  # 依赖
    'data': [
        # 'views/sale_quotation_view.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'auto_install': False,  # 是否自动安装
    'installable': True,  # 是否可安装
}
