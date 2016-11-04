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

class purchase_apply(models.Model):
    _name='purchase.apply'
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
    order = fields.One2many('purchase.apply.order', 'apply', states=READONLY_STATES,string=u'采购申请明细')
    create_date = fields.Datetime(u'创建时间', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string=u'创建人', select=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string=u'申请人',states=READONLY_STATES, default=_default_employee_get)
    employee_sh_id = fields.Many2one('res.users', string=u'审核人', readonly=True)
    department_id = fields.Many2one('hr.department', string=u'申请部门',states=READONLY_STATES)
    ly = fields.Many2one('sale.order', string=u'来源', readonly=True)
    state = fields.Selection([('draft', u'草稿'), ('done', u'完成'),('quxiao',u'取消')], u'状态', default='draft')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.department_id = self.employee_id.department_id

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.apply') or '/'
        res = super(purchase_apply, self).create(vals)
        return res

    @api.multi
    def button_confirm(self):
        for order in self:
            order.write({'state': 'done','employee_sh_id':self.env.uid})
            for i in order.order:
                if i.state != 'done':
                    i.write({'state': 'sent'})
        return {}

    @api.multi
    def button_confirm_fan(self):
        for order in self:
            order.write({'state': 'draft'})
            for i in order.order:
                if i.state != 'done':
                    i.write({'state': 'draft'})
        return {}

    @api.multi
    def button_quxiao(self):
        for order in self:
            order.write({'state': 'quxiao'})
            for i in order.order:
                if i.state=='done':
                    raise UserError(_(u's已经有成功创建采购单的明细，无法删除申请单！'))
                i.write({'state': 'quxiao'})
        return {}

class purchase_apply_order(models.Model):
    _name='purchase.apply.order'
    _order = 'id desc'

    @api.depends('product_id','product_id.default_gys')
    def _onchange_product_id(self):
        for i in self:
            if i.product_id.default_gys:
                i.default_gys = i.product_id.default_gys.id

    apply = fields.Many2one('purchase.apply', string=u'申请单',ondelete='cascade')
    apply_ly = fields.Many2one('sale.order', related='apply.ly', string=u'销售订单', store=False, readonly=True)
    product_id=fields.Many2one('product.product', string=u'产品', domain=[('purchase_ok','=',True)], change_default=True)
    product_qty=fields.Float(string=u'数量',digits_compute=dp.get_precision('Product Unit of Measure'),required=True)
    dhsj=fields.Date(string=u'到货时间')
    state = fields.Selection([
        ('draft', u'待审批'),
        ('sent', u'通过审批'),
        ('done', u'已创建采购单'),
        ('quxiao', u'已取消')
        ], string=u'状态', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')
    purchase = fields.Many2one('purchase.order', string=u'采购单', readonly=True)
    default_gys = fields.Many2one('res.partner', u'默认供应商', compute='_onchange_product_id', store=True,domain=[('supplier', '=', True)], ondelete='cascade')
    @api.multi
    def open_this_rec(self):
        if self.purchase:
            return {
                    'name': _('采购单'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'purchase.order',
                    'view_id': self.env.ref('purchase.purchase_order_form').id,
                    'type': 'ir.actions.act_window',
                    'res_id': self.purchase.id,
                }

class purchase_apply_order_create(models.Model):
    _name='purchase.apply.order.create'
    @api.multi
    def add_purchase_new(self):
        ids = self._context['active_ids']
        model = self._context['active_model']
        order = self.env[model].browse(ids)
        vals = {
            'date_order':datetime.datetime.now()-datetime.timedelta(hours=8),
            'partner_id': 1,
            'order_line':[],
        }
        for line in order:
            if line.state!='sent':
                raise UserError(_(u'只有通过审批状态下的采购申请明细可以创建采购单！'))
            result={
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom':line.product_id.uom_po_id.id or line.product_id.uom_id.id,
                'date_planned':line.dhsj or datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'price_unit': line.product_qty,
                'name':line.product_id.name
            }
            vals['order_line'].append([0,0,result])
        b = self.env['purchase.order'].create(vals)
        order.write({'state': 'done','purchase':b.id})
        return {
                'name': _('采购单'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'view_id': self.env.ref('purchase.purchase_order_form').id,
                'type': 'ir.actions.act_window',
                'res_id': b.id,
            }




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
