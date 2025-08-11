# Copyright 2025 Georgie Dekker
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from unittest.mock import patch

from odoo.exceptions import ProgrammingError
from odoo.tests.common import TransactionCase


class TestProductSupplierInfoInstallation(TransactionCase):
    """Test product_supplierinfo installation robustness."""

    def test_get_default_instructions_handles_missing_table(self):
        """Test _get_default_instructions handles missing return_instruction table."""

        # Get the model class to test the method directly
        supplierinfo_model = self.env["product.supplierinfo"]

        # Mock the search to raise a ProgrammingError (table doesn't exist)
        def mock_search(*args, **kwargs):
            raise ProgrammingError('relation "return_instruction" does not exist')

        # Patch the return.instruction model's search method
        with patch.object(
            self.env["return.instruction"], "search", side_effect=mock_search
        ):
            result = supplierinfo_model._get_default_instructions()
            self.assertFalse(
                result,
                "Should return False when return_instruction table doesn't exist",
            )

    def test_get_default_instructions_normal_operation(self):
        """Test that _get_default_instructions works normally when table exists."""

        # Create a default return instruction
        return_instruction = self.env["return.instruction"].create(
            {
                "name": "Test Default Instructions",
                "is_default": True,
                "instructions": "Test instructions for returns",
            }
        )

        supplierinfo_model = self.env["product.supplierinfo"]
        result = supplierinfo_model._get_default_instructions()

        self.assertEqual(
            result,
            return_instruction,
            "Should return the default return instruction when it exists",
        )

    def test_get_default_instructions_no_default(self):
        """Test _get_default_instructions returns empty recordset when no default."""

        # Ensure no default return instructions exist
        self.env["return.instruction"].search([("is_default", "=", True)]).unlink()

        supplierinfo_model = self.env["product.supplierinfo"]
        result = supplierinfo_model._get_default_instructions()

        self.assertFalse(
            result,
            "Should return empty recordset when no default exists",
        )
