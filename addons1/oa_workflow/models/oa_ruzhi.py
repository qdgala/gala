# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp.tools import image
from . import oa_base as ob

_SELECT_STATE = [('sq', u'行政部填写'), ('ok', u'完成')]


class oa_ruzhi(models.Model):
    _name = 'oa.ruzhi'
    _description = u'入职信息登记表'
    _inherit = ['ir.needaction_mixin']
    _order = 'create_date desc'

    image = fields.Binary(u'图片', attachment=True)

    # 当事人申请→行政部经理审批→部门经理审批→总经理审批→人事专员确认
    # state = fields.Selection([('sq', u'当事人申请'), ('xzb', u'行政部经理审批'), ('bm', u'部门经理审批'),
    #                           ('zjl', u'总经理审批'), ('rs', u'人事专员确认'),
    #                           ('ok', u'完成'), ('off', u'关闭')], copy=False, string=u"状态")
    state = fields.Selection(_SELECT_STATE, copy=False, string=u"状态", default='sq')

    name = fields.Char(u'姓名')
    gender = fields.Selection([('male', u'男'), ('female', u'女'), ('other', u'其它')], u'性别')
    age = fields.Integer(u'年龄')
    blood = fields.Selection([('a', 'A'), ('b', 'B'), ('ab', 'AB'), ('o', 'O'), ('other', u'其它')], u'血型')
    native = fields.Char(u'籍贯')
    nation = fields.Char(u'民族')
    job = fields.Char(u'职称', required=True)
    xueli = fields.Selection([('yjs', u'研究生'), ('bk', u'本科'), ('dz', u'大专'), ('zz', u'中专'), ('gz', u'高中')], u'最高学历')
    health = fields.Char(u'健康情況')
    height = fields.Char(u'身高')
    weight = fields.Char(u'体重')
    marital = fields.Selection([('yh', u'已婚'), ('wh', u'未婚'), ('ly', u'离异')], u'婚姻情况')
    id_no = fields.Char(u'身份证')
    phone = fields.Char(u'联系电话')
    native_place = fields.Char(u'户籍所在地')
    skills = fields.Char(u'特长技能')
    addr = fields.Char(u'现居住地址')
    plan_salary = fields.Char(u'期望薪资')
    emergency_phone = fields.Char(u'紧急电话')
    zip_code = fields.Char(u'邮政编码')

    edu_exp_ids = fields.One2many('edu.exp', 'ruzhi_id', u'教育培训经历')
    family_info_ids = fields.One2many('family.info', 'ruzhi_id', u'家庭信息')
    work_exp_ids = fields.One2many('work.exp', 'ruzhi_id', u'工作经验')

    rongyu = fields.Text(u'受过何种奖励或专业训练')
    tianbiao = fields.Boolean(u'填表人申明')

    ruzhi_date = fields.Date(u'入职时间')
    department_id = fields.Many2one('hr.department', u'所属部门')
    job_id = fields.Many2one('hr.job', u'岗位/职务')
    shiyong_sj = fields.Char(u'试用时间')
    shiyong_gz = fields.Char(u'试用期工资')
    zhuanzheng_gz = fields.Char(u'转正后工资')

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

        ids = self.search([('department_id', 'child_of', emp.department_ids.ids)])  # 上级领导
        if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
            ids |= self.search([('state', '=', 'sq')])  # 行政部
        if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
            ids |= self.search([('state', '=', 'sq')])  # 总经理

        # ids = self.search([('state', '=', 'sq'), ('create_uid', '=', user.id)])  # 以申请人的身份
        # if user in self.env.ref('oa_workflow.group_oa_department_xzb').users:
        #     ids |= self.search([('state', '=', 'xzb')])  # 行政部
        # ids |= self.search([('state', '=', 'bm'), ('department_id', 'in', emp.department_ids.ids)])  # 部门经理
        # if user in self.env.ref('oa_workflow.group_oa_department_boss').users:
        #     ids |= self.search([('state', '=', 'zjl')])  # 总经理
        # if user in self.env.ref('oa_workflow.group_oa_department_rszy').users:
        #     ids |= self.search([('state', '=', 'rs')])  # 人事专员

        return [('id', 'in', ids.ids)]

    @api.multi
    def is_bmld(self):
        if self.department_id.manager_id.user_id == self.env.user:
            return True

        raise UserError(_(u"仅部门领导可审批"))
