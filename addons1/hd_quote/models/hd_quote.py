# -*- coding: utf-8 -*-
import xlrd
import json
import base64
from openerp import models, fields, api, _
from openerp.exceptions import UserError


class hd_quote(models.Model):
    _name = 'hd.quote'
    _description = u'华丹 报价单'

    name = fields.Char(u'名称')
    xshth = fields.Char(u'销售合同号')
    order_ids = fields.One2many('sale.order', 'hd_quote_id', u'明细单')
    partner_id = fields.Many2one('res.partner', u'客户', required=True, domain=[('company_type', '=', 'company')])
    excel = fields.Binary(u'文件', attachment=True, required=True)
    jiacheng = fields.Integer(u'销售加成', default=100)

    report_content = fields.Text(u'报表打印源数据')

    # 打印报表时，首先从excel中读取数据并以json的格式保存入该字段
    # 显示字段时，从该字段中取值

    @api.model
    def create(self, vals):
        res = super(hd_quote, self).create(vals)
        res.btn_import_data()
        res._tc_yuanshi_dj()
        res.compute_zk()
        return res

    @api.onchange('jiacheng')
    def onc_jiacheng(self):
        for i in self.order_ids:
            i.jiacheng = self.jiacheng

    @api.multi
    def btn_import_data(self):
        if not self.excel:
            raise UserError(_(u'请上传文件.'))

        import sys
        reload(sys)
        sys.setdefaultencoding(u'utf8')

        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.excel))
        except:
            raise UserError(_(u'文件格式不匹配或文件内容错误.'))

        # 获取页签字典
        sheet_dict = {}
        for i in wb.sheets():
            sheet_dict[i.name[:3]] = i.number

        # 从 系统分类 页签中读取有效的系统
        sheet = wb.sheet_by_index(1)
        if sheet.ncols <= 3:
            raise UserError(_(u'系统分类页签异常'))

        xtbm_dict = {
            '1000000000': u'???????',
            '1000010000': u'鸡笼',
            '1000020000': u'鸡粪',
            '1000030000': u'饲喂',
            '1000040000': u'饮水',
            '1000050000': u'仓储',
            '1000060000': u'上料',
            '1000070000': u'通风',
            '1000080000': u'控制',
            '1000090000': u'尾部鸡粪输送',
            '1000100000': u'安装工具',
            '1000110000': u'钢格板',
            # '1000120000': u'电器',
            '1000120000': u'照明',
            '1000140000': u'饲料集中运输',
            '1000150000': u'鸡粪集中运输',
            '2000000000': u'???????',
            '2000010000': u'',
            '2000020000': u'',
            '2000030000': u'',
            '2000040000': u'',
            '2000050000': u'',
            '2000060000': u'',
            '2000070000': u'',
            '2000080000': u'',
            '2000090000': u'',
            '2000100000': u'',
            '2000110000': u'',
            '2000120000': u'',
            '2000130000': u'',
            '2000140000': u'',
            '2000150000': u'',
            '2000160000': u'',

        }

        for i in range(2, sheet.nrows):
            if sheet.cell(i, 3).value == 'q':
                code = str(int(sheet.cell(i, 0).value))
                if code =='1000000000' : continue
                vals = {
                    'partner_id': self.partner_id.id,
                    'order_line': [],
                    'hd_quote_id': self.id,
                    'xshth': self.xshth,
                    'hb_type': self.env['product.product'].search([('default_code', '=', code)]).id,
                    'jiacheng': self.jiacheng
                }

                # 处理明细表
                st = wb.sheet_by_name(xtbm_dict[code])
                try:
                    e_list = [v.value and str(int(v.value)) for v in st.col_slice(1, 6, st.nrows) if v.value != ""]
                except Exception, e:
                    raise UserError(u'请检查报价单中合计的位置（编码列下不能有其它字段）')

                product_dcit = {}
                if e_list:
                    self._cr.execute('select id,default_code from product_product where default_code in %s', [tuple(e_list)])
                    for t in self._cr.fetchall():
                        product_dcit[t[1]] = t[0]
                print product_dcit

                # 将数字转为字符串格式
                def _get_str(v):
                    if not isinstance(v, float):
                        return v
                    tmp = int(v)
                    if tmp == v:
                        return str(int(v))
                    else:
                        return str(v)

                old_r = []
                old_xh = ''
                for i in range(6, st.nrows):
                    r = st.row_values(i)
                    xh = _get_str(r[0])
                    if xh[:-2] == old_xh or old_r == []:
                        print old_xh
                    else:
                        vals['order_line'].append([0, 0, {
                            'product_id': product_dcit[str(int(old_r[1]))],
                            'product_uom_qty': old_r[3],
                            'guige': old_r[10],
                            'jiagong_fs': {
                                u'国内': 'gn',
                                u'国内采购': 'gn',
                                u'国外': 'gw',
                                u'国外采购': 'gw',
                                u'自制': 'zz',
                                u'采购直发': 'cgzf',
                                u'国内直发': 'gnzf',
                                u'管箍厂家配': None,
                                u'': False}[old_r[13]]
                        }])
                    old_r = r
                    old_xh = xh
                if old_r and old_xh and old_r[1]:
                    vals['order_line'].append([0, 0, {
                        'product_id': product_dcit[str(int(old_r[1]))],
                        'product_uom_qty': old_r[3],
                        'guige': old_r[10],
                        'jiagong_fs':{
                                u'国内': 'gn',
                                u'国内采购': 'gn',
                                u'国外': 'gw',
                                u'国外采购': 'gw',
                                u'自制': 'zz',
								u'采购直发': 'cgzf',
                                u'国内直发': 'gnzf',
                                u'': False}[old_r[13]]
                    }])

                print self.order_ids.create(vals)
        sheet = wb.sheet_by_index(0)
        self.name = sheet.cell(6, 4).value + '-' + sheet.cell(7, 4).value

    @api.multi
    def _tc_yuanshi_dj(self):
        for order in self.order_ids:
            for line in order.order_line:
                line.yuanshi_dj = line.product_id.ysdj

    @api.multi
    def compute_zk(self):
        '''
            两个参数，财务加成、销售加成，其中财务加成分为国内、国外、自制三个比例，销售加成是一个统一的比例，财务加成可以在报价外面设置，销售加成在销售报价中填写
                财务加成    全局参数
                    国内、国外、自制

                销售加成
                    默认为100， 修改后的值覆盖明细表中的值
        '''
        self._tc_yuanshi_dj()
        jc = {
            'gn': int(self.env["ir.config_parameter"].get_param("caiwu.jiacheng.gn")),
            'gw': int(self.env["ir.config_parameter"].get_param("caiwu.jiacheng.gw")),
            'zz': int(self.env["ir.config_parameter"].get_param("caiwu.jiacheng.zz")),
            'cgzf': int(self.env["ir.config_parameter"].get_param("caiwu.jiacheng.cgzf")),
            'gnzf': int(self.env["ir.config_parameter"].get_param("caiwu.jiacheng.gnzf")),
            'gnfy': int(self.env["ir.config_parameter"].get_param("caiwu.fy.gn")),
            'gwfy': int(self.env["ir.config_parameter"].get_param("caiwu.fy.gw")),
            'zzfy': int(self.env["ir.config_parameter"].get_param("caiwu.fy.zz")),
            'cgzffy': int(self.env["ir.config_parameter"].get_param("caiwu.fy.cgzf")),
            'gnzffy': int(self.env["ir.config_parameter"].get_param("caiwu.fy.gnzf")),
        }

        # 计算各明细行中的折扣
        for order in self.order_ids:
            xs = order.jiacheng
            for line in order.order_line:
                if line.jiagong_fs:
                    vals = {}
                    vals['caiwu_danjia'] = line.yuanshi_dj * jc[line.jiagong_fs]*jc[line.jiagong_fs+'fy'] / 10000.0
                    vals['caiwu_heji'] = vals['caiwu_danjia'] * line.product_uom_qty
                    vals['price_unit'] = vals['caiwu_danjia'] * xs / 100.0
                    vals['price_subtotal'] = vals['price_unit'] * line.product_uom_qty
                    print vals
                    line.write(vals)

    # 读取报价单第一页
    @api.multi
    def btn_read_header(self):
        import sys
        reload(sys)
        sys.setdefaultencoding(u'utf8')

        # 将首列信息转为字典
        def read_first_col(data):
            # 目录/明细/汇总表

            vl = [i for i in data]
            kl = [i for i in range(len(vl))]
            fr_dict = dict(zip(kl, vl))

            for i in fr_dict.copy():
                if fr_dict[i] == '': del fr_dict[i]

            fr_f_dict = dict(zip(vl, kl))

            a = fr_f_dict.get(u'1.1.')
            b = fr_f_dict.get(u'序')
            mx_dict = {}
            for i in fr_dict:
                if i >= a and i < b:
                    mx_dict[fr_dict[i]] = i

            return fr_dict, fr_f_dict, mx_dict

        # 读取目录页
        def read_mulu():
            index = fr_f_dict[u'目录']

            result = {}
            result_f = {}
            while True:
                index += 1
                row = [i for i in sheet.row_values(index) if i != '']
                if row == []: break
                result[row[0]] = row[1]
                result_f[row[1]] = row[0]

            return result, result_f

        # 读取系统描述
        def read_xtms():
            index = fr_mx_r_dict[u'1.1.']

            result = {}
            while True:
                index += 1
                row = [i for i in sheet.row_values(index) if i != '']
                if row == []: break
                result[row[0]] = row[1]
            return result

        # 读取系统列表
        def read_xtlb():
            index = fr_mx_r_dict[1.2]
            result = {}
            while True:
                index += 1
                row = [i for i in sheet.row_values(index) if i != '']
                if row == []: break
                result[index] = row[0]
            return result

        def read_xtflmx(xt, index):
            if xt == u'1000010000':
                value = {
                    'jg': sheet.cell(index, 7).value,
                    'mgjldyjs': sheet.cell(index + 2, 3).value,
                    'jlcg': sheet.cell(index + 2, 7).value,
                    'lg': sheet.cell(index + 3, 3).value,
                    'jlls': sheet.cell(index + 3, 7).value,
                    'lk': sheet.cell(index + 4, 3).value,
                    'mtxjlsl': sheet.cell(index + 4, 7).value,
                    'ls': sheet.cell(index + 5, 3).value,
                    'jlcd': sheet.cell(index + 5, 7).value,
                    'jwmj': sheet.cell(index + 6, 3).value,
                    'jlzs': sheet.cell(index + 6, 7).value,
                    'ddyjzl': sheet.cell(index + 7, 7).value,

                    'jscd': sheet.cell(index + 8, 3).value,
                    'jskd': sheet.cell(index + 9, 3).value,
                    'jscqgd': sheet.cell(index + 10, 3).value,
                    'jsdg': sheet.cell(index + 11, 3).value,

                    'mlmcddjsl': sheet.cell(index + 12, 5).value,
                    'dddjzs': sheet.cell(index + 13, 5).value,
                    'djgl': sheet.cell(index + 14, 5).value,
                    'xtzgl': sheet.cell(index + 15, 5).value,
                    'dqyd': sheet.cell(index + 16, 2).value,
                }
            elif xt in [u'1000020000', u'1000030000', u'1000040000']:
                value = {
                    'jg': sheet.cell(index, 7).value,
                }
            elif xt == u'1000050000':
                value = {
                    'jg': sheet.cell(index, 7).value,
                    'ltxh': sheet.cell(index + 1, 2).value,
                    'ltsl': sheet.cell(index + 1, 4).value,
                    'bz': sheet.cell(index + 2, 5).value,
                    'ltdw': sheet.cell(index + 2, 2).value,
                    'zdw': sheet.cell(index + 2, 4).value,
                    'jsdwyts': sheet.cell(index + 3, 3).value,

                    'xh1': sheet.cell(index + 2, 7).value,
                    'xh2': sheet.cell(index + 3, 7).value,
                    'xh3': sheet.cell(index + 4, 7).value,
                }
            elif xt == u'1000060000':
                value = {
                    'jg': sheet.cell(index, 7).value,
                    'ltsl': [sheet.cell(index + 6, 3).value, sheet.cell(index + 6, 5).value, sheet.cell(index + 6, 6).value],
                    'jlbzxs': [sheet.cell(index + 7, 3).value, sheet.cell(index + 7, 5).value, sheet.cell(index + 7, 6).value],
                    'clksl': [sheet.cell(index + 8, 3).value, sheet.cell(index + 8, 5).value, sheet.cell(index + 8, 6).value],
                    '90djllg': [sheet.cell(index + 9, 3).value, sheet.cell(index + 9, 5).value, sheet.cell(index + 9, 6).value],
                    'ltljsdjl': [sheet.cell(index + 10, 3).value, sheet.cell(index + 10, 5).value, sheet.cell(index + 10, 6).value],
                    's90lgcd': [sheet.cell(index + 11, 3).value, sheet.cell(index + 11, 5).value, sheet.cell(index + 11, 6).value],
                    'jlcd': [sheet.cell(index + 12, 3).value, sheet.cell(index + 12, 5).value, sheet.cell(index + 12, 6).value],
                    'jldjsl': [sheet.cell(index + 13, 3).value, sheet.cell(index + 13, 5).value, sheet.cell(index + 13, 6).value],
                    'jldjgl': [sheet.cell(index + 14, 3).value, sheet.cell(index + 14, 5).value, sheet.cell(index + 14, 6).value],
                    'lsdjsl': [sheet.cell(index + 15, 3).value, sheet.cell(index + 15, 5).value, sheet.cell(index + 15, 6).value],
                    'szdjgl': [sheet.cell(index + 16, 3).value, sheet.cell(index + 16, 5).value, sheet.cell(index + 16, 6).value],
                    'xtzgl': [sheet.cell(index + 17, 3).value, sheet.cell(index + 17, 5).value, sheet.cell(index + 17, 6).value],
                }


            elif xt == u'1000070000':
                value = {
                    sheet.cell(index, 6).value: sheet.cell(index, 7).value,
                    sheet.cell(index + 7, 2).value: sheet.cell(index + 7, 4).value,
                    sheet.cell(index + 7, 5).value: sheet.cell(index + 7, 7).value,
                    sheet.cell(index + 8, 2).value: sheet.cell(index + 8, 4).value,
                    sheet.cell(index + 8, 5).value: sheet.cell(index + 8, 7).value,
                    sheet.cell(index + 9, 2).value: sheet.cell(index + 9, 4).value,
                    sheet.cell(index + 9, 5).value: sheet.cell(index + 9, 7).value,
                    sheet.cell(index + 10, 2).value: sheet.cell(index + 10, 4).value,
                    sheet.cell(index + 11, 2).value: sheet.cell(index + 11, 3).value,
                }
            elif xt == u'1000080000':
                value = {
                    'jg': sheet.cell(index, 7).value,
                }
            elif xt == u'1000090000':
                value = {}
            elif xt == u'xxxxxxxxxxxxx':
                value = {}
            else:
                value = {

                }

            return value

        if not self.excel:
            raise UserError(_(u'请上传文件.'))

        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.excel))
        except:
            raise UserError(_(u'文件格式不匹配或文件内容错误.'))
        sheet = wb.sheet_by_index(0)

        res = {}
        # 读取首页标题
        res['khmc'] = sheet.cell(6, 4).value
        res['hwmc'] = sheet.cell(7, 4).value
        res['bjdh'] = sheet.cell(28, 4).value
        res['bjrq'] = sheet.cell(29, 4).value
        res['bjyxq'] = sheet.cell(30, 4).value
        res['bjr'] = sheet.cell(31, 4).value
        res['htbh'] = sheet.cell(32, 4).value

        # 读取使用的系统分类

        def get_current_xt():
            sheet2 = wb.sheet_by_index(1)
            data = {}
            data_list = {}
            for i in range(2, sheet2.nrows):
                if sheet2.cell(i, 3).value == 'q':
                    code = str(int(sheet2.cell(i, 0).value))
                    if code == '1000000000': continue
                    if code[0] not in data:
                        data[code[0]] = {}
                        data_list[code[0]] = []
                    data[code[0]][code] = sheet2.cell(i, 1).value
                    data_list[code[0]].append(code)
            return data, data_list

        res['ml'], res['ml_list'] = get_current_xt()

        # 读取系统描述
        fr_dict, fr_f_dict, fr_mx_r_dict = read_first_col(sheet.col_values(0))
        res['xtms'] = read_xtms()  # 读取系统描述

        # 读取系统列表
        mulu_dict, mulu_f_dict = read_mulu()  # 读取目录
        res['xtlb'] = read_xtlb()  # 读取系统列表

        res['mx_dict'] = {}

        try:
            for xt in res['ml']:
                for mx in res['ml'][xt]:
                    index = fr_mx_r_dict[mulu_f_dict[res['ml'][xt][mx]]]
                    res['mx_dict'][mx] = read_xtflmx(mx, index)
        except Exception, e:
            raise UserError(e.message)

        print sheet.name

        self.report_content = json.dumps(res)

    @api.multi
    def get_value(self, k=False):
        # if not self.report_content:
        #     self.btn_read_header()
        self.btn_read_header()
        if k:
            return json.loads(self.report_content).get(k)
        else:
            return json.loads(self.report_content)
