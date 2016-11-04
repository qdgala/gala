# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'

    @api.onchange('datas')
    def onc_datas(self):
        self.name = self.datas_fname
