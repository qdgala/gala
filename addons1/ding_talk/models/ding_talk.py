# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError
from ..DingTalk import dingtalk


class ding_talk(models.Model, dingtalk):
    _name = 'ding.talk'

    def convert_empid(self, empids):
        '''
        通过employee_ids获取对应的钉钉userid
        :param uids:id 列表
        '''
        if dingtalk._conf.IS_DEMO:
            return dingtalk._conf.demo_userid

        res = []
        for empid in self.env['hr.employee'].browse(empids):
            if not empid.dingding:
                raise UserError(empid.id + u"没有设置钉钉账号")
            res.append(empid.dingding)

            "|".join(res)

    def convert_uid(self, uids):
        '''
        通过res.users 获取对应的钉钉userid
        '''
        if dingtalk._conf.IS_DEMO:
            return dingtalk._conf.demo_userid

        res = []
        for i in uids:
            if not i.employee_ids[0].dingding:
                print i.name + u"没有设置钉钉账号"
                # raise UserError(_(i.name + u"没有设置钉钉账号"))
            res.append(i.employee_ids[0].dingding)

        return "|".join(res)
