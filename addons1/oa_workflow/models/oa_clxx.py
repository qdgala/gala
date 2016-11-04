# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob



class oa_clxx(models.Model):
    _name = 'oa.clxx'
    _description = u'车辆信息维护表'
    _order = 'create_date desc'

    name = fields.Char(u'车辆名称')
    code = fields.Char(u'车牌号')
    jsr = fields.Char(u'驾驶人')
    wlgs = fields.Char(u'物流公司')
