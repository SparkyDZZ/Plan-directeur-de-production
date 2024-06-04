odoo.define('owl.mps', function (require) {
    "use strict";
    
    const {ComponentWrapper} = require('web.OwlCompatibility');
    var AbstractAction = require('web.AbstractAction');
    var config = require('web.config');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var field_utils = require('web.field_utils');
    var concurrency = require('web.concurrency');
    const QWeb = core.qweb;
    const _t = core._t;

    var OwlMps = AbstractAction.extend({
        template: 'owl.MPS',
        hasControlPanel: true,
        loadControlPanel: true,
        withSearchBar: true,
        searchMenuTypes: ['filter', 'favorite'],

        events: {
            'click .o_create_mps': '_onClickCreate',
            'click .o_mrp_mps_replenish': '_onClickReplenish',
            'click .o_unlink_mps': '_onClickUnlink',
            'mouseover .o_mrp_mps_replenish': '_onMouseOverReplenish',
            'mouseout .o_mrp_mps_replenish': '_onMouseOutReplenish'
        },
        custom_events: _.extend({}, AbstractAction.prototype.custom_events, {
            closed: '_onActionFormClosed',
        }),

        init: function (parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.context = action.context 
            this.actionManager = parent;
            this.formatFloat = field_utils.format.float;
            this.searchModelConfig = { modelName: 'mps' };
            this.product_lines = [];
            this.periods = []; 
            this.products = []; 
            this.boms = []; 
            this.bom_lines = []; 
            this.mps = [];
            this.state = {};
            this._renderButtons();
            this.GeneratePeriods();

            this.mutex = new concurrency.Mutex();
        },

        willStart: function () {
            return this._super.apply(this, arguments).then(() => {
                return (this.load());
            });
        },

        start: async function() {
            await this._super(...arguments);
            this.$el.html(QWeb.render(this.template, { widget: this, }));
            await this.update_cp();
        },

       _renderButtons: function () {
            this.$buttons = $(QWeb.render('OwlMps.Buttons'));
        },

        update_cp: async function() {
                const res = await this.updateControlPanel({
                    title: _t('Master Production Schedule'),
                    cp_content: {
                        $buttons: this.$buttons,
                    },
                });
                return res;
        },

        // generatePeriods: function () {
        //     const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        //     const currentDate = new Date();
        //     let currentMonthIndex = currentDate.getMonth();
        //     let currentYear = currentDate.getFullYear();
        //     const periods = [];

        //     for (let i = 0; i < 12; i++) {
        //         periods.push(`${months[currentMonthIndex]} ${currentYear}`);
        //         currentMonthIndex++;
        //         if (currentMonthIndex === 12) {
        //             currentMonthIndex = 0;
        //             currentYear++;
        //         }
        //     }

        //     this.periods = periods;
        // },

        _onClickCreate: function (ev) {
            this.mutex.exec(() => {
                return this.do_action({
                    type: 'ir.actions.act_window',
                    res_model: 'mps',
                    views: [[false, 'form']],
                    target: 'new',
                }, { on_close: () => this.load() });
            });
        },

        _onClickReplenish: function (ev) {
            console.log('Replenish button clicked');
        },

        _onMouseOverReplenish: function (ev) {
            console.log('Mouse over replenish button');
        },

        _onMouseOutReplenish: function (ev) {
            console.log('Mouse out replenish button');
        },

        _unlinkProduct: function(productionScheduleId) {
            var self = this;
            function doIt() {
                self.mutex.exec(function() {
                    return self._rpc({
                        model: 'mps',
                        method: 'unlink',
                        args: [productionScheduleId],
                    }).then(function() {
                        self.load();
                        self.render();
                    });
                });
            }
            Dialog.confirm(this, _t("Are you sure you want to delete this record ?"), {
                confirm_callback: doIt,
            });

        }, 

        GeneratePeriods: async function() {
            return this._rpc({
                model: 'mps',
                method: 'generate_periods',
                args: [[]],
            }).then((periods) => {
                this.periods = periods;
                const periodStrArray = periods.map(period => period.period_str);
                console.log(periodStrArray);
            });
        },

        _onClickUnlink: function(ev) {
            ev.preventDefault();
            var productionScheduleId = $(ev.target).closest('.o_mps_content').data('id');
            console.log(productionScheduleId);
            this._unlinkProduct(productionScheduleId);
        },

        get_mps: function () {
            return this._rpc({
                model: 'mps',
                method: 'search_read',
                args: [[]],
                kwargs: { fields: [] },
            }).then((product_lines) => {
                this.product_lines = product_lines;
                return this.get_forecasts();
            }).then(() => {
                this.product_lines.forEach(product_line => {
                    product_line.forecast_quantities = this.forecast_lines.filter(forecast => 
                        product_line.forecast_ids.includes(forecast.id)
                    );
                });
                console.log(this.product_lines);
                this.render();
            });
        },
        
        get_forecasts: function () {
            return this._rpc({
                model: 'mps.forecasted.qty',
                method: 'search_read',
                args: [[]],
                kwargs: { fields: [] }, // Fetch necessary fields
            }).then((forecast_lines) => {
                this.forecast_lines = forecast_lines;
                console.log(this.forecast_lines);
            });
        },        

        load: function () {
            return this.mutex.exec(() => {
                return this.get_mps();
            });
        },

        _onActionFormClosed: function (event) {
            this.load();
        },

        render: async function () {
            if (this.$el) {
                this.$('.o_content').html(QWeb.render('owl.MPS', { widget: this, }));
            }
        },
    });

    core.action_registry.add('owl.action_mps_js', OwlMps);
});
