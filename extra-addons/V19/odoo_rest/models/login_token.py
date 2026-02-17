from odoo import models, fields, _, api
from odoo.exceptions import UserError
import random
import string
import jwt
import datetime
import logging
_logger = logging.getLogger(__name__)


class LoginToken(models.Model):
    _name = "login.token"
    _description = "Login Token"

    def user_id_domain(self):
        _logger.info('============= context ===%r=======', self.env.context)
        return []
    

    login_token_compute = fields.Char("Login Token " , compute="get_token", readonly=True, default="")
    login_token = fields.Char("Login Token", readonly=True)
    api_id = fields.Many2one(string="API ID", comodel_name="rest.api")
    user_id = fields.Many2one(string="USER ID", comodel_name="res.users", domain=user_id_domain)


    limit_for_hits = fields.Boolean(string="Limit for Hits", default=False, related="api_id.limit_for_hits")
    hit_limits = fields.Integer( string='Limit',related="api_id.hit_limits")
    hit_count = fields.Integer( string='Limit')
    last_hit_date = fields.Date("Last hit date")


    def check_throttling(self):
        if self.limit_for_hits:
            if not self.last_hit_date or self.last_hit_date<fields.date.today():
                self.hit_count=1
                self.last_hit_date=fields.date.today()
                return True
            else:
                if self.hit_count<self.hit_limits:
                    self.hit_count+=1
                    return True
                else:
                    return False
        else:
            return True
    

    def get_token(self):
        for rec in self:
            if rec.api_id and rec.user_id:
                token = {"login": rec.user_id.login, "uid": rec.user_id.id }
                rec.login_token_compute = jwt.encode(token,rec.api_id.api_key , algorithm="HS256")
            else:
                rec.login_token_compute=""
            
            rec.login_token= rec.login_token_compute

    @api.model_create_multi
    def create(self, vals):
        id = False
        for val in vals:
            id = self.env['login.token'].search([('api_id','=',val['api_id']),('user_id','=',val['user_id'])])
        
        if id:
            raise UserError("token already generated for this api key")
        else:
            res = super(LoginToken,self).create(vals)
            return res
    
    def delete_user_token(self):
        self.unlink()
