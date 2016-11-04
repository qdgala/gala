# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'借款人申请'),
                 ('bmsp', u'上级领导审批'),
                 ('fgfz', u'分管副总'),
                 ('cwsp', u'财务领导审批'),
                 ('zjl', u'总经理'),
                 ('cnqr', u'出纳确认'),
                 ('lkrqr', u'领款人确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]


class oa_jiekuan(models.Model):
    _name = 'oa.jiekuan'
    _description = u'借款申请'
    _rec_name = 'jiekuan_no'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    jiekuan_no = fields.Char(u'借款单编号')
    apply_date = fields.Date(u'申请日期', default=lambda self: fields.Date.today())
    # user_id = fields.Many2one('res.users', u'借款人', default=lambda self: self.env.user)
    emp_id = fields.Many2one('hr.employee', u'借款人', default=lambda self: self.env.user.employee_ids)
    department_id = fields.Many2one('hr.department', u'部门')
    job_num = fields.Char(u'工号')
    amount = fields.Float(u'借款金额')
    plan_hk_date = fields.Date(u'预计还款日期')

    xiangguan = fields.Char(u'相关项目$客户')
    is_bx = fields.Boolean(u'已报销')

    reason = fields.Text(u'借款事由')
    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    emp_is_cwb_user = ob.emp_is_cwb_user
    emp_is_cwb_manager = ob.emp_is_cwb_manager
    is_not_in = ob.is_not_in
    is_user = ob.is_user
    is_fz = ob.is_fz
    is_bmld = ob.is_bmld
    _cmpt_spyj = ob._cmpt_spyj
    emp_is_child = ob.emp_is_child
    emp_ls_is_fz = ob.emp_ls_is_fz
    wkf_change_and_notice = ob.wkf_change_and_notice
    emp_is_fz = ob.emp_is_fz

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', 'in', ['sq', 'lkrqr']), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'bmsp'), ('emp_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份
        if user in self.env.ref('oa_workflow.group_oa_department_fz').users:
            ids |= self.search([('state', '=', 'fgfz'), ('emp_id', 'child_of', emp.child_ids.ids)])  # 分管副总
        if user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            ids |= self.search([('state', '=', 'cwsp')])  # 财务部
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjl')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_cn').users:
            ids |= self.search([('state', '=', 'cnqr')])  # 出纳

        return [('id', 'in', ids.ids)]

    @api.model
    def create(self, vals):
        vals['jiekuan_no'] = self.env['ir.sequence'].next_by_code('oa.jiekuan.no')
        return super(oa_jiekuan, self).create(vals)

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])

        res = super(oa_jiekuan, self).write(vals)
        return res

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'bmsp':
            user_ids = ob.get_ld(self)
        elif state == 'fgfz':
            user_ids = ob.get_fz(self)
        elif state == 'cwsp':
            user_ids = ob.get_cwb(self)
        elif state == 'zjl':
            user_ids = ob.get_zjl(self)
        elif state == 'cnqr':
            user_ids = ob.get_cn(self)
        elif state == 'lkrqr':
            user_ids = [self.emp_id.user_id.id]

        if ob.check_users(user_ids): return

        vals = ({"key": u"借款单编号:", "value": self.jiekuan_no},
                {"key": u"借款人 :", "value": self.emp_id.name},
                {"key": u"部门 :", "value": self.department_id.name},
                {"key": u"借款金额 :", "value": self.amount},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
