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

import openerp.pooler as pooler

import time
import openerp
from openerp.osv import osv
import openerp.modules.registry
from openerp.tools.translate import _
from openerp.tools import config
from openerp import SUPERUSER_ID
import openerp.http as openerpweb


#----------------------------------------------------------
# OpenERP Web helpers
#----------------------------------------------------------


class WklDataSet(openerpweb.Controller):
    _cp_path = "/web/workflow_info"

    @openerpweb.jsonrequest
    def info(self, req, model, id, signal,status,note):
        """
        self._db = False
        self._uid = False
        self._login = False
        self._password = False
        """
        result = False 
        object = pooler.get_pool(req.session._db).get(model)
        cr = pooler.get_db(req.session._db).cursor()
        uid = req.session._uid 
        if not object:
            raise osv.except_osv(_('Error!'), 'Object %s doesn\'t exist' % str(model))
        try:
            wkf_logs_obj = pooler.get_pool(req.session._db).get("workflow.logs")
            if wkf_logs_obj._trg_validate(cr, uid, model, id, signal) :
                cr.execute('select id from wkf_instance where res_id=%s and res_type=%s and state=%s', (id, model, 'active'))
                instance_id = cr.dictfetchone()['id']
                
                cr.execute("""
                    select * from wkf_workitem where inst_id=%s""", (instance_id,))
                workitem = cr.dictfetchall()[0]
                
                result = object.signal_workflow(cr, uid, [id], signal)[id]

                context={}
                vals={'res_type':model,
                        'res_id':id,
                        'time':time.strftime('%Y-%m-%d %H:%M:%S'),
                        'uid':uid,
                        'act_id':workitem['act_id'],
                        'status':status,
                        'info':note,
                      }
                wkf_logs_obj.create(cr,SUPERUSER_ID,vals,context=context)
                cr.commit()
            else:
                result = {'error': _('错误, 当前用户没有审批权限 !'), 'title': _(u'工作流审批')}
        except Exception:
            cr.rollback()
            result = {'error': _('错误, 审批报错!'), 'title': _(u'工作流审批')}
        finally:
            cr.close()
        return result

# vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:
