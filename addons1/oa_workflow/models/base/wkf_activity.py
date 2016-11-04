# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class wkf_activity(models.Model):
    _inherit = 'workflow.activity'

    state = fields.Char(u'state')
