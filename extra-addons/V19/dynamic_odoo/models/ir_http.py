from odoo.models import BaseModel, AbstractModel


class Http(AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(Http, self).session_info()
        if self.env.user.has_group('dynamic_odoo.odoo_studio'):
            result['showStudio'] = True
        result['user_groups'] = self.env.user.groups_id.ids
        return result
