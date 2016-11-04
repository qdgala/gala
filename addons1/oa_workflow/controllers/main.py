# -*- coding:utf-8 -*-
import json
import pytz
import time
import datetime
from openerp import http
from openerp.http import request
from openerp import models, fields, api
from openerp.addons.web.controllers.main import ensure_db

import functools


def oa(text):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            ensure_db()
            uid = request.session.uid
            if uid:
                try:
                    obj = request.env[text].sudo(uid).search([('id', '=', kw.get('mid'))])
                    if not obj:
                        return err_html
                    request.env['load.logs'].sudo(uid).add(text, kw['mid'])
                    args[0]._uid = uid
                    args[0]._obj = obj
                    return func(*args, **kw)
                except Exception, e:
                    return e
            else:
                return login_html % ("http://zwg.store:1233?id=/dingtalk/message_notice/" + str(kw['mid']), request.csrf_token())

        return wrapper

    return decorator


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
<p>请登录电脑查看详细信息</p>
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


class DingTalk_OA(http.Controller):
    @http.route('/oa_workflow/oa_recruitment/<int:mid>', auth="none", methods=['GET'])
    @oa('oa.recruitment')
    def oa_recruitment(self, *args, **kw):
        return message_html

    @http.route('/oa_workflow/oa_zhuanzheng/<int:mid>', auth="none", methods=['GET'])
    @oa('oa.zhuanzheng')
    def oa_zhuanzheng(self, *args, **kw):
        return message_html

    @http.route('/oa_workflow/oa_qingjia/<int:mid>', auth="none", methods=['GET'])
    @oa('oa.qingjia')
    def oa_qingjia(self, *args, **kw):
        return message_html
