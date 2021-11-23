# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import time, datetime
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
	_inherit = "product.template"
	vdl = fields.Boolean(string="VDL", default=False)
	type_vdl_form = fields.Selection([
		('catalogue', 'Catalogue'),
		('neuf', 'Neuf'),
		('occasion', 'Occasion'),
		], string='Type', default='catalogue')
	owner_id = fields.Many2one('res.partner', string='Propriétaire')

	# Porteur
	porteur_id = fields.Many2one('porteur', string='Marque du châssis')
	model_porteur_id = fields.Many2one('model.porteur', string='Type du châssis')
	serie_porteur = fields.Char(string='Numéro série')
	type_mines = fields.Char(string='Type mines')

	# Cellule
	type_mines = fields.Char('Type mines')
	code_constructeur = fields.Char('Code constructeur')
	couchage = fields.Integer('Couchages')
	longueur = fields.Float(string="Longueur (m)")
	largeur = fields.Float(string="Largeur (m)")
	hauteur = fields.Float(string="Hauteur (m)")

	reservoir_eau_propre = fields.Float(string='Rés. eau propre (L)')
	reservoir_eau_usee = fields.Float(string='Rés. eau usée (L)')

	poids_vide = fields.Float(string="Poids à vide (Kg)")
	charge_utile = fields.Float(string="Charge utile (Kg)")
	poids_charge = fields.Float(string="Poids en charge (kg)")

	# option_cellule = fields.Char(string='Options cellule')
	# accessoires = fields.Char(string='Accessoires')

	porteur_id = fields.Many2one('porteur', string='Marque du châssis')
	model_porteur_id = fields.Many2one('model.porteur', string='Type du châssis')
	nb_place = fields.Integer('Nb place carte grise')
	poids_tractable = fields.Float(string="Poids tractable (kg)")
	puissance_fiscale = fields.Char('Puissance Fiscale')
	din = fields.Char('DIN')
	kw = fields.Char('KW')

	equipement_serie_ids = fields.Many2many('equipement.serie', 'equipement_serie_rel', string='Equipements de série')
	equipement_option_line_ids = fields.One2many('equipement.option.line', 'vdl_id', string='Equipements en option')

	garantie_line_ids = fields.One2many('garantie.line', 'vdl_id', string='Garanties')
	financement_line_ids = fields.One2many('financement.line', 'vdl_id', string='Financements')

	#Infos vehicule
	date_entree_stock = fields.Date(string="Date d'entrée en stock")
	num_serie = fields.Char('Numéro série (E)')
	num_serie_cellule = fields.Char('Numéro série cellule')
	date_circulation = fields.Date(string='Mise en circulation (B)')
	immatriculation = fields.Char(string='Immatriculation')
	date_immatriculation = fields.Date(string='Date immat.')
	premiere_main = fields.Boolean(string="Première main", default=False)
	km = fields.Integer('Kilométrage ')
	date_km = fields.Date("Relevé le")
	certifie_km = fields.Boolean(string="Certifié", default=False)
	num_cle = fields.Char(string='N° de clé')
	num_police = fields.Char(string='N° de police')

	date_CT = fields.Date("Date CT")
	date_next_CT = fields.Date("Prochain CT")

	date_control_etanche = fields.Date("Contrôle d'étanchéité")
	date_next_control_etanche = fields.Date("Prochain contrôle")
	Commentaire_vdl = fields.Text(string="Commentaires")

	prix_vente_equipement = fields.Float(string="Prix équipements", compute='compute_prix_equipement')
	prix_vente_equipement_tax_included = fields.Float(string="Prix équipements TTC", compute='compute_prix_vente_equipement_tax_included')

	prix_vente_vdl_tax_included = fields.Float(string="Prix VDL TTC", compute='compute_prix_vente_vdl_tax_included')

	total_prix_vente = fields.Float(string="Total", compute='compute_total_prix_vente')
	total_prix_vente_tax_included = fields.Float(string="Total TTC", compute='compute_total_prix_vente_tax_included')

	cout_cession_interne = fields.Float(string="Cessions internes")
	cout_travaux_extérieur = fields.Float(string="Travaux extérieurs")
	cout_autre_session = fields.Float(string="Autres")
	cout_reprise_total= fields.Float(string="Coût total de reprise", compute='compute_cout_reprise_total')
	cout_accessoire= fields.Float(string="Accessoires", compute='compute_cout_accessoire')

	marge_vdl = fields.Float(string="Marge net", compute='compute_marge_vdl')


	@api.depends('equipement_option_line_ids.prix_vente')
	def compute_prix_equipement(self):
		res = 0
		for equipement_line in self.equipement_option_line_ids:
			res = res + equipement_line.prix_vente
		self.prix_vente_equipement = res
		return res

	@api.depends('total_prix_vente','cout_reprise_total')
	def compute_marge_vdl(self):
		_logger.debug("------------- compute_marge_vdl ------------- ")
		self.marge_vdl = self.total_prix_vente - self.cout_reprise_total

	@api.depends('standard_price','cout_cession_interne','cout_travaux_extérieur','cout_accessoire','cout_autre_session')
	def compute_cout_reprise_total(self):
		self.cout_reprise_total = self.standard_price + self.cout_cession_interne + self.cout_travaux_extérieur + self.cout_accessoire + self.cout_autre_session

	@api.depends('prix_vente_equipement','list_price')
	def compute_total_prix_vente(self):
		self.total_prix_vente = self.prix_vente_equipement + self.list_price

	@api.depends('prix_vente_equipement_tax_included','prix_vente_vdl_tax_included')
	def compute_total_prix_vente_tax_included(self):
		self.total_prix_vente_tax_included = self.prix_vente_equipement_tax_included + self.prix_vente_vdl_tax_included

	@api.depends('equipement_option_line_ids.equipement_id.taxes_id', 'equipement_option_line_ids.equipement_id.list_price')
	def compute_prix_vente_equipement_tax_included(self):
		resultat = 0
		for equipement_line in self.equipement_option_line_ids:
			equipement = equipement_line.equipement_id
			currency = equipement.currency_id
			res = equipement.taxes_id.compute_all(equipement.list_price)
			resultat = resultat + res['total_included'] #['total_excluded']

		self.prix_vente_equipement_tax_included = resultat

	@api.depends('equipement_option_line_ids.equipement_id.taxes_id', 'equipement_option_line_ids.equipement_id.list_price')
	def compute_prix_vente_vdl_tax_included(self):
		currency = self.currency_id
		res = self.taxes_id.compute_all(self.list_price)
		self.prix_vente_vdl_tax_included = res['total_included'] #['total_excluded']

	@api.depends('equipement_option_line_ids.prix_revient')
	def compute_cout_accessoire(self):
		_logger.debug("------------- compute_cout_accessoire ------------- ")
		res = 0
		for equipement_line in self.equipement_option_line_ids:
			res = res + equipement_line.prix_revient
		self.cout_accessoire = res
		return res

	@api.onchange('porteur_id')
	def onchange_porteur_id(self):
		for obj in self:
			list_model = obj.porteur_id.model_porteur_ids.ids
			domain = {'model_porteur_id': [('id', 'in', list_model)]}
		result = {'domain': domain}
		return result


class porteur(models.Model):
	_name = 'porteur'
	name = fields.Char(string='Marque')
	product_template_ids = fields.One2many('product.template', 'porteur_id', string='Véhicules')
	model_porteur_ids = fields.One2many('model.porteur', 'porteur_id', string='Modèles porteur')


class model_porteur(models.Model):
	_name = 'model.porteur'
	name = fields.Char(string='Modèle')
	porteur_id = fields.Many2one('porteur', string='Marque')
	product_template_ids = fields.One2many('product.template', 'model_porteur_id', string='Véhicules')


class equipement_serie(models.Model):
	_name = 'equipement.serie'
	name = fields.Char(string='Equipement')
	_sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Le nom existe déjà')]

class equipement_option_line(models.Model):
	_name = 'equipement.option.line'
	vdl_id = fields.Many2one('product.template', string='Véhicule')
	equipement_id = fields.Many2one('product.template', string='Equipement')
	quantite = fields.Integer('Quantité', default=1)
	currency_id = fields.Many2one('res.currency', related='equipement_id.currency_id')
	prix_revient = fields.Float(string='Prix de revient', related='equipement_id.standard_price')
	prix_vente = fields.Float(string='Prix de vente HT', related='equipement_id.list_price')
	prix_vente_tax_included = fields.Float(string='Prix de vente TTC', compute='compute_prix_vente_tax_included')

	@api.depends('equipement_id.taxes_id', 'prix_vente')
	def compute_prix_vente_tax_included(self):
		for line in self:
			currency = line.currency_id
			res = line.equipement_id.taxes_id.compute_all(line.prix_vente)
			line.prix_vente_tax_included = res['total_included'] #['total_excluded']

class garantie_line(models.Model):
	_name = 'garantie.line'
	vdl_id = fields.Many2one('product.template', string='Véhicule')
	name = fields.Char(string='Prestataire')
	quantite = fields.Integer('Durée', default=1)
	unite_garantie = fields.Selection([
		('mois', 'Mois'),
		('annee', 'Année'),
		], string='Unité', default='mois')
	num_contrat = fields.Char(string='Numéro de contrat')
	kilometre = fields.Integer(string='Kilomètre')
	debut = fields.Date(string='Début')
	fin = fields.Date(string='Fin')

class financement_line(models.Model):
	_name = 'financement.line'
	vdl_id = fields.Many2one('product.template', string='Véhicule')
	type_financement_id = fields.Many2one('type.financement', string='Type financement')
	organisme_financement_id = fields.Many2one('organisme.financement', string='Organisme financement')
	num_contrat = fields.Char(string='Numéro de contrat')
	debut = fields.Date(string='Début')
	fin = fields.Date(string='Fin')
	company_id = fields.Many2one('res.company', 'Company',default=lambda self:self.env.user.company_id.id, index=1)
	currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self:self.env.user.company_id.currency_id.id,required=True)
	montant_credit = fields.Float(string='Montant crédit')
	montant_traite = fields.Float(string='Montant traite')

class type_financement(models.Model):
	_name = 'type.financement'
	name = fields.Char(string='Type')
	_sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Le nom existe déjà')]

class organisme_financement(models.Model):
	_name = 'organisme.financement'
	name = fields.Char(string='Organisme')
	_sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Le nom existe déjà')]
