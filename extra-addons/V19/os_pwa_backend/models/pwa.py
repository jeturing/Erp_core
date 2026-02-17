# Part of Odoo Stars .
from odoo import models, fields, api

BLACKLIST = ["os_pwa_backend"]


class PWAConfig(models.Model):
    _name = 'os.pwa'
    _description = 'PWA'

    name = fields.Char("Name", required=True, default='Odoo Stars PWA')
    short_name = fields.Char("Short Name", required=True, default='OS-PWA')
    description = fields.Text("Short description")
    theme_color = fields.Char("Theme Color", default='#7a19ca')
    background_color = fields.Char("Background Color", default='#cbb5dd')
    display = fields.Selection(string="Display",
                               selection=[('fullscreen', 'Fullscreen'),
                                          ('standalone', 'Standalone'),
                                          ('minimal-ui', 'Minimal')],
                               default='standalone')
    display_override = fields.Selection(
        selection=[('fullscreen', 'Fullscreen'),
                   ('standalone', 'Standalone'),
                   ('minimal-ui', 'Minimal'),
                   ('browser', 'browser'),
                   ('window-controls-overlay', 'window-controls-overlay'),
                   ],
        default='standalone')

    orientation = fields.Selection(string="Orientation", selection=[('any', 'Any'), ('natural', 'Natural'), ('landscape', 'Landscape'), ('portrait', 'Portrait')])
    icon = fields.Image(
        help='Set a big app icon. Must be at least 512x512 pixels')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id.id)
    shortcut_ids = fields.Many2many('ir.module.module', string='Shortcuts', domain=[('state', '=', 'installed'), ('application', '=', True), ('name', 'not in', BLACKLIST)])

    icon_64 = fields.Image("PWA icon 64", related="icon", max_width=64, max_height=64, store=True)
    icon_128 = fields.Image("PWA icon 128", related="icon", max_width=128, max_height=128, store=True)
    icon_144 = fields.Image("PWA icon 144", related="icon", max_width=144, max_height=144, store=True)
    icon_152 = fields.Image("PWA icon 152", related="icon", max_width=152, max_height=152, store=True)
    icon_192 = fields.Image("PWA icon 192", related="icon", max_width=192, max_height=192, store=True)
    icon_200 = fields.Image("PWA icon 200", related="icon", max_width=200, max_height=200, store=True)
    icon_256 = fields.Image("PWA icon 256", related="icon", max_width=256, max_height=256, store=True)
    icon_462 = fields.Image("PWA icon 462", related="icon", max_width=462, max_height=462, store=True)
    icon_512 = fields.Image("PWA icon 512", related="icon", max_width=512, max_height=512, store=True)

    screenshot_1 = fields.Image("screenshot 1", help="Set This screenshot for desktop")
    screenshot_2 = fields.Image("screenshot 2", help="Set This screenshot for desktop")
    screenshot_3 = fields.Image("screenshot 3", help="Set This screenshot for desktop")
    screenshot_4 = fields.Image("screenshot 4", help="Set This screenshot for Mobile")
    screenshot_5 = fields.Image("screenshot 5", help="Set This screenshot for Mobile")
    screenshot_6 = fields.Image("screenshot 6", help="Set This screenshot for Mobile")
    screenshot_7 = fields.Image("screenshot 7", help="Set This screenshot for Mobile")
    screenshot_8 = fields.Image("screenshot 8", help="Set This screenshot for Mobile")
