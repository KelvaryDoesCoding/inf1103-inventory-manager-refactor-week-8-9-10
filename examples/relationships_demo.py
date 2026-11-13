"""Run from the project root: python -m examples.relationships_demo."""

from digital_product import DigitalProduct
from inventory import Inventory
from order import Order
from physical_product import PhysicalProduct
from product import Product
from supplier import Supplier


def show_product_details(product: Product) -> None:
    product.display_information()
    print(product.get_fulfilment_info())


def main() -> None:
    supplier = Supplier("S001", "Demo Supplier", "demo@example.com")
    physical = PhysicalProduct("P001", "Laptop", 1200, 15, 1.5, supplier)
    digital = DigitalProduct("P002", "Software", 25.5, 40, 500, supplier)
    del supplier
    print("After deleting the supplier variable, both product references still work:")
    for product in (physical, digital):
        product.supplier.display_information()

    inventory_a, inventory_b = Inventory(), Inventory()
    inventory_a.add_product(physical)
    removed = inventory_a.remove_product("P001")
    print("Removed product is the original object:", removed is physical)
    removed.update_stock(12)
    inventory_b.add_product(removed)
    inventory_b.add_product(digital)
    print("One Product loop handles both subclasses:")
    for product in inventory_b.products:
        show_product_details(product)

    first, second = Order("O001"), Order("O002")
    first.add_order_line(physical, 2)
    first.add_order_line(digital, 3)
    second.add_order_line(physical, 1)
    first.display_information()
    print("Distinct order lines:", first.order_lines[0] is not second.order_lines[0])
    print("Same product:", first.order_lines[0].product is second.order_lines[0].product)
    first.remove_order_line(1)
    first.cancel()
    print("Cancelled order has no lines:", not first.order_lines)
    print("Other order and product remain usable:")
    second.display_information()


if __name__ == "__main__":
    main()
