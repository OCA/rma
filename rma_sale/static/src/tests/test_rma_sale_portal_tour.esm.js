/* Copyright 2021 Tecnativa - David Vidal
   Copyright 2025 Tecnativa - Víctor Martínez
   License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl). */

import {registry} from "@web/core/registry";

registry.category("web_tour.tours").add("rma_sale_portal", {
    url: "/my/orders",
    steps: () => [
        {
            content: "Open the test sale order",
            trigger: 'a:contains("Test Sale RMA SO")',
            run: "click",
        },
        {
            content: "Open the RMA request pop-up",
            trigger: 'a:contains("Request RMAs")',
            run: "click",
        },
        {
            content:
                "Submit button is disabled until we set quanity and requested operation",
            trigger: "button[type='submit'][disabled]",
        },
        {
            content: "Return 1 unit for the first row",
            trigger: "input[name='0-quantity']",
            run: "edit 1",
        },
        {
            content: "Select the operation",
            trigger: "select[name='0-operation_id']",
            run: "select 1",
        },
        {
            content: "Write some comments",
            trigger: "textarea[name='0-description']",
            run: "edit I'd like to change this product",
        },
        {
            content: "Unfold the Delivery Address picker",
            trigger: "button:contains('Choose a delivery address')",
            run: "click",
        },
        {
            content: "Choose another address",
            trigger: ".o_rma_portal_shipping_card:contains('Another address')",
            run: "click",
        },
        {
            content: "Submit the RMA",
            trigger: "button[type='submit']",
            run: "click",
        },
        {
            content: "We're redirected to the new draft RMA",
            trigger: "h5:contains('RMA Order')",
        },
    ],
});
