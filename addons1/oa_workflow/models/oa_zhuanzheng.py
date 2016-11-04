# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from . import oa_base as ob

_SELECT_STATE = [('sq', u'试用期人员申请'),
                 ('xzb', u'行政部'),
                 ('ldsp', u'直接上级领导审批'),
                 ('fzsp', u'副总审批'),
                 ('zjlsp', u'总经理审批'),
                 ('rszyqr', u'人事专员确认'),
                 ('ok', u'完成'),
                 ('off', u'关闭')]

_SELECT_JIEGUO = [('a', u'提前转正，正式工待遇，从月日起正式聘用'),
                  ('b', u'按期转正，正式工待遇'),
                  ('c', u'按期转正，试用期待遇'),
                  ('d', u'延长试用期个月（到年月日）'),
                  ('e', u'试用期不合格，不拟聘用')]


class oa_zhuanzheng(models.Model):
    _name = 'oa.zhuanzheng'
    _description = u'转正申请'
    _rec_name = 'emp_id'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    _get_zz_select_5 = lambda self: [(str(i), str(i)) for i in range(5 + 1)]
    _get_zz_select_10 = lambda self: [(str(i), str(i)) for i in range(10 + 1)]
    _get_zz_select_15 = lambda self: [(str(i), str(i)) for i in range(15 + 1)]
    _get_zz_select_20 = lambda self: [(str(i), str(i)) for i in range(20 + 1)]

    state = fields.Selection(_SELECT_STATE, u"状态", default='sq')
    # user_id = fields.Many2one('res.users', u'姓名', required=True)
    emp_id = fields.Many2one('hr.employee', u'姓名', required=True, default=lambda self: self.env.user.employee_ids)
    department_id = fields.Many2one('hr.department', u'部门')
    job_id = fields.Many2one('hr.job', u'职务')
    xueli = fields.Selection([('yjs', u'研究生'), ('bk', u'本科'), ('dz', u'大专'), ('zz', u'中专'), ('gz', u'高中')], u'学历')
    profession = fields.Char(u'专业')
    dg_date = fields.Date(u'到岗日期')
    shiyong_qj = fields.Char(u'试用期间')
    wage = fields.Char(u'工资标准')

    biaoxian = fields.Text(u'试用期间的主要工作表现')
    jianyi = fields.Text(u'对公司或部门有何建议')

    zhishi = fields.Selection(_get_zz_select_20, u'专业知识(20)', default=False)
    gongzuo = fields.Selection(_get_zz_select_20, u'工作能力(20)', default=False)
    xiaolv = fields.Selection(_get_zz_select_15, u'工作效率(15)', default=False)
    xietiao = fields.Selection(_get_zz_select_15, u'协调能力(15)', default=False)
    taidu = fields.Selection(_get_zz_select_15, u'工作态度(15)', default=False)
    pinde = fields.Selection(_get_zz_select_10, u'品德(10)', default=False)
    shangjinxin = fields.Selection(_get_zz_select_5, u'上进心(5)', default=False)
    zhishi_b = fields.Selection(_get_zz_select_20, u'专业知识(20)', default=False)
    gongzuo_b = fields.Selection(_get_zz_select_20, u'工作能力(20)', default=False)
    xiaolv_b = fields.Selection(_get_zz_select_15, u'工作效率(15)', default=False)
    xietiao_b = fields.Selection(_get_zz_select_15, u'协调能力(15)', default=False)
    taidu_b = fields.Selection(_get_zz_select_15, u'工作态度(15)', default=False)
    pinde_b = fields.Selection(_get_zz_select_10, u'品德(10)', default=False)
    shangjinxin_b = fields.Selection(_get_zz_select_5, u'上进心(5)', default=False)

    chidao = fields.Selection(_get_zz_select_10, u'迟到')
    zhaotui = fields.Selection(_get_zz_select_10, u'早退')
    bingjia = fields.Selection(_get_zz_select_10, u'病假')
    shijia = fields.Selection(_get_zz_select_10, u'事假')
    kuanggong = fields.Selection(_get_zz_select_10, u'旷工')

    zpr = fields.Many2one('res.users', related='emp_id.user_id', string=u'自评人')
    zpfs = fields.Float(string=u'自评分数', compute='_cmpt_zpfs', store=True)
    chr = fields.Many2one('res.users', u'初核人')
    chfs = fields.Float(u'初核分数', compute='_cmpt_chfs', store=True)

    @api.depends('zhishi', 'gongzuo', 'xiaolv', 'xietiao', 'taidu', 'pinde', 'shangjinxin')
    def _cmpt_zpfs(self):
        a = int(self.zhishi or 0) + int(self.gongzuo or 0) + int(self.xiaolv or 0) + int(self.xietiao or 0) + int(self.taidu or 0) + int(self.pinde or 0) + int(self.shangjinxin or 0)
        self.zpfs = str(a)

    @api.depends('zhishi_b', 'gongzuo_b', 'xiaolv_b', 'xietiao_b', 'taidu_b', 'pinde_b', 'shangjinxin_b')
    def _cmpt_chfs(self):
        a = int(self.zhishi_b or 0) + int(self.gongzuo_b or 0) + int(self.xiaolv_b or 0) + int(self.xietiao_b or 0) + int(self.taidu_b or 0) + int(self.pinde_b or 0) + int(self.shangjinxin_b or 0)
        self.chfs = str(a)

    jieguo = fields.Selection(_SELECT_JIEGUO, string=u'考核结果')

    @api.multi
    def get_jieguo(self, jieguo):
        if jieguo:
            return _SELECT_JIEGUO[jieguo]
        return '...'

    new_date = fields.Date(u'指定日期')
    bm_opinion = fields.Text(u'部门主管审核评估')
    opinion = fields.Text(u'意见')

    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    @api.model
    def _search_is_needaction(self, operator, operand):
        # 申请人
        user = self.env.user
        emp = user.employee_ids and user.employee_ids[0]

        ids = self.search([('state', 'in', ['sq']), ('emp_id', '=', emp.id)])  # 以申请人的身份
        ids |= self.search([('state', '=', 'ldsp'), ('emp_id', 'in', emp.child_ids.ids)])  # 以直接上级领导的身份
        if user in self.env.ref('oa_workflow.group_oa_department_fz').users:
            ids |= self.search([('state', '=', 'fzsp'), ('emp_id', 'child_of', emp.child_ids.ids)])  # 分管副总
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'zjlsp')])  # 总经理
        if user in self.env.ref('oa_workflow.group_oa_department_rszy').users:
            ids |= self.search([('state', '=', 'rszyqr')])  # 人事专员

        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'xzb')])  # 行政部

        return [('id', 'in', ids.ids)]

    _cmpt_is_needaction = ob._cmpt_is_needaction
    _needaction_domain_get = ob._needaction_domain_get
    get_spyj = ob.get_spyj

    _cmpt_spyj = ob._cmpt_spyj
    is_not_in = ob.is_not_in
    emp_is_cwb_manager = ob.emp_is_cwb_manager
    emp_is_cwb_user = ob.emp_is_cwb_user
    is_user = ob.is_user
    is_fz = ob.is_fz
    wkf_change_and_notice = ob.wkf_change_and_notice

    @api.multi
    def emp_is_xzb_user(self):
        if self.emp_id.department_id == self.env.ref("oa_workflow.data_hr_department_hd_16"):
            return True
        return False

    @api.multi
    def is_ld(self):
        if self.env.user.employee_ids[0] == self.emp_id.parent_id:
            return True
        raise UserError(_(u"申请人的领导才拥有此权限"))

    @api.multi
    def btn_ldsp(self):
        self.is_ld()
        self.sudo().chr = self.env.user

        return {
            'name': _(u"转正申请 领导审批"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'oa.zhuanzheng',
            'view_id': self.env.ref('oa_workflow.view_oa_zhuanzheng_bmld_form').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'context': {'default_opinion': u'同意'},
            'target': 'new'
        }

    @api.multi
    def write(self, vals):
        if vals.get('state') and len(vals) == 1 and not self._context.get('_sudo'):
            self.send_message(vals['state'])
        if vals.get('opinion'):
            self.is_ld()
            if self.state == 'ldsp':
                if not self.jieguo and not vals.get('jieguo'):
                    raise UserError(_(u"请录入考勤结果"))
                vals['bm_opinion'] = vals['opinion']

            vals.pop('opinion')
            return super(oa_zhuanzheng, self).sudo().write(vals)
        return super(oa_zhuanzheng, self).write(vals)

    @api.onchange('emp_id')
    def onc_emp_id(self):
        self.job_id = self.emp_id.job_id
        self.department_id = self.emp_id.department_id

    @api.multi
    def emp_manager_is_fz(self):
        # 用户的员工是副总
        if self.emp_id.parent_id.user_id in self.env.ref("oa_workflow.group_oa_department_fz").users:
            return True
        return False

    @api.multi
    def send_message(self, state):
        user_ids = []
        if state == 'xzb':
            user_ids = ob.get_xzb(self)
        elif state == 'ldsp':
            user_ids = ob.get_ld(self)
        elif state == 'fzsp':
            user_ids = ob.get_fz(self)
        elif state == 'zjlsp':
            user_ids = ob.get_zjl(self)
        elif state == 'rszyqr':
            user_ids = ob.get_rszy(self)

        if ob.check_users(user_ids): return

        vals = ({"key": u"姓名:", "value": self.emp_id.name},
                {"key": u"部门 :", "value": self.department_id.name},
                {"key": u"职务 :", "value": self.job_id.name},
                {"key": u"当前状态 :", "value": dict(_SELECT_STATE)[state]},
                {"key": u"接收人 :", "value": ",".join([i.name for i in self.env['res.users'].browse(user_ids)])})

        if True:
            ob._notice_dingding(self, user_ids, vals)
            ob._notice_webclient(self, user_ids, vals)
