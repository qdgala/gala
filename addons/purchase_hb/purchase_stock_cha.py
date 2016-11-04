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

class stock_search_s(models.Model):
    _name='stock.search.s'
    date_start = fields.Datetime(u'开始时间', required=True)
    date_end = fields.Datetime(u'截止时间', required=True)

    @api.multi
    def action_stock_s(self):
        cha = self.env['stock.cha']
        pro = self.env['product.product']
        a = cha.search([]) or cha
        a.unlink()
        p = pro.search([('type','=','product')])
        for i in p:
            his = self.env['stock.history']
            qm = 0.0
            qc = 0.0
            qin = 0.0
            qout = 0.0
            rm = 0.0
            rc = 0.0
            rin = 0.0
            rout = 0.0
            jm = 0.0
            jc = 0.0
            jin = 0.0
            jout = 0.0
            his_qm = his.search([('product_id','=',i.id),('date', '<=',self.date_end)])
            for qs1 in his_qm:
                qm += qs1.quantity
                rm += qs1.inventory_value
            his_qc = his.search([('product_id','=',i.id),('date', '<=',self.date_start)])
            for qs2 in his_qc:
                qc += qs2.quantity
                rc += qs2.inventory_value
            his = his.search([('product_id','=',i.id),('date', '>=',self.date_start),('date', '<=',self.date_end)])
            for qs3 in his:
                if qs3.quantity>0:
                    qin += qs3.quantity
                    rin += qs3.inventory_value
                if qs3.quantity<0:
                    qout += qs3.quantity
                    rout += qs3.inventory_value
            if qm!=0:
                jm = rm/qm
            if qc!=0:
                jc = rc/qc
            if qin!=0:
                jin = rin/qin
            if qout!=0:
                jout = rout/qout
            result={
                'product_id': i.id,
                'date_start': self.date_start,
                'date_end':self.date_end,
                'quantity_start':qc,
                'quantity_end':qm,
                'quantity_in':qin,
                'quantity_out':qout,
                'jz_start':rc,
                'jz_end':rm,
                'jz_in':rin,
                'jz_out':rout,
                'dj_start':jc,
                'dj_end':jm,
                'dj_in':jin,
                'dj_out':jout,
                'stock_ids':[[6,0,his.ids]]
            }
            cha.create(result)
        return {
                'name': _('库存数量'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'stock.cha',
                'type': 'ir.actions.act_window',
            }

class stock_cha(models.Model):
    _name='stock.cha'
    product_id = fields.Many2one('product.product', u'产品名称',readonly=True)
    date_start = fields.Datetime(u'开始时间',readonly=True)
    date_end = fields.Datetime(u'截止时间',readonly=True)
    dj_start = fields.Float(u'期初单价',readonly=True)
    quantity_start = fields.Float(u'期初数量',readonly=True)
    jz_start = fields.Float(u'期初金额',readonly=True)
    dj_end = fields.Float(u'期末单价',readonly=True)
    quantity_end = fields.Float(u'期末数量',readonly=True)
    jz_end = fields.Float(u'期末金额',readonly=True)
    dj_in = fields.Float(u'入库单价',readonly=True)
    quantity_in = fields.Float(u'入库数量',readonly=True)
    jz_in = fields.Float(u'入库金额',readonly=True)
    dj_out = fields.Float(u'出库单价',readonly=True)
    quantity_out = fields.Float(u'出库数量',readonly=True)
    jz_out = fields.Float(u'出库金额',readonly=True)
    stock_ids = fields.Many2many('stock.history', string=u'库存移动', copy=False,readonly=True)




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
