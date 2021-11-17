# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import time, datetime

class ProductTemplate(models.Model):
	_inherit = "product.template"
	vdl = fields.Boolean(string="VDL", default=False)
	porteur_id = fields.Many2one('porteur', string='Marque')
	model_porteur_id = fields.Many2one('model.porteur', string='Model')
	serie_porteur = fields.Char(string='Numéro série')
	cellule_id = fields.Many2one('cellule', string='Marque')
	owner_id = fields.Many2one('res.partner', string='Propriétaire')
	model_cellule_id = fields.Many2one('model.cellule', string='Model')
	serie_cellule = fields.Char(string='Numéro série')
	annee_millesime = fields.Char('Année millésime')
	date_circulation = fields.Date("Mise en circulation")
	immatriculation = fields.Char(string='Immatriculation')
	km = fields.Integer('Kilométrage')
	date_next_CT = fields.Date("Prochain CT")
	option_cellule = fields.Char(string='Options cellule')
	accessoires = fields.Char(string='Accessoires')
	control_etancher_ids = fields.Many2many('control.etanche', 'control_etanche_rel',string='Contrôles étanchéités')

	@api.onchange('porteur_id')
	def onchange_porteur_id(self):
		for obj in self:
			list_model = obj.porteur_id.model_porteur_ids.ids
			domain = {'model_porteur_id': [('id', 'in', list_model)]}
		result = {'domain': domain}
		return result

	@api.onchange('cellule_id')
	def onchange_cellule_id(self):
		for obj in self:
			list_model = obj.cellule_id.model_cellule_ids.ids
			domain = {'model_cellule_id': [('id', 'in', list_model)]}
		result = {'domain': domain}
		return result
 
class porteur(models.Model):
	_name = 'porteur'
	name = fields.Char(string='Marque')
	product_template_ids = fields.One2many('product.template','porteur_id',string='Véhicules')
	model_porteur_ids = fields.One2many('model.porteur','porteur_id',string='Modèles porteur')

class model_porteur(models.Model):
	_name = 'model.porteur'
	name = fields.Char(string='Modèle')
	porteur_id = fields.Many2one('porteur', string='Marque')
	product_template_ids = fields.One2many('product.template','model_porteur_id',string='Véhicules')

class cellule(models.Model):
	_name = 'cellule'
	name = fields.Char(string='Marque')
	product_template_ids = fields.One2many('product.template','cellule_id',string='Véhicules')
	model_cellule_ids = fields.One2many('model.cellule','cellule_id',string='Modèles cellule')

class control_etanche(models.Model):
	_name = 'control.etanche'
	name = fields.Char(string='Date')

class model_cellule(models.Model):
	_name = 'model.cellule'
	name = fields.Char(string='Modèle')
	cellule_id = fields.Many2one('cellule', string='Marque')
	product_template_ids = fields.One2many('product.template','model_cellule_id',string='Véhicules')
