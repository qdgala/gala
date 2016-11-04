#Hr employee tree structure..
{
    'name':'hr_organization_tree',
    'version': '1.0',
    'author': 'leetaizhu',
    'category': 'Human Resources',
    'website': 'http://www.openerp.com',
    'summary': 'HR Organization Chart Employee',
    'description': """
Human Resources Management
==========================
    This is Application of Employee of Organization displayee in Hierarchycal View

    """,
    'depends': ['hr','web_organization_tree'],
    'data': ['hr_organization_tree_view.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
