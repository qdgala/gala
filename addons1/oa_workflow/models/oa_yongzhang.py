# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'副总申请'),
                 ('xzld', u'行政部领导审批'),
                 ('zjl', u'总经理审批'),
                 ('xzzy', u'行政专员确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]
_SELECT_TYPE = [('gz', u'公章'), ('htz', u'合同章'), ('cwz', u'财务章'),
                ('fpz', u'发票章'), ('frz', u'法人章')]

_SELECT_WAY = [('gz', u'盖章'), ('wj', u'外借')]


class oa_yongzhang(models.Model):
    _name = 'oa.yongzhang'
    _description = u'用章申请'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    type = fields.Selection(_SELECT_TYPE, u'印章种类', required=True)
    way = fields.Selection(_SELECT_WAY, u'使用方式', required=True)
    department_id = fields.Many2one('hr.department', u'用章部门')
    # user_id = fields.Many2one('res.users', u'用章人', default=lambda self: self.env.user)
    emp_id = fields.Many2one('hr.employee', u'用章人', default=lambda self: self.env.user.employee_ids, required=True)
    date = fields.Date(u'用章日期')

    wenjian = fields.Text(u'需盖章文件')
    yuanyou = fields.Text(u'用章原由')

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

        ids = self.search([('state', '=', 'sq'), ('emp_id', '=', emp.id)])  # 以申请人的身份
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'xzld')])  # 行政部
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjl')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_xzzy').users:
            ids |= self.search([('state', '=', 'xzzy')])  # 行政专员

        return [('id', 'in', ids.ids)]

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        res = super(oa_yongzhang, self).write(vals)
        return res

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'xzld':
            user_ids = ob.get_xzb(self)
        elif state == 'zjl':
            user_ids = ob.get_zjl(self)
        elif state == 'xzzy':
            user_ids = ob.get_xzzy(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"用章人 :", "value": self.emp_id.name},
                {"key": u"用章部门 :", "value": self.department_id.name},
                {"key": u"印章种类 :", "value": dict(_SELECT_TYPE)[self.type]},
                {"key": u"使用方式 :", "value": dict(_SELECT_WAY)[self.way]},
                {"key": u"用章日期 :", "value": self.date},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
