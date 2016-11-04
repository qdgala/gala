# -*- coding: utf-8 -*-
import xlrd
import json
import base64
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class quote_pzb(models.Model):
    _name = 'quote.pzb'
    _description = u'报价单配置表'

    name = fields.Char(u'名称')
    hd_quote = fields.Many2one('hd.quote', u'报价单', required=True)
    order_ids = fields.One2many('quote.pzb.order', 'quote', u'配置表明细')

class quote_pzb_order(models.Model):
    _name = 'quote.pzb.order'
    _description = u'报价单配置表明细'
    quote = fields.Many2one('quote.pzb', u'报价单', required=True)
    excel = fields.Binary(u'文件', attachment=True, required=True)
    create_date = fields.Datetime(u'创建时间', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string=u'创建人', select=True, readonly=True)