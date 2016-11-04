# 工作流日志模块V9版

基于 workflow_info 模块修改实现

# 使用方法

1、安装该模块后，在自己的模块中添加如下所示字段：
```
    opinion_ids = fields.One2many('wkf.logs', 'info', compute="_cmpt_spyj", string=u'审批意见')

    @api.multi
    def _cmpt_spyj(self):
        self.opinion_ids = self.env['wkf.logs'].search([('res_model', '=', self._name), ('res_id', '=', self.ids[0])])
```


2、在xml中引用：

```
    <field name="opinion_ids"/>
```

3、按钮设置：
```
基础类型：
    workflow_submit     提交，不弹窗
    workflow_ok         审批，弹窗
    workflow_no         拒绝，弹窗
    workflow_stop       流程结束，弹窗
例：
    <button type="workflow_submit" name="to_sale" string="提交"  class="oe_highlight"/>
    <button type="workflow_ok"     name="to_dele" string="审批"  class="oe_highlight"/>
    <button type="workflow_no"     name="refuse"  string="拒绝"  class="oe_highlight"/>
    <button type="workflow_stop"   name="refuse"  string="拒绝"  class="oe_highlight"/>


特殊类型1：
    workflow_proxy      将当前页面中log_field字段的值传入wkf_log中，类型为 log_type
例：
    <field name="opinion" class="wkf_logs_proxy" required="1"/>
    <button string="审批" name="lds" type="workflow_proxy" log_field="opinion" log_type="ok" class="oe_highlight"/>
介绍：
    将表单中的log_field字段中值存入wkf_logs中


特殊类型2：
    log_type="reproxy" log_field="字段名" type="基础类型"
例：
    <button string="审批" name="bmsp" type="workflow_ok" log_field="reason" log_type="reproxy" class="oe_highlight"/>
介绍：
    type的可选值为 workflow_ok、workflow_no、workflow_stop
    实现的效果：
        创建wkf_Logs并将弹窗中录入的内容存入表单中的log_field字段中


```