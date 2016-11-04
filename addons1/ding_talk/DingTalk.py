# -*- coding: utf-8 -*-
import logging
import json
import time
import requests
import conf

_logger = logging.getLogger(__name__)


class dingtalk:
    _conf = conf

    def get_access_tocken(self):
        '''
        调用jsp方法重新获取参数，然后通过读取文件获取参数
        目的：减少网络请求的次数
        :return: 获取最新的 access_tocken
        '''
        # if time.time() - conf._ACCESS_TOCKEN_BEGIN_TIME > 7200:
        #     url = "http://192.168.1.88:4321/demo/odoo?corpId=" + conf.CORPID
        #     _access_tocken = requests.get(url).content
        #
        #     with open(mac_per + "accesstoken.xml") as f:
        #         data = json.loads(f.read())['dingc162986a3194f9b3']
        #         assert _access_tocken == data['access_token']
        #         conf._ACCESS_TOCKEN_BEGIN_TIME = data['begin_time']
        #         conf._ACCESS_TOKEN = data['access_token']
        #
        # return conf._ACCESS_TOKEN
        url = "https://oapi.dingtalk.com/gettoken?corpid=%s&corpsecret=%s" % (conf.Corpid, conf.Corpsecret)
        content = requests.get(url, verify=False).content
        return eval(content)['access_token']

    def send_message(self, data):
        '''
        企业会话消息样例：
        {
            'touser': "UserID1|UserID2|UserID3",
            'toparty': "PartyID1|PartyID2",
            'agentid': "1",
            'msgtype': "text",
            "text": {
                "content": "张三的请假申请"
            }
        }

        消息头：
        touser	String	否	员工ID列表（消息接收者，多个接收者用’ | '分隔）。特殊情况：指定为@all，则向该企业应用的全部成员发送
        toparty	String	否	部门id列表，多个接收者用’ | '分隔。当touser为@all时忽略本参数 touser或者toparty 二者有一个必填
        agentid	String	是	企业应用id，这个值代表以哪个应用的名义发送消息

        消息体：
        msgtype	String	是	消息类型


        :param data:
            消息体类型及数据格式：
            text消息：{
                            "msgtype": "text",
                            "text": {
                                "content": "张三的请假申请"
                            }
                        }
                msgtype	    String	是	消息类型
                content	    String	是	消息内容

            image消息:{
                            "msgtype": "image",
                            "image": {
                                "media_id": "MEDIA_ID"
                            }
                        }
                media_id	String	是	图片媒体文件id，可以调用上传媒体文件接口获取。建议宽600像素 x 400像素，宽高比3：2

            voice消息：{
                            "msgtype": "voice",
                            "voice": {
                               "media_id": "MEDIA_ID"
                            }
                        }
                media_id	String	是	语音媒体文件id，可以调用上传媒体文件接口获取。2MB，播放长度不超过60s，AMR格式

            file消息：{
                            "msgtype": "file",
                            "file": {
                               "media_id": "MEDIA_ID"
                            }
                        }
                media_id	String	是	媒体文件id，可以调用上传媒体文件接口获取。10MB

            link消息：{
                        "msgtype": "link",
                        "link": {
                            "messageUrl": "http://s.dingtalk.com/market/dingtalk/error_code.php",
                            "picUrl":"@lALOACZwe2Rk",
                            "title": "测试",
                            "text": "测试"
                        }
                    }
                link.messageUrl	String	是	消息点击链接地址
                link.picUrl	    String	是	图片媒体文件id，可以调用上传媒体文件接口获取
                link.title	    String	是	消息标题
                link.text	    String	是	消息描述

            OA消息：{
                         "msgtype": "oa",
                         "oa": {
                            "message_url": "http://dingtalk.com",
                            "head": {
                                "bgcolor": "FFBBBBBB",
                                "text": "头部标题"
                            },
                            "body": {
                                "title": "正文标题",
                                "form": [
                                    {"key": "姓名:", "value": "张三"},
                                    {"key": "年龄:","value": "20"},
                                    {"key": "身高:","value": "1.8米"},
                                    {"key": "体重:","value": "130斤"},
                                    {"key": "学历:","value": "本科"},
                                    {"key": "爱好:","value": "打球、听音乐"}
                                ],
                                "rich": {
                                    "num": "15.6",
                                    "unit": "元"
                                },
                                "content": "大段文本大段文本大段文本大段文本大段文本大段文本大段文本大段文本大段文本大段文本大段文本大段文本",
                                "image": "@lADOADmaWMzazQKA",
                                "file_count": "3",
                                "author": "李四 "
                            }
                        }
                    }
                    oa.message_url	    String	是	客户端点击消息时跳转到的H5地址
                    oa.pc_message_url	String	否	PC端点击消息时跳转到的H5地址
                    oa.head	            String	是	消息头部内容
                    oa.head.bgcolor	    String	是	消息头部的背景颜色。长度限制为8个英文字符，其中前2为表示透明度，后6位表示颜色值。不要添加0x
                    oa.head.text	    String	是	消息的头部标题
                    oa.body	            Array[JSON Object]	是	消息体
                    oa.body.title	    String	否	消息体的标题
                    oa.body.form	    Array[JSON Object]	否	消息体的表单，最多显示6个，超过会被隐藏
                    oa.body.form.key	String	否	消息体的关键字
                    oa.body.form.value	String	否	消息体的关键字对应的值
                    oa.body.rich	    JSON Object	否	单行富文本信息
                    oa.body.rich.num	String	否	单行富文本信息的数目
                    oa.body.rich.unit	String	否	单行富文本信息的单位
                    oa.body.content	    String	否	消息体的内容，最多显示3行
                    oa.body.image	    String	否	消息体中的图片media_id
                    oa.body.file_count	String	否	自定义的附件数目。此数字仅供显示，钉钉不作验证
                    oa.body.author	    String	否	自定义的作者名字
        :return:成功返回True，失败报异常
        '''
        url = "https://oapi.dingtalk.com/message/send?access_token=" + self.get_access_tocken()
        r = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'}, verify=False)
        print r.content
        assert json.loads(r.content).get('errcode') == 0
        return True


if __name__ == '__main__':
    d = dingtalk()
    print d.send_message({
        'touser': conf.zwg_userid,
        'toparty': "",
        'agentid': conf.hd_agentid,
        'msgtype': "text",
        "text": {
            "content": "张三的请假申请"
        }
    })

    # manager4173
