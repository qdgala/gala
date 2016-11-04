# -*- coding: utf-8 -*-
##############################################################################
#
#    yeahliu
#    Copyright (C) yeahliu (<talent_qiao@163.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
# from openerp.workflow import wkf_expr
import time
from openerp import SUPERUSER_ID


class wkf_logs(osv.osv):
    _name = "workflow.logs"
    _table = "wkf_logs"
    _order = "id desc"
    _columns = {
        'res_type': fields.char('资源类型', size=256, required=True),
        'res_id': fields.integer('资源ID',  required=True),
        'uid': fields.many2one('res.users', '用户',required=True),
        'act_id': fields.many2one('workflow.activity', '工作流阶段'),
        'time': fields.datetime('处理时间'),
        'info': fields.text('记录'),
        'status':fields.selection([('ok','通过'),('no','拒绝'),('submit','提交'),('stop','中止')],'状态'),        
    }
    
    def workflow_signal_info(self, cr, uid, ids, model, id, signal, status, note, context=None):

        result = False 
        object = self.pool.get(model)
        if not object:
            raise osv.except_osv(_('Error!'), 'Object %s doesn\'t exist' % str(model))
        
        if self._trg_validate(cr, uid, model, id, signal) :
            cr.execute('select id from wkf_instance where res_id=%s and res_type=%s and state=%s', (id, model, 'active'))
            instance_id = cr.dictfetchone()['id']
            
            cr.execute("""
                select * from wkf_workitem where inst_id=%s""", (instance_id,))
            workitem = cr.dictfetchall()[0]
            
            result =  object.signal_workflow(cr, uid, [id], signal)[id]

            context={}
            vals={'res_type':model,
                    'res_id':id,
                    'time':time.strftime('%Y-%m-%d %H:%M:%S'),
                    'uid':uid,
                    'act_id':workitem['act_id'],
                    'status':status,
                    'info':note,
                  }
            self.create(cr,SUPERUSER_ID,vals,context=context)
        else:
            raise osv.except_osv(_('Error!'), u'单据的工作流没有执行权限或者条件不符合')

        return result
    
    ####################################################################################
    ##  修改标准工作流中判迁移中条件的判断是否为真
    ##
    #################
    def _trg_validate(self, cr, uid, res_type, res_id, signal):
        """
        Fire a signal on a given workflow instance
    
        :param res_type: the model name 模型的名称
        :param res_id: the model instance id the workflow belongs to 当前模型表单的id
        :signal: the signal name to be fired 触发工作流的按钮名称
        :param cr: a database cursor 
        """
        result = False
        ident = (uid,res_type,res_id)
        # ids of all active workflow instances for a corresponding resource (id, model_nam)
        cr.execute('select id from wkf_instance where res_id=%s and res_type=%s and state=%s', (res_id, res_type, 'active'))
        for (id,) in cr.fetchall():
            res2 = self._validate(cr, id, ident, signal)
            result = result or res2 #如果有一个为真 就返回真
        return result
    
    
    def _validate(self, cr, inst_id, ident, signal, force_running=False):
        cr.execute("select * from wkf_workitem where inst_id=%s", (inst_id,))
        result = False
        for witem in cr.dictfetchall():
            res2 = self._process(cr, witem, ident, signal, force_running)
            result = result or res2 #如果有一个为真 就返回真
        return result
    
    
    
    def _process(self, cr, workitem, ident, signal=None, force_running=False):
        cr.execute('select * from wkf_activity where id=%s', (workitem['act_id'],))
        activity = cr.dictfetchone()
    
        if workitem['state']=='complete' or force_running:
            ok = self._split_test(cr, workitem, activity['split_mode'], ident, signal)
        return ok
    
    
    def _split_test(self, cr, workitem, split_mode, ident, signal=None):
        cr.execute('select * from wkf_transition where act_from=%s', (workitem['act_id'],))
        test = False
        transitions = []
        alltrans = cr.dictfetchall()
        if split_mode=='XOR' or split_mode=='OR':
            for transition in alltrans:
                if wkf_expr.check(cr, workitem, ident, transition,signal):
                    test = True
                    transitions.append((transition['id'], workitem['inst_id']))
                    if split_mode=='XOR':
                        break
        else:
            test = True
            for transition in alltrans:
                if not wkf_expr.check(cr, workitem, ident, transition,signal):
                    test = False
                    break
                cr.execute('select count(*) from wkf_witm_trans where trans_id=%s and inst_id=%s', (transition['id'], workitem['inst_id']))
                if not cr.fetchone()[0]:
                    transitions.append((transition['id'], workitem['inst_id']))
        if test and len(transitions):
            return True
        return False

wkf_logs()





        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

