# -*- coding: utf-8 -*-
from openerp import models, fields, api, _


class family_info(models.Model):
    _name = 'family.info'
    _description = u'家庭信息'

    relation = fields.Char(u'关系')
    name = fields.Char(u'姓名')
    unit = fields.Char(u'工作单位')
    phone = fields.Char(u'联系电话')

    ruzhi_id = fields.Many2one('oa.ruzhi', u'入职申请')
