{
    'name': 'Activity Management',
    'version': '19.0.1.0.1',
    'category': 'Extra Tools',
    'summary': 'Dashboard for streamlined management of all activities.',
    'description': """Simplify activity management with a comprehensive 
     dashboard, offering centralized control and oversight for seamless 
     organization-wide coordination and tracking.""",
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/activity_tag_views.xml',
        'views/activity_dashbord_views.xml',
        'views/mail_activity_views.xml',
    ],
    'assets': {'web.assets_backend': ['activity_dashboard_mngmnt/static/src/css/dashboard.css', 'activity_dashboard_mngmnt/static/src/css/style.scss', 'activity_dashboard_mngmnt/static/src/css/material-gauge.css', 'activity_dashboard_mngmnt/static/src/xml/activity_dashboard_template.xml', 'activity_dashboard_mngmnt/static/src/js/activity_dashboard.js']},
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
    'application': True,
}
