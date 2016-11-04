# -*- coding: utf-8 -*-
from openerp.osv import osv,fields
from openerp import SUPERUSER_ID

class hr_employee(osv.Model):
    _inherit = ['hr.employee']


    def get_organization_tree(self, cr, uid, ids, domain=[], context=None):

        root_list = []

        def cal_tree_dpt(node):
            if node['is_cal']:
                node['is_cal'] = 0
                if node['parent_id']:
                    id = node['parent_id'][0]
                    department_list[id]['children'].append(node)
                    cal_tree_dpt(department_list[id])
                elif node['company_id']:
                    id = node['company_id'][0]
                    company_list[id]['children'].append(node)
                else:
                    root_list.append(node)

        def cal_tree_com(node):
            if node['is_cal']:
                node['is_cal'] = 0
                if node['parent_id']:
                    id = node['parent_id'][0]
                    company_list[id]['children'].append(node)
                    cal_tree_com(company_list[id])
                else:
                    root_list.append(node)


        limit = 1000

        employee_res = self.search_read(cr, SUPERUSER_ID, domain, ['id', 'parent_id', 'name', 'job_id', 'department_id', 'company_id'], limit=limit, context=context)
        department_res = self.pool('hr.department').search_read(cr, SUPERUSER_ID, domain, ['id', 'parent_id', 'name', 'company_id', 'manager_id'], limit=limit, context=context)
        company_res = self.pool('res.company').search_read(cr, SUPERUSER_ID, domain, ['id', 'parent_id', 'name'], limit=limit, context=context)


        for company in company_res:
            company['model'] = 'res.company'
            company['is_cal'] = 1
            company['children'] = []
        company_list = {company['id']:company for company in company_res}

        for department in department_res:
            department['model'] = 'hr.department'
            department['is_cal'] = 1
            department['children'] = []
            if department['manager_id']:
                department['name'] += '/' + department['manager_id'][1]
        department_list = {department['id']:department for department in department_res}

        for employee in employee_res:
            employee['model'] = 'hr.employee'
            employee['is_cal'] = 1
            if employee['job_id']:
                employee['name'] += ' /' + employee['job_id'][1]

            if employee['department_id']:
                department_list[employee['department_id'][0]]['children'].append(employee)
            elif employee['company_id']:
                company_list[ employee['company_id'][0]]['children'].append(employee)
            else:
                root_list.append(employee)

        #调用递归
        for department in department_res:
            cal_tree_dpt(department)

        for company in company_res:
            cal_tree_com(company)

        #################################
        config = {'hr.employee': ["hr", "open_view_employee_list"],
                  'hr.department': ["hr_organization_tree", "open_view_department_list"]
        }

        return root_list, config


        #return (employee_res, department_res, company_res)
