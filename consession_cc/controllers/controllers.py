# -*- coding: utf-8 -*-
# from odoo import http


# class ConsessionCc(http.Controller):
#     @http.route('/consession_cc/consession_cc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/consession_cc/consession_cc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('consession_cc.listing', {
#             'root': '/consession_cc/consession_cc',
#             'objects': http.request.env['consession_cc.consession_cc'].search([]),
#         })

#     @http.route('/consession_cc/consession_cc/objects/<model("consession_cc.consession_cc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('consession_cc.object', {
#             'object': obj
#         })
