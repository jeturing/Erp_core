# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Odoo Rest API",
  "summary"              :  """The module create RESTful API for Odoo and allows you to access and modify data using HTTP requests to manage fetch and manage data from the Odoo. Keywords: Rest| API | Odoo RESTful API | Odoo data management API | Odoo HTTP requests | Access Odoo data via API | Odoo API for data modification | Odoo REST API module | Odoo API for CRUD operations | RESTful API for Odoo ERP | HTTP-based Odoo API | Manage Odoo records via API | Odoo data access using HTTP requests | Odoo API for automation | Modify Odoo data with API | Odoo REST API for business | External access to Odoo data API""",
  "category"             :  "Extra Tools",
  "version"              :  "1.2.3",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-REST-API.html",
  "description"          :  """Odoo Rest Api
Add record to database
Delete record to Database
Modify data in Odoo database
Use HTTP to modify data
RESTful API in Odoo
Use HTTP requests to fetch data in Odoo""",
  "live_test_url"        :  "https://store.webkul.com/Odoo-REST-API.html#",
  "depends"              :  ['base','web'],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'template/swagger_doc.xml',
                             'views/rest_api_views.xml',
                             'views/templates.xml',
                             'views/res_user.xml',
                             'views/login_token.xml',
                            ],
  
  "demo"                 :  ['demo/demo.xml'],
  "assets"               : {
                            
                            "odoo_rest.swagger_assets":[
                                '/odoo_rest/static/lib/swagger-ui/swagger-ui-bundle.js',
                                '/odoo_rest/static/lib/swagger-ui/swagger-ui-standalone-preset.js',
                                '/odoo_rest/static/src/components/docs/doc.scss',
                                '/odoo_rest/static/lib/swagger-ui/swagger-ui.css',
                                '/odoo_rest/static/src/js/swagger_doc_dark_mode.js'
                            ]
                           },
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  99,
  "currency"             :  "USD",
  "external_dependencies":  {'python': ['Pyjwt']},
}
