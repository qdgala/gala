# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class product_template_qxs(models.Model):
    _inherit = 'product.template'

    @api.multi
    @api.depends('ckjc','yfjc','gczj','sbzj','jgf','standard_price')
    def _ysdj_count(self):
        for product in self:
            product.ysdj = product.standard_price*(1+product.ckjc/100+product.yfjc/100)+product.gczj+product.sbzj+product.jgf

    ckjc = fields.Float(u'仓库加成(%)')
    yfjc = fields.Float(u'运费加成(%)')
    gczj = fields.Float(u'工厂折旧')
    sbzj = fields.Float(u'设备折旧')
    jgf = fields.Float(u'加工费')
    ysdj = fields.Float(compute='_ysdj_count', string=u'原始单价')

    @api.multi
    def ckjc_update(self):
        ckjc_ids = self.env['product.template'].search([('jiagong_fs', '=', self.jiagong_fs)])
        ckjc_ids.write({'ckjc': self.ckjc})

    @api.multi
    def yfjc_update(self):
        yfjc_ids = self.env['product.template'].search([('jiagong_fs', '=', self.jiagong_fs)])
        yfjc_ids.write({'yfjc': self.yfjc})