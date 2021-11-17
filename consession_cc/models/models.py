# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class consession_cc(models.Model):
#     _name = 'consession_cc.consession_cc'
#     _description = 'consession_cc.consession_cc'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
