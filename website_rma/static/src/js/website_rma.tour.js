/* Copyright 2020 Tecnativa - Ernesto Tejeda
/* License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
odoo.define("website_sale_vat_required.tour", function(require) {
    "use strict";

    var tour = require("web_tour.tour");
    var base = require("web_editor.base");

    tour.register(
        "request_rma",
        {
            test: true,
            url: "/my",
            wait_for: base.ready(),
        },
        [
            {
                content: "Click on RMA form page link",
                trigger: ".o_portal_my_home a[href='/requestrma']",
            },
            {
                content: "Fill form",
                trigger: "#rma_request_form",
                extra_trigger: "#rma_request_form",
                run: function() {
                    $("select[name='operation_id'] > option:eq(1)").prop(
                        "selected",
                        true
                    );
                    $("textarea[name='description']").val("RMA test from website form");
                },
            },
            {
                content: "Click on request button with the form empty",
                trigger: "a.o_website_form_send",
            },
            {
                content: "Click on RMA form page link",
                trigger: "div#request_rma_thanks",
            },
        ]
    );
});
