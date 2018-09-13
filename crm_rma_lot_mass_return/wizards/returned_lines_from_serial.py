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
from openerp.exceptions import ValidationError


class ClaimLineWizard(models.TransientModel):

    _name = "claim.line.wizard"

    product_id = fields.Many2one("product.product",
                                 string="Product",
                                 help="Product to claim")
    lot_id = fields.Many2one("stock.production.lot",
                             string="Lot",
                             help="Product to claim")
    invoice_line_id = fields.Many2one("account.invoice.line",
                                      required=True,
                                      string="Invoice Line",
                                      help="Invoice Line")
    name = fields.Char(compute="_compute_get_complete_name",
                       string="Complete Lot Name",)

    @api.constrains('product_id', 'invoice_line_id')
    def _check_product_id(self):
        for record in self:
            if record.product_id != \
                    record.invoice_line_id.product_id:
                raise ValidationError(_("The product of the"
                                        " invoice %s is not same"
                                        " that product %s" %
                                      (record.invoice_line_id.product_id.name,
                                       record.product_id.name)))

    @api.depends('invoice_line_id', 'lot_id', 'product_id')
    def _compute_get_complete_name(self):
        for wizard in self:
            invoice_number = wizard.invoice_line_id.invoice_id.number
            product_name = wizard.product_id.name

            lot_name = False
            if wizard.lot_id:
                lot_name = wizard.lot_id.name

            if not lot_name:
                name = _("(ID: %s) - %s - %s") % \
                    (wizard.id,
                     product_name,
                     invoice_number)
            else:
                name = _("(ID: %s) - %s - %s - %s") % \
                    (wizard.id,
                     product_name,
                     invoice_number,
                     lot_name)

            wizard.name = name


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
    def create_claim_line(self, claim_id, claim_origin,
                          product_record, claim_line_wizard,
                          qty, name):
        clima_line = self.env['claim.line']
        if claim_line_wizard.lot_id:
            inv_line = self.prodlot_2_invoice_line(
                claim_line_wizard.lot_id.name)
            lot_id = claim_line_wizard.lot_id.id
        else:
            inv_line = claim_line_wizard.invoice_line_id
            lot_id = False
        line_rec = clima_line.create({
            'claim_id': claim_id,
            'claim_origin': claim_origin,
            'product_id': product_record and product_record.id or False,
            'name': name and name or (product_record and
                                      product_record.name or
                                      inv_line.name),
            'invoice_line_id': inv_line.id,
            'product_returned_quantity': qty,
            'prodlot_id': lot_id,
        })
        line_rec.set_warranty()

    # If "Cancel" button pressed
    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}

    partner_id = fields.Many2one('res.partner',
                                 'Partner',
                                 default=_get_default_partner_id)

    def _get_claim_type(self):
        claim_id = self.env.context.get('active_id')
        claim_record = self.env['crm.claim'].browse(claim_id)
        current_claim_type = claim_record.claim_type
        customer_claim_type = \
            self.env.ref('crm_claim_type.crm_claim_type_customer')
        supplier_claim_type = \
            self.env.ref('crm_claim_type.crm_claim_type_supplier')
        return current_claim_type, customer_claim_type, supplier_claim_type

    @api.model
    def prodlot_2_invoice_line(self, prodlot):
        """
        Return the last line of customer invoice
        based in serial/lot number
        """
        lot_obj = self.env['stock.production.lot']
        current_claim_type, customer_claim_type, supplier_claim_type = \
            self._get_claim_type()

        prodlot = lot_obj.search([('name', '=', str(prodlot))])

        if supplier_claim_type == current_claim_type:
            if prodlot.supplier_invoice_line_id:
                return prodlot.supplier_invoice_line_id
        elif customer_claim_type == current_claim_type:
            if prodlot.invoice_line_id:
                return prodlot.invoice_line_id
        else:
            if prodlot.invoice_line_id:
                return prodlot.invoice_line_id
            elif prodlot.supplier_invoice_line_id:
                return prodlot.supplier_invoice_line_id

        return False

    lines_list_id = fields.Many2many('claim.line.wizard',
                                     'claim_line_wizard_returned',
                                     'wizard_id',
                                     'claim_line_wizard_id',
                                     string='Products selected',
                                     help='Field used to show the current '
                                          'status of the lots '
                                          'loaded')
    option_ids = fields.Many2many('claim.line.wizard',
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
        lot_set_ids = []
        lots_lot_set_ids = []

        if not input_lines:
            return False, False, False

        current_claim_type, customer_claim_type, supplier_claim_type = \
            self._get_claim_type()

        claim_line_wizard = self.env['claim.line.wizard']

        for line in input_lines:
            # if there is no invoice/serial in it
            if not line[0]:
                continue

            number_serial = line[0].encode('utf8')
            # search invoices first
            invoice_ids = invoice.search([('number', '=', number_serial)])
            element_searched = False
            if invoice_ids:

                if supplier_claim_type == current_claim_type:
                    invoice_field = 'supplier_invoice_line_id'
                elif customer_claim_type == current_claim_type:
                    invoice_field = 'invoice_line_id'

                for inv in invoice_ids:
                    for inv_line in inv.invoice_line:
                        clw = claim_line_wizard.\
                            search([('invoice_line_id', '=', inv_line.id)])
                        enter = False
                        lot_ids = lot.\
                            search([(invoice_field, '=',
                                     inv_line.id)])
                        if len(clw) < int(inv_line.quantity):
                            for asd in clw:
                                if asd not in lot_set_ids:
                                    lot_set_ids.append(asd)
                                    lot_ids = lot_ids - asd.lot_id
                            num_to_create = int(inv_line.quantity) - len(clw)
                            for num in xrange(0, num_to_create):
                                clw = \
                                    claim_line_wizard.\
                                    create({
                                        'product_id':
                                        inv_line.product_id.id,
                                        'invoice_line_id': inv_line.id,
                                    })
                                if lot_ids:
                                    lot = lot_ids[0]
                                    clw.write({'lot_id': lot.id})
                                    lot_ids = lot_ids - lot
                                for asd in clw:
                                    if asd not in lot_set_ids:
                                        lot_set_ids.append(asd)
                            enter = True
                        if not enter:
                            for asd in clw:
                                if asd not in lot_set_ids:
                                    if lot_ids:
                                        lot = lot_ids[0]
                                        asd.write({'lot_id': lot.id})
                                        lot_ids = lot_ids - lot
                                    lot_set_ids.append(asd)

                element_searched = lot_set_ids
            else:
                # if not, it must be a serial lot number
                prodlot_ids = lot
                if supplier_claim_type == current_claim_type:
                    prodlot_ids = \
                        lot.search([('name', '=', number_serial),
                                    ('supplier_invoice_line_id', '!=', False)])
                    invoice_line = prodlot_ids.supplier_invoice_line_id
                elif customer_claim_type == current_claim_type:
                    prodlot_ids = \
                        lot.search([('name', '=', number_serial),
                                    ('invoice_line_id', '!=', False)])
                    invoice_line = prodlot_ids.invoice_line_id
                else:
                    prodlot_ids = \
                        lot.search([('name', '=', number_serial), '|',
                                    ('supplier_invoice_line_id', '!=', False),
                                    ('invoice_line_id', '!=', False),
                                    ])
                    if prodlot_ids.invoice_line_id:
                        invoice_line = prodlot_ids.invoice_line_id
                    else:
                        invoice_line = prodlot_ids.supplier_invoice_line_id
                if prodlot_ids:
                    for lot_id in prodlot_ids:
                        clw = claim_line_wizard.\
                            search([('lot_id', '=', lot_id.id)])
                        if not clw:
                            clw = \
                                claim_line_wizard.\
                                create({
                                    'product_id': lot_id.product_id.id,
                                    'lot_id': lot_id.id,
                                    'invoice_line_id': invoice_line.id,
                                })
                        for asd in clw:
                            if asd not in lot_set_ids:
                                lot_set_ids.append(asd)
                    element_searched = True

                for item in prodlot_ids:
                    item_name = item.product_id \
                        and item.product_id.name.encode('utf8') or False
                    prodlot_set_ids |= {'%s+%s' % (item.id, item_name)}

                for asd in lot_set_ids:
                    if asd not in lots_lot_set_ids:
                        lots_lot_set_ids.append(asd)

            # if at least one line is not found, then return error
            if not element_searched:
                return False, line[0], False

        # all lines were found, then return those lots
        return lot_set_ids, prodlot_set_ids, lots_lot_set_ids

    @api.multi
    def onchange_load_products(self, input_data, lines_list_id):
        """
        Load claim lines from partner invoices or related production lots
        into the current claim massively
        """
        lot_lots_ids = []
        prodlot_set_ids = set()
        lines_set_ids = []
        current_status = scaned_data = ''

        elements_searched, line_found, lot_lots_ids = \
            self._get_lots_from_scan_data(input_data)

        if not elements_searched and not line_found:
            return {
                'value': {
                    'option_ids': [],
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

        lines_set_ids = [asd.id for asd in lines_set_ids]
        return {
            'value': {
                'option_ids': [(6, 0, lines_set_ids)],
                'current_status': current_status,
                'scaned_data': scaned_data,
            },
            'domain': {
                'lines_list_id': [('id', 'in', lines_set_ids)]
            }
        }

    def _get_lot_ids(self):
        lot = self.env['stock.production.lot']
        lot_ids = set()
        if self.scaned_data:
            lot_ids |= {lot_id
                        for lid in self.scaned_data.strip().split('\n')
                        for lot_id in lot.browse(int(lid))}

        claim_line_wizard = self.env['claim.line.wizard']

        lot_ids_2 = []
        for wizard_id in lot_ids:
            clws = claim_line_wizard.search([('lot_id', '=', wizard_id.id)])
            for clw in clws:
                lot_ids_2.append(clw)

        lot_ids = set(lot_ids_2)

        if self.lines_list_id:
            lot_ids |= {lid for lid in self.lines_list_id}

        return lot_ids

    @api.model
    def _get_invalid_lots_set(self, claim_line_wizard_ids, add=False):
        """
        Return only those lots are related to claim lines
        """
        claim_line_wizard = self.env['claim.line.wizard']
        valid = claim_line_wizard.browse(claim_line_wizard_ids)
        invalid_lots = []
        for clw in claim_line_wizard.browse(claim_line_wizard_ids):
            if clw.lot_id:
                invalid_lot = self.env['claim.line'].search([
                    ('invoice_line_id', '=', clw.invoice_line_id.id),
                    ('product_id', '=', clw.product_id.id),
                    ('prodlot_id', '=', clw.lot_id.id),
                ])
                if not invalid_lot:
                    valid = valid - clw
                if invalid_lot:
                    invalid_lots.append(clw)

        for clw in valid.mapped('invoice_line_id'):

            # mac1, None -> claim.line
            invalid_lot = self.env['claim.line'].search([
                ('invoice_line_id', '=', clw.id),
                ('product_id', '=', clw.product_id.id),
            ])

            # mac1, mac2, mac3, mac4, None -> breaked down
            clws = self.env['claim.line.wizard'].\
                search([('invoice_line_id', '=', clw.id),
                        ])

            if invalid_lot:
                for item in invalid_lot:
                    if item.prodlot_id:
                        add = clws.search([
                            ('lot_id', '=', item.prodlot_id.id),
                            ('id', 'in', clws.mapped('id')),
                            ('id', 'not in', [rdy.id for rdy in invalid_lots]),
                        ])
                    else:
                        add = clws.search([
                            ('lot_id', '=', False),
                            ('id', 'in', clws.mapped('id')),
                            ('id', 'not in', [rdy.id for rdy in invalid_lots]),
                        ])
                    if add:
                        invalid_lots.append(add[0])

        # mac1, None -> like claim.line.wizard
        return invalid_lots and invalid_lots or []

    @api.multi
    def add_claim_lines(self):
        info = self.get_data_of_products(self.scan_data)
        lot_ids = self._get_lot_ids()
        lot_ids = [lid.id for lid in lot_ids]
        clw_ids = set(self._get_lot_ids()) - \
            set(self._get_invalid_lots_set(lot_ids, True))
        clw_ids = list(clw_ids)
        # It creates only those claim lines that have a valid production lot,
        # i. e. not using in others claims
        info = dict(info)

        if clw_ids:
            for clw_id in clw_ids:
                product_id = clw_id.product_id

                claim_line_info = False
                if clw_id.lot_id.name in info:
                    claim_line_info = info.get(clw_id.lot_id.name, False)
                elif clw_id.invoice_line_id.invoice_id.number in info:
                    claim_line_info = \
                        info.get(clw_id.invoice_line_id.invoice_id.number,
                                 False)

                num = claim_line_info and claim_line_info[0] or '0'
                name = claim_line_info and claim_line_info[1] or ''
                if num.isdigit():
                    num = int(num)
                else:
                    num = 0

                current_claim_type, customer_claim_type, \
                    supplier_claim_type = \
                    self._get_claim_type()
                self.create_claim_line(self.env.context.get('active_id'),
                                       self.env[
                                           'claim.line']._get_subject(num),
                                       product_id, clw_id, 1, name)
            ids_to_delete = tuple([clw.id for clw in clw_ids])
            self._cr.execute(
                "DELETE FROM claim_line_wizard where id IN %s",
                (ids_to_delete, ))

        # normal execution
        self.action_cancel()

    @api.multi
    def change_list(self, lines):
        return {
            'value': {
                'lines_list_id': lines,
            }
        }

    message = fields.Text(string='Message',
                          compute='_compute_set_message'
                          )

    @api.depends('current_status', 'lines_list_id', 'scan_data')
    def _compute_set_message(self):
        """
        Notify for missing (not added) claim lines that are in use in others
        claims
        """
        for wizard in self:
            msg = ''
            all_lots = wizard._get_lots_from_scan_data(wizard.scan_data)
            not_valid_lot_ids = set()
            if all_lots[0]:
                all_lots_0 = [item for item in all_lots[0]]
                not_valid_lot_ids = set(all_lots_0)
            if all_lots[2]:
                all_lots_2 = [item for item in all_lots[2]]
                not_valid_lot_ids |= set(all_lots_2)

            if not_valid_lot_ids:
                not_valid_lot_ids = [item.id for
                                     item in list(not_valid_lot_ids)]
                not_valid_lot_ids = wizard.\
                    _get_invalid_lots_set(not_valid_lot_ids)
                not_valid_lot_ids = list(set(not_valid_lot_ids))
                claim_with_lots_msg = ""

                for line_id in not_valid_lot_ids:
                    claim_with_lots_msg += "\t- %s\n" % \
                        line_id.name
                if claim_with_lots_msg:
                    msg = _("The following Serial/Lot numbers won't be added,"
                            " because all of them (listed below)"
                            " are currently in"
                            " use:\n\n %s") % (claim_with_lots_msg) or ''

            wizard.message = msg
