# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api
from odoo.osv import osv

from odoo import tools

AVAILABLE_PRIORITIES = [
   ('0', 'Low'),
   ('1', 'Normal'),
   ('2', 'High')
]


class crm_claim_report(models.Model):
    """ CRM Claim Report"""

    _name = "crm.claim.report"
    _auto = False
    _description = "CRM Claim Report"


    user_id = fields.Many2one('res.users', 'User', readonly=True)
    team_id = fields.Many2one('crm.team', 'Team', oldname='section_id', readonly=True)
    nbr =  fields.Integer('# of Claims', readonly=True)  # TDE FIXME master: rename into nbr_claims
    company_id =  fields.Many2one('res.company', 'Company', readonly=True)
    create_date =  fields.Datetime('Create Date', readonly=True, select=True)
    claim_date =  fields.Datetime('Claim Date', readonly=True)
    delay_close =  fields.Float('Delay to close', digits=(16,2),readonly=True, group_operator="avg",help="Number of Days to close the case")
    stage_id =  fields.Many2one ('crm.claim.stage', 'Stage', readonly=True,domain="[('team_ids','=',team_id)]")
    categ_id =  fields.Many2one('crm.claim.category', 'Category',readonly=True)
    partner_id =  fields.Many2one('res.partner', 'Partner', readonly=True)
    company_id =  fields.Many2one('res.company', 'Company', readonly=True)
    priority =  fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
    type_action =  fields.Selection([('correction','Corrective Action'),('prevention','Preventive Action')], 'Action Type')
    date_closed =  fields.Datetime('Close Date', readonly=True, select=True)
    date_deadline =  fields.Date('Deadline', readonly=True, select=True)
    delay_expected =  fields.Float('Overpassed Deadline',digits=(16,2),readonly=True, group_operator="avg")
    email =  fields.Integer('# Emails', size=128, readonly=True)
    subject =  fields.Char('Claim Subject', readonly=True)

    @api.model_cr
    def init(self):


        """ Display Number of cases And Team Name
        @param cr: the current row, from the database cursor,
         """
        cr = self.env.cr
        tools.drop_view_if_exists(cr, 'crm_claim_report')
        cr.execute("""
            CREATE or REPLACE VIEW crm_claim_report as (
                select
                    c.id as id,
                    c.date as claim_date,                    
                    c.date_closed as date_closed,
                    c.date_deadline as date_deadline,
                    c.user_id,
                    c.stage_id,
                    c.team_id,
                    c.partner_id,
                    c.company_id,
                    c.categ_id,
                    c.name as subject,
                    count(*) as nbr,
                    c.priority as priority,
                    c.type_action as type_action,
                    c.create_date as create_date,
                    avg(extract('epoch' from (c.date_closed-c.create_date)))/(3600*24) as  delay_close,
                    (SELECT count(id) FROM mail_message WHERE model='crm.claim' AND res_id=c.id) AS email,
                    extract('epoch' from (c.date_deadline - c.date_closed))/(3600*24) as  delay_expected
                from crm_claim c
                
                group by c.date,
                        c.user_id,
                        c.team_id,
                        c.stage_id,
                        c.categ_id,
                        c.partner_id,
                        c.company_id,
                        c.create_date,
                        c.priority,
                        c.type_action,
                        c.date_deadline,
                        c.date_closed,
                        c.id
            )""")
