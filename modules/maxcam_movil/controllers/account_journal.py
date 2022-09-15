# -*- coding: utf-8 -*-
import logging
import json

from pprint import pprint
from odoo import http
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class AppAccountJournal(http.Controller):
	FIELDNAMES = ['id', 'name', 'company_id','type']

	@http.route('/app/account_journal', type='http', methods=['GET'], auth='public', website=False, sitemap=False)
	def app_account_move_movil(self, limit=200, offset=0,create_uid=None,deposit=None):
		data = {'status': 200, 'msg': 'Success'}
		domain = [('active', '=', True), ('type', 'in', ['bank', 'cash'])]
		_logger.info("domain %s",domain)
		# Search Read
		journal_ids = request.env['account.journal'].sudo().search_read(domain=domain, fields=self.FIELDNAMES,
																		limit=int(limit), offset=int(offset),
																		order='name asc')
		all_journal_count = request.env['account.journal'].sudo().search_count(domain)
		journal_ids_copy = journal_ids.copy()
		if create_uid and create_uid != 5000:
			_logger.info("USER RECIBIDO %s",create_uid)
			seller = request.env['hr.employee'].sudo().search([('user_id','=',int(create_uid))])
			if seller and seller.journal_id_maxcam:
				for jo in journal_ids_copy:
					_logger.info("JOURNAL %s",jo)
					#si el diario es efectivo pero no el asociado al vendedor
					obj_j = request.env['account.journal'].sudo().browse(int(jo.get('id',False)))
					if obj_j and obj_j.id != seller.journal_id_maxcam.id and obj_j.type == 'cash':
						_logger.info("remover %s",jo)
						journal_ids.remove(jo)
		if deposit:
			for j in journal_ids:
				seller = request.env['hr.employee'].sudo().search([('journal_id_maxcam','=',int(j.get('id',False)))])
				if seller:
					_logger.info("remover %s",j)
					journal_ids.remove(j)
		journal_count = len(journal_ids)
		if journal_count > 0:
			data.update({'data': journal_ids, 'count': journal_count, 'total_count': all_journal_count})
		else:
			data.update({'status': 204, 'msg': 'Diarios no encontrado', 'count': 0, 'data': False})
		return json.dumps(data)
