# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError

needaction_pool = {}


class message_notice(models.Model):
    _name = 'message.notice'
    _description = u'信息公告'
    _order = 'create_date desc'
    _inherit = ['ir.needaction_mixin']

    state = fields.Selection([('draft', u'草稿'), ('ing', u'发布'), ('ok', u'完成')], copy=False, string=u"状态", default='draft')
    user_id = fields.Many2one('res.users', u'发起人', default=lambda self: self.env.user, required=True)
    recver_ids = fields.Many2many('res.users', string=u'接收人')
    msg = fields.Text(u'消息正文', required=True)

    readed_user_ids = fields.Many2many('load.logs', compute='_cmpt_readed_user', string=u'已查看人员')
    is_needaction = fields.Boolean(u'待处理', compute="_cmpt_is_needaction", search="_search_is_needaction")

    @api.multi
    def _cmpt_is_needaction(self):
        if self._uid in needaction_pool:
            for i in self:
                if i.id in needaction_pool[self._uid]:
                    i.is_needaction = True

    @api.model
    def _search_is_needaction(self, operator, operand):
        ids = self.search([('state', '=', 'ing'), ('recver_ids', 'in', self.env.user.id)])  # 接收人

        # 过滤掉已查看过的消息
        gl = self.env['load.logs'].search([('create_uid', '=', self._uid), ('res_model', '=', 'message.notice'), ('res_id', 'in', ids.ids)])
        yidu = [i.res_id for i in gl]
        ids = [i.id for i in ids if str(i.id) not in yidu]

        needaction_pool[self._uid] = ids
        return [('id', 'in', ids)]

    @api.model
    def _needaction_domain_get(self):
        return self._search_is_needaction('x', 'x')

    @api.multi
    def _cmpt_readed_user(self):
        self.readed_user_ids = self.env['load.logs'].search([('res_model', '=', self._name), ('res_id', '=', self.ids[0])])

    @api.multi
    def btn_to_ing(self):
        if self.env.user == self.user_id:
            if len(self.msg) < 5:
                raise UserError(_(u'消息内容长度过短.'))
            if len(self.recver_ids) < 1:
                raise UserError(_(u'无消息接收人.'))
            self.state = 'ing'

            body = u"<h3>消息通知：</h3>%s" % (self.msg)
            mc = self.env['mail.channel']
            a = mc.channel_get_and_minimize([user.partner_id.id for user in self.recver_ids])
            mc.browse(a['id']).message_post(body, None, 'comment', 'mail.mt_comment', False, )

            ding = self.env['ding.talk']
            ding.send_message({
                "msgtype": "oa",
                "oa": {
                    "message_url": ding._conf.public_url + "/dingtalk/message_notice/" + str(self.id),
                    "body": {
                        "content": self.msg,
                        "author": self.user_id.name
                    }
                },

                'touser': ding.convert_uid(self.recver_ids),
                'agentid': ding._conf.hd_agentid,
            })
        else:
            raise UserError(u'仅' + self.user_id.name + u'有权限发布本消息')

    @api.multi
    def btn_to_ok(self):
        if self.env.user == self.user_id:
            self.sudo().state = 'ok'
        else:
            raise UserError(u'仅' + self.user_id.name + u'有权限结束本消息')

    @api.model
    def create(self, vals):
        if self._context.get('_luck') == '1401717':
            res = super(message_notice, self).create(vals)
        else:
            ctx = dict(self._context)
            ctx['_luck'] = '1401717'
            res = super(message_notice, self).with_context(ctx).create(vals)

        return res
