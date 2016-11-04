#Hr employee tree structure..
{
    'name':'Web Organization Tree 2',
    'version': '1.0',
    'author': 'leetaizhu',
    'category': 'Hidden',
    'website': 'http://www.odo0.com',
    'summary': 'Organization Tree Chart',
    'description': """
Human Resources Management
==========================
    This is Application of Organization Tree Chart displayee in View

    """,
    # 'depends': ['web_graph'],
    'data': ['views/web_organization_tree.xml',
    ],
    'qweb': [
        'static/src/xml/web_organization_tree.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
