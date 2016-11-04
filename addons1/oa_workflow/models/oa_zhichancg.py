# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'使用人申请'),
                 ('bm', u'上级领导审批'),
                 ('cw', u'财务部门领导审批'),
                 ('fz', u'副总（或总经理）'),
                 ('cg', u'采购专员确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]


class oa_zhichancg(models.Model):
    _name = 'oa.zhichancg'
    _description = u'资产采购申请'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    apply_date = fields.Date(u'申购日期', default=lambda self: fields.Date.today())
    department_id = fields.Many2one('hr.department', u'申购部门')
    # user_id = fields.Many2one('res.users', u'申请人', default=lambda self: self.env.user)
    emp_id = fields.Many2one('hr.employee', u'申请人', default=lambda self: self.env.user.employee_ids, required=True)
    plan_amount = fields.Float(u'预计费用')
    name = fields.Char(u'资产名称')
    danhao = fields.Char(u'申购单号')
    cause = fields.Text(u'申购说明')
    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    fujian_ids = fields.Many2many('ir.attachment', string=u'附件')

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    emp_is_cwb_user = ob.emp_is_cwb_user
    emp_is_cwb_manager = ob.emp_is_cwb_manager
    is_not_in = ob.is_not_in
    is_user = ob.is_user
    is_bmld = ob.is_bmld
    _cmpt_spyj = ob._cmpt_spyj
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', '=', 'sq'), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'bm'), ('emp_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份
        if user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            ids |= self.search([('state', '=', 'cw')])  # 财务部
        if user in self.env.ref('oa_workflow.group_oa_department_fz').users:
            ids |= self.search([('state', '=', 'fz'), ('emp_id', 'child_of', emp.child_ids.ids)])  # 分管副总
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'fz')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_cgzy').users:
            ids |= self.search([('state', '=', 'cg')])  # 采购专员

        return [('id', 'in', ids.ids)]

    @api.multi
    def is_fz(self):
        if self.emp_id in self.env['hr.employee'].search(
                [('id', 'child_of', self.env.user.employee_ids[0].id)]):
            return True

        raise UserError(_(u"仅分管副总可审批"))

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        res = super(oa_zhichancg, self).write(vals)
        return res

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'bm':
            user_ids = ob.get_xzb(self)
        elif state == 'cw':
            user_ids = ob.get_cwb(self)
        elif state == 'fz':
            user_ids = ob.get_fz(self)
        elif state == 'cg':
            user_ids = ob.get_cg(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"申请人 :", "value": self.emp_id.name},
                {"key": u"申购部门 :", "value": self.department_id.name},
                {"key": u"预计费用 :", "value": self.plan_amount},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)

    @api.multi
    def emp_is_manager(self):
        if self.emp_id.user_id in self.env.ref("oa_workflow.group_oa_department_manager").users:
            return True
        else:
            return False
