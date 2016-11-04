# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    dingding = fields.Char(u'钉钉')
