# -*- coding: utf-8 -*-
from openerp import models, fields, api, _


class edu_exp(models.Model):
    _name = 'edu.exp'
    _description = u'教育培训经历'

    qzny=fields.Char(u'起止年月')
    jigou = fields.Char(u'教育培训机构')
    zhuanye = fields.Char(u'专业')
    zhengshu = fields.Char(u'证书')

    ruzhi_id = fields.Many2one('oa.ruzhi', u'入职申请')
