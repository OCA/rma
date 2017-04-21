
import odoo
from odoo import models, fields, api
from odoo import osv
from odoo import tools
from odoo.tools.translate import _
from odoo.tools import html2plaintext
from dateutil.tz import tzoffset
from datetime import datetime
import pytz


class crm_claim_stage(models.Model):
    """ Model for claim stages. This models the main stages of a claim
        management flow. Main CRM objects (leads, opportunities, project
        issues, ...) will now use only tages, instead of state and stages.
        Stages are for example used to display the kanban view of records."""

    _name = "crm.claim.stage"
    _description = "Claim stages"
    _rec_name = 'name'
    _order = "sequence"

    
    name = fields.Char('Stage Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', help="Used to order stages. Lower is better.",default=lambda *args: 1)
    team_ids = fields.Many2many('crm.team', 'crm_team_claim_stage_rel', 'stage_id', 'team_id', string='Teams',
                        help="Link between stages and sales teams. When set, this limitate the current stage to the selected sales teams.")
    case_default = fields.Boolean('Common to All Teams',
                        help="If you check this field, this stage will be proposed by default on each sales team. It will not assign this stage to existing teams.")
    


class crm_claim(models.Model):
    """ Crm claim
    """
    _name = "crm.claim"
    _description = "Claim"
    _order = "priority,date desc"
    _inherit = ['mail.thread']



    name = fields.Char('Claim Subject', required=True)
    active = fields.Boolean('Active', default=True)
    action_next = fields.Char('Next Action')
    date_action_next = fields.Datetime('Next Action Date')
    description = fields.Text('Description')
    resolution = fields.Text('Resolution')
    create_date = fields.Datetime('Creation Date' , readonly=True)
    write_date = fields.Datetime('Update Date' , readonly=True)
    date_deadline = fields.Date('Deadline')
    date_closed = fields.Datetime('Closed', readonly=True)
    date = fields.Datetime('Claim Date', select=True)
    categ_id = fields.Many2one('crm.claim.category', 'Category')
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    type_action = fields.Selection([('correction','Corrective Action'),('prevention','Preventive Action')], 'Action Type')
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always', default= lambda self,cr,uid,context:uid) 
    user_fault = fields.Char('Trouble Responsible')
    team_id = fields.Many2one('crm.team', 'Sales Team',select=True)
    company_id =  fields.Many2one('res.company', 'Company',default= lambda self,cr,uid,context:self.pool.get('res.company')._company_default_get(cr, uid, 'crm.case', context=None))
    partner_id =  fields.Many2one('res.partner', 'Partner')
    email_cc =  fields.Text('Watchers Emails', size=252, help="These email addresses will be added to the CC field of all inbound and outbound emails for this record before being sent. Separate multiple email addresses with a comma")
    email_from =  fields.Char('Email', size=128, help="Destination email for email gateway.")
    partner_phone =  fields.Char('Phone')
    stage_id =  fields.Many2one ('crm.claim.stage', 'Stage',
            domain="['|', ('team_ids', '=', team_id), ('case_default', '=', True)]")
    cause = fields.Text('Root Cause')


    @api.multi
    def _get_default_stage_id(self,cr,uid, context=None):
        """ Gives default stage_id """
        team_id = self.pool['crm.team']._get_default_team_id( context=context)
        return self.stage_find(cr,uid,[], team_id, [('sequence', '=', '1')], context=context)


    @api.model
    def create(self, vals, context=None):
        context = dict(context or {})
        if vals.get('team_id') and not context.get('default_team_id'):
            context['default_team_id'] = vals.get('team_id')
        return super(crm_claim, self).create(vals)
   

    def stage_find(self,cases, team_id, domain=[], order='sequence', context=None):
        if isinstance(cases, (int, long)):
            cases = self.browse(cr, uid, cases, context=context)
        team_ids = []
        if team_id:
            team_ids.append(team_id)
        for claim in cases:
            if claim.team_id:
                team_ids.append(claim.team_id.id)
        search_domain = []
        if team_ids:
            search_domain += [('|')] * len(team_ids)
            for team_id in team_ids:
                search_domain.append(('team_ids', '=', team_id))
        search_domain.append(('case_default', '=', True))
        search_domain += list(domain)
        stage_ids = self.pool.get('crm.claim.stage').search(cr, uid, search_domain, order=order, context=context)
        if stage_ids:
            return stage_ids[0]
        return False

    @api.multi
    @api.onchange('partner_id')
    def partner_change(self):

        partner_email = self.partner_id.email
        partner_number=self.partner_id.phone
        return {'value':{'partner_phone':partner_number,'email_from':partner_email}}

    
    def copy(self, cr, uid, id, default=None, context=None):
        claim = self.browse(cr, uid, id, context=context)
        default = dict(default or {},
            stage_id = self._get_default_stage_id(cr, uid, context=context),
            name = _('%s (copy)') % claim.name)
        return super(crm_claim, self).copy(cr, uid, id, default, context=context)

    # -------------------------------------------------------
    # Mail gateway
    # -------------------------------------------------------

    def message_new(self, cr, uid, msg, custom_values=None, context=None):
        """Overrides mail_thread message_new that is called by the mailgateway
           through message_process."""  
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'partner_id': msg.get('author_id', False),
        }
        if msg.get('priority'):
            defaults['priority'] = msg.get('priority')
        defaults.update(custom_values)
        return super(crm_claim, self).message_new(cr, uid, msg, custom_values=defaults, context=context)

class res_partner(models.Model):
    _inherit = 'res.partner'
    def _claim_count(self, cr, uid, ids, field_name, arg, context=None):
        Claim = self.pool['crm.claim']
        return {
            partner_id: Claim.search_count(cr,uid, [('partner_id', '=', partner_id)], context=context)  
            for partner_id in ids
        }

        claim_count = fields.Function(_claim_count, string='# Claims', type='integer'),
    

class crm_claim_category(models.Model):
    _name = "crm.claim.category"
    _description = "Category of claim"
    
    name = fields.Char('Name', required=True, translate=True)
    team_id = fields.Many2one('crm.team', 'Sales Team')
  







