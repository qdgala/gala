odoo.define('load_logs.FormView', function (require) {
    "use strict";

    var core = require('web.core');
    var FormView = require('web.FormView');

    FormView.include({
        load_record: function (record) {
            var res = this._super(record);
            if (record.id) {
                this.rpc('/load_logs/update', {
                    res_model: this.dataset.model,
                    res_id: record.id
                }).then(function (result) {
                    if (result == 'new') {
                        core.bus.trigger('do_reload_needaction');
                    }
                });
            }
            return res;

        }
    });
});
