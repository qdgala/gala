1、导入模块

      import xlrd

2、打开Excel文件读取数据

       data = xlrd.open_workbook('excel.xls')

3、获取一个工作表

    table = data.sheets()[0]             #通过索引顺序获取
    table = data.sheet_by_index(0)       #通过索引顺序获取
    table = data.sheet_by_name(u'Sheet1')#通过名称获取

4、获取整行和整列的值（返回数组）
         table.row_values(i)
         table.col_values(i)

5、获取行数和列数　
        table.nrows
        table.ncols

6、获取单元格
　　table.cell(0,0).value
    table.cell(2,3).value