# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    department_ids = fields.One2many('hr.department', 'manager_id', u'负责部门')
