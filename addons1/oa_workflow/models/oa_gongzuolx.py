# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'申请人申请'),
                 ('jsrqr', u'接收人确认'),
                 ('sqrqr', u'申请人确认'),
                 ('ok', u'归档'),
                 ('off', u'关闭')]


class oa_gongzuolx(models.Model):
    _name = 'oa.gongzuolx'
    _description = u'工作联系单'
    _inherit = ['ir.needaction_mixin']
    _rec_name = 'from_emp_id'
    _order = 'create_date desc'

    # 行政部归档

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')
    from_department_id = fields.Many2one('hr.department', u'发出部门')
    from_emp_id = fields.Many2one('hr.employee', u'发出人', required=True, default=lambda self: self.env.user.employee_ids)
    from_time = fields.Datetime(u'发出时间', default=lambda self: fields.datetime.utcnow())
    to_department_id = fields.Many2one('hr.department', u'接收部门')
    # to_user_id = fields.Many2one('res.users', u'接收人', required=True)
    to_emp_id = fields.Many2one('hr.employee', u'接收人', required=True)
    to_time = fields.Datetime(u'接收时间')

    fujian_ids = fields.Many2many('ir.attachment', string=u'附件')
    neirong = fields.Text(u'需联系的工作内容', required=True)
    chuli = fields.Text(u'接收部门反馈意见及处理方法')
    pingjia = fields.Text(u'发出部门对反馈意见及处理方法的评价')

    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')

    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj
    is_from_user = ob.is_user
    _cmpt_spyj = ob._cmpt_spyj
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        emp_id = self.env.user.employee_ids
        if emp_id:
            ids = self.search([('state', 'in', ['sq', 'sqrqr']), ('from_emp_id', '=', emp_id[0].id)])
            ids |= self.search([('state', 'in', ['jsrqr']), ('to_emp_id', '=', emp_id[0].id)])

            return [('id', 'in', ids.ids)]
        return False

    @api.multi
    def is_to_user(self):
        if self.env.user != self.to_emp_id.user_id:
            raise UserError(_(u"只能提交自己的单据"))

        return True

    @api.onchange('from_emp_id')
    def onc_from_emp_id(self):
        self.from_department_id = self.from_emp_id.department_id

    @api.onchange('to_emp_id')
    def onc_to_emp_id(self):
        self.to_department_id = self.to_emp_id.department_id

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        res = super(oa_gongzuolx, self).write(vals)
        return res

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'jsrqr':
            user_ids = [self.to_emp_id.user_id.id]
        elif state == 'sqrqr':
            user_ids = [self.from_emp_id.user_id.id]

        if ob.check_users(user_ids): return

        vals = ({"key": u"发出人:", "value": self.from_emp_id.name},
                {"key": u"发出部门 :", "value": self.from_department_id.name},
                {"key": u"接收部门 :", "value": self.to_department_id.name},
                {"key": u"联系内容 :", "value": self.neirong},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
