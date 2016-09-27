openerp.crm_claim_rma = function(openerp) {
    var _t = openerp.web._t,
        _lt = openerp.web._lt;
    var QWeb = openerp.web.qweb;
    /*
    This widget is supposed to be used only in places where you need to load several
    barcodes at same time. In order to save locally information and trigger save
    data "ala on_change" but without lose the focus.
    */

    openerp.web.form.BarcodeText = openerp.web.form.FieldText.extend({
        events: {
            'keypress': function(e) {
                if (e.which === $.ui.keyCode.ENTER) {
                    this.store_dom_value();
                    e.stopPropagation();
                }
            },
            'change textarea': function(e) {
                this.store_dom_value();
                e.stopPropagation();
                $('textarea[name="scan_data"]').focus();
                $('textarea[name="scan_data"]').trigger('focus');
            },
        },
    });

    openerp.web.form.ChangeFocus = openerp.web.form.FieldChar.extend({
        play_bip: function(){
            var sound = document.getElementById("rma_alert");
            sound.volume = 0.9;
            sound.play();
        },

        events: {
            'keypress': function(e) {
                if (e.which === $.ui.keyCode.ENTER) {
                    $('textarea[name="scan_data"]').focus();
                    this.store_dom_value();
                    e.stopPropagation();
                }
            },
            'change input': function(e) {
                var self = this;
                this.store_dom_value();
                e.stopPropagation();
                $('.packing_cache_button').click(function(e) {
                    $('body').off("keypress");
                });
                $('body').keypress(function(p) {
                    if ($._data($('body')[0], 'events').keypress.length > 1) {
                        $._data($('body')[0], 'events').keypress.pop();

                    }
                    var search = p.target.parentElement.className.search('pack_search');
                    if (p.target.name !== 'scan_data' && search < 0 && p.keyCode === $.ui.keyCode.ENTER){
                        self.play_bip();
                    }
                });
                $('textarea[name="scan_data"]').focus();
                $('textarea[name="scan_data"]').trigger('focus');
            },
        },

    });
    openerp.web.FormView.include({
        play_bip: function(){
            var sound = document.getElementById("rma_alert");
            sound.volume = 0.9;
            sound.play();
        },
        on_processed_onchange: function(result){
            try {
                var result2 = result;
                if (!_.isEmpty(result2.warning) && this.model === 'returned.lines.from.serial.wizard') {
                    this.play_bip();
                    new openerp.web.Dialog(this, {
                        size: 'medium',
                        title: result2.warning.title,
                        buttons: [{
                            text: _t("-->"),
                            click: function() {
                                return;
                            }
                        }, {
                            text: _t("Ok"),
                            click: function() {
                                this.parents('.modal').modal('hide');
                            }
                        }]
                    }, QWeb.render("CrashManager.warning", result2.warning)).open();

                    $("span:contains('-->')").focus();
                } else {
                    this._super.apply(this, arguments);
                }
            } catch (e) {
                openerp.webclient.crashmanager.show_message(e);
                return $.Deferred().reject();
            }


        },
    });
    openerp.web.form.widgets.add('barcode_text', 'openerp.web.form.BarcodeText');
    openerp.web.form.widgets.add('change_focus', 'openerp.web.form.ChangeFocus');
};
