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
    name = fields.Char(compute="_compute_complete_name",
                       string="Complete Lot Name",)

    @api.constrains('product_id', 'invoice_line_id')
    def _check_product_id(self):
        for line_id in self:
            if line_id.product_id != line_id.invoice_line_id.product_id:
                raise ValidationError(_("The product of the invoice %s is not "
                                      "same that product %s") %
                                      (line_id.invoice_line_id.product_id.name,
                                       line_id.product_id.name))

    @api.depends('invoice_line_id', 'lot_id', 'product_id')
    def _compute_complete_name(self):
        for line_id in self:
            invoice_number = line_id.invoice_line_id.invoice_id.number
            product_name = line_id.product_id.name
            name_format = "(ID: %s) - %s - %s"
            name_values = (line_id.id, product_name, invoice_number)
            if line_id.lot_id:
                name_format += " - %s"
                name_values += (line_id.lot_id.name,)
            line_id.name = name_format % name_values


class ReturnedLinesFromSerial(models.TransientModel):

    _name = 'returned.lines.from.serial.wizard'
    _description = 'Wizard to create product return lines'
    ' from serial numbers or invoices'

    @api.model
    def _get_default_partner_id(self):
        """Obtain partner from the claim
        """
        claim_id = self.env.context.get('active_id')
        partner_id = self.env['crm.claim'].browse(claim_id).partner_id
        return partner_id and partner_id[0] or self.env['res.partner']

    @api.model
    def create_claim_line(self, claim_id, claim_origin, product_id,
                          claim_line_wizard, qty, name):
        inv_line = claim_line_wizard.invoice_line_id
        lot_id = False
        if claim_line_wizard.lot_id:
            inv_line = self.prodlot_2_invoice_line(claim_line_wizard.lot_id)
            lot_id = claim_line_wizard.lot_id.id
        line_id = self.env['claim.line'].create({
            'claim_id': claim_id,
            'claim_origin': claim_origin,
            'product_id': product_id and product_id.id or False,
            'name': name and name or (product_id and product_id.name or
                                      inv_line.name),
            'invoice_line_id': inv_line.id,
            'product_returned_quantity': qty,
            'prodlot_id': lot_id,
        })
        line_id.set_warranty()
        return line_id

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
        customer_type = self.env.ref('crm_claim_rma.crm_claim_type_customer')
        supplier_type = self.env.ref('crm_claim_rma.crm_claim_type_supplier')
        return current_claim_type, customer_type, supplier_type

    @api.model
    def prodlot_2_invoice_line(self, lot_id):
        """Return the last line of customer invoice
        based in serial/lot number
        """
        current_type, customer_type, supplier_type = self._get_claim_type()
        customer_line_id = lot_id.invoice_line_id
        supplier_line_id = lot_id.supplier_invoice_line_id
        invoice_line_id = customer_line_id or supplier_line_id
        if supplier_type == current_type:
            invoice_line_id = supplier_line_id
        elif customer_type == current_type:
            invoice_line_id = customer_line_id

        return invoice_line_id or False

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
        """@return: view with metasearch field
        """
        view_id = self.env.\
            ref('crm_claim_rma.view_enter_product')
        return view_id

    @api.multi
    def render_metasearch_view(self):
        """Render wizard view with metasearch field
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

    @staticmethod
    def get_data_of_products(input_data):
        """It parses all invoices and serial lot numbers added by the user,
        this is received as a long string. The data is split based on
        break lines in the first place to be able to parse each line
        separately. After that, splitting is made using a '*' char to know if a
        given line contains a reason and comment (optional).'
        :param input_data: Input given by the user in the wizard
        :return A list of tuples containing parsed lines

        """
        data_line = []
        input_data = (input_data or '').strip('\n ')
        for line in input_data.split('\n'):
            line = line.strip()
            line_parts = line.split('*')
            if not line or ('*' in line and not line_parts[0]):
                continue

            reason = line_parts[1] if len(line_parts) in [2, 3] else '0'
            comment = line_parts[2] if len(line_parts) == 3 else ''
            line = (line_parts[0], (reason.strip(), comment.strip()))
            data_line.append(line)
        return data_line

    def _search_lots_by_invoices(self, invoice_ids):
        line_set_ids = self.env.context.get('line_set_ids', [])
        invoice_ids = invoice_ids or self.env['account.invoice']
        invoice_line_ids = invoice_ids.mapped("invoice_line")
        current_claim_type, supplier_claim_type = self._get_claim_type()[0::2]
        invoice_field = 'supplier_invoice_line_id'\
            if supplier_claim_type == current_claim_type else\
            'invoice_line_id'
        for invoice_line_id in invoice_line_ids:
            enter = False
            # Search items displayed with the current invoice line
            current_item_ids = self.env['claim.line.wizard'].search([
                ('invoice_line_id', '=', invoice_line_id.id)])

            # Search serial/lot numbers with that invoice line
            lot_ids = self.env['stock.production.lot'].search(
                [(invoice_field, '=', invoice_line_id.id)])

            if len(current_item_ids) < int(invoice_line_id.quantity):
                # Displays missing product of invoice line
                # on the wizard
                lot_filtered_ids = current_item_ids.filtered(
                    lambda r: r not in line_set_ids)
                lot_ids -= lot_filtered_ids.mapped('lot_id')

                # Calculate the missing items to create
                num_to_create = int(invoice_line_id.quantity) - \
                    len(current_item_ids)
                num = 0
                while num < num_to_create:
                    line_id = self.env['claim.line.wizard'].create({
                        'product_id': invoice_line_id.product_id.id,
                        'invoice_line_id': invoice_line_id.id,
                    })
                    # If in the invoice line there are products with
                    # serial/lot numbers, displays serial/lot number
                    if lot_ids:
                        lot_id = lot_ids[0]
                        lot_ids -= lot_id
                        line_id.write({'lot_id': lot_id.id})

                    line_set_ids.extend(
                        [line_id] if line_id not in line_set_ids
                        else [])
                    num += 1
                enter = True

            # If there is still product that belongs to an
            # invoice line without serial/lot number and there is
            # available serial/lot numbers to be used
            if not enter:
                item_wo_lot = [el for el in current_item_ids
                               if el not in line_set_ids]
                used_lot_ids = []
                for item, lot_id in zip(item_wo_lot, lot_ids):
                    item.write({'lot_id': lot_id.id})
                    used_lot_ids.append(lot_id.id)
                line_set_ids.extend([item for item in item_wo_lot])
                lot_ids -= self.env['stock.production.lot'].browse(
                    used_lot_ids)
        return line_set_ids

    def _get_lots_from_scan_data(self, input_data):
        """Given a raw input data from the wizard, this method will find
        all invoices and serial/lot records related

        :input_data: input entered by the user right in the wizard
        """
        input_lines = self.get_data_of_products(input_data)
        invoice = self.env['account.invoice']
        lot = self.env['stock.production.lot']
        clw = self.env['claim.line.wizard']
        ctx = dict(self.env.context or {})
        prodlot_set_ids = set()
        line_set_ids = []
        lots_lot_set_ids = []

        if not input_lines:
            return False, False, False

        for line in input_lines:
            number_serial = line[0].encode('utf8')
            # search invoices first
            invoice_ids = invoice.search([('number', '=', number_serial)])
            element_searched = False

            if invoice_ids:
                ctx.update({'line_set_ids': line_set_ids})
                element_searched = self.with_context(ctx).\
                    _search_lots_by_invoices(invoice_ids)
            else:  # it must be a serial lot number
                prodlot_ids, invoice_line_id = \
                    self._search_lot_by_name_based_on_type(number_serial)
                # assign lots to wizard serial lot (as wizard items)
                if prodlot_ids:
                    lots_mapped = prodlot_ids.mapped('id')
                    # create wizard items for those lots that haven't been
                    # assigned yet
                    item_ids = clw.search(
                        [('lot_id', 'in', lots_mapped)])
                    item_lots = item_ids.mapped('lot_id.id')
                    lot4create = [l for l in lots_mapped if l not in item_lots]
                    for lot_id in lot4create:
                        lot_id = lot.browse(lot_id)
                        clw.create({
                            'product_id': lot_id.product_id.id,
                            'lot_id': lot_id.id,
                            'invoice_line_id': invoice_line_id.id,
                        })

                    # keep wizard lines if aren't already
                    item_ids = clw.search(
                        [('lot_id', 'in', lots_mapped)])
                    line_set_ids.extend(
                        [e for e in item_ids if e not in line_set_ids])
                    element_searched = True

                for item in prodlot_ids:
                    item_name = item.product_id \
                        and item.product_id.name.encode('utf8') or False
                    prodlot_set_ids |= {'%s+%s' % (item.id, item_name)}

                lots_lot_set_ids.extend(
                    [l for l in line_set_ids if l not in lots_lot_set_ids])

            # if at least one line is not found, then return error
            if not element_searched:
                return False, line[0], False

        # all lines were found, then return those lots
        return line_set_ids, prodlot_set_ids, lots_lot_set_ids

    @api.model
    def _search_lot_by_name_based_on_type(self, lot_number):
        """Search a product serial/lot number on its name and returns
        the invoice line based on claim type
        :lot_number: serial/lot number assigned when it was created
        :returns: record for serial/lot number and related invoice line record
        """
        lot = self.env['stock.production.lot']
        claim_type, customer_type, supplier_type = self._get_claim_type()
        lot_id = False
        # Determine names list to be used in domain
        field_names = ['invoice_line_id', 'supplier_invoice_line_id']
        if customer_type == claim_type:
            field_names = field_names[:1]
        elif supplier_type == claim_type:
            field_names = field_names[1:]

        # Build domain
        domain = ['|'] if len(field_names) > 1 else []
        for field in field_names:
            domain.append((field, '!=', False))
        domain = [('name', '=', lot_number)] + domain

        # Search lot and set invoice line
        lot_id = lot.search(domain)
        field_name = field_names[0]
        if claim_type not in [customer_type, supplier_type]:
            field_name = field_names[0] if lot_id.invoice_line_id else \
                field_names[1]
        invoice_line_id = getattr(lot_id, field_name)

        return lot_id, invoice_line_id

    @api.multi
    def onchange_load_products(self, input_data, lines_list_id):
        """Load claim lines from partner invoices or related production lots
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
                    'message':
                    (_('The product or invoice %s was not found')
                     % line_found.decode('utf8'))
                },
            }
        else:
            lines_set_ids = elements_searched
            prodlot_set_ids = line_found

        for line in prodlot_set_ids:
            name = line.split('+')
            current_status += name[1] + '\n'
            scaned_data += name[0] + '\n'

        lines_set_ids = [wizard_item_id.id for wizard_item_id in lines_set_ids]
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
        clw = self.env['claim.line.wizard']
        lot = self.env['stock.production.lot']
        lot_ids = []
        if self.scaned_data:
            lot_ids = [lot_id
                       for lid in self.scaned_data.strip().split('\n')
                       for lot_id in lot.browse(int(lid))]
        lot_ids = list(set([lot_id.id for lot_id in lot_ids]))
        clw_ids = clw.search([('lot_id', 'in', lot_ids)])
        lot_ids = set([line for line in clw_ids])

        if self.lines_list_id:
            lot_ids |= {lid for lid in self.lines_list_id}

        return lot_ids

    @api.model
    def _get_invalid_lots_set(self, claim_line_wizard_ids, add=False):
        """Return only those lots are related to claim lines
        """
        clw = self.env['claim.line.wizard']
        claim_line = self.env['claim.line']
        valid_lot_ids = clw.browse(claim_line_wizard_ids)
        invalid_lots_list = []
        line_ids = clw.browse(claim_line_wizard_ids).filtered(
            lambda r: r.lot_id)
        for line_id in line_ids:
            invalid_lot = claim_line.search([
                ('invoice_line_id', '=', line_id.invoice_line_id.id),
                ('product_id', '=', line_id.product_id.id),
                ('prodlot_id', '=', line_id.lot_id.id),
            ])
            if invalid_lot:
                invalid_lots_list.append(line_id)
            else:
                valid_lot_ids = valid_lot_ids - line_id

        for inv_line_id in valid_lot_ids.mapped('invoice_line_id'):
            invalid_lot = claim_line.search([
                ('invoice_line_id', '=', inv_line_id.id),
                ('product_id', '=', inv_line_id.product_id.id), ])

            if not invalid_lot:
                continue

            inv_line_ids = \
                clw.search([('invoice_line_id', '=', inv_line_id.id), ])

            for item_id in invalid_lot:
                lot_id = item_id.prodlot_id.id or False
                wizard_line_id = clw.search([
                    ('lot_id', '=', lot_id),
                    ('id', 'in', inv_line_ids.mapped('id')),
                    ('id', 'not in', [il.id for il in invalid_lots_list])])
                if wizard_line_id:
                    invalid_lots_list.append(wizard_line_id[0])

        return invalid_lots_list and invalid_lots_list or []

    @api.multi
    def add_claim_lines(self):
        info = self.get_data_of_products(self.scan_data)
        lot_ids = self._get_lot_ids()
        lot_ids = [lid.id for lid in lot_ids]
        clw_ids = set(self._get_lot_ids()) - \
            set(self._get_invalid_lots_set(lot_ids, True))
        clw_ids = list(clw_ids)
        # It creates only those claim lines that have a valid production lot,
        # i.e. not using in others claims
        info = dict(info)
        new_claim_lines = []

        for clw_id in clw_ids:
            product_id = clw_id.product_id

            claim_line_info = False
            if clw_id.lot_id.name in info:
                claim_line_info = info.get(clw_id.lot_id.name, False)
            elif clw_id.invoice_line_id.invoice_id.number in info:
                claim_line_info = \
                    info.get(clw_id.invoice_line_id.invoice_id.number, False)

            num = claim_line_info and claim_line_info[0] or '0'
            num = int(num) if num.isdigit() else 0
            name = claim_line_info and claim_line_info[1] or ''

            new_claim_lines.append(self.create_claim_line(
                self.env.context.get('active_id'),
                self.env['claim.line']._get_subject(num),
                product_id, clw_id, 1, name))

        if clw_ids:
            # Clean items in wizard model
            ids = tuple([clw.id for clw in clw_ids])
            self.env.cr.execute("DELETE FROM claim_line_wizard "
                                "WHERE id IN %s", (ids,))

        # normal execution
        self.action_cancel()
        return new_claim_lines

    @api.multi
    def change_list(self, lines):
        return {
            'value': {
                'lines_list_id': lines,
            }
        }

    message = fields.Text(compute='_compute_set_message')

    @api.depends('current_status', 'lines_list_id', 'scan_data')
    def _compute_set_message(self):
        """Notify for missing (not added) claim lines that are in use in
        others claims
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

    @api.multi
    def button_show_help(self):
        """It shows help
        """
        view_id = self.env.ref('crm_claim_rma.help_message_form')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def button_get_back_to_wizard(self):
        ctx = dict(self.env.context or {})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'active_id': ctx.get('active_id'),
            'active_ids': ctx.get('active_ids'),
            'context': ctx,
        }
