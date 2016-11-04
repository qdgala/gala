odoo.define('oa_workflow.oa_wkf', function (require) {
    'use strict';

    var Dialog = require('web.Dialog');
    var View = require('web.View');
    var core = require('web.core');

    var QWeb = core.qweb;
    var _t = core._t;

    View.include({
        x_display_error: function (error) {
            return new Dialog(this, {
                size: 'medium',
                title: error.title,
                $content: $('<div>').html(error.error)
            }).open();
        },

        do_execute_action: function (action_data, dataset, record_id, on_closed) {
            var self = this;
            if (action_data.type == "workflow_ok" || action_data.type == "workflow_no" || action_data.type == "workflow_stop" || action_data.log_type == "reproxy") {
                var sta = "";
                var _title = "";
                if (action_data.type == "workflow_no") {
                    sta = "no";
                    _title = "输入拒绝意见：";
                } else if (action_data.type == "workflow_ok") {
                    sta = "ok";
                    _title = "输入审批意见(可不填)：";
                } else if (action_data.type == "workflow_stop") {
                    sta = "stop";
                    _title = "输入中止原因：";
                } else if (action_data.type == "workflow_submit") {
                    console.log('workflow_submit 不能和 reproxy 属性同时出现');
                    return;
                }

                var dialog = new Dialog(this, {
                    title: _title,
                    size: 'medium',
                    $content: QWeb.render("textbox_pft_wkl"),
                    buttons: [{
                        text: _t("确定"), click: function () {
                            // return dataset.exec_workflow(record_id, action_data.name).then(handler);

                            self.rpc('/web/workflow_info/info', {
                                model: dataset.model,
                                id: record_id, // wkf_instance id
                                signal: action_data.name,
                                note: dialog.$el.find(".oe_textbox_pft_wkl").val(),
                                status: sta,
                                log_type: action_data.log_type,
                                log_field: action_data.log_field
                            }).done(function (result) {
                                if (result.error) {
                                    self.x_display_error(result);
                                    return;
                                }
                            }).then(function () {
                                dialog.destroy();
                            }).then(function () {
                                self.reload();
                                core.bus.trigger('do_reload_needaction');
                            })
                        }
                    }]
                }).open();


                if (action_data.type == "workflow_no") {
                    dialog.$el.find(".oe_textbox_pft_wkl").text("不同意");
                } else if (action_data.type == "workflow_ok") {
                    dialog.$el.find(".oe_textbox_pft_wkl").text("同意");
                } else if (action_data.type == "workflow_stop") {
                    dialog.$el.find(".oe_textbox_pft_wkl").text("中止");
                }
                var result_handler = function () {
                    if (on_closed) {
                        on_closed.apply(null, arguments);
                    }
                    if (self.getParent() && self.getParent().on_action_executed) {
                        var ss = self.getParent().on_action_executed.apply(null, arguments);
                        core.bus.trigger('do_reload_needaction');
                        return ss;

                    }
                };
                var handler = function (action) {
                    if (action && action.constructor == Object) {
                        // filter out context keys that are specific to the current action.
                        // Wrong default_* and search_default_* values will no give the expected result
                        // Wrong group_by values will simply fail and forbid rendering of the destination view
                        var ncontext = new data.CompoundContext(
                            _.object(_.reject(_.pairs(dataset.get_context().eval()), function (pair) {
                                return pair[0].match('^(?:(?:default_|search_default_|show_).+|.+_view_ref|group_by|group_by_no_leaf|active_id|active_ids)$') !== null;
                            }))
                        );
                        ncontext.add(action_data.context || {});
                        ncontext.add({active_model: dataset.model});
                        if (record_id) {
                            ncontext.add({
                                active_id: record_id,
                                active_ids: [record_id],
                            });
                        }
                        ncontext.add(action.context || {});
                        action.context = ncontext;
                        return self.do_action(action, {
                            on_close: result_handler,
                        });
                    } else {
                        self.do_action({"type": "ir.actions.act_window_close"});
                        return result_handler();
                    }
                };
                return $.when().then(handler);
            }
            else if (action_data.type == "workflow_submit") {
                return self.rpc('/web/workflow_info/info', {
                    model: dataset.model,
                    id: record_id, // wkf_instance id
                    signal: action_data.name,
                    note: "提交",
                    status: 'submit'
                }).done(function (result) {
                    if (result.error) {
                        self.x_display_error(result);
                        return;
                    }
                    self.reload();
                    core.bus.trigger('do_reload_needaction');
                });
            }
            else if (action_data.type == "workflow_proxy") {
                var note = $('.wkf_logs_proxy [name="' + action_data.log_field + '"]').val();


                return self.rpc('/web/workflow_info/info', {
                    model: dataset.model,
                    id: record_id, // wkf_instance id
                    signal: action_data.name,
                    note: note,
                    status: action_data.log_type
                }).done(function (result) {
                    if (result.error) {
                        self.x_display_error(result);
                        return;
                    } else {
                        setTimeout(function () {
                            $('.modal-footer .btn-default').trigger('click');
                            core.bus.trigger('do_reload_needaction');
                        }, 500)

                    }
                });
            }
            else {
                console.log('use super');
                return this._super.apply(this, arguments);
            }
        }
    });
});