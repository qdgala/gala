# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'离职人员申请'),
                 ('bmsp', u'上级领导审批'),
                 ('lhsp', u'仓管/行政/财务 审批'),
                 ('zjlsp', u'总经理审批'),
                 ('rssp', u'人事专员确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]


class oa_lizhi(models.Model):
    _name = 'oa.lizhi'
    _description = u'离职申请'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    # user_id = fields.Many2one('res.users', u'姓名', default=lambda self: self.env.user, required=True)
    emp_id = fields.Many2one('hr.employee', u'姓名', required=True)
    gender = fields.Selection([('male', u'男'), ('female', u'女'), ('other', u'其它')], u'性别')
    department_id = fields.Many2one('hr.department', u'部门')
    reason = fields.Text(u'离职原因')
    apply_date = fields.Date(u'申请日期')
    lizhi_date = fields.Date(u'正式离职日期')
    work_days = fields.Integer(u'实际出勤天数')
    own_manager_id = fields.Many2one('res.users', u'本部门')

    ck_manager_id = fields.Many2one('res.users', u'仓库')
    xz_id = fields.Many2one('res.users', u'行政部')
    cw_id = fields.Many2one('res.users', u'财务部')

    is_ck = fields.Boolean(u'仓管部经理确认')
    is_xz = fields.Boolean(u'行政部经理确认')
    is_cw = fields.Boolean(u'财务部经理确认')

    bm_user_id = fields.Many2one('res.users', u'部门经理')
    ck_user_id = fields.Many2one('res.users', u'仓管部经理')
    xz_user_id = fields.Many2one('res.users', u'行政部经理')
    cw_user_id = fields.Many2one('res.users', u'财务部经理')
    bm_yj = fields.Text(u'部门经理意见')
    ck_yj = fields.Text(u'仓管部经理意见')
    xz_yj = fields.Text(u'行政部经理意见')
    cw_yj = fields.Text(u'财务部经理意见')
    zjl_yj = fields.Text(u'总经理意见')

    opinion = fields.Text(u'审批意见')

    # ('cksp', u'仓管部经理审批'),('xzsp', u'行政部经理审批'), ('cwsp', u'财务部经理审批'),
    # 离职人员申请→部门经理审批→（仓管部经理审批（判断）→行政部经理审批→财务部经理审批）→总经理审批→人事专员确认
    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    is_not_in = ob.is_not_in
    _cmpt_spyj = ob._cmpt_spyj
    is_bmld = ob.is_bmld
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', 'in', ['sq']), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'bmsp'), ('emp_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份

        if user in self.env.ref('oa_workflow.group_oa_department_wlb').users:
            ids |= self.search([('state', '=', 'lhsp')])  # 仓管部
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'lhsp')])  # 行政部
        if user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            ids |= self.search([('state', '=', 'lhsp')])  # 财务部

        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjlsp')])  # 总经理

        if user in self.env.ref('oa_workflow.group_oa_department_rszy').users:
            ids |= self.search([('state', '=', 'rssp')])  # 人事

        return [('id', 'in', ids.ids)]

    @api.multi
    def btn_lhsp(self):
        if self.env.user in self.env.ref('oa_workflow.group_oa_department_wlb').users:
            pass  # 物流部
        elif self.env.user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            pass  # 行政部
        elif self.env.user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            pass  # 财务部
        else:
            raise UserError(_(u"仅 仓管/行政/财务 经理有权限审批"))
        self.sudo().opinion = u"同意"
        return {
            'name': u'审批意见',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'oa.lizhi',
            'view_id': self.env.ref('oa_workflow.view_oa_lizhi_opinion_form').id,
            'res_id': self.ids[0],
            'type': 'ir.actions.act_window',
            'context': {},
            'target': 'new'
        }

    @api.multi
    def btn_lhsp_sp(self):
        if self.env.user in self.env.ref('oa_workflow.group_oa_department_wlb').users:
            self.sudo().is_ck = True  # 物流部
        elif self.env.user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            self.sudo().is_xz = True  # 行政部
        elif self.env.user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            self.sudo().is_cw = True  # 财务部
        else:
            raise UserError(_(u"仅 仓管/行政/财务 经理有权限审批"))
        try:
            self._cr.execute('select id from wkf_instance where res_id=%s and res_type=%s and state=%s',
                             (self.id, self._name, 'active'))
            instance_id = self._cr.dictfetchone()['id']
            self._cr.execute("""select * from wkf_workitem where inst_id=%s""", (instance_id,))
            workitem = self._cr.dictfetchall()[0]
        except Exception, e:
            self._cr.rollback()
            return {'error': _(u'错误, 审批报错!\n\n' + e.message), 'title': _(u'工作流审批')}

        vals = {
            'res_model': self._name,
            'res_id': self.id,
            'info': self.opinion,
            'status': 'ok',
            'act_id': workitem['act_id'],
        }
        self.sudo().opinion = ""
        self.env['wkf.logs'].create(vals)

    @api.multi
    def is_ld(self):
        if self.env.user.employee_ids == self.emp_id.parent_id:
            return True
        raise UserError(_(u"申请人的领导才拥有此权限"))

    @api.multi
    def is_user(self):
        if self.env.user == self.create_uid:
            return True
        if self.env.user == self.emp_id.user_id:
            return True

        raise UserError(_(u"只能提交自己的单据"))

    @api.onchange('emp_id')
    def onc_create_uid(self):
        self.department_id = self.emp_id.department_id
        self.gender = self.emp_id.gender

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        res = super(oa_lizhi, self).write(vals)
        return res

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'bmsp':
            user_ids = ob.get_ld(self)
        elif state == 'lhsp':
            user_ids = list(set(ob.get_xzb(self) + ob.get_cwb(self) + ob.get_wlb(self)))
        elif state == 'zjlsp':
            user_ids = ob.get_zjl(self)
        elif state == 'rssp':
            user_ids = ob.get_rszy(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"申请人:", "value": self.emp_id.name},
                {"key": u"部门 :", "value": self.department_id.name},
                {"key": u"离职原因 :", "value": self.reason},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
