# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('bmldsq', u'申请'),
                 ('fzsp', u'副总审批'),
                 ('zjlsp', u'总经理审批'),
                 ('xzbqr', u'行政部确认'),
                 ('ok', u'完成'),
                 ('cancel', u'取消')]


class oa_recruitment(models.Model):
    _name = 'oa.recruitment'
    _description = u'招聘申请'
    _rec_name = 'apply_no'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    apply_no = fields.Char(u'申请单号')
    apply_date = fields.Date(u'申请日期', default=lambda self: fields.Date.today())
    plan_date = fields.Date(u'期望到岗日期')
    # apply_user_id = fields.Many2one('res.users', u'申请人', default=lambda self: self.env.user)
    apply_emp_id = fields.Many2one('hr.employee', u'申请人', default=lambda self: self.env.user.employee_ids)
    department_id = fields.Many2one('hr.department', u'部门')
    apply_count = fields.Integer(u'申请人数', default=1)
    job_id = fields.Many2one('hr.job', u'申请招聘职位')
    salary_range = fields.Char(u'薪资定位')
    cause = fields.Text(u'申请原因')
    required = fields.Text(u'人员要求')
    # approval_opinion = fields.Text(u'审批意见')
    state = fields.Selection(_SELECT_STATE, u'状态', default='bmldsq')
    # opinion_ids = fields.One2many('wkf.opinion', 'recruitment_id', string=u'审批意见')
    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')

    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    is_not_in = ob.is_not_in
    is_tbr = ob.is_user
    _cmpt_spyj = ob._cmpt_spyj
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]
        # 申请人/副总/总经理/行政部
        ids = self.search([('state', '=', 'bmldsq'), ('apply_emp_id', '=', emp.id)])  # 以申请人的身份
        if user in self.env.ref('oa_workflow.group_oa_department_fz').users:
            ids |= self.search([('state', '=', 'fzsp'), ('apply_emp_id', 'child_of', emp.child_ids.ids)])  # 分管副总
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjlsp')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'xzbqr')])  # 行政部

        return [('id', 'in', ids.ids)]

    @api.model
    def create(self, vals):
        vals['apply_no'] = self.env['ir.sequence'].next_by_code('oa.recruitment.no')

        return super(oa_recruitment, self).create(vals)

    @api.multi
    def is_fz(self):
        if self.env.user in self.env.ref('oa_workflow.group_oa_department_fz').users:  # 是副总
            if self.apply_emp_id in self.env['hr.employee'].search([('id', 'child_of', self.env.user.employee_ids.id)]):  # 是 申请人的副总
                return True
        return False

    @api.multi
    def is_current_fz(self):
        if self.apply_emp_id.user_id == self.env.user:
            return True
        if self.apply_emp_id.department_id in self.env.user.employee_ids[0].department_id.child_ids:
            return True
        else:
            return False

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1:
            self.send_message(vals['state'])
        return super(oa_recruitment, self).write(vals)

    @api.onchange('apply_emp_id')
    def onc_apply_emp_id(self):
        self.department_id = self.apply_emp_id.department_id

    @api.multi
    def emp_is_cwb(self):
        if self.apply_emp_id.department_id == self.env.ref("oa_workflow.data_hr_department_hd_17"):
            return True
        return False

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'bmldsq':
            pass
        elif state == 'fzsp':
            user_ids = self.get_fz()
        elif state == 'zjlsp':
            user_ids = ob.get_zjl(self)
        elif state == 'xzbqr':
            user_ids = ob.get_xzb(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"申请单号 :", "value": self.apply_no},
                {"key": u"申请人:", "value": self.apply_emp_id.name},
                {"key": u"申请招聘职位 :", "value": self.job_id.name},
                {"key": u"申请人数 :", "value": self.apply_count},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)

    @api.multi
    def get_fz(self):
        par_ids = self.env['hr.employee'].search([('id', 'parent_of', self.apply_emp_id.id)])  # emp 获取申请人的所有领导
        fz_ids = self.env.ref('oa_workflow.group_oa_department_fz').users.ids  # user 获取所有副总
        res = [emp.user_id.id for emp in par_ids if emp.user_id.id in fz_ids]  # uesr
        return res
