# -*- coding: utf-8 -*-
{
    'name': 'oa workflow',  # 模块名
    'description': 'OA工作流',  # 注释
    'author': 'ZWG',  # 作者
    'website': 'www.surveyerp.xicp.net:8072',  # 网站
    'category': 'other',  # 分类
    'version': '1.0',  # 版本号
    'depends': [
        'hr',
        'stock',
        'wkf_logs',
        'ding_talk',
    ],  # 依赖
    'data': [
        'data/report_paperformat.xml',
        'data/users_data.xml',
        'data/hr_department_data.xml',
        'data/hr_employee_data.xml',
        'data/hr_department_data2.xml',

        'security/wkf_workflow_security.xml',
        'security/ir.model.access.csv',

        'security/oa_recruitment_security.xml',
        'security/oa_zhuanzheng_security.xml',
        'security/oa_qingjia_security.xml',
        'security/oa_lizhi_security.xml',
        'security/oa_jiekuan_security.xml',
        'security/oa_feiyongbx_security.xml',
        'security/oa_yunfeibx_security.xml',
        'security/oa_fukuan_security.xml',
        'security/oa_yongzhang_security.xml',
        'security/oa_zhichancg_security.xml',
        'security/oa_bangongcg_security.xml',
        'security/oa_gongzuolx_security.xml',
        'security/oa_chuchai_security.xml',
        'security/oa_jiangcheng_security.xml',
        'security/oa_ruzhi_security.xml',

        'views/oa_recruitment_view.xml',
        'views/oa_zhuanzheng_view.xml',
        'views/oa_qingjia_view.xml',
        'views/oa_lizhi_view.xml',
        'views/oa_jiekuan_view.xml',
        'views/oa_feiyongbx_view.xml',
        'views/oa_yunfeibx_view.xml',
        'views/oa_fukuan_view.xml',
        'views/oa_yongzhang_view.xml',
        'views/oa_zhichancg_view.xml',
        'views/oa_bangongcg_view.xml',
        'views/oa_clxx_view.xml',
        'views/oa_clxs_view.xml',
        'views/oa_gongzuolx_view.xml',
        'views/oa_chuchai_view.xml',
        'views/oa_jiangcheng_view.xml',
        'views/oa_ruzhi_view.xml',

        'views/lines/edu_exp_view.xml',
        'views/lines/work_exp_view.xml',
        'views/lines/family_info_view.xml',
        'views/lines/oa_chuchai_line_view.xml',

        'views/base/extend_res_users_view.xml',

        'report/oa_recruitment_report_view.xml',
        'report/oa_zhuanzheng_report_view.xml',
        'report/oa_qingjia_report_view.xml',
        'report/oa_lizhi_report_view.xml',
        'report/oa_jiekuan_report_view.xml',
        'report/oa_feiyongbx_report_view.xml',
        'report/oa_yunfeibx_report_view.xml',
        'report/oa_fukuan_report_view.xml',
        'report/oa_yongzhang_report_view.xml',
        'report/oa_zhichancg_report_view.xml',
        'report/oa_bangongcg_report_view.xml',
        'report/oa_gongzuolx_report_view.xml',
        'report/oa_chuchai_report_view.xml',
        'report/oa_jiangcheng_report_view.xml',
        'report/oa_ruzhi_report_view.xml',

        'workflow/oa_recruitment_workflow.xml',
        'workflow/oa_zhuanzheng_workflow.xml',
        'workflow/oa_qingjia_workflow.xml',
        'workflow/oa_lizhi_workflow.xml',
        'workflow/oa_jiekuan_workflow.xml',
        'workflow/oa_feiyongbx_workflow.xml',
        'workflow/oa_yunfeibx_workflow.xml',
        'workflow/oa_fukuan_workflow.xml',
        'workflow/oa_yongzhang_workflow.xml',
        'workflow/oa_zhichancg_workflow.xml',
        'workflow/oa_bangongcg_workflow.xml',
        'workflow/oa_gongzuolx_workflow.xml',
        'workflow/oa_chuchai_workflow.xml',
        'workflow/oa_jiangcheng_workflow.xml',
        'workflow/oa_ruzhi_workflow.xml',
    ],
    'qweb': [
        # 'static/src/xml/*.xml',
    ],
    'auto_install': False,  # 是否自动安装
    'installable': True,  # 是否可安装
}
