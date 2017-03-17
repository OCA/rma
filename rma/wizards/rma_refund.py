# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import models, fields, exceptions, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError


class RmaRefund(models.TransientModel):
    _name = "rma.refund"

    @api.model
    def _get_reason(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', False)
        if active_ids:
            rma_lines = self.env['rma.order.line'].browse(active_ids[0])
            return rma_lines.rma_id.name
        return ''

    @api.returns('rma.order.line')
    def _prepare_item(self, line):
        values = {'product_id': line.product_id.id,
                  'name': line.name,
                  'product_qty': line.product_qty,
                  'uom_id': line.uom_id.id,
                  'qty_to_refund': line.qty_to_refund,
                  'line_id': line.id,
                  'wiz_id': self.env.context['active_id']}
        return values

    @api.model
    def default_get(self, fields):
        """Default values for wizard, if there is more than one supplier on
        lines the supplier field is empty otherwise is the unique line
        supplier.
        """
        res = super(RmaRefund, self).default_get(
            fields)
        rma_line_obj = self.env['rma.order.line']
        rma_line_ids = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']

        if not rma_line_ids:
            return res
        assert active_model == 'rma.order.line', \
            'Bad context propagation'

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res['item_ids'] = items
        return res

    date_invoice = fields.Date(string='Refund Date',
                               default=fields.Date.context_today,
                               required=True)
    date = fields.Date(string='Accounting Date')
    description = fields.Char(string='Reason', required=True,
                              default=_get_reason)
    item_ids = fields.One2many(
        'rma.refund.item',
        'wiz_id', string='Items')

    @api.multi
    def compute_refund(self, mode='refund'):
        for form in self:
            date = form.date or False
            description = form.description
            if len(self.item_ids) > 0:
                template = self.item_ids[0].line_id.invoice_line_id.invoice_id
            else:
                raise UserError(_('Nothing to refund'))
            values = self._prepare_refund(template, date_invoice=template.date,
                                          date=date, description=description,
                                          journal_id=template.journal_id.id,
                                          line=self.item_ids[0].line_id)
            new_refund = self.env['account.invoice'].create(values)
            for item in self.item_ids:
                line = item.line_id
                inv = line.invoice_line_id.invoice_id
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise UserError(_('Cannot refund draft/proforma/cancelled'
                                      ' invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_('Cannot refund invoice which is already'
                                      ' reconciled, invoice should be'
                                      ' unreconciled first. You can only '
                                      'refund this invoice.'))
                refund_line_values = self.prepare_refund_line(line)
                refund_line_values.update(invoice_id=new_refund.id)
                refund_line_id = self.env['account.invoice.line'].create(
                    refund_line_values)
                line.write({'refund_line_id': refund_line_id.id})
            # Put the reason in the chatter
            subject = _("Invoice refund")
            body = description
            new_refund.message_post(body=body, subject=subject)
            return new_refund

    @api.multi
    def invoice_refund(self):
        rma_line_ids = self.env['rma.order.line'].browse(
            self.env.context['active_ids'])
        for line in rma_line_ids:
            if line.operation != 'refund':
                raise exceptions.Warning(
                    _('The operation is not refund for at least one line'))
            if line.state != 'approved':
                raise exceptions.Warning(
                    _('RMA %s is not approved') %
                    line.rma_id.name)
        new_invoice = self.compute_refund()
        action = 'action_invoice_tree1' if (
            new_invoice.type in ['out_refund', 'out_invoice']) \
            else 'action_invoice_tree2'
        result = self.env.ref('account.%s' % action).read()[0]
        invoice_domain = result['domain']
        invoice_domain.append(('id', '=', new_invoice.id))
        result['domain'] = invoice_domain
        return result

    @api.model
    def prepare_refund_line(self, line):
        values = {}
        inv_line = line.invoice_line_id
        for name, field in inv_line._fields.iteritems():
            if name in ('id', 'create_uid', 'create_date', 'write_uid',
                        'write_date'):
                continue
            elif field.type == 'many2one' and name != 'invoice_id':
                values[name] = inv_line[name].id
            elif name == 'origin':
                values[name] = line.rma_id.name
            elif field.type not in ['many2many', 'one2many']:
                values[name] = inv_line[name]
        return values

    @api.model
    def _prepare_refund(self, invoice_template, date_invoice=None, date=None,
                        description=None, journal_id=None, line=None):
        values = {}
        for field in ['name', 'comment', 'date_due', 'company_id',
                      'account_id', 'currency_id', 'payment_term_id',
                      'user_id', 'fiscal_position_id']:
            if invoice_template._fields[field].type == 'many2one':
                values[field] = invoice_template[field].id
            else:
                values[field] = invoice_template[field] or False

            if len(line.rma_id.delivery_address_id):
                values['partner_id'] = line.rma_id.invoice_address_id.id
            else:
                values['partner_id'] = line.rma_id.partner_id.id
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
        elif invoice_template['type'] == 'in_invoice':
            journal = self.env['account.journal'].search(
                [('type', '=', 'purchase')], limit=1)
        else:
            journal = self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1)
        values['journal_id'] = journal.id
        if invoice_template['type'] == 'out_invoice':
            values['type'] = 'out_refund'
        else:
            values['type'] = 'in_refund'
        values['date_invoice'] = date_invoice
        values['state'] = 'draft'
        values['number'] = False

        if date:
            values['date'] = date
        if description:
            values['name'] = description
        return values


class RmaRefundItem(models.TransientModel):
    _name = "rma.refund.item"
    _description = "RMA Lines to refund"

    wiz_id = fields.Many2one(
        'rma.refund',
        string='Wizard', required=True)
    line_id = fields.Many2one('rma.order.line',
                              string='RMA order Line',
                              required=True,
                              readonly=True)
    rma_id = fields.Many2one('rma.order',
                             related='line_id.rma_id',
                             string='RMA',
                             readonly=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 readonly=True)
    name = fields.Char(string='Description', required=True)
    product_qty = fields.Float(
        string='Quantity Ordered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'),
        readonly=True)
    qty_to_refund = fields.Float(
        string='Quantity To Refund',
        digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
                             readonly=True)
