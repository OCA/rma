from odoo.tests import TransactionCase, tagged

from odoo.addons.rma.hooks import post_init_hook


@tagged("current")
class TestRmaHooks(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestRmaHooks, cls).setUpClass()
        cls.res_partner = cls.env["res.partner"]

    def test_post_init_hook(self):

        result = post_init_hook(self.env.cr, self.env.registry)
        self.assertEqual(result, None)

        result = post_init_hook(self.env.cr, self.env.registry)
        self.assertEqual(result, None)
