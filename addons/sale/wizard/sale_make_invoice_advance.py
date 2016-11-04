# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError

class SaleAdvancePaymentInv(models.TransientModel):
    _name = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.model
    def _get_advance_payment_method(self):
        if self._count() == 1:
            sale_obj = self.env['sale.order']
            order = sale_obj.browse(self._context.get('active_ids'))[0]
            if all([line.product_id.invoice_policy == 'order' for line in order.order_line]) or order.invoice_count:
                return 'all'
        return 'delivered'

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.values'].get_default('sale.config.settings', 'deposit_product_id_setting')
        return self.env['product.product'].browse(product_id)

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id().property_account_income_id

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().taxes_id
    #增加系统发票选项
    advance_payment_method = fields.Selection([
        ('delivered', 'Invoiceable lines'),
        ('all', 'Invoiceable lines (deduct down payments)'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)'),
        ('xitong', u'系统发票(百分比)')
        ], string='What do you want to invoice?', default=_get_advance_payment_method, required=True)
    product_id = fields.Many2one('product.product', string='Down Payment Product', domain=[('type', '=', 'service')],\
        default=_default_product_id)
    count = fields.Integer(default=_count, string='# of Orders')
    amount = fields.Float('Down Payment Amount', digits=dp.get_precision('Account'), help="The amount to be invoiced in advance, taxes excluded.")
    deposit_account_id = fields.Many2one("account.account", string="Income Account", domain=[('deprecated', '=', False)],\
        help="Account used for deposits", default=_default_deposit_account_id)
    deposit_taxes_id = fields.Many2many("account.tax", string="Customer Taxes", help="Taxes used for deposits", default=_default_deposit_taxes_id)

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            return {'value': {'amount': 0}}
        return {}

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            prop_id = prop and prop.id or False
            account_id = order.fiscal_position_id.map_account(prop_id)
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') % \
                    (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        #qxs增加选项开具系统发票
        elif self.advance_payment_method == 'xitong':
            amount = order.amount_untaxed * self.amount / 100
            name = _("%s : %s%%") % (so_line.product_id.name+u'付款',self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': so_line.product_id.uom_id.id,
                'product_id': so_line.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, [x.id for x in self.product_id.taxes_id])],
                'account_analytic_id': order.project_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
        })
        invoice.compute_taxes()
        return invoice

    @api.multi
    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))

        if self.advance_payment_method == 'delivered':
            sale_orders.action_invoice_create()
        elif self.advance_payment_method == 'all':
            sale_orders.action_invoice_create(final=True)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.values'].sudo().set_default('sale.config.settings', 'deposit_product_id_setting', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                if self.advance_payment_method == 'percentage':
                    amount = order.amount_untaxed * self.amount / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                #增加判断条件开系统发票
                if self.advance_payment_method == 'xitong':
                    amount = order.amount_untaxed * self.amount / 100
                    so_line = sale_line_obj.create({
                    'name': _('%s: %s') % (sale_orders.hb_type.name,time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'order_id': order.id,
                    'discount': 0.0,
                    'product_uom': sale_orders.hb_type.uom_id.id,
                    'product_id': sale_orders.hb_type.id,
                    'tax_id': [(6, 0, sale_orders.hb_type.taxes_id.ids)],
                })
                else:
                    so_line = sale_line_obj.create({
                        'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                        'price_unit': amount,
                        'product_uom_qty': 0.0,
                        'order_id': order.id,
                        'discount': 0.0,
                        'product_uom': self.product_id.uom_id.id,
                        'product_id': self.product_id.id,
                        'tax_id': [(6, 0, self.product_id.taxes_id.ids)],
                    })
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.deposit_account_id.id,
            'taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
        }
