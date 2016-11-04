# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

# from_string = fields.Datetime.from_string

_SELECT_STATE = [('sq', u'申请人申请'),
                 ('ldsp', u'上级领导审批'),
                 ('jlsp', u'副总(总经理)审批'),
                 ('xzbqr', u'行政部确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]


class oa_qingjia(models.Model):
    _name = 'oa.qingjia'
    _description = u'请假申请'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    # user_id = fields.Many2one('res.users', u'姓名', default=lambda self: self.env.user, required=True)
    emp_id = fields.Many2one('hr.employee', u'姓名', default=lambda self: self.env.user.employee_ids)
    department_id = fields.Many2one('hr.department', u'部门')
    apply_date = fields.Date(u'申请日期', default=lambda self: fields.Date.today())
    start_time = fields.Datetime(u'请假开始时间', default=lambda self: fields.datetime.utcnow())
    end_time = fields.Datetime(u'请假结束时间')
    total_time = fields.Float(u'请假时间合计(天)')
    reason = fields.Text(u'请假理由')

    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    emp_is_cwb_manager = ob.emp_is_cwb_manager
    is_not_in = ob.is_not_in
    _cmpt_spyj = ob._cmpt_spyj
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', 'in', ['sq']), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'ldsp'), ('emp_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份
        if user in self.env.ref('oa_workflow.group_oa_department_fz').users:
            ids |= self.search([('state', '=', 'jlsp'), ('emp_id', 'child_of', emp.child_ids.ids)])  # 分管副总
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'jlsp')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'xzbqr')])  # 行政部

        return [('id', 'in', ids.ids)]

    # @api.onchange('start_time', 'end_time')
    # def onc_total_time(self):
    #     if not self.start_time or not self.end_time:
    #         self.total_time = "/"
    #     elif self.start_time > self.end_time:
    #         self.total_time = "/"
    #     else:
    #         self.total_time = (from_string(self.end_time) - from_string(self.start_time)).seconds / (3600 * 24)

    @api.multi
    def days_than_3(self):
        # 申请时间超过3天，返回True
        if self.total_time >= 3:
            return True
        return False

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        if len(vals) == 1 and vals.get('state') and self._uid != 1:
            return super(oa_qingjia, self).with_context().sudo().write(vals)
        return super(oa_qingjia, self).write(vals)

    @api.multi
    def is_ld(self):
        if self.env.user.employee_ids[0] != self.emp_id.parent_id:
            raise UserError(_(u"申请人的领导才拥有此权限"))
        return True

    @api.multi
    def is_user(self):
        if self.env.user != self.create_uid:
            raise UserError(_(u"只能提交自己的请假单"))

        return True

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'ldsp':
            user_ids = ob.get_ld(self)
        elif state == 'jlsp':
            user_ids = list(set(ob.get_fz(self) + ob.get_zjl(self)))
        elif state == 'xzbqr':
            user_ids = ob.get_xzb(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"申请人:", "value": self.emp_id.name},
                {"key": u"开始时间 :", "value": self.start_time},
                {"key": u"结束时间 :", "value": self.end_time},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
