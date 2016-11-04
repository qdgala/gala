# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class oa_chuchai_line(models.Model):
    _name = 'oa.chuchai.line'
    _description = u'同行人员明细'

    emp_id = fields.Many2one('hr.employee', u'姓名')
    cc_date = fields.Datetime(u'实际出差日期')
    hc_date = fields.Datetime(u'实际回差日期')
    dates = fields.Float(u'出差天数')

    cc_id = fields.Many2one('oa.chucai', u'出差表')
