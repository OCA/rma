/** @odoo-module */
/* Copyright 2021 Tecnativa - David Vidal
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

import tour from "web_tour.tour";

tour.register(
    "rma_sale_portal",
    {
        test: true,
        url: "/my/orders",
    },
    [
        {
            content: "Open the test sale order",
            trigger: 'a:containsExact("Test Sale RMA SO")',
        },
        {
            content: "Open the RMA request pop-up",
            trigger: 'a:contains("Request RMAs")',
        },
        {
            content:
                "Submit button is disabled until we set quanity and requested operation",
            trigger: "button[type='submit'][disabled]",
        },
        {
            content: "Return 1 unit for the first row",
            trigger: "input[name='0-quantity']",
            run: "text 1",
        },
        {
            content: "Select the operation",
            trigger: "select[name='0-operation_id']",
            run: "text Replace",
        },
        {
            content: "Write some comments",
            trigger: "textarea[name='0-description']",
            run: "text I'd like to change this product",
        },
        {
            content: "Unfold the Delivery Address picker",
            trigger: "button:contains('Choose a delivery address')",
        },
        {
            content: "Choose another address",
            trigger: ".o_rma_portal_shipping_card:contains('Another address')",
            run: "click",
        },
        {
            content: "Submit the RMA",
            trigger: "button[type='submit']",
        },
        {
            content: "We're redirected to the new draft RMA",
            trigger: "h5:contains('RMA Order')",
        },
        {
            content: "We're redirected to the new draft RMA",
            trigger: "h5:contains('RMA Order')",
        },
    ]
);
