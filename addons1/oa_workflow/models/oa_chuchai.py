# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'出差人申请'),
                 ('ld', u'上级领导审批'),
                 ('rs', u'人事专员确认'),
                 ('sqqr', u'申请人确认'),
                 ('xzb', u'行政部'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]


class oa_chuchai(models.Model):
    _name = 'oa.chuchai'
    _description = u'出差申请单（除销售人员外）'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    department_id = fields.Many2one('hr.department', u'部门')
    # user_id = fields.Many2one('res.users', u'出差人员', default=lambda self: self.env.user)
    emp_id = fields.Many2one('hr.employee', u'出差人员', default=lambda self: self.env.user.employee_ids, required=True)
    apply_date = fields.Datetime(u'申请日期', default=lambda self: fields.datetime.utcnow())
    plan_amount = fields.Float(u'预计费用')
    luxian = fields.Text(u'出差路线')
    reason = fields.Text(u'出差事由')
    plan_dates = fields.Float(u'预计出差天数')
    real_dates = fields.Float(u'实际出差天数')
    plan_date_a = fields.Datetime(u'预计出差日期')
    plan_date_b = fields.Datetime(u'预计回差日期')
    real_date_a = fields.Datetime(u'实际出差日期')
    real_date_b = fields.Datetime(u'实际回差日期')
    line_ids = fields.One2many('oa.chuchai.line', 'cc_id', u'人员明细')

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')

    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    is_user = ob.is_user
    _cmpt_spyj = ob._cmpt_spyj
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', 'in', ['sq', 'sqqr']), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'ld'), ('emp_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份
        if user in self.env.ref('oa_workflow.group_oa_department_rszy').users:
            ids |= self.search([('state', '=', 'rs')])  # 人事专员
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'xzb')])  # 行政部

        return [('id', 'in', ids.ids)]

    @api.multi
    def is_ld(self):
        if self.env.user.employee_ids[0] == self.emp_id.parent_id:
            return True
        raise UserError(_(u"申请人的领导才拥有此权限"))

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id

    @api.multi
    def change_line_ids(self):
        if not (self.real_date_a and self.real_date_b and self.real_dates):
            raise UserError(u'请填写实际日期')

        flg = 0
        if self.state == 'sq' and self.env.user == self.emp_id.user_id:
            flg = 1
        if self.state == 'xzb' and self.env.user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            flg = 1
        if flg == 0:
            raise UserError(u'仅 发起状态下发起人 及 行政部确认状态下行政部 可执行此操作')
        for line in self.line_ids:
            line.cc_date = self.real_date_a
            line.hc_date = self.real_date_b
            line.dates = self.real_dates

    @api.multi
    def btn_xzbqr(self):
        if self.env.user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ctx = {'xzbqr': True}
            ctx.update(self._context)
            return {
                'name': u'行政部确认',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'oa.chuchai',
                'view_id': self.env.ref('oa_workflow.view_oa_chuchai_xzb_form').id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
                'context': ctx,
                # 'target': 'new'
            }
        else:
            raise UserError(_(u'仅行政部有权限进行此操作'))

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])

        if self._context.get('xzbqr'):
            ctx = dict(self._context)
            ctx.pop('xzbqr')

            return super(oa_chuchai, self).sudo().with_context(ctx).write(vals)

        return super(oa_chuchai, self).write(vals)

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'ld':
            user_ids = ob.get_ld(self)
        elif state == 'rs':
            user_ids = ob.get_rszy(self)
        elif state == 'sqqr':
            user_ids = [self.emp_id.user_id.id]
        elif state == 'xzb':
            user_ids = ob.get_xzb(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"出差人员 :", "value": self.emp_id.name},
                {"key": u"部门 :", "value": self.department_id.name},
                {"key": u"申请日期 :", "value": self.apply_date},
                {"key": u"预计费用 :", "value": self.plan_amount},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
