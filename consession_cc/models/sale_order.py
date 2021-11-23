#-*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from odoo import api, fields, models
from odoo.tools.float_utils import float_round, float_is_zero
import time, datetime
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
	_inherit = "sale.order"
	is_vdl = fields.Boolean(string="Contient un VDL", compute='compute_is_vdl')
	is_dossier_financement= fields.Boolean(string="Dossier de financement", default=False)
	is_reprise = fields.Boolean(string="Reprise", default=False)
	vdl_en_stock = fields.Boolean(string="VDL en stock", default=False)
	vdl_neuf = fields.Boolean(string="VDL neuf", default=False)
	project_id = fields.Many2one('project.project', 'Projet', copy=False)

	@api.depends('order_line.product_template_id.vdl')
	def compute_is_vdl(self):
		for obj in self:
			res = False
			for order_line in obj.order_line:
				if order_line.product_template_id.vdl:
					res = True
					break
			obj.is_vdl = res

	def create_project(self):

		context = self._context
		current_uid = context.get('uid')
		user_id = self.env['res.users'].browse(current_uid)

		if not self.project_id:
			vals = {'user_id': user_id.id, 'name':'Vente VDL: '+self.partner_id.name, 'partner_id':self.partner_id.id, 'date_start':self.signed_on}
			self.project_id = self.env['project.project'].create(vals)

			task_type_waiting = self.env['project.task.type'].search([('name','=',"En attente")])
			if len(task_type_waiting) == 0:
				_logger.debug("--------------- En attente task create, project : "+ str(self.project_id))
				task_type_waiting = self.env['project.task.type'].create({
					'name':"En attente",
					'project_ids':[(4,self.project_id.id)]
					})
				_logger.debug(" --------------- project_ids : "+ str(task_type_waiting.project_ids))

			elif len(task_type_waiting) > 0:
				_logger.debug("--------------- En attente task en piste, project : "+ str(self.project_id))
				task_type_waiting = task_type_waiting[0]
				_logger.debug("--------------- task_type_waiting.project_ids.ids "+ str(task_type_waiting.project_ids.ids))
				if self.project_id.id not in task_type_waiting.project_ids.ids:
					task_type_waiting.project_ids = [(4,self.project_id.id)]
					_logger.debug(" --------------- project_ids : "+ str(task_type_waiting.project_ids))

			task_type_ready = self.env['project.task.type'].search([('name','=',"Prêt")])
			if len(task_type_ready) == 0:
				task_type_ready = self.env['project.task.type'].create({
					'name':"Prêt",
					'project_ids':[(4,self.project_id.id)]
					})
			elif len(task_type_ready) > 0:
				task_type_ready=task_type_ready[0]
				if self.project_id.id not in task_type_ready.project_ids.ids:
					task_type_ready.project_ids = [(4,self.project_id.id)]
	
			task_type_runing = self.env['project.task.type'].search([('name','=',"En cours")])
			if len(task_type_runing) == 0:
				task_type_runing = self.env['project.task.type'].create({
					'name':"En cours",
					'project_ids':[(4,self.project_id.id)]
					})
			elif len(task_type_runing) > 0:
				task_type_runing = task_type_runing[0]
				if self.project_id.id not in task_type_runing.project_ids.ids:
					task_type_runing.project_ids = [(4,self.project_id.id)]
	
			task_type_done = self.env['project.task.type'].search([('name','=',"Terminé")])
			if len(task_type_done) == 0:
				task_type_done = self.env['project.task.type'].create({
					'name':"Terminé",
					'project_ids':[(4,self.project_id.id)]
					})
			elif len(task_type_done) > 0:
				task_type_done = task_type_done[0]
				if self.project_id.id not in task_type_done.project_ids.ids:
					task_type_done.project_ids = [(4,self.project_id.id)]

		self.create_task()

	def create_task(self):

		#Dossier de financement
		if self.is_dossier_financement:
			task_financement = self.env['project.task'].create({
				'name': "Dossier de financement",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				'sequence':0
				})

			task_document_client = self.env['project.task'].create({
				'name': "Récupérer les documents auprès du client",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_financement.id,
				'sequence':0,
				'description':"CNI, Justificatif de revenu, etc."
				})

			task_document_transmission = self.env['project.task'].create({
				'name': "Transmettre les documents à l'organisme financier",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_financement.id,
				'sequence':1,
				'description':"CNI, Justificatif de revenu, etc."
				})
			task_document_suivi = self.env['project.task'].create({
				'name': "Suivre la demande",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_financement.id,
				'sequence':2,
				'description':"Rappeler l'organisme de financement pour obtenir une réponse"
				})
			task_retour_financenement = self.env['project.task'].create({
				'name': "Enregistrer la réponse ",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_financement.id,
				'sequence':3,
				'description':"Envoyer un courrier de confirmation crédit au client + copie au secrétariat commercial \r\n Valider la commande après le délai de rétractation de 15 jours (sauf livraison plus tôt et délai raccourci à 3 jours) suivant l'acceptation, ce qui déclenche la suite du processus"
				})


		#Dossier de reprise
		if self.is_reprise:
			task_reprise= self.env['project.task'].create({
				'name': "Dossier de Reprise",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				'sequence':1,
				})

			task_fiche_descriptive= self.env['project.task'].create({
				'name': "Récupérer la fiche descriptive",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':0,
				'description':"Etat des lieux du véhicule et des accessoires"
				})

			task_borderaux_achat= self.env['project.task'].create({
				'name': "Borderaux d'achat",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':1,
				'description':"Bordereau d'achat (sur le SIV) "
				})
			task_creation_fiche_vdl= self.env['project.task'].create({
				'name': "Création de la fiche VDL",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':2,
				'description':"Création de la fiche véhicule"
				})
			task_cerfa_certification = self.env['project.task'].create({
				'name': "CERFA de certification de cession",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':3,
				'description':"Gérer le CERFA de certification de cession (15 776*02) pdf prérempli depuis fiche véhicule Odoo"
				})
			task_non_gage = self.env['project.task'].create({
				'name': "Certificat de non gage",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':4,
				'description':"Vérification de l'absence de gage sur le véhicule repris"
				})
			task_livre_police = self.env['project.task'].create({
				'name': "Gestion du livre de police",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':5,
				'description':""
				})
			task_controle_technique = self.env['project.task'].create({
				'name': "Contrôle technique",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':6,
				'description':"Vérification du contrôle technique du véhicule à reprendre"
				})
			task_entree_VDL_reprise = self.env['project.task'].create({
				'name': "Planifier la rentrée du VDL repris",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':7,
				'description':"Lors d’une reprise le véhicule ne rentre pas forcément tout de suite en stock. Nous devrons avoir de la visibilité sur ceux dont l’entrée est prévue ultérieurement car ils pourraient intéresser des clients potentiels."
				})
			task_entree_VDL_stock = self.env['project.task'].create({
				'name': "Entrée en stock du VDL repris",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':8,
				'description':"révision de la fiche descriptive pour voir si le véhicule est conforme."
				})
			task_fiche_de_prix = self.env['project.task'].create({
				'name': "Fiche de prix du VDL repris",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_reprise.id,
				'sequence':9,
				'description':"Editer des fiches de prix répondant aux normes obligatoires (dont l’affichage du numéro du livre de police, logo Destinéa)."
				})

		#Suivi de commande
		task_suivi_commande = self.env['project.task'].create({
			'name': "Suivi de commande",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			'sequence':2,
			})

		task_suivi_accessoire = self.env['project.task'].create({
			'name': "Suivi accessoires",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			# 'date_start':task.date_planned_start,
			# 'date_end':task.date_planned_finished,
			'parent_id': task_suivi_commande.id,
			'sequence':0,
			'description':"Achat/Réservation des accessoires"
			})

		task_suivi_atelier = self.env['project.task'].create({
			'name': "Suivi atelier",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			# 'date_start':task.date_planned_start,
			# 'date_end':task.date_planned_finished,
			'parent_id': task_suivi_commande.id,
			'sequence':1,
			'description':"CT a prévoir, planification des tâches et réservation des ressources nécessaires pour la préparation du véhicule avant livraison (contrôle du véhicule, pose des accessoires, lavage intérieur, extérieur, etc.)"
			})

		if self.vdl_en_stock:
			task_suivi_vdl_en_stock = self.env['project.task'].create({
				'name': "Suivi VDL",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_suivi_commande.id,
				'sequence':2,
				'description':"Affectation du véhicule en stock au client"
				})
		else:
			task_suivi_vdl_no_stock = self.env['project.task'].create({
				'name': "Suivi VDL",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_suivi_commande.id,
				'sequence':2,
				'description':"Achat/Suivi/Transport/Reception du véhicule client"
				})

			task_achat_vdl_client = self.env['project.task'].create({
				'name': "Achat du véhicule client",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_suivi_vdl_no_stock.id,
				'sequence':0,
				'description':"Passer la commande auprès du fournisseur ou affecter la précommande"
				})

			task_suivi_achat_vdl_client = self.env['project.task'].create({
				'name': "Suivre la commande du véhicule client",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_suivi_vdl_no_stock.id,
				'sequence':1,
				'description':"S'assurer que le véhicule sera livré dans les temps (Si le fournisseur repousse la date de livraison de plus de 15 jours il faut faire un avenant à la commande et obtenir la signature du client)."
				})

			task_transport_vdl_client = self.env['project.task'].create({
				'name': "Gérer le transport",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_suivi_vdl_no_stock.id,
				'sequence':2,
				'description':""
				})

			task_reception_vdl_client = self.env['project.task'].create({
				'name': "Réception du VDL client",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_suivi_vdl_no_stock.id,
				'sequence':3,
				'description':"on s’assure d’avoir les accessoires et les ressources humaines nécessaires, et on fixe un rdv avec le client pour la livraison. On passe alors de la pré-planification à la planification. "
				})

		#Livraison client
		task_livraison_client = self.env['project.task'].create({
			'name': "Livraison client",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			'sequence':3,
			})

		task_permis_assurance = self.env['project.task'].create({
			'name': "Vérifier le permis et l'assurance client",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			# 'date_start':task.date_planned_start,
			# 'date_end':task.date_planned_finished,
			'parent_id': task_livraison_client.id,
			'sequence':0,
			'description':"Attacher ces documents à la commande dans le respect des normes RGPD.(Si VN il faudra peut être fournir le certificat Préalable à l'immatriculation (CPI) pour obtenir l'assurance)"
			})

		if self.is_reprise:
			task_finaliser_reprise = self.env['project.task'].create({
				'name': "Finaliser le dossier de reprise",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_livraison_client.id,
				'sequence':1,
				'description':""
				})

		if self.is_dossier_financement:
			task_finaliser_financement = self.env['project.task'].create({
				'name': "Finaliser le dossier de financement",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_livraison_client.id,
				'sequence':2,
				'description':""
				})

		task_facture = self.env['project.task'].create({
			'name': "Etablissement de la facture client",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			# 'date_start':task.date_planned_start,
			# 'date_end':task.date_planned_finished,
			'parent_id': task_livraison_client.id,
			'sequence':3,
			'description':""
			})

		if self.is_dossier_financement:
			task_declancher_paiement = self.env['project.task'].create({
				'name': "Déclancher le paiement et le suivre",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_livraison_client.id,
				'sequence':4,
				'description':""
				})

		task_enregistrer_reglement = self.env['project.task'].create({
			'name': "Enregistrer le règlement client",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			# 'date_start':task.date_planned_start,
			# 'date_end':task.date_planned_finished,
			'parent_id': task_livraison_client.id,
			'sequence':5,
			'description':""
			})

		task_immatriculation = self.env['project.task'].create({
			'name': "Opération d'immatriculation",
			'company_id':self.env.company.id,
			'project_id':self.project_id.id,
			# 'date_start':task.date_planned_start,
			# 'date_end':task.date_planned_finished,
			'parent_id': task_livraison_client.id,
			'sequence':6,
			'description':"Opérations d’immatriculation en respectant le cahier des charges SIV qui consiste à conserver le COC du véhicule pour un VN et l'ancienne carte grise barré pour un VO, les documents d’identité et le justificatif de domicile du client sur une durée définie et d’être en capacité de les fournir à première demande. On doit pouvoir remplir automatiquement par fusion les CERFA liés à la vente du véhicule (demande de carte grise VN/VO, mandat d’immatriculation VN/VO, certificat de cession si VO) "
			})

		if self.vdl_neuf:
			task_garantie = self.env['project.task'].create({
				'name': "Enregistrer le règlement client",
				'company_id':self.env.company.id,
				'project_id':self.project_id.id,
				# 'date_start':task.date_planned_start,
				# 'date_end':task.date_planned_finished,
				'parent_id': task_livraison_client.id,
				'sequence':7,
				'description':"Déclencher les garanties constructeur (envoi du CPI)"
				})


