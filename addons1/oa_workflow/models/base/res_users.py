# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class res_users(models.Model):
    _inherit = 'res.users'

    def get_childs(self):
        eid = self.env.user.employee_ids.ids[0]
        res = self.env['hr.employee'].search([('id', 'child_of', eid)]).ids
        print res
        print self.env.user.name
        return res

    # x_parent_id = fields.Many2one('res.users', u'上级领导')
    # x_child_ids = fields.One2many('res.users', 'x_parent_id', u'下级员工')

    # @api.multi
    # def update_relation_from_hr(self):
    #     # 读取hr.employee表中的上下级关系
    #     pass

    # extend_id = fields.Many2one('extend.res.users', u'扩展表')
