# -*- coding: utf-8 -*-
import time
from openerp import http, SUPERUSER_ID, _
from openerp.http import request


class oa_wkf_web(http.Controller):
    @http.route('/web/workflow_info/info', type='json', auth="user")
    def exec_workflow(self, model, id, signal, note, status, log_type='', log_field=''):
        cr = request.cr
        try:
            cr.execute('select id from wkf_instance where res_id=%s and res_type=%s and state=%s',
                       (id, model, 'active'))
            instance_id = request.env.cr.dictfetchone()['id']
            cr.execute("""select * from wkf_workitem where inst_id=%s""", (instance_id,))
            workitem = request.env.cr.dictfetchall()[0]
            if request.env['wkf.logs']._trg_validate(model, id, signal):
                # result = request.env[model].browse(id).signal_workflow(signal)[id]
                vals = {
                    'res_model': model,
                    'res_id': id,
                    'info': note,
                    'status': status,
                    'act_id': workitem['act_id'],

                    # 'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                    # 'uid': request.uid,
                }
                request.env['wkf.logs'].with_context({}).create(vals)
                if log_type == "reproxy":
                    request.env[model].sudo().browse(id).write({log_field: note})
                cr.commit()
            else:
                return {'error': _(u'错误, 当前用户没有审批权限!'), 'title': _(u'工作流审批')}
        except Exception, e:
            cr.rollback()
            try:
                msg = e.message or e.name
            except:
                msg = u"异常"
            return {'error': _(u'错误, 审批报错!\n\n' + msg), 'title': _(u'工作流审批')}
        return {}
