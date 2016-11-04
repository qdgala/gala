/*---------------------------------------------------------
 * workflow 增强
 * 2013-12-22 加入workflow_stop标识，表示中止工作流
 * Copyright 2013 yeahliu <talent_qiao@163.com>
 *---------------------------------------------------------*/
openerp.workflow_info = function(instance) {
    var _t = instance.web._t,
        _lt = instance.web._lt;
    var QWeb = instance.web.qweb;

    instance.web.View.include({
        x_display_error: function (error) {
            return new instance.web.Dialog(this, {
            size: 'medium',
            title: error.title,
            buttons: [
                {text: _t("Ok"), click: function() { this.parents('.modal').modal('hide'); }}
            ]
        }, $('<div>').html(error.error)).open();
        },
        
        do_execute_action: function (action_data, dataset, record_id, on_closed) {
	    	//alert("action_data :"+action_data + "  dataset:"+dataset+ "  record_id: "+record_id+"  on_closed: "+on_closed )
	    	var self = this;
	    	if(action_data.type == "workflow_ok" || action_data.type == "workflow_no"
	    		|| action_data.type == "workflow_stop"){
	    		sta = "" ;
	    		_title= "" ;
	    		if( action_data.type == "workflow_no"){
	    			sta = "no" ;
	    			_title = "输入拒绝意见：" ;
	    		} else if(action_data.type=="workflow_ok"){
	    			sta = "ok";
	    			_title = "输入审批意见(可不填)：";
	    		} else if( action_data.type=="workflow_stop"){
	    			sta = "stop";
	    			_title = "输入中止原因：";
	    		}
	    		
	    		var dialog = new instance.web.Dialog(this,{
	    			title: _title,
	    			dialogClass: 'oe_act_window',
	    			width:500
	    		},	QWeb.render("textbox_pft_wkl"));
	    		
	    		buttons=[
					                {text: _t("确定"), click: function() { 
						                	return self.rpc('/web/workflow_info/info', {
										            model: dataset.model,
										            id: record_id, // wkf_instance id
										            signal: action_data.name,
										            note:dialog.$el.find(".oe_textbox_pft_wkl").val(),
										            status: sta
										        }).done(function(result) {
										            if (result.error) {
										                self.x_display_error(result);
										                return;
										            }
										        }).then(function(){
										        	dialog.destroy();									        
										        }).then(function () {
										        	self.reload();
									            });
					                	}
					                }
					            ];
	    		dialog._add_buttons(buttons);
	    		dialog.open();
	    		
	    		if( action_data.type == "workflow_no"){
	    			dialog.$el.find(".oe_textbox_pft_wkl").text("不同意");
	    		} else if(action_data.type=="workflow_ok"){
	    			dialog.$el.find(".oe_textbox_pft_wkl").text("同意");
	    		} else if( action_data.type=="workflow_stop"){
	    			dialog.$el.find(".oe_textbox_pft_wkl").text("中止");
	    		}
	    		
	    	} else if (action_data.type == "workflow_submit"){
	    		return self.rpc('/web/workflow_info/info', {
										            model: dataset.model,
										            id: record_id, // wkf_instance id
										            signal: action_data.name,
										            note:'提交',
										            status: 'submit'
										        }).done(function(result) {
										            if (result.error) {
										                self.x_display_error(result);
										                return;
										            }
										            self.reload();
										        });
	    	} else {
	    		return this._super(action_data, dataset, record_id, on_closed) ;
    	}
    }
    });
    
};

// vim:et fdc=0 fdl=0 foldnestmax=3 fdm=syntax:
