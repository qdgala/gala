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

class hb_gdzc(models.Model):
    _name='hb.gdzc'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string=u'名称',required=True)
    date = fields.Datetime(u'时间', select=True)
    create_date = fields.Datetime(u'创建时间', select=True, readonly=True)
    create_uid = fields.Many2one('res.users', string=u'制单人', select=True, readonly=True)
    employee_sh_id = fields.Many2one('res.users', string=u'采购人', readonly=True)
    department_id = fields.Many2one('hr.department', string=u'部门')



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
