# -*- coding: utf-8 -*-
{
    'name': 'hd quote',  # 模块名
    'description': '华丹 报价单',  # 注释
    'author': 'ZWG',  # 作者
    'website': 'www.surveyerp.xicp.net:8072',  # 网站
    'category': 'other',  # 分类
    'version': '1.0',  # 版本号
    'depends': [
        'sale',
        'product',
        'oa_workflow'
    ],  # 依赖
    'data': [
        'data/ir.config_parameter.csv',

        # 'views/hd_xt_view.xml',
        'views/hd_quote_view.xml',
        # 'views/sale_quotation_view.xml',


        'wizard/hd_product_import.xml',

        'report/hd_quote_report_view.xml',
        'report/hd_quote_report2_view.xml',
        'quote_pzb_view.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'auto_install': False,  # 是否自动安装
    'installable': True,  # 是否可安装
}
