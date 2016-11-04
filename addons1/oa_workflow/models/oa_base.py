# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp import SUPERUSER_ID


@api.multi
def _cmpt_spyj(self):
    self.opinion_ids = self.env['wkf.logs'].search([('res_model', '=', self._name), ('res_id', '=', self.ids[0])])


@api.multi
def _cmpt_is_needaction(self):
    pass


@api.model
def _needaction_domain_get(self):
    return self._search_is_needaction('x', 'x')


@api.multi
def emp_is_cwb_manager(self):
    # 判断申请人是否是财务部经理
    if self.emp_id == self.env.ref("oa_workflow.data_hr_department_hd_17").manager_id:
        return True
    return False


@api.multi
def is_not_in(self, datas):
    groups_ids = self.env.user.groups_id.ids
    for data in datas:
        if self.env.ref(data).id in groups_ids:
            return False

    return True


@api.multi
def is_fz(self):
    if self.emp_id in self.env['hr.employee'].search([('id', 'child_of', self.env.user.employee_ids[0].id)]):
        return True

    raise UserError(_(u"仅分管副总可审批"))


@api.multi
def is_bmld(self):
    if self.emp_id.parent_id.user_id == self.env.user:
        return True

    raise UserError(_(u"仅上级领导可审批"))


@api.multi
def is_user(self):
    if self.env.user == self.create_uid:
        return True

    raise UserError(_(u"只能提交自己的单据"))


@api.multi
def emp_is_cwb_user(self):
    # 判断申请人是否是财务部员工
    if self.emp_id.department_id == self.env.ref("oa_workflow.data_hr_department_hd_17"):
        return True
    return False


@api.multi
def emp_ls_is_fz(self):
    # 判断员工的上级是副总
    if self.emp_id.parent_id.user_id in self.env.ref('oa_workflow.group_oa_department_fz').users:
        return True
    else:
        return False


@api.multi
def emp_is_fz(self):
    # 判断申请人是副总
    if self.emp_id.user_id in self.env.ref('oa_workflow.group_oa_department_fz').users:
        return True
    return False


@api.multi
def get_spyj(self):
    res = []
    for opinion_id in self.opinion_ids:
        res.append({
            'czr': opinion_id.create_uid.name,
            'spsj': opinion_id.create_date,
            'gzljd': opinion_id.act_id.name,
            'spyj': opinion_id.info,
            'spjg': {'ok': u'通过', 'no': u'拒绝', 'submit': u'提交', 'stop': u'中止'}[opinion_id.status]
        })

    return res


###dingding######
def check_users(user_ids):
    if not isinstance(user_ids, list): return True

    SUPERUSER_ID in user_ids and user_ids.remove(SUPERUSER_ID)
    return not user_ids


@api.multi
def get_ld(self):
    return self.emp_id.parent_id.user_id.id


@api.multi
def get_xzb(self):
    return self.env.ref('oa_workflow.group_oa_department_xzb').users.ids


@api.multi
def get_xzzy(self):
    return self.env.ref('oa_workflow.group_oa_department_xzzy').users.ids


@api.multi
def get_cwb(self):
    return self.env.ref('oa_workflow.group_oa_department_cwb').users.ids


@api.multi
def get_wlb(self):
    return self.env.ref('oa_workflow.group_oa_department_wlb').users.ids


@api.multi
def get_rszy(self):
    return self.env.ref('oa_workflow.group_oa_department_rszy').users.ids


@api.multi
def get_cn(self):
    return self.env.ref('oa_workflow.group_oa_department_cn').users.ids


@api.multi
def get_cg(self):
    return self.env.ref('oa_workflow.group_oa_department_cgzy').users.ids


@api.multi
def get_zjl(self):
    return self.env.ref('oa_workflow.group_oa_department_boss').users.ids


@api.multi
def get_rszy(self):
    return self.env.ref('oa_workflow.group_oa_department_rszy').users.ids


@api.multi
def get_fz(self):
    par_ids = self.env['hr.employee'].search([('id', 'parent_of', self.emp_id.id)])  # emp 获取申请人的所有领导
    fz_ids = self.env.ref('oa_workflow.group_oa_department_fz').users.ids  # user 获取所有副总
    res = [emp.user_id.id for emp in par_ids if emp.user_id.id in fz_ids]  # uesr
    return res


@api.multi
def emp_is_child(self):
    if self.emp_id.parent_id.user_id == self.env.user:
        return True
    else:
        return False


###dingding######
@api.multi
def wkf_change_and_notice(self, state):
    self.send_message(state)
    self.sudo().state = state


@api.multi
def uid2pid(self, uids):
    ids = self.env['res.users'].browse(uids)
    return [i.partner_id.id for i in ids]


@api.multi
def _notice_dingding(self, user_ids, vals):
    ding = self.env['ding.talk']
    ding.send_message({
        "msgtype": "oa",
        "oa": {
            "message_url": ding._conf.public_url + "/oa_workflow/%s/%s" % (self._table, str(self.id)),
            "body": {
                "title": self._description,
                "form": vals,
                "author": self.env.user.name
            }
        },

        'touser': ding.convert_empid(user_ids),
        'agentid': ding._conf.hd_agentid,
    })


@api.multi
def _notice_webclient(self, user_ids, vals):
    body = u"<h3>%s</h3>" % (self._description)

    for val in vals:
        body += u"<b>%s</b>%s<br/>" % (val['key'], val['value'])

    mc = self.env['mail.channel']
    a = mc.channel_get_and_minimize(uid2pid(self, user_ids))
    mc.browse(a['id']).message_post(body, None, 'comment', 'mail.mt_comment')
