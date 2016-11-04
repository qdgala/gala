# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class extend_res_users(models.Model):
    _name = 'extend.res.users'
    _description = u'用户表扩展'

    user_id = fields.One2many('res.users', 'extend_id', u'用户')
    parent_id = fields.Many2one('res.users', u'上级领导')
    child_ids = fields.Many2many('res.users', 'extend_res_users_child_rel', string=u'下级员工')
    all_child_ids = fields.Many2many('res.users', 'extend_res_users_all_child_rel', string=u'所有下级员工')

    @api.multi
    def update_relation_from_hr(self):
        def get_all_child(extend, emp):
            for child in emp.child_ids:
                if child.id == emp.id:
                    continue
                print child, emp.child_ids

                extend.all_child_ids += child.user_id
                get_all_child(extend, child)

        # 给每一个用户关联一个 扩展表
        for user in self.env['res.users'].search([('extend_id', '=', False)]):
            user.extend_id = self.create({})

        # 读取hr.employee表中的上下级关系,并更新到本表中
        for emp in self.env['hr.employee'].search([('user_id', '!=', False)]):
            extend = emp.user_id.extend_id
            extend.parent_id = emp.parent_id.user_id
            extend.child_ids = False
            for child in emp.child_ids:
                extend.child_ids += child.user_id

            # 计算每个用户的所有下级员工
            get_all_child(extend, emp)
