/* Copyright 2021 Tecnativa - David Vidal
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

odoo.define("rma_sale.animation", function (require) {
    "use strict";

    var sAnimation = require("website.content.snippets.animation");

    // In the customer portal when a RMA operation is selected show the comments
    // selector so the user doesn't miss the chance to add his comments
    sAnimation.registry.rma_operation_portal = sAnimation.Class.extend({
        selector: ".rma-operation",
        start: function () {
            this.id = this.el.name.replace("-operation_id", "");
            this.$comment = $("#comment-" + this.id);
            this.$comment_input = $("[name='" + this.id + "-description']");
            var _this = this;
            this.$el.on("change", function () {
                _this._onChangeOperationId();
            });
        },
        _show_comment: function () {
            if (this.$comment) {
                this.$comment.removeClass("show");
                this.$comment.addClass("show");
                if (this.$comment_input) {
                    this.$comment_input.focus();
                }
            }
        },
        _hide_comment: function () {
            if (this.$comment) {
                this.$comment.removeClass("show");
            }
        },
        _onChangeOperationId: function () {
            // Toggle comment on or off if an operation is requested
            if (this.$el && this.$el.val()) {
                this._show_comment();
            } else {
                this._hide_comment();
            }
        },
    });
});
