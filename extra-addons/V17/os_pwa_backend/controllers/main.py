# Part of Odoo Stars .
import json
from odoo import http
from odoo.tools.translate import _
import base64
from io import BytesIO
from odoo.tools import ustr, file_open

from odoo import SUPERUSER_ID

from odoo.tools.mimetypes import guess_mimetype
import logging
from odoo.tools import ImageProcess

logger = logging.getLogger(__name__)

import mimetypes
from odoo.exceptions import AccessError


class PWAController(http.Controller):

    def _get_pwa_shortcuts(self, pwa_record):
        shortcuts = []
        if pwa_record.shortcut_ids:
            module_names = []
            for module in pwa_record.shortcut_ids:
                module_names.append(module.name)

            try:
                module_ids = http.request.env['ir.module.module'].sudo().search([('state', '=', 'installed'), ('name', 'in', module_names)]).sorted(key=lambda r: module_names.index(r["name"]))
            except AccessError:
                return []
            menu_roots = http.request.env['ir.ui.menu'].with_user(SUPERUSER_ID).search([('parent_id', '=', False)])
            datas = http.request.env['ir.model.data'].sudo().search([('model', '=', 'ir.ui.menu'),
                                                                     ('res_id', 'in', menu_roots.ids),
                                                                     ('module', 'in', module_names)])
            for module in module_ids:
                data = datas.filtered(lambda res: res.module == module.name)
                if data:
                    shortcuts.append({
                        'name': module.display_name,
                        'url': '/web#menu_id=%s' % data.mapped('res_id')[0],
                        'description': module.summary,
                        'icons': [{
                            'sizes': '100x100',
                            'src': module.icon,  # FIXME change icon based on theme pack ?
                            'type': mimetypes.guess_type(module.icon)[0] or 'image/png'
                        }]
                    })
        return shortcuts

    def get_asset_urls(self, bundle_name):
        assets = http.request.env["ir.qweb"].sudo()._get_asset_nodes(bundle_name, debug=http.request.session.debug, js=True, css=True)
        urls = []
        for asset in assets:
            if asset[0] == 'link':
                urls.append(asset[1]['href'])
            if asset[0] == 'script':
                urls.append(asset[1]['src'])
        return urls

    @http.route('/service-worker.js', type='http', auth="public")
    def pwa_http(self):
        with file_open('os_pwa_backend/static/src/js/service_worker.js') as f:
            body = f.read()
        urls = []
        urls.extend(self.get_asset_urls("web.assets_common"))
        urls.extend(self.get_asset_urls("web.assets_backend"))
        version_list = []
        company_id = http.request.env.user.company_id.id
        for url in urls:
            version_list.append(url.split('/')[3])
        cache_version = '-'.join(version_list)
        cache_name = cache_version + '-pwa_cache-' + str(company_id)
        body = body.replace('__OS__CACHE__NAME__', cache_name)
        response = http.request.make_response(body, [('Content-Type', 'text/javascript'), ("Content-Length", len(body)), ])
        return response

    def _get_pwa_screenshots(self, pwa_record, company):
        screenshots = []
        for number in [1, 2, 3, 4, 5, 6, 7, 8]:
            screenshot = getattr(pwa_record, "screenshot_" + str(number))
            if screenshot:
                content = base64.b64decode(screenshot)
                mimetype = guess_mimetype(content)
                image = ImageProcess(content)
                w, h = image.image.size
                data = {
                    "src": '/os/pwa/screenshot/' + str(company) + "/" + str(number),
                    "sizes": "{}x{}".format(str(w), str(h)),
                    "type": mimetype,
                }

                if number in [1, 2, 3]:
                    data.update({'form_factor': 'wide'})
                screenshots.append(data)
        return screenshots

    def _get_pwa_icons(self, pwa_icon, company):
        icons = []
        if not pwa_icon:
            for size in [
                (64, 64),
                (128, 128),
                (144, 144),
                (152, 152),
                (192, 192),
                (200, 200),
                (256, 256),
                (462, 462),
                (512, 512),
            ]:
                icons.append(
                    {
                        "src": "/os_pwa_backend/static/src/img/icons/icon%sx%s.png"
                               % (str(size[0]), str(size[1])),
                        "sizes": "{}x{}".format(str(size[0]), str(size[1])),
                        "type": "image/png",
                    }
                )
        else:
            content = base64.b64decode(pwa_icon)
            mimetype = guess_mimetype(content)

            for size in [
                (64, 64),
                (128, 128),
                (144, 144),
                (152, 152),
                (192, 192),
                (200, 200),
                (256, 256),
                (462, 462),
                (512, 512),
            ]:
                icons.append(
                    {
                        "src": '/os/pwa/icon/' + str(company) + "/" + str(size[0]),
                        "sizes": "{}x{}".format(str(size[0]), str(size[1])),
                        "type": mimetype,
                    }
                )

        return icons

    def process_manifest_json(self, company):
        company = company or 1
        data = {
            "name": "Odoo Stars PWA",
            "short_name": "OS-PWA",
            "description": _("""Butterfly, The most customizable Odoo Backend Theme Ever built, with trending designs and many features.Creative & unique including many features like several icons pack, app drawer builder, it is not only a theme but an Odoo backend theme builder."""),
            "scope": "/",
            "start_url": "/web",
            "background_color": "#cbb5dd",
            "theme_color": "#7a19ca",
            "display": "standalone",
            "icons": [{
                "src": "/os_pwa_backend/static/src/img/icon/icon.png",
                "sizes": "192x192",
                "type": "image/png"
            }],
        }
        pwa_record = http.request.env['os.pwa'].sudo().search([('company_id', '=', int(company))], limit=1)
        if pwa_record:
            if pwa_record.name:
                data.update({'name': pwa_record.name})
            if pwa_record.short_name:
                data.update({'short_name': pwa_record.short_name})
            if pwa_record.theme_color:
                data.update({'theme_color': pwa_record.theme_color})
            if pwa_record.background_color:
                data.update({'background_color': pwa_record.background_color})
            if pwa_record.display:
                data.update({'display': pwa_record.display})
            if pwa_record.orientation:
                data.update({'orientation': pwa_record.orientation})
            if pwa_record.description:
                data.update({'description': _(pwa_record.description)})

            icons = self._get_pwa_icons(pwa_record.icon, company)
            screenshots = self._get_pwa_screenshots(pwa_record, company)

            if len(icons) > 0:
                data.update({'icons': icons})

            if len(screenshots) > 0:
                data.update({'screenshots': screenshots})

            if pwa_record.shortcut_ids:
                shortcuts = self._get_pwa_shortcuts(pwa_record)
                data.update({'shortcuts': shortcuts})

        return data

    def process_icon(self, company, size):
        pwa_record = http.request.env['os.pwa'].sudo().search([('company_id', '=', int(company))], limit=1)
        if pwa_record:
            pwa_icon = getattr(pwa_record, "icon_" + str(size))
            if pwa_icon:
                content = base64.b64decode(pwa_icon)
                pwa_icon_mimetype = guess_mimetype(content)
                icon = BytesIO(base64.b64decode(pwa_icon))
                return http.request.make_response(icon.read(), [('Content-Type', pwa_icon_mimetype)])
            else:
                return "/os_pwa_backend/static/src/img/icons/icon%sx%s.png" % (size, size)

    def process_screenshot(self, company, number):
        pwa_record = http.request.env['os.pwa'].sudo().search([('company_id', '=', int(company))], limit=1)
        if pwa_record:
            pwa_screenshot = getattr(pwa_record, "screenshot_" + str(number))
            if pwa_screenshot:
                content = base64.b64decode(pwa_screenshot)
                pwa_screenshot_mimetype = guess_mimetype(content)
                icon = BytesIO(base64.b64decode(pwa_screenshot))
                return http.request.make_response(icon.read(), [('Content-Type', pwa_screenshot_mimetype)])

    @http.route('/os/pwa/manifest/json/<string:cid>', type='http', auth="public")
    def get_manifest_json(self, **post):
        company = post.get('cid')
        return json.dumps(self.process_manifest_json(company))

    @http.route('/os/pwa/icon/<string:cid>/<string:size>', type='http', auth="none")
    def get_icon(self, **post):
        company = post.get('cid')
        size = post.get('size')
        return self.process_icon(company, str(size))

    @http.route('/os/pwa/screenshot/<string:cid>/<string:number>', type='http', auth="none")
    def get_screenshot(self, **post):
        company = post.get('cid')
        number = post.get('number')
        return self.process_screenshot(company, str(number))

    @http.route('/os/pwa/shortcut/<string:id_shortcut>', type='http', auth="none")
    def get_icon_shortcut(self, **post):
        id_shortcut = post.get('id_shortcut')
        shortcut_record = http.request.env['os.pwa.shortcut'].sudo().search([('id', '=', int(id_shortcut))], limit=1)
        shortcut_icon = shortcut_record.icon_192

        if shortcut_icon:
            content = base64.b64decode(shortcut_icon)
            mimetype = guess_mimetype(content)
            icon = BytesIO(base64.b64decode(shortcut_icon))
            return http.request.make_response(icon.read(), [('Content-Type', mimetype)])

    @http.route('/pwa/offline', type='http', auth='none')
    def offline(self):
        """ Returns the offline page used by the 'website' PWA
        """
        with file_open('os_pwa_backend/static/src/js/offline.html', 'rb') as f:
            body = f.read()

        return http.request.make_response(body, headers=[('Content-Type', 'text/html')])
