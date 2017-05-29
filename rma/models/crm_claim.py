# -*- coding: utf-8 -*-
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models

from odoo.tools import html2plaintext
from .invoice_no_date import InvoiceNoDate
from .product_no_supplier import ProductNoSupplier


class CrmClaim(models.Model):
    _name = "crm.claim"
    _description = "Claim"
    _order = "priority,date desc"
    _inherit = ['mail.thread']

    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_stage_id(self):
        """ Gives default stage_id """
        team_id = self.env['crm.team']._get_default_team_id(user_id=self.env.uid)
        return self.stage_find([], team_id, [('sequence', '=', '1')])

    @api.model
    def _get_default_warehouse(self):
        company_id = self.env.user.company_id.id
        wh_obj = self.env['stock.warehouse']
        wh = wh_obj.search([('company_id', '=', company_id)], limit=1)
        if not wh:
            raise exceptions.UserError(
                _('There is no warehouse for the current user\'s company.')
            )
        return wh

    def _get_picking_ids(self):
        """ Search all stock_picking associated with this claim.

        Either directly with claim_id in stock_picking or through a
        procurement_group.
        """
        picking_model = self.env['stock.picking']
        for claim in self:
            claim.picking_ids = picking_model.search([
                '|',
                ('claim_id', '=', claim.id),
                ('group_id.claim_id', '=', claim.id)
            ])

    @api.multi
    def name_get(self):
        res = []
        for claim in self:
            code = claim.code and str(claim.code) or ''
            res.append((claim.id, '[' + code + '] ' + claim.name))
        return res

    id = fields.Integer('ID', readonly=True)
    name = fields.Char('Claim Subject', required=True)
    active = fields.Boolean('Active', default=True)
    action_next = fields.Char('Next Action')
    date_action_next = fields.Datetime('Next Action Date')
    description = fields.Text('Description')
    resolution = fields.Text('Resolution')
    create_date = fields.Datetime('Creation Date', readonly=True)
    write_date = fields.Datetime('Update Date', readonly=True)
    date_deadline = fields.Date('Deadline')
    date_closed = fields.Datetime('Closed', readonly=True)
    date = fields.Datetime('Claim Date', index=True, default=fields.Datetime.now)
    # ref = fields.Reference('Reference')# selection=odoo.addons.base.res.res_request.referenceable_models)
    categ_id = fields.Many2one('crm.claim.category', 'Category')
    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], 'Priority', default='1')
    type_action = fields.Selection([('correction', 'Corrective Action'), ('prevention', 'Preventive Action')],
                                   'Action Type')
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always', default=lambda self: self.env.uid)
    user_fault = fields.Char('Trouble Responsible')
    team_id = fields.Many2one('crm.team', 'Sales Team', oldname='section_id',
                              index=True, help="Responsible sales team."
                                                " Define Responsible user and Email account for"
                                                " mail gateway.",
                              default=lambda self: self.env['crm.team']._get_default_team_id())
    company_id = fields.Many2one('res.company', change_default=True,
                                 default=lambda self:
                                 self.env['res.company']._company_default_get(
                                     'crm.claim'))
    partner_id = fields.Many2one('res.partner', 'Partner')
    email_cc = fields.Text('Watchers Emails', size=252,
                           help="These email addresses will be added to the CC field of all inbound and outbound "
                           " emails for this record before being sent. Separate multiple email addresses with a comma")
    email_from = fields.Char('Email', size=128, help="Destination email for email gateway.")
    partner_phone = fields.Char('Phone')
    stage_id = fields.Many2one('crm.claim.stage', 'Stage', track_visibility='onchange',
                               domain="['|', ('team_ids', '=', team_id), ('case_default', '=', True)]",
                               default=lambda s: s._get_default_stage_id())
    cause = fields.Text('Root Cause')
    claim_line_ids = fields.One2many('claim.line', 'claim_id',
                                     string='Return lines')
    planned_revenue = fields.Float('Expected revenue')
    planned_cost = fields.Float('Expected cost')
    real_revenue = fields.Float()
    real_cost = fields.Float()
    invoice_ids = fields.One2many('account.invoice', 'claim_id', 'Refunds',
                                  copy=False)
    picking_ids = fields.One2many('stock.picking',
                                  compute=_get_picking_ids,
                                  string='RMA',
                                  copy=False)
    invoice_id = fields.Many2one('account.invoice', string='Invoice',
                                 help='Related original Cusotmer invoice')
    pick = fields.Boolean('Pick the product in the store')
    delivery_address_id = fields.Many2one('res.partner',
                                          string='Partner delivery address',
                                          help="This address will be used to "
                                          "deliver repaired or replacement "
                                          "products.")
    sequence = fields.Integer(default=lambda *args: 1)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse',
                                   required=True,
                                   default=_get_default_warehouse)
    rma_number = fields.Char(size=128, help='RMA Number provided by supplier')
    claim_type = fields.Many2one('crm.claim.type', help="Claim classification")
    stage_id = fields.Many2one(
        'crm.claim.stage',
        string='Stage',
        track_visibility='onchange',
        domain="[ '&',"
               "'|',('team_ids', '=', team_id), "
               "('case_default', '=', True), "
               "'|',('claim_type', '=', claim_type)"
               ",('claim_common', '=', True)]")
    code = fields.Char(
        string='Claim Number', required=True, default="/", readonly=True)

    _sql_constraints = [
        ('crm_claim_unique_code', 'UNIQUE (code)',
         'The code must be unique!'),
    ]

    @api.model
    def stage_find(self, cases, team_id, domain=[], order='sequence'):
        """ Override of the base.stage method
            Parameter of the stage search taken from the lead:
            - team_id: if set, stages must belong to this team or
              be a default case
        """
        if isinstance(cases, (int, long)):
            cases = self.browse(cases)
        # collect all team_ids
        team_ids = []
        if team_id:
            team_ids.append(team_id)
        for claim in cases:
            if claim.team_id:
                team_ids.append(claim.team_id.id)
        # OR all team_ids and OR with case_default
        search_domain = []
        if team_ids:
            search_domain += [('|')] * len(team_ids)
            for team_id in team_ids:
                search_domain.append(('team_ids', '=', team_id))
        search_domain.append(('case_default', '=', True))
        # AND with the domain in parameter
        search_domain += list(domain)
        # perform search, return the first found
        stage_ids = self.env['crm.claim.stage'].search(search_domain, order=order)
        if stage_ids:
            return stage_ids[0]
        return False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """This function returns value of partner address based on partner
           :param email: ignored
        """
        if not self.partner_id:
            return {'value': {'email_from': False, 'partner_phone': False}}
        address = self.env['res.partner'].browse([self.partner_id.id])
        return {'value': {'email_from': address.email, 'partner_phone': address.phone}}

    @api.model
    def create(self, vals):
        values = vals or {}
        if 'code' not in values or not values.get('code') \
                or values.get('code') == '/':

            claim_type = values.get('claim_type')
            if not claim_type:
                claim_type = self._get_claim_type_default().id

            values['code'] = self._get_sequence_number(claim_type)

        # context: no_log, because subtype already handle this
        return super(CrmClaim, self).create(vals)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default['name'] = self.name
        default['stage_id'] = self._get_default_stage_id()
        if default is None:
            default = {}
        if 'code' not in default:
            default['code'] = self.env['ir.sequence'].next_by_code('crm.claim')
        return super(CrmClaim, self).copy(default=default)

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------
    @api.model
    def message_new(self, msg, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        create_context = dict(self.env.context or {})
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'partner_id': msg.get('author_id', False),
        }
        if custom_values:
            defaults.update(custom_values)
        if msg.get('priority'):
            defaults['priority'] = msg.get('priority')
        defaults.update(custom_values)
        return super(CrmClaim, self.with_context(create_context)).message_new(msg, custom_values=defaults)

    @api.model
    def _get_claim_type_default(self):
        return self.env.ref('rma.crm_claim_type_customer')

    claim_type = fields.Many2one('crm.claim.type', default=_get_claim_type_default,
                        help="Claim classification",
                        required=True)

    @api.onchange('invoice_id')
    def _onchange_invoice(self):
        # Since no parameters or context can be passed from the view,
        # this method exists only to call the onchange below with
        # a specific context (to recreate claim lines).
        # This does require to re-assign self.invoice_id in the new object
        claim_with_ctx = self.with_context(
            create_lines=True
        )
        claim_with_ctx.invoice_id = self.invoice_id
        claim_with_ctx._onchange_invoice_warehouse_type_date()
        values = claim_with_ctx._convert_to_write(claim_with_ctx._cache)
        self.update(values)

    @api.onchange('warehouse_id', 'claim_type', 'date')
    def _onchange_invoice_warehouse_type_date(self):
        context = self.env.context
        claim_line = self.env['claim.line']
        if not self.warehouse_id:
            self.warehouse_id = self._get_default_warehouse()
        claim_type = self.claim_type
        claim_date = self.date
        warehouse = self.warehouse_id
        company = self.company_id
        create_lines = context.get('create_lines')

        def warranty_values(invoice, product):
            values = {}
            try:
                warranty = claim_line._warranty_limit_values(
                    invoice, claim_type, product, claim_date)
            except (InvoiceNoDate, ProductNoSupplier):
                # we don't mind at this point if the warranty can't be
                # computed and we don't want to block the user
                values.update({'guarantee_limit': False, 'warning': False})
            else:
                values.update(warranty)

            warranty_address = claim_line._warranty_return_address_values(
                product, company, warehouse)
            values.update(warranty_address)
            return values

        if create_lines:  # happens when the invoice is changed
            claim_lines = []
            invoices_lines = self.invoice_id.invoice_line_ids.filtered(
                lambda line: line.product_id.type in ('consu', 'product')
            )
            for invoice_line in invoices_lines:
                location_dest = claim_line.get_destination_location(
                    invoice_line.product_id, warehouse)
                line = {
                    'name': invoice_line.name,
                    'claim_origin': "none",
                    'invoice_line_id': invoice_line.id,
                    'product_id': invoice_line.product_id.id,
                    'product_returned_quantity': invoice_line.quantity,
                    'unit_sale_price': invoice_line.price_unit,
                    'location_dest_id': location_dest.id,
                    'state': 'draft',
                }
                line.update(warranty_values(invoice_line.invoice_id,
                                            invoice_line.product_id))
                claim_lines.append((0, 0, line))

            value = self._convert_to_cache(
                {'claim_line_ids': claim_lines}, validate=False)
            self.update(value)

        if self.invoice_id:
            self.delivery_address_id = self.invoice_id.partner_id.id

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        """ Override to get the reply_to of the parent project.
        """
        results = dict.fromkeys(res_ids, default or False)
        if res_ids:
            claims = self.browse(res_ids)
            results.update({
                claim.id: self.env['crm.team'].message_get_reply_to(
                    [claim.team_id], default
                )[claim.team_id] for claim in claims if claim.team_id
            })

        return results

    @api.multi
    def message_get_suggested_recipients(self):
        recipients = super(CrmClaim, self).message_get_suggested_recipients()
        try:
            for claim in self:
                if claim.partner_id:
                    claim._message_add_suggested_recipient(
                        recipients,
                        partner=claim.partner_id,
                        reason=_('Customer')
                    )
                elif claim.email_from:
                    claim._message_add_suggested_recipient(
                        recipients,
                        email=claim.email_from,
                        reason=_('Customer Email')
                    )
        except exceptions.AccessError:
            # no read access rights -> just ignore suggested recipients
            # because this imply modifying followers
            pass
        return recipients

    def _get_sequence_number(self, code_id):
        claim_type_code = self.env['crm.claim.type'].browse([code_id]).ir_sequence_id.code
        sequence = self.env['ir.sequence']
        return claim_type_code and sequence.next_by_code(
            claim_type_code
        ) or '/'


    @api.multi
    def copy(self, default=None):
        self.ensure_one()

        default = default or {}
        std_default = {
            'code': '/'
        }

        std_default.update(default)
        return super(CrmClaim, self).copy(default=std_default)


class CrmClaimCategory(models.Model):
    _name = "crm.claim.category"
    _description = "Category of claim"

    name = fields.Char('Name', required=True, translate=True)
    team_id = fields.Many2one('crm.team', 'Sales Team')


class CrmClaimStage(models.Model):
    """ Model for claim stages. This models the main stages of a claim
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only stages, instead of state and stages.
        Stages are for example used to display the kanban view of records.
    """
    _name = "crm.claim.stage"
    _description = "Claim stages"
    _rec_name = 'name'
    _order = "sequence"

    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Used to order stages. Lower is better.", default=1)
    team_ids = fields.Many2many('crm.team', 'crm_team_claim_stage_rel',
                                'stage_id', 'team_id', string='Teams',
                                help="Link between stages and sales teams. When set, "
                                "this limitate the current stage to the selected sales teams.")
    case_default = fields.Boolean('Common to All Teams',
                                  help="If you check this field, this stage will be proposed by default "
                                  " on each sales team. It will not assign this stage to existing teams.")
    claim_type = fields.Many2one('crm.claim.type', help="Claim classification")
    claim_common = fields.Boolean(string='Common to All Claim Types',
                                  help="If you check this field,"
                                       " this stage will be proposed"
                                       " by default on each claim type.")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _claim_count(self):
        claim = self.env['crm.claim']
        for partner in self:
            partner.claim_count = claim.search_count(
                ['|', ('partner_id', 'in', partner.child_ids.ids), ('partner_id', '=', partner.id)])

    claim_count = fields.Integer(compute='_claim_count', string='# Claims')
