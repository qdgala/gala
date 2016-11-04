odoo.define('web_organization_tree.Organization_View', function (require) {
    'use strict';

    var Graph = require('web.GraphView');
    var core = require('web.core');
    var View = require('web.View');
    var Model = require('web.Model');
    var Organization_Tree_Widget = require('web_organization_tree.Organization_Tree_Widget');

    var QWeb = core.qweb;
    var _lt = core._lt;
    var _t = core._t;

    var Organization_View = Organization_Tree_Widget.extend({
        display_name: _lt('Organization Tree'),
        view_type: 'graph',
        init: function (parent, dataset, view_id, options) {
            var self = this;
            this._super(parent, dataset, view_id, options);
            this.dataset = dataset;
            this.model = new Model(dataset.model, {group_by_no_leaf: true});
            this.search_view = parent.searchview;
        },

        do_search: function (domain, context, group_by) {

            var self = this;

            if (!this.tree_widget) {

                this.tree_widget = new Organization_Tree_Widget(this, this.model, domain, context, this.options);
                this.tree_widget.appendTo(this.$el);

                this.ViewManager.on('switch_mode', this, function (e) {
                    if (e === 'organization_tree') {

                    }
                });
                return;
            }

        },

        do_show: function () {
            this.do_push_state({});
            return this._super();
        }


    });

    core.view_registry.add('otree', Organization_View);

    return Organization_View;

});