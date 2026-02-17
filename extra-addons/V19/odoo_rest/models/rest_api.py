# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################
from odoo import models, fields,_, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools.misc import file_path
from odoo.fields import Field, Datetime, Command
from collections import defaultdict
from odoo.models import BaseModel
import random
import string
import datetime
import base64
import logging
_logger = logging.getLogger(__name__)

# LOG_ACCESS_COLUMNS = ['create_uid', 'create_date', 'write_uid', 'write_date']
# MAGIC_COLUMNS = ['id'] + LOG_ACCESS_COLUMNS
MAGIC_COLUMNS = []


def _default_unique_key(size, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))



class BaseModel(models.AbstractModel):
    _inherit = 'base'


    @api.returns(None, lambda value: value[0])
    def rest_copy_data(self, default=None, fields=[]):
        self.ensure_one()

        if '__copy_data_seen' not in self._context:
            self = self.with_context(__copy_data_seen=defaultdict(set))
        seen_map = self._context['__copy_data_seen']

        if self.id in seen_map[self._name]:
            return
        seen_map[self._name].add(self.id)

        default = dict(default or [])
        blacklist = set(MAGIC_COLUMNS + ['parent_path'])
        whitelist = set(
            name for name, field in self._fields.items() if not field.inherited)

        def blacklist_given_fields(model):
            for parent_model, parent_field in model._inherits.items():
                blacklist.add(parent_field)
                if parent_field in default:
                    blacklist.update(
                        set(self.env[parent_model]._fields) - whitelist)
                else:
                    blacklist_given_fields(self.env[parent_model])

        blacklist_given_fields(self)

        fields_to_copy = {name: field
                          for name, field in self._fields.items()
                          if name not in default and name not in blacklist}

        for name, field in fields_to_copy.items():
            if not fields or  name in fields:
                if field.type == 'one2many' or field.type == 'many2many':
                    try:
                        lines = [{'id':rec.id,'name':rec.name} for rec in self[name].sorted(key='id')]
                    except:
                        lines = [{'id':rec.id} for rec in self[name].sorted(key='id')]
                    default[name] = lines
                elif field.type == 'binary':
                    default[name] = False
                else:
                    default[name] = field.convert_to_write(self[name], self)
        return [default]


class RestAPI(models.Model):
	_name = "rest.api"
	_description = "RESTful Web Services"

	def write(self, val):
		if not val.get("advanced_features", True):
			val['api_validity'] = False
			val['limit_for_hits'] = False
		res = super(RestAPI, self).write(val)
		return res

	def _default_unique_key(size, chars=string.ascii_uppercase + string.digits ):
		return ''.join(random.choice(chars) for x in range(size))

	@api.model
	def _check_permissions(self, model_name,user_id , context=None):
		response = {'success':True, 'message':'OK','permissions':{}}
		model_exists = self.env['ir.model'].sudo().search([('model','=',model_name)])
		if not model_exists:
			response['success'] = False
			response['responseCode'] = 401
			response['message'] = "Model(%s) doen`t exists !!!"%model_name
			return response
		elif self.availabilty == "all":
			response['success']= True
			response['responseCode'] = 200
			response['message'] = "Allowed %s Models Permission" % (model_exists.name)
			response['model_id'] = model_exists.id
			response['permissions'].update({'read':True,'write':True,'delete':True,'create':True})
		else:
			#Check for existense
			resource_allowed = self.env['rest.api.resources'].sudo().search([('api_id','=',self.id),('model_id','=',model_exists.id)])
			if resource_allowed:
				response['success'] = True
				response['responseCode'] = 200
				response['message'] = "Allowed %s Models Permission: %s" % (model_exists.name, self.availabilty)
				response['model_id'] = model_exists.id
				response['permissions'].update({'read': resource_allowed.read_ok, 'write': resource_allowed.write_ok, 'delete': resource_allowed.unlink_ok, 'create': resource_allowed.create_ok})
			else:
				response['success'] = False
				response['responseCode'] = 403
				response['message'] = "Sorry,you don`t have enough permission to access this Model(%s). Please consult with your Administrator."%model_name
				return response
		if user_id != 1:
			list_access_rights_id = self.env['res.users'].browse(user_id).action_show_accesses().get('domain')[0][2]
			current_model_access_rights = self.env['ir.model.access'].search([('model_id.model','=',model_name),('id','in',list_access_rights_id)])
			read_perm = False
			write_perm = False
			create_perm = False
			unlink_perm = False
			for i in current_model_access_rights:
				read_perm = read_perm or i.perm_read
				write_perm = write_perm or i.perm_write
				create_perm = create_perm or i.perm_create
				unlink_perm = unlink_perm or i.perm_unlink
				
		# 	# current_model_access_rights = self.env['ir.model.access'].search([('model_id.name','=',model_name),('id','=',list_access_rights_id)])
		# 	test = self.env['ir.model.access'].browse(current_model_access_rights.ids[-1])
			response['permissions']['read'] = response['permissions']['read'] and read_perm
			response['permissions']['write'] = response['permissions']['write'] and write_perm
			response['permissions']['create'] = response['permissions']['create'] and create_perm
			response['permissions']['delete'] = response['permissions']['delete'] and unlink_perm
		
		
		return response

	@api.model
	def _validate(self, api_key, context=None):
		context = context or {}
		response = {'success':False, 'message':'Unknown Error !!!'}
		if not api_key:
			response['responseCode'] = 401
			response['message'] = 'Invalid/Missing Api Key !!!'
			return response
		try:
            # Get Conf
			Obj_exists = self.sudo().search([('api_key','=',api_key)])
			if not Obj_exists:
				response['responseCode'] = 401
				response['message'] = "API Key is invalid !!!"
			else:
				if not Obj_exists.api_validity or Obj_exists.expiry_date >= fields.date.today():
					response['success'] = True
					response['responseCode'] = 200
					response['message'] = 'Login successfully.'
					response['confObj'] = Obj_exists

				else:
					response['success'] = False
					response['responseCode'] = 401
					response['message'] = 'API Key is expired !!!'
					response['confObj'] = Obj_exists

		except Exception as e:
			response['responseCode'] = 401
			response['message'] = "Login Failed: %r"%e.message or e.name
		return response

	name = fields.Char('Name', required=True)
	description = fields.Text('Extra Information', help="Quick description of the key", translate=True)
	# api_key = fields.Char(string='API Secret key', default=_default_unique_key(32), required=1)
	api_key = fields.Char(string='API Secret key')
	active = fields.Boolean(default=True)
	resource_ids = fields.One2many('rest.api.resources','api_id', string='Choose Resources')
	availabilty = fields.Selection([
        ('all', 'All Resources'),
        ('specific', 'Specific Resources')], 'Available for', default='all',
        help="Choose resources to be available for this key.", required=True)
	
	user_authenticate=fields.Boolean(string="User Authenticate",default=False)

	@api.depends('validity_time')
	def compute_expiry_date(self):
		for rec in self:
			rec.advanced_features = rec.api_validity or rec.limit_for_hits
			if rec.api_validity:
				if rec.validity_time_selection == "day":
					rec.expiry_date = (rec.last_api_refresh_date or rec.create_date or fields.date.today(
					)) + relativedelta(days=rec.validity_time)
				elif rec.validity_time_selection == "week":
					rec.expiry_date = (rec.last_api_refresh_date or rec.create_date or fields.date.today(
					)) + relativedelta(weeks=rec.validity_time)
				elif rec.validity_time_selection == "month":
					rec.expiry_date = (rec.last_api_refresh_date or rec.create_date or fields.date.today(
					)) + relativedelta(months=rec.validity_time)
				elif rec.validity_time_selection == "year":
					rec.expiry_date = (rec.last_api_refresh_date or rec.create_date or fields.date.today(
					)) + relativedelta(years=rec.validity_time)
			else:
				rec.expiry_date = fields.date.today()

	advanced_features = fields.Boolean(string="", default=False)
	last_api_refresh_date = fields.Date(string="Last Api Key Update Date")

	is_api_key_created = fields.Boolean(
		string="Api Key Created", default=False)
	api_validity = fields.Boolean(string="Api Validity", default=False)
	validity_time = fields.Integer(string='Validity')
	validity_time_selection = fields.Selection([
		('day', 'day(s)'),
		('week', 'week(s)'), ('month', 'month(s)'), ('year', 'year(s)')], string='', default='day', required=True)
	expiry_date = fields.Date(string="API Expiry Date",
								compute="compute_expiry_date")

	limit_for_hits = fields.Boolean(string="Limit for Hits", default=False)
	hit_limits = fields.Integer(string='Limit')
	hit_count = fields.Integer(string='Limit')
	last_hit_date = fields.Date("Last hit date")


	# user_ids=fields.Many2many(string="User Ids",comodel_name="res.users")
	user_ids_count=fields.Integer(compute="_count_user_ids")
	login_token_ids=fields.One2many(string="Login Token Ids", inverse_name="api_id", comodel_name="login.token")

	def generate_secret_key(self):
		self.api_key = _default_unique_key(32)
		self.last_api_refresh_date = fields.date.today()
		self.is_api_key_created = True

	# 	def copy(self, default=None):
		raise UserError(_("You can't duplicate this Configuration."))

	# 	def unlink(self):
		raise UserError(_('You cannot delete this Configuration, but you can disable/In-active it.'))

	def _count_user_ids(self):
		for rec in self:
			rec.user_ids_count=len(rec.login_token_ids)
		return

	def action_show_users(self):
		self.ensure_one()
		return {
            'name': _('Login Tokens'),
            'view_mode': 'tree,form',
            'res_model': 'login.token',
            'type': 'ir.actions.act_window',
            'context': {'create': True, 'delete': False},
            'domain': [('id', 'in', self.login_token_ids.ids)],
            'target': 'new',
        }
	
	def download_file(self):
		module_path = file_path("odoo_rest")
		file_path_1 = module_path + "/views/postman_collection.zip"
		result = None
		with open(file_path_1 , 'rb') as reader:
			result = base64.b64encode(reader.read())
		attachment_obj = self.env['ir.attachment'].sudo()
		name = "rest_zip"
		if not attachment_obj.search([('name','=',name)]):
			attachment_id = attachment_obj.create({
        	    'name': name,
        	    'datas': result,
        	    'public': False
        	})
		else:
			attachment_id = attachment_obj.search([('name','=',name)])
		download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
		return download_url
	

	@api.model_create_multi
	def create(self, vals):
		records = super(RestAPI,self).create(vals)
		for rec in records:
			rec.generate_secret_key()
		return records


	def riderct_rest_url(self):
		action = self.env.ref('odoo_rest.odoorestapi_action') 
		if action:
			action_id = action.id
			return f"/web#action={action_id}&model=rest.api&view_type=list"
		else:
			return "#"
		
	def check_throttling(self):
        # return True
		if self.limit_for_hits:
			if not self.last_hit_date or self.last_hit_date < fields.date.today():
				self.hit_count = 1
				self.last_hit_date = fields.date.today()
				return True
			else:
				if self.hit_count < self.hit_limits:
					self.hit_count += 1
					return True
				else:
					return False
		else:
			return True

