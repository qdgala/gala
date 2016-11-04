# -*- coding: utf-8 -*-
from openerp import models, fields, api, _


class work_exp(models.Model):
    _name = 'work.exp'
    _description = u'工作经验'

    qzny = fields.Char(u'起止年月')
    company = fields.Char(u'工作单位')
    job = fields.Char(u'职位')
    lizhi_yuanyin = fields.Text(u'离职原因')

    ruzhi_id = fields.Many2one('oa.ruzhi', u'入职申请')

