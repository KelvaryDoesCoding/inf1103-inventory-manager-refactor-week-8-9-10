import contextlib
import io
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from can_be_shipped import CanBeShipped
from digital_product import DigitalProduct
from examples.relationships_demo import show_product_details
from file_handling import load_inventory, save_inventory
from inventory import Inventory
import main
from order import Order
from physical_product import PhysicalProduct
from product import Product
from supplier import Supplier


class RelationshipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.supplier = Supplier("S001", "Supplier", "sales@example.com")
        self.physical = PhysicalProduct("P001", "Laptop", 1200, 15, 1.5, self.supplier)
        self.digital = DigitalProduct("P002", "Software", 25.5, 40, 500, self.supplier)

    def test_association_survives_variable_deletion(self) -> None:
        supplier = self.supplier
        del self.supplier
        del supplier
        self.assertIs(self.physical.supplier, self.digital.supplier)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.physical.supplier.display_information()
        self.assertIn("sales@example.com", output.getvalue())

    def test_aggregation_transfer_and_missing_product(self) -> None:
        first, second = Inventory(), Inventory()
        first.add_product(self.physical)
        removed = first.remove_product(" p001 ")
        self.assertIs(removed, self.physical)
        self.assertIsNone(first.find_product("P001"))
        removed.update_stock(8)
        second.add_product(removed)
        self.assertIs(second.find_product("P001"), self.physical)
        del first
        self.assertEqual(self.physical.stock, 8)
        with self.assertRaises(ValueError):
            second.remove_product("missing")

    def test_composition_and_product_independence(self) -> None:
        first, second = Order("O001"), Order("O002")
        first.add_order_line(self.physical, 2)
        first.add_order_line(self.digital, 3)
        second.add_order_line(self.physical, 1)
        self.assertIsNot(first.order_lines[0], second.order_lines[0])
        self.assertIs(first.order_lines[0].product, second.order_lines[0].product)
        self.assertEqual(first.order_lines[0].calculate_subtotal(), 2400)
        self.assertEqual(first.calculate_total(), 2476.5)
        self.assertIsInstance(first.order_lines, tuple)
        first.remove_order_line(1)
        self.assertEqual(first.calculate_total(), 76.5)
        first.cancel()
        self.assertEqual(first.order_lines, ())
        self.assertEqual(first.calculate_total(), 0.0)
        self.assertEqual(second.calculate_total(), 1200)
        self.assertEqual(self.physical.stock, 15)
        with self.assertRaises(ValueError):
            first.add_order_line(self.physical, 1)

    def test_order_validation(self) -> None:
        order = Order("O001")
        for value in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                order.add_order_line(self.physical, value)
        for number in (0, 1, True):
            with self.assertRaises(ValueError):
                order.remove_order_line(number)
        self.assertEqual(order.order_lines, ())

    def test_lsp_and_polymorphism(self) -> None:
        inventory = Inventory()
        for product in (self.physical, self.digital):
            inventory.add_product(product)
        for product in inventory.products:
            for stock in (0, 50):
                inventory.update_stock(product.product_id, stock)
                self.assertEqual(product.stock, stock)
            with self.assertRaises(ValueError):
                product.update_stock(-1)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                show_product_details(product)
            self.assertIn(product.name, output.getvalue())
            self.assertIn(product.get_fulfilment_info(), output.getvalue())
            self.assertIsInstance(product.get_fulfilment_info(), str)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            inventory.display_all()
        self.assertIn("1.5 kg", output.getvalue())
        self.assertIn("500 MB", output.getvalue())

    def test_existing_abstract_and_shipping_contracts(self) -> None:
        with self.assertRaises(TypeError):
            Product("P001", "Item", 1, 1, self.supplier)
        with self.assertRaises(TypeError):
            CanBeShipped()
        self.assertEqual(self.physical.calculate_shipping_cost(), 7.5)
        heavier = PhysicalProduct("P003", "Item", 1, 1, 3, self.supplier)
        self.assertEqual(heavier.calculate_shipping_cost(), 15)
        self.assertNotIsInstance(self.digital, CanBeShipped)

    def test_invalid_product_and_supplier_inputs(self) -> None:
        with self.assertRaises(TypeError):
            PhysicalProduct("P003", "Item", 1, 1, 1, "S001")
        with self.assertRaises(ValueError):
            Supplier("", "Supplier", "sales@example.com")
        for invalid in (-1, float("inf"), float("nan"), True):
            with self.assertRaises(ValueError):
                PhysicalProduct("P003", "Item", 1, 1, invalid, self.supplier)
            with self.assertRaises(ValueError):
                DigitalProduct("P003", "Item", 1, 1, invalid, self.supplier)

    def test_json_preserves_supplier_identity_and_legacy_data(self) -> None:
        inventory = Inventory()
        inventory.add_product(self.physical)
        inventory.add_product(self.digital)
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "inventory.json"
            save_inventory(inventory, path)
            loaded = load_inventory(path)
            self.assertIs(loaded.products[0].supplier, loaded.products[1].supplier)
            self.assertEqual(loaded.products[0].supplier.supplier_id, "S001")
            self.assertEqual(loaded.products[1].download_size, 500)
            code = ("from pathlib import Path; from file_handling import load_inventory; "
                    "import sys; i=load_inventory(Path(sys.argv[1])); "
                    "assert i.products[0].supplier is i.products[1].supplier; "
                    "print(type(i.products[0]).__name__, type(i.products[1]).__name__)")
            result = subprocess.run([sys.executable, "-B", "-c", code, str(path.resolve())],
                                    check=True, capture_output=True, text=True)
            self.assertIn("PhysicalProduct DigitalProduct", result.stdout)
            records = json.loads(path.read_text())
            records[1]["supplier"]["name"] = "Conflicting supplier"
            path.write_text(json.dumps(records))
            with self.assertRaises(ValueError):
                load_inventory(path)
            for record in records:
                del record["supplier"]
            path.write_text(json.dumps(records))
            legacy = load_inventory(path)
            self.assertEqual(legacy.products[0].supplier.supplier_id, "UNKNOWN")
            self.assertIs(legacy.products[0].supplier, legacy.products[1].supplier)

    def test_menu_integration(self) -> None:
        answers = ["2", "1", "Laptop", "1200", "15", "S001", "Supplier",
                   "sales@example.com", "1.5", "2", "2", "Software", "25.5", "40",
                   "S001", "500", "8", "O001", "9", "O001", "P001", "2",
                   "9", "O001", "P002", "3", "10", "O001", "7", "P001",
                   "10", "O001", "11", "O001", "1", "12", "O001", "5", "6"]
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / "inventory.json"
            with patch.object(main, "DATA_FILE", path), \
                    patch("builtins.input", side_effect=answers), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                main.main()
            self.assertIn("Total: $2476.50", output.getvalue())
            self.assertIn("Order cancelled", output.getvalue())
            restored = load_inventory(path)
            self.assertEqual(len(restored.products), 1)
            self.assertEqual(restored.products[0].supplier.supplier_id, "S001")


if __name__ == "__main__":
    unittest.main()
