# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class load_logs(models.Model):
    _name = 'load.logs'
    _description = u'查看表单日志'
    # 可以记录 某人第一次和最后一次查看某记录是什么时间
    # craete_uid
    # craete_date
    # update_date

    res_model = fields.Char(u'源对象')
    res_id = fields.Char(u'源ID')
    count = fields.Integer(u'访问次数')

    @api.multi
    def add(self, res_model, res_id):
        data = self.search([('create_uid', '=', self._uid), ('res_model', '=', res_model), ('res_id', '=', res_id)])
        if data:
            data[0].count += 1
            return 'old'
        else:
            self.create({
                'res_model': res_model,
                'res_id': res_id,
                'count': 1
            })
            return 'new'
