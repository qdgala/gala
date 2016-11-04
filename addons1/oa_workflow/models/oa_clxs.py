# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

class oa_clxs(models.Model):
    _name = 'oa.clxs'
    _description = u'办公用品采购'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    cl = fields.Many2one('oa.clxx', u'车辆名称')
    # user_id = fields.Many2one('res.users', u'申请人', default=lambda self: self.env.user)
    jsr = fields.Char(u'驾驶人',related='cl.jsr')
    code = fields.Char(u'车牌号',related='cl.code')
    wlgs = fields.Char(u'物流公司',related='cl.wlgs')
    lcs = fields.Float(u'里程数')
    yf = fields.Float(u'运费')
    sfd = fields.Char(u'始发地')
    mdd = fields.Char(u'目的地')

    @api.multi
    def create_yfbx(self):
        vals = {
            'cl':self.cl.id,
            'lcs': self.lcs,
            'heji':self.yf,
            'sfd':self.sfd,
            'mdd': self.mdd,
        }
        b = self.env['oa.yunfeibx'].create(vals)
        return {
                'name': _('运费报销'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'oa.yunfeibx',
                'view_id': self.env.ref('oa_workflow.view_oa_yunfeibx_form').id,
                'type': 'ir.actions.act_window',
                'res_id': b.id,
            }