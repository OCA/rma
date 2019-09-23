# -*- coding: utf-8 -*-
# Copyright 2017 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.multi
    def write(self, vals):
        stage_id = vals.get('stage_id')
        if stage_id:
            stage = self.env['crm.claim.stage'].browse(stage_id)
            for rec in self:
                for claim_line in rec.claim_line_ids:
                    states = []
                    for question in claim_line.question_ids:
                        states.append(question.checklist_id.claim_state.name)
                    claim_line.show_questions = True if stage.name in \
                        states else False
        return super(CrmClaim, self).write(vals)


class ClaimLine(models.Model):
    _inherit = 'claim.line'

    question_ids = fields.Many2many(
        'rma.claim.checklist.question',
        relation='claim_line_question_rel',
        column1='claim_line_id',
        column2='question_id')
    show_questions = fields.Boolean()

    @api.model
    def create(self, vals):
        vals = self.set_questions(vals)
        return super(ClaimLine, self).create(vals)

    @api.multi
    def write(self, vals):
        vals = self.set_questions(vals)
        return super(ClaimLine, self).write(vals)

    def set_questions(self, vals):
        product_id = vals.get('product_id')
        if product_id:
            product = self.env['product.product'].browse(product_id)
            questions = self._get_questions(product)
            if questions:
                states = []
                for question in questions:
                    states.append(question.checklist_id.claim_state.name)
                show_questions = True if self.claim_id.stage_id.name in \
                    states else False
                vals.update(
                    {'question_ids':
                     [(6, 0, questions.ids)],
                     'show_questions': show_questions})
        return vals

    def _get_questions(self, product):
        checklist_model = self.env['rma.claim.checklist']
        questions = self.env['rma.claim.checklist.question']
        checklists = checklist_model.search(
            ['|',
             ('product_id.id', '=', product.id),
             ('product_category_id.id', '=', product.categ_id.id)])
        for checklist in checklists:
            questions += checklist.question_ids
        return questions
