# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'填报人申请'),
                 ('ldsp', u'上级领导审批'),
                 ('zjl', u'总经理审批'),
                 ('xzb', u'行政部确认'),
                 ('cwb', u'财务部确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]


class oa_jiangcheng(models.Model):
    _name = 'oa.jiangcheng'
    _description = u'奖惩呈批表'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    tb_date = fields.Date(u'填表日期', default=lambda self: fields.Date.today())
    tb_user_id = fields.Many2one('hr.employee', u'填表人', default=lambda self: self.env.user.employee_ids, required=True)
    tb_department_id = fields.Many2one('hr.department', u'填报部门')
    job_num = fields.Char(u'员工编号')
    # user_id = fields.Many2one('res.users', u'姓名')
    emp_id = fields.Many2one('hr.employee', u'姓名')
    rz_date = fields.Date(u'入职时间')
    department_id = fields.Many2one('hr.department', u'部门')
    job_id = fields.Many2one('hr.job', u'岗位')
    reason = fields.Text(u'主要事迹或违纪事实')
    opinion = fields.Text(u'奖惩意见')

    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    _cmpt_spyj = ob._cmpt_spyj
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', '=', 'sq'), ('tb_user_id', '=', user.employee_ids.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'ldsp'), ('tb_user_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjl')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'xzb')])  # 行政部
        if user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            ids |= self.search([('state', '=', 'cwb')])  # 财务部

        return [('id', 'in', ids.ids)]

    @api.multi
    def is_ld(self):
        if self.env.user.employee_ids == self.tb_user_id.parent_id:
            return True
        raise UserError(_(u"申请人的领导才拥有此权限"))

    @api.multi
    def is_tbr_or_create_user(self):
        if self.env.user == self.tb_user_id.user_id:
            return True
        if self.env.user == self.create_uid:
            return True
        raise UserError(_(u"只能提交自己的单据"))

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id
        self.job_id = self.emp_id.job_id

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        res = super(oa_jiangcheng, self).write(vals)
        return res

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'ldsp':
            user_ids = ob.get_ld(self)
        elif state == 'zjl':
            user_ids = ob.get_zjl(self)
        elif state == 'xzb':
            user_ids = ob.get_xzb(self)
        elif state == 'cwb':
            user_ids = ob.get_cwb(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"姓名:", "value": self.emp_id.name},
                {"key": u"部门 :", "value": self.department_id.name},
                {"key": u"岗位 :", "value": self.job_id.name},
                {"key": u"入职时间 :", "value": self.rz_date},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)

    @api.multi
    def emp_is_zjl(self):
        if self.tb_user_id.user_id in self.env.ref('oa_workflow.group_oa_department_boss').users:
            return True
        return False
