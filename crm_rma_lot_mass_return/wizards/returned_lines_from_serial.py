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
from openerp import _, api, fields, models


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
        clima_line = self.env['claim.line']
        line_rec = clima_line.create({
            'claim_id': claim_id,
            'claim_origin': claim_origin,
            'product_id': product_record and product_record.id or False,
            'name': name and name or product_record.name,
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
                    data_line.append((comput[0], (data_it_1, data_it_2)))
            else:
                if item.strip():
                    data_line.append((item.strip(), ('0', '')))
        return data_line

    def _get_lots_from_scan_data(self, input_data):

        input_lines = self.get_data_of_products(input_data)
        invoice = self.env['account.invoice']
        lot = self.env['stock.production.lot']

        prodlot_set_ids = set()
        lot_set_ids = set()
        invoice_lot_set_ids = set()
        lots_lot_set_ids = set()

        if not input_lines:
            return False, False

        for line in input_lines:
            # if there is no invoice/serial in it
            if not line[0]:
                continue

            number_serial = line[0].encode('utf8')
            # search invoices first
            invoice_ids = invoice.search([('number', '=', number_serial)])
            element_searched = False
            if invoice_ids:
                line_ids = lot.\
                    search([('invoice_line_id', 'in',
                             invoice_ids.mapped('invoice_line.id'))])
                lot_set_ids |= set(line_ids.mapped('id'))
                element_searched = lot_set_ids
                invoice_lot_set_ids |= lot_set_ids

            else:
                # if not, it must be a serial lot number
                prodlot_ids = lot.search([('name', '=', number_serial),
                                          ('invoice_line_id', '!=', False)])

                if prodlot_ids:
                    element_searched = True

                for item in prodlot_ids:
                    item_name = item.product_id \
                        and item.product_id.name.encode('utf8') or False
                    prodlot_set_ids |= {'%s+%s' % (item.id, item_name)}

                lots_lot_set_ids |= set(prodlot_ids.mapped('id'))

            # if at least one line is not found, then return error
            if not element_searched:
                return False, line[0], False

        # all lines were found, then return those lots
        return invoice_lot_set_ids, prodlot_set_ids, lots_lot_set_ids

    @api.multi
    def onchange_load_products(self, input_data, lines_list_id):
        """
        Load claim lines from partner invoices or related production lots
        into the current claim massively
        """
        lot_lots_ids = set()
        prodlot_set_ids = set()
        lines_set_ids = set()
        current_status = scaned_data = ''

        elements_searched, line_found, lot_lots_ids = \
            self._get_lots_from_scan_data(input_data)

        if not elements_searched and not line_found:
            return {
                'value': {
                    'lines_id': [],
                    'current_status': current_status,
                    'scaned_data': scaned_data,
                },
                'domain': {
                    'lines_list_id': [('id', 'in', [])]
                }
            }
        if not elements_searched and not lot_lots_ids and line_found:
            return {
                'warning': {
                    'message': (_('The product or invoice %s'
                                  ' was not found') % line_found)},
            }
        else:
            lines_set_ids = elements_searched
            prodlot_set_ids = line_found

        for line in prodlot_set_ids:
            name = line.split('+')
            current_status += name[1] + '\n'
            scaned_data += name[0] + '\n'

        return {
            'value': {
                'lines_id': [(6, 0, list(lines_set_ids))],
                'current_status': current_status,
                'scaned_data': scaned_data,
            },
            'domain': {
                'lines_list_id': [('id', 'in', list(lines_set_ids))]
            }
        }

    def _get_lot_ids(self):
        lot = self.env['stock.production.lot']
        lot_ids = set()
        if self.scaned_data:
            lot_ids |= {lot_id
                        for lid in self.scaned_data.strip().split('\n')
                        for lot_id in lot.browse(int(lid))}

        if self.lines_list_id:
            lot_ids |= {lid for lid in self.lines_list_id}

        return lot_ids

    @api.model
    def _get_invalid_lots_set(self):
        """
        Return only those lots are related to claim lines
        """
        lot_ids = self._get_lot_ids()
        invalid_lots = self.env['claim.line'].search(
            [('prodlot_id', 'in', [lid.id for lid in lot_ids])]
        )
        return invalid_lots and invalid_lots.mapped('prodlot_id') or []

    @api.multi
    def add_claim_lines(self):
        info = self.get_data_of_products(self.scan_data)

        valid_lot_ids = set(self._get_lot_ids()) - \
            set(self._get_invalid_lots_set())

        # It creates only those claim lines that have a valid production lot,
        # i. e. not using in others claims
        info = dict(info)
        if valid_lot_ids:
            for lot_id in valid_lot_ids:
                product_id = lot_id.product_id

                claim_line_info = False
                if lot_id.name in info:
                    claim_line_info = info.get(lot_id.name, False)
                elif lot_id.invoice_line_id.invoice_id.number in info:
                    claim_line_info = \
                        info.get(lot_id.invoice_line_id.invoice_id.number,
                                 False)

                num = claim_line_info and claim_line_info[0] or '0'
                name = claim_line_info and claim_line_info[1] or ''
                if num.isdigit():
                    num = int(num)
                else:
                    num = 0

                self.create_claim_line(self.env.context.get('active_id'),
                                       self.env[
                                           'claim.line']._get_subject(num),
                                       product_id, lot_id, 1, name,
                                       lot_id.invoice_line_id)
        # normal execution
        self.action_cancel()

    @api.multi
    def change_list(self, lines):
        return {
            'value': {
                'lines_list_id': lines,
            }
        }

    message = fields.Text(string='Message', compute='_set_message')

    @api.depends('current_status', 'lines_list_id', 'scan_data')
    def _set_message(self):
        """
        Notify for missing (not added) claim lines that are in use in others
        claims
        """
        msg = ''
        all_lots = self._get_lots_from_scan_data(self.scan_data)
        not_valid_lot_ids = len(
            all_lots) > 2 and all_lots[0] | all_lots[2] or False
        if not_valid_lot_ids:
            not_valid_lot_ids = self.env['claim.line'].search(
                [('prodlot_id', 'in', list(not_valid_lot_ids))]
            ).mapped('prodlot_id')
            claim_with_lots_msg = ""

            for line_id in not_valid_lot_ids:
                claim_with_lots_msg += "\t- %s\n" % \
                    line_id._get_lot_complete_name()
            if claim_with_lots_msg:
                msg = _("The following Serial/Lot numbers won't be added,"
                        " because all of them (listed below) are currently in"
                        " used:\n\n %s" % (claim_with_lots_msg)) or ''

        self.message = msg
