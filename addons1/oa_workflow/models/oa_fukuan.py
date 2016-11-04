# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from ..NumToCny import to_rmb_upper
from . import oa_base as ob

_SELECT_STATE = [('sq', u'付款申请人'),
                 ('bm', u'上级领导审批'),
                 ('fz', u'分管副总'),
                 ('cw', u'财务经理'),
                 ('zjl', u'总经理'),
                 ('cn', u'出纳'),
                 ('fkr', u'付款人'),
                 ('ok', u'完成'),
                 ('off', u'关闭'),
                 ('err', u'作废'),

                 ]


class oa_fukuan(models.Model):
    _name = 'oa.fukuan'
    _description = u'付款申请'
    _inherit = ['ir.needaction_mixin']
    _rec_name = 'emp_id'
    _order = 'create_date desc'

    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')

    fukuan_no = fields.Char(u'付款编号')
    apply_date = fields.Date(u'申请日期', default=lambda self: fields.Date.today())
    zhuangtai = fields.Char(u'状态')
    job_num = fields.Char(u'申请人工号')
    # user_id = fields.Many2one('res.users', u'申请人姓名', default=lambda self: self.env.user)
    emp_id = fields.Many2one('hr.employee', u'申请人姓名', default=lambda self: self.env.user.employee_ids, required=True)
    department_id = fields.Many2one('hr.department', u'部门')
    fukuanqx = fields.Char(u'付款期限')
    fapiaoqk = fields.Char(u'发票情况')
    xuantian = fields.Boolean(u'选填合同号(订单号)')
    danhao = fields.Char(u'订单号')
    yfk_zhonge = fields.Float(u'应付款总额')
    fk_bili = fields.Char(u'付款比例')
    fk_shuoming = fields.Text(u'付款说明')

    sk_danwei = fields.Char(u'收款单位')
    fk_fangshi = fields.Char(u'付款方式')
    kaihuhang = fields.Char(u'开户行')
    zhanghao = fields.Char(u'账号')
    fk_mingxi = fields.Text(u'付款明细')
    heji = fields.Float(u'合计支付金额')
    daxie = fields.Char(u'大写金额', compute='_cmpt_daxie', store=True)

    fujian_ids = fields.Many2many('ir.attachment', string=u'附件')

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

    @api.depends('heji')
    def _cmpt_daxie(self):
        print '_cmpt_daxie'
        self.daxie = to_rmb_upper(self.heji)

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', 'in', ['sq', 'fkr']), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'bm'), ('department_id', 'in', emp.department_ids.ids)])  # 以部门经理的身份
        if user in self.env.ref('oa_workflow.group_oa_department_fz').users:
            ids |= self.search([('state', '=', 'fz'), ('emp_id', 'child_of', emp.child_ids.ids)])  # 分管副总
        if user in self.env.ref('oa_workflow.group_oa_department_cwb').users:
            ids |= self.search([('state', '=', 'cw')])  # 财务部
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjl')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_cn').users:
            ids |= self.search([('state', '=', 'cn')])  # 出纳

        return [('id', 'in', ids.ids)]

    @api.model
    def create(self, vals):
        vals['fukuan_no'] = self.env['ir.sequence'].next_by_code('oa.fukuan.no')

        return super(oa_fukuan, self).create(vals)

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.department_id = self.emp_id.department_id

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        return super(oa_fukuan, self).write(vals)

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'bm':
            user_ids = ob.get_ld(self)
        elif state == 'fz':
            user_ids = ob.get_fz(self)
        elif state == 'cw':
            user_ids = ob.get_cwb(self)
        elif state == 'zjl':
            user_ids = ob.get_zjl(self)
        elif state == 'cn':
            user_ids = ob.get_cn(self)
        elif state == 'fkr':
            user_ids = [self.emp_id.user_id.id]

        if ob.check_users(user_ids): return

        vals = ({"key": u"付款编号:", "value": self.fukuan_no},
                {"key": u"付款人 :", "value": self.emp_id.name},
                {"key": u"部门 :", "value": self.department_id.name},
                {"key": u"应付款总额 :", "value": self.yfk_zhonge},
                {"key": u"合计支付金额 :", "value": self.heji},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)

    @api.multi
    def btn_err(self):
        self.sudo().state = 'err'
