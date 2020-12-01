/* Copyright 2020 Tecnativa - Ernesto Tejeda
/* License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
 */
odoo.define("website_rma.website_rma", function(require) {
    "use strict";

    require("web.dom_ready");

    $("#rma_request_form input[name='product_id']").select2({
        width: "100%",
        placeholder: "Select a product",
        allowClear: true,
        selection_data: false,
        ajax: {
            url: "/website_rma/get_products",
            dataType: "json",
            data: function(term) {
                return {
                    q: term,
                    l: 50,
                };
            },
            results: function(data) {
                var res = [];
                _.each(data, function(x) {
                    res.push({
                        id: x.id,
                        text: x.display_name,
                        uom_id: x.uom_id[0],
                        uom_name: x.uom_id[1],
                    });
                });
                return {results: res};
            },
        },
    });
    // Set UoM on selected onchange
    $("#rma_request_form input[name='product_id']").change(function() {
        var select2_data = $(this).select2("data");
        var uom_id = select2_data ? select2_data.uom_id : "";
        var uom_name = select2_data ? select2_data.uom_name : "";
        $("input[name='product_uom']").val(uom_id);
        $("input[name='product_uom_name']").val(uom_name);
    });
});
