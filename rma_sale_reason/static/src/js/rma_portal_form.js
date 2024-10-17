/*  Copyright 2024 Raumschmiede GmbH
    Copyright 2024 BCIM
    Copyright 2024 ACSONE SA/NV
    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).*/

odoo.define("rma_sale_reason.animation", function (require) {
    "use strict";
    const publicWidget = require("rma_sale.animation");
    publicWidget.registry.PortalRmaSale.include({
        events: _.extend({}, publicWidget.registry.PortalRmaSale.prototype.events, {
            "change .rma-reason": "_onChangeReasonId",
        }),
        _onChangeReasonId: function () {
            this._checkCanSubmit();
        },
        _canSubmit: function () {
            var can_submit = false;
            var is_rma_reason_required = this.$el
                .find('input[name="is_rma_reason_required"]')
                .val();
            if (is_rma_reason_required === "0") {
                return this._super(...arguments);
            }
            for (const id of this.rows_ids) {
                const row = this.rows[id];
                var reason = this.$(`[name='${id}-reason_id']`);
                if (
                    row &&
                    // A reason is defined
                    reason &&
                    reason.val()
                ) {
                    can_submit = true;
                    break;
                }
            }
            return can_submit && this._super(...arguments);
        },
    });
});
