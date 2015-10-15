# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2015 Vauxoo
#    Copyright (C) 2009-2011 Akretion
#    Author: Emmanuel Samyn,
#            Yanina Aular,
#            Osval Reyes
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _


class ReturnedLinesFromSerial(models.TransientModel):

    _name = 'returned.lines.from.serial.wizard'
    _description = 'Wizard to create product return lines'
    ' from serial numbers or invoices'

    # Get partner from case is set to filter serials
    @api.model
    def _get_default_partner_id(self):
        """
        Obtain partner from the claim
        """
        crm_claim_model = self.env['crm.claim']
        claim_id = self.env.context.get('active_id')
        partner_record = crm_claim_model.browse(claim_id).\
            partner_id
        return partner_record and partner_record[0] or \
            self.env['res.partner']

    @api.model
    def prodlot_2_product(self, prodlot_ids):
        quant_model = self.env['stock.production.lot']
        quant_records = quant_model.search([('id', 'in', prodlot_ids)])
        res = [prod.product_id.id for prod
               in quant_records if prod.product_id]
        return set(res)

    # Method to get the product id from set
    @api.model
    def get_product_id(self, product_set):
        product_id = False
        for product in self.prodlot_2_product([product_set]):
            product_id = product
        return product_id

    @api.model
    def create_claim_line(self, claim_id, claim_origin,
                          product_record, prodlot_id, qty, name,
                          invline_record=False):
        claim_line_model = self.env['claim.line']
        line_rec = claim_line_model.create({
            'claim_id': claim_id,
            'claim_origin': claim_origin,
            'product_id': product_record and product_record.id or False,
            'name': product_record and product_record.name or
            invline_record.name,
            'invoice_line_id': self.prodlot_2_invoice_line(prodlot_id.name).id,
            'product_returned_quantity': qty,
            'prodlot_id': prodlot_id.id,
        })
        line_rec.set_warranty()

    # If "Cancel" button pressed
    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    partner_id = fields.Many2one('res.partner',
                                 'Partner',
                                 default=_get_default_partner_id)

    @api.model
    def prodlot_2_invoice_line(self, prodlot):
        """
        Return the last line of customer invoice
        based in serial/lot number
        """
        lot_obj = self.env['stock.production.lot']
        prodlot = lot_obj.search([('name', '=', str(prodlot))])
        if prodlot.invoice_line_id:
            return prodlot.invoice_line_id
        else:
            return False

    lines_list_id = fields.Many2many('stock.production.lot',
                                     'lot_returned_wizard',
                                     'wizard_id',
                                     'lot_id',
                                     string='Lots selected',
                                     help='Field used to show the current '
                                          'status of the lots '
                                          'loaded')
    lines_id = fields.Many2many('stock.production.lot',
                                string='Invoice Lines to Select',
                                help='Field used to load the ids of '
                                     'invoice lines in invoices writed')
    scan_data = fields.Text('Products',
                            help='Field used to load and show the '
                            'products')
    scaned_data = fields.Text('Products',
                              help='Field used to load the ids of '
                              'products loaded')
    current_status = fields.Text('Status',
                                 help='Field used to show the current '
                                 'status of the product '
                                 'loaded(Name and quantity)')

    @api.multi
    def get_metasearch_view_brw(self):
        """
        @return: view with metasearch field
        """
        view_id = self.env.\
            ref('crm_rma_lot_mass_return.view_enter_product')
        return view_id

    @api.multi
    def render_metasearch_view(self):
        """
        Render wizard view with metasearch field
        """
        view = self.get_metasearch_view_brw()
        if view:
            return {
                'name': _('Search Product'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'returned.lines.from.serial.wizard',
                'view_id': view.id,
                'views': [(view.id, 'form')],
                'target': 'new',
                'res_id': self.id,
            }

    @api.model
    def get_data_of_products(self, input_data):
        data_line = []
        for item in input_data and input_data.split('\n') or []:
            if '*' in item:

                comput = item.split('*')
                data_it_1 = '0'
                data_it_2 = ''
                if len(comput) >= 2:
                    data_it_1 = comput[1]
                if len(comput) >= 3:
                    data_it_2 = comput[2]
                if comput[0]:
                    data_line.append((comput[0], data_it_1, data_it_2))
            else:
                if item.strip():
                    data_line.append((item.strip(), '0', ''))
        return data_line

    @api.multi
    def onchange_load_products(self, input_data, lines_list_id, context=None):
        """
        To load products or invoice lines for the claim lines
        """
        context = context or None
        invoice = self.env['account.invoice']
        lot_obj = self.env['stock.production.lot']
        input_lines = self.get_data_of_products(input_data)
        mes = ''
        ids_data = ''
        all_prod = []
        lot_ids = set()
        for line in input_lines or []:
            # if there is no invoice/serial in it
            if not line[0]:
                continue

            number_serial = line[0].encode('utf8')

            # search invoices first
            invoice_ids = invoice.search([('number', '=', number_serial)])

            element_searched = False
            if invoice_ids:
                line_ids = lot_obj.\
                    search([('invoice_line_id', 'in',
                             invoice_ids.mapped('invoice_line.id'))])
                lot_ids |= set(line_ids.mapped('id'))
                element_searched = lot_ids
            else:
                prodlot_ids = lot_obj.search(
                    ['&', ('name', '=', number_serial),
                     ('invoice_line_id', '!=', False)])

                if prodlot_ids:
                    for item in prodlot_ids:
                        item_name = item.product_id \
                            and item.product_id.name.encode('utf8') \
                            or False
                        line_id = '{pid}+{pname}'.format(pid=item.id,
                                                         pname=item_name)
                        all_prod.append((line_id, 1))
                element_searched = prodlot_ids

            if not element_searched:
                return {
                    'warning': {
                        'message': (_('The product or invoice %s'
                                      ' was not found') % line[0])},
                        'value': {
                            'scan_data': '\n'.join(
                                input_data.split('\n')[0:-1])
                    }
                }

        for line in all_prod:
            name = line[0].split('+')
            mes = mes + '{0} \t {1}\n'.format(name[1], line[1])
            ids_data = ids_data + '{pid}\n'.format(pid=name[0]) * line[1]

        lot_ids = list(lot_ids)

        res = {
            'value': {
                'lines_id': [(6, 0, lot_ids)],
                'current_status': mes,
                'scaned_data': ids_data,
            },
            'domain': {
                'lines_list_id': [('id', 'in', lot_ids)]
            }
        }
        return res

    @api.multi
    def add_claim_lines(self):
        context = self._context
        prodlot_obj = self.env['stock.production.lot']
        inv_recs = []
        info = self.get_data_of_products(self.scan_data)
        if self.scaned_data:
            inv_recs += [prodlot_obj.browse(int(inv_id))
                         for inv_id in self.scaned_data.strip().split('\n')]
        if self.lines_list_id:
            inv_recs += self.lines_list_id

        len_info = len(info)
        index = 0
        for prodlot_brw in inv_recs:
            product_brw = prodlot_brw.product_id

            name = ''
            num = 0
            if index < len_info:
                num = info[index][1]
                if num.isdigit():
                    num = int(num)
                else:
                    num = 0
                name = info[index][2]
                index += 1

            self.create_claim_line(context.get('active_id'),
                                   self.env['claim.line']._get_subject(num),
                                   product_brw,
                                   prodlot_brw, 1,
                                   name,
                                   prodlot_brw.invoice_line_id)
        self.action_cancel()

    @api.multi
    def change_list(self, lines):
        res = {
            'value': {
                'lines_list_id': lines,
            }
        }
        return res
