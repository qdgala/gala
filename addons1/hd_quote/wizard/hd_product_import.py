# -*- coding: utf-8 -*-
import base64
import xlrd

from openerp import models, fields, api, _
from openerp.exceptions import UserError


class hd_product_import_demo(models.Model):
    _name = 'hd.product.import.demo'
    _description = u'华丹 产品导入'

    excel = fields.Binary(u'文件', attachment=True, required=True)

    @api.multi
    def btn_cb_import(self):
        # 导入成本价
        import sys
        reload(sys)
        sys.setdefaultencoding('utf8')

        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.excel))
        except:
            raise UserError(_('文件格式不匹配或文件内容错误.'))

        self._cr.execute("select default_code from product_product")
        code_list = [i[0] for i in self._cr.fetchall()]

        for sheet in wb.sheets():
            if sheet.name == u'报价单':
                pass
            elif sheet.name == u'系统分类':
                pass
            else:
                self._handle_mx_cb(sheet, code_list)

    @api.multi
    def _handle_mx_cb(self, sheet, codes):
        pt = self.env['product.template']
        # 直接从第六行开始读取数据
        for i in range(6, sheet.nrows):
            code = sheet.cell(i, 1).value
            if isinstance(code, unicode):
                pass
            elif isinstance(code, float):
                code = str(int(code))
            else:
                print code
                continue

            if code in codes:
                ysdj = sheet.cell(i, 5).value
                if isinstance(ysdj, (float, int)):
                    pt.search([('default_code', '=', code)]).standard_price = ysdj
                else:
                    print ysdj

    @api.multi
    def btn_import(self):
        import sys
        reload(sys)
        sys.setdefaultencoding('utf8')

        try:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.excel))
        except:
            raise UserError(_('文件格式不匹配或文件内容错误.'))

        self._cr.execute("select name,id from res_partner where supplier = 't'")
        gys_dict = dict(self._cr.fetchall())

        for sheet in wb.sheets():
            if sheet.name == u'报价单':
                self._handle_bjd(sheet)
            elif sheet.name == u'系统分类':
                self._handle_xtfl(sheet)
                self._import_cplb(sheet)
            else:
                self._handle_mx(sheet, gys_dict)

    @api.multi
    def _handle_bjd(self, sheet):
        print u'__报价单'

    @api.multi
    def _handle_xtfl(self, sheet):
        print u'__系统分类'

        xt = self.env['product.template']

        # 通过sql获取所有编码
        self._cr.execute("select default_code from product_product where id in (select id from product_template)")
        code_list = [i[0] for i in self._cr.fetchall()]
        for i in range(2, sheet.nrows):
            code = str(int(sheet.cell(i, 0).value))
            if code in code_list:
                xt.search([('default_code', '=', code)]).type = 'xt'
            else:
                xt.create({
                    'name': sheet.cell(i, 1).value,
                    'default_code': code,
                    'type': 'xt',
                    'description_sale': sheet.cell(i, 2).value,
                })

    @api.multi
    def _handle_mx(self, sheet, gys_dict):
        print u'明细:' + sheet.name
        pt = self.env['product.template']

        # 通过sql获取所有编码
        self._cr.execute("select default_code from product_product")
        code_list = [i[0] for i in self._cr.fetchall()]
        dy = {
            u'国内': 'gn',
            u'国内采购': 'gn',
            u'国外': 'gw',
            u'国外采购': 'gw',
            u'自制': 'zz',
            u'采购直发': 'cgzf',
            u'国内直发': 'gnzf',
            u'管箍厂家配': None,
        }
        pz = {}
        # 直接从第六行开始读取数据
        for i in range(6, sheet.nrows):
            code = sheet.cell(i, 1).value
            if isinstance(code, unicode):
                pass
            elif isinstance(code, float):
                code = str(int(code))
            else:
                print code
                continue

            if not code or code in code_list:
                continue
            else:
                if len(code) < 7:
                    continue
                part = code[:6]
                if part not in pz:
                    pz[part] = self.env['product.category'].search([('code', '=', part + "0000")]).id
                    if not pz[part]:
                        raise UserError(u"错误的编号：" + code)

                print 'ddd' + code
                jgfs = sheet.cell(i, 13).value
                vals = {
                    'name': sheet.cell(i, 2).value,
                    'default_code': code,
                    'categ_id': pz[part],
                    'guige': sheet.cell(i, 10).value,
                    'jiagong_fs': jgfs and dy[jgfs],
                    'weight': sheet.cell(i, 11).value or 0,
                }

                ysdj = sheet.cell(i, 5).value
                if isinstance(ysdj, (float, int)):
                    vals['standard_price'] = ysdj

                gys_name = sheet.cell(i, 15).value
                if gys_name != "":
                    if gys_name in gys_dict:
                        gys_id = gys_dict[gys_name]
                    else:
                        gys_id = self.env['res.partner'].create({
                            'name': gys_name,
                            'company_type': 'company',
                            'supplier': True,
                            'customer': False,
                        }).id
                        gys_dict[gys_name] = gys_id
                    vals['default_gys'] = gys_id
                    vals['seller_ids'] = [[0, 0, {'name': gys_id, }]]

                pt.create(vals)
                code_list.append(code)

    @api.multi
    def _import_cplb(self, sheet):
        # 创建产品类别
        pc = self.env['product.category']
        self._cr.execute("select code from product_category")
        code_list2 = [i[0] for i in self._cr.fetchall()]
        datas = {}
        for i in range(2, sheet.nrows):
            code = str(int(sheet.cell(i, 0).value))
            if code not in code_list2:
                datas[code] = sheet.cell(i, 1).value

        for i in datas:
            if i[1:] == "000000000":
                pc.create({
                    'name': datas[i],
                    'code': i,
                    # 'property_cost_method': 'average',
                    # 'property_valuation': 'real_time',
                })

        for i in datas:
            if i[1:] != "000000000":
                pc.create({
                    'name': datas[i],
                    'parent_id': pc.search([('code', '=', i[:1] + "000000000")]).id,
                    'code': i,
                    # 'property_cost_method': 'average',
                    # 'property_valuation': 'real_time',
                })
