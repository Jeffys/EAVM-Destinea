# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import time, datetime

class Partner(models.Model):
	_description = 'Contact'
	_inherit = "res.partner"
	vdl_ids = fields.One2many('product.template', 'owner_id', string='Propriétaire', domain=[('active', '=', True)])
