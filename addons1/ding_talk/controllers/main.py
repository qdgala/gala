# -*- coding:utf-8 -*-
import json
import pytz
import time
import datetime
from openerp import http
from openerp.http import request
from openerp import models, fields, api
from openerp.addons.web.controllers.main import ensure_db

login_html = '''
<html lang="en">
<head>
    <title>登陆</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <script src="http://code.jquery.com/jquery-1.8.0.min.js"></script>
</head>
<body>
<div id="redirect" style="display:none;">%s</div>
账号：<input type="text" id="login_name"/><br/>
密码：<input type="password" id="login_pwd"/><br/>

<button type="button" id="btn_login">登陆</button>
<script>
    $("#btn_login").on('click', function () {
        var login_name = $("#login_name").val();
        var login_pwd = $("#login_pwd").val();
        if (login_name == '' || login_name == null || login_name == undefined) {
            alert("请输入账号")
        } else if (login_pwd == '' || login_pwd == null || login_pwd == undefined) {
            alert("请输入密码")
        } else {
            $.post("/web/login", {'login': login_name, 'password': login_pwd,'csrf_token':'%s'}, function (vals) {
                window.location.href = $("#redirect").val();
            })
        }
    })
</script>
</body>
</html>
'''
message_html = '''
<html lang="en">
<head>
    <title>消息通知</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
</head>
<body>
<p><b>发起人：</b>%s</p>
<p><b>接收人：</b>%s</p>
<p><b>消息正文：</b>%s</p>
</body>
</html>
'''
err_html = '''
<html lang="en">
<head>
    <title>消息通知</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
</head>
<body>
记录不存在
</body>
</html>
'''


class DingTalk(http.Controller):
    @http.route('/dingtalk/message_notice/<int:mid>', auth="none", methods=['GET'])
    def qj_message_notice_context(self, *args, **kw):
        ensure_db()
        uid = request.session.uid
        if uid:
            try:
                obj = request.env['message.notice'].sudo(uid).search([('id', '=', kw.get('mid'))])
                if not obj:
                    return err_html
                msg = (obj.msg).encode('utf-8')
                jsr = ",".join([i.name.encode('utf-8') for i in obj.recver_ids])
                request.env['load.logs'].sudo(uid).add('message.notice', kw['mid'])
                return message_html % (obj.user_id.name.encode('utf-8'), jsr, msg)
            except Exception, e:
                return e
        else:
            return login_html % ("http://zwg.store:1233?id=/dingtalk/message_notice/" + str(kw['mid']), request.csrf_token())
