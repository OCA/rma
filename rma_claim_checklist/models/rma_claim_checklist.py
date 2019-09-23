# -*- coding: utf-8 -*-
# Copyright 2017-2018 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class RmaClaimChecklist(models.Model):
    _name = 'rma.claim.checklist'

    claim_state = fields.Many2one(
        'crm.claim.stage',
        help='Select the claim state in which you want the checklist to appear'
    )
    product_id = fields.Many2one('product.product', string='Product')
    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category')
    question_ids = fields.One2many(
        'rma.claim.checklist.question', 'checklist_id')

    @api.onchange('claim_state')
    def onchange_claim_state(self):
        """
        Find the Claims this checklist has it's questions attached to and
        calculate if these questions should be visible at the current stage
        of the claim.
        """
        self.env.cr.execute(
            "SELECT claim_line_id FROM claim_line_question_rel WHERE"
            " question_id = ANY(%s)",
            (self.question_ids.ids, ))
        for line_id in self.env.cr.fetchall():
            line = self.env['claim.line'].browse(line_id)
            if self.claim_state.name == line.claim_id.stage_id.name:
                self.env.cr.execute(
                    "UPDATE claim_line SET show_questions = True")


class RmaClaimChecklistQuestion(models.Model):
    _name = 'rma.claim.checklist.question'

    @api.depends('answer')
    def _compute_answer_text(self):
        for this in self:
            if this.answer.get('type') == 'free_text':
                this.answer_text = this.answer['value']

    def _inverse_answer_text(self):
        for this in self:
            this.answer = {
                'type': 'free_text',
                'value': this.answer_text}

    @api.depends('answer')
    def _compute_answer_char(self):
        for this in self:
            if this.answer.get('type') == 'textbox':
                this.answer_char = this.answer['value']

    def _inverse_answer_char(self):
        for this in self:
            this.answer = {
                'type': 'textbox',
                'value': this.answer_char}

    @api.depends('answer')
    def _compute_answer_float(self):
        for this in self:
            if this.answer.get('type') == 'numerical_box':
                this.answer_float = this.answer['value']

    def _inverse_answer_float(self):
        for this in self:
            this.answer = {
                'type': 'numerical_box',
                'value': this.answer_float}

    @api.depends('answer')
    def _compute_answer_datetime(self):
        for this in self:
            if this.answer.get('type') == 'datetime':
                this.answer_datetime = this.answer['value']

    def _inverse_answer_datetime(self):
        for this in self:
            this.answer = {
                'type': 'datetime',
                'value': this.answer_datetime}

    @api.depends('answer')
    def _compute_answer_selection(self):
        for this in self:
            if this.answer.get('type') == 'simple_choice':
                this.answer_selection = this.answer['value']

    def _inverse_answer_selection(self):
        for this in self:
            this.answer = {
                'type': 'simple_choice',
                'value': this.answer_selection.id}

    @api.depends('answer')
    def _compute_answer_display(self):
        for this in self:
            if this.answer:
                if this.answer['type'] not in [
                        'simple_choice', 'multiple_choice']:
                    this.answer_display = this.answer['value']
                else:
                    # we save the ids of the relational fields but we want to
                    # show their name attr on the overview list.
                    answer_ids = self.env['rma.claim.checklist.answer'].browse(
                        this.answer['value'])
                    answers_to_view = ''
                    for answer in answer_ids:
                        answers_to_view += answer.name
                        answers_to_view += ', '
                    this.answer_display = answers_to_view

    name = fields.Char(string='Question')
    type = fields.Selection(
        selection=[
            ('free_text', 'Long Text Zone'),
            ('textbox', 'Text Input'),
            ('numerical_box', 'Numerical Value'),
            ('datetime', 'Date and Time')],
        string='Type of Question')
    hint = fields.Char(
        string='Hint',
        help='A hint for the claim handler as to which the correct answer to'
             ' this question should be.')
    checklist_id = fields.Many2one('rma.claim.checklist', 'Checklist')
    answer = fields.Serialized()
    answer_text = fields.Text(
        compute='_compute_answer_text',
        inverse='_inverse_answer_text')
    answer_char = fields.Char(
        compute='_compute_answer_char',
        inverse='_inverse_answer_char')
    answer_float = fields.Float(
        compute='_compute_answer_float',
        inverse='_inverse_answer_float')
    answer_datetime = fields.Datetime(
        compute='_compute_answer_datetime',
        inverse='_inverse_answer_datetime')
    answer_selection = fields.Many2one(
        'rma.claim.checklist.answer',
        compute='_compute_answer_selection',
        inverse='_inverse_answer_selection')
    answer_display = fields.Char(
        compute='_compute_answer_display')


class RmaClaimChecklistAnswer(models.Model):
    _name = 'rma.claim.checklist.answer'

    name = fields.Char(string='Answer')
