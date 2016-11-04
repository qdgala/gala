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

class mrp_apply(models.Model):
    _name='mrp.apply'
    _inherit = ['mail.thread']
    _order = 'id desc'
    READONLY_STATES = {
        'done': [('readonly', True)],
        'quxiao': [('readonly', True)],
    }
    @api.multi
    @api.onchange('ly')
    def _amount_all(self):
        self.amount_total = self.ly.amount_total

    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id
    name = fields.Char(string=u'序号',required=True,default="/")
    order = fields.One2many('mrp.apply.order', 'apply', states=READONLY_STATES,string=u'生产计划明细')
    create_date = fields.Datetime(u'创建时间', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string=u'创建人', select=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string=u'申请人',states=READONLY_STATES, default=_default_employee_get)
    employee_sh_id = fields.Many2one('res.users', string=u'审核人', readonly=True)
    department_id = fields.Many2one('hr.department', string=u'申请部门',states=READONLY_STATES)
    ly = fields.Many2one('sale.order', string=u'来源', readonly=True)
    amount_total = fields.Float(string=u'销售总价', readonly=True, compute='_amount_all', track_visibility='always')
    state = fields.Selection([('draft', u'草稿'), ('done', u'完成'),('quxiao',u'取消')], u'状态', default='draft')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.department_id = self.employee_id.department_id

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('mrp.apply') or '/'
        res = super(mrp_apply, self).create(vals)
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
                    raise UserError(_(u'已经有成功创建生产单的明细，无法删除计划单！'))
                i.write({'state': 'quxiao'})
        return {}

class mrp_apply_order(models.Model):
    _name='mrp.apply.order'
    _order = 'id desc'
    #qxs计算实时库存方法
    @api.multi
    @api.onchange('product_id')
    def _get_pro_qty(self):
        for line in self:
            line.qty_pro = line.product_id.qty_available
    apply = fields.Many2one('mrp.apply', string=u'申请单',ondelete='cascade')
    product_id=fields.Many2one('product.product', string=u'产品', change_default=True)
    product_qty=fields.Float(string=u'数量',digits_compute=dp.get_precision('Product Unit of Measure'),required=True)
    dhsj=fields.Date(string=u'计划时间')
    wcsj=fields.Date(string=u'计划完成时间')
    state = fields.Selection([
        ('draft', u'待审批'),
        ('sent', u'通过审批'),
        ('done', u'已创建生产单'),
        ('quxiao', u'已取消')
        ], string=u'状态', readonly=True, select=True, copy=False, default='draft', track_visibility='onchange')
    mrp = fields.Many2one('mrp.production', string=u'生产单', readonly=True)
    #qxs增加实时显示的库存字段
    qty_pro = fields.Float(
        compute='_get_pro_qty', string=u'库存', store=False, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'), default=0.0)
    @api.multi
    def open_this_rec(self):
        if self.mrp:
            return {
                    'name': _('生产单'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mrp.production',
                    'view_id': self.env.ref('mrp.mrp_production_form_view').id,
                    'type': 'ir.actions.act_window',
                    'res_id': self.mrp.id,
                }

class mrp_apply_order_create(models.Model):
    _name='mrp.apply.order.create'
    @api.multi
    def add_mrp_new(self):
        ids = self._context['active_ids']
        model = self._context['active_model']
        order = self.env[model].browse(ids)
        for line in order:
            if line.state!='sent':
                raise UserError(_(u'只有通过审批状态下的生产计划明细可以创建生产单！'))
            if line.product_id.bom_ids.id==False:
                raise UserError(_(u'产品%s没有物料清单，无法创建生产单！') % (line.product_id.name))
            elif line.product_id.bom_ids.type == "phantom":
                raise UserError(_(u'产品%s没有物料清单，无法创建生产单！') % (line.product_id.name))
            result={
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'product_uom':line.product_id.uom_po_id.id or line.product_id.uom_id.id,
                'bom_id':line.product_id.bom_ids.id,
                'date_planned':line.dhsj or datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'price_unit': line.product_qty,
            }
            b = self.env['mrp.production'].create(result)
            line.write({'state': 'done','mrp':b.id})

class mrp_purchase_apply_order_create(models.Model):
    _name='mrp.purchase.apply.order.create'
    @api.multi
    def create_purchase(self):
        ids = self._context['active_ids']
        model = self._context['active_model']
        order = self.env[model].browse(ids)
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        vals = {
            'employee_id': emp.id,
            'department_id' : emp.department_id.id,
            'order':[],
        }
        for line in order:
            a = 1
            for i in vals['order']:
                if i[2]['product_id']:
                    if  i[2]['product_id'] == line.product_id.id:
                        i[2]['product_qty'] += line.product_qty
                        a = 2
            if a == 1:
                result={
                'product_id': line.product_id.id,
                'default_gys': line.product_id.default_gys.id,
                'product_qty': line.product_qty,
                'state':'draft'
                }
                vals['order'].append([0,0,result])
        b = self.env['purchase.apply'].create(vals)
        return {
                'name': _('采购申请单'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.apply',
                'view_id': self.env.ref('purchase_hb.purchase_apply_form').id,
                'type': 'ir.actions.act_window',
                'res_id': b.id,
            }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
