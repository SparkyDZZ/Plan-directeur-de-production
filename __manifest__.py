{
    'name' : 'Plan Directeur De Production',
    'version' : '1.0',
    'summary': 'Owl MPS Learn',
    'sequence': -1,
    'description': """
        Owl Learn
    """,
    'category': 'Manufacturing',
    'depends' : ['mrp', 'base'],
    'images' : ['static/description/icon.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/mps_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'assets' : {
        'web.assets_backend': [
            'owl/static/src/components/*/*.scss',
            'owl/static/src/components/*/*.js',
        ],
        'web.assets_qweb': [
            'owl/static/src/components/*/*.xml',
        ],
    },
}