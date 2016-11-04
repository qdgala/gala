# -*- coding: utf-8 -*-
import time
from openerp import http, SUPERUSER_ID, _
from openerp.http import request


class load_logs(http.Controller):
    @http.route('/load_logs/update', type='json', auth="user")
    def load_logs(self, res_model, res_id):
        return request.env['load.logs'].add(res_model, res_id)
