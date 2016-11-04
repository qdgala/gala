# -*- coding: utf-8 -*-
import time
from openerp import models, fields, api, _, SUPERUSER_ID

from openerp.exceptions import UserError
from openerp.workflow import workitem
from openerp.workflow.helpers import Record, Session

wkf_item = workitem.WorkflowItem


class wkf_logs(models.Model):
    _name = 'wkf.logs'
    _description = u'工作流日志'

    res_model = fields.Char(u'源对象')
    res_id = fields.Integer(u'源id')
    act_id = fields.Many2one('workflow.activity', u'工作流阶段')
    info = fields.Text(u'记录')
    status = fields.Selection([('ok', u'通过'), ('no', u'拒绝'), ('submit', u'提交'), ('stop', u'中止')], string=u'审批结果')

    # from_state
    # to_state

    ####################################################################################
    ##  修改标准工作流中判迁移中条件的判断是否为真
    ####################################################################################



    def _trg_validate(self, cr, uid, res_type, res_id, signal):
        # :param res_type: the model name 模型的名称
        # :param res_id: the model instance id the workflow belongs to 当前模型表单的id
        # :signal: the signal name to be fired 触发工作流的按钮名称
        # :param cr: a database cursor

        result = False
        ident = (uid, res_type, res_id)

        cr.execute('select id from wkf_instance where res_id=%s and res_type=%s and state=%s',
                   (res_id, res_type, 'active'))

        for (id,) in cr.fetchall():
            cr.execute("select * from wkf_workitem where inst_id=%s", (id,))
            for witem in cr.dictfetchall():
                res2 = self._process(cr, uid, res_type, res_id, witem, ident, signal, force_running=False)
                result = result or res2  # 如果有一个为真 就返回真
        return result

    def _process(self, cr, uid, res_type, res_id, workitem, ident, signal=None, force_running=False):

        wkit = wkf_item(Session(cr, uid), Record(res_type, res_id), workitem)

        cr.execute('select * from wkf_activity where id=%s', (workitem['act_id'],))
        activity = cr.dictfetchone()
        ok = False
        if workitem['state'] == 'complete' or force_running:
            ok = wkit._split_test(activity['split_mode'], signal, [])
        return ok
