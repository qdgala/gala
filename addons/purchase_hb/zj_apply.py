# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning
from openerp.exceptions import AccessError
import datetime
from openerp.exceptions import UserError
AWAY_TIMER = 600 # 10 minutes
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT

class zj_apply(models.Model):
    _name='zj.apply'
    _inherit = ['mail.thread']
    _order = 'id desc'
    READONLY_STATES = {
        'done': [('readonly', True)],
        'quxiao': [('readonly', True)],
    }

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id
    name = fields.Char(string=u'序号',required=True,default="/")
    partner_id = fields.Many2one('res.partner',string=u'供应商名称')
    date = fields.Datetime(u'时间', select=True)
    sale = fields.Many2one('sale.order', string=u'销售订单',  select=True)
    purchase = fields.Many2one('purchase.order', string=u'采购订单',  select=True)
    department = fields.Many2one('hr.department', string=u'车间',  select=True)
    order = fields.One2many('zj.apply.order', 'apply', states=READONLY_STATES,string=u'生产计划明细')
    create_date = fields.Datetime(u'创建时间', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string=u'制单人', select=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string=u'检验员',states=READONLY_STATES, default=_default_employee_get)
    employee_sh_id = fields.Many2one('res.users', string=u'核准人', readonly=True)
    department_id = fields.Many2one('hr.department', string=u'申请部门',states=READONLY_STATES)
    state = fields.Selection([('draft', u'草稿'), ('done', u'完成'),('quxiao',u'取消')], u'状态', default='draft')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.department_id = self.employee_id.department_id

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('zj.apply') or '/'
        res = super(zj_apply, self).create(vals)
        return res

    @api.multi
    def button_confirm(self):
        for order in self:
            order.write({'state': 'done','employee_sh_id':self.env.uid})
        return {}

    @api.multi
    def button_confirm_fan(self):
        for order in self:
            order.write({'state': 'draft'})
        return {}

    @api.multi
    def button_quxiao(self):
        for order in self:
            order.write({'state': 'quxiao'})
        return {}

class zj_apply_order(models.Model):
    _name='zj.apply.order'
    _order = 'id desc'
    @api.onchange('product_qty','bl')
    def _onchange_qty_jy(self):
        if self.product_qty and self.bl:
            self.qty_jy = self.product_qty * self.bl/100

    @api.onchange('hg','qty_jy')
    def _onchange_hg(self):
        if self.qty_jy and self.hg:
            self.bhg = self.qty_jy - self.hg
            self.hgl = (self.hg / self.qty_jy)*100

    @api.onchange('sjth','product_qty')
    def _onchange_sjth(self):
        if self.product_qty and self.sjth:
            self.sjsh = self.product_qty - self.sjth
    apply = fields.Many2one('zj.apply', string=u'质检单',ondelete='cascade')
    partner_id = fields.Many2one('res.partner', related='apply.partner_id', string=u'供应商名称', store=True, readonly=True)
    date = fields.Datetime(related='apply.date', string=u'时间', store=True, readonly=True)
    create_uid = fields.Many2one('res.users', string=u'制单人', select=True, readonly=True)
    product_id = fields.Many2one('product.product', string=u'产品', change_default=True)
    product_qty = fields.Float(string=u'到货数量',digits_compute=dp.get_precision('Product Unit of Measure'),required=True)
    bl = fields.Float(string=u'检验比例(%)',required=True)
    qty_jy = fields.Float(string=u'检验数量',digits_compute=dp.get_precision('Product Unit of Measure'),readonly=True)
    hg = fields.Float(string=u'合格数量',digits_compute=dp.get_precision('Product Unit of Measure'),required=True)
    bhg = fields.Float(string=u'不合格数量',digits_compute=dp.get_precision('Product Unit of Measure'),readonly=True)
    blyy = fields.Many2one('zj.blyy', string=u'不良原因')
    xth=fields.Float(string=u'需退货数量',digits_compute=dp.get_precision('Product Unit of Measure'))
    sjth = fields.Float(string=u'实际退货数量',digits_compute=dp.get_precision('Product Unit of Measure'))
    sjsh = fields.Float(string=u'实际收货量',digits_compute=dp.get_precision('Product Unit of Measure'))
    hgl = fields.Float(string=u'合格率（%）',readonly=True)


class zj_blyy(models.Model):
    _name='zj.blyy'
    name = fields.Char(string=u'不良原因')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
