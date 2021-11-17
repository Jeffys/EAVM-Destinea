# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import time, datetime

# class AccountMoveLine(models.Model):
# 	_name = "account.move.line"
# 	price_subtotal_ttc = fields.Monetary(string='Subtotal TTC', store=True, readonly=True,
# 		currency_field='always_set_currency_id')
	
# 	@api.depends('price_subtotal','tax_ids')
# 	def set_price_subtotal_ttc(self):
# 		price = self.
# 	