# Console menu for the inventory system

from pathlib import Path

from file_handling import load_inventory, save_inventory
from physical_product import PhysicalProduct
from digital_product import DigitalProduct
from order import Order
from supplier import Supplier


DATA_FILE = Path(__file__).resolve().with_name("inventory.json")


def choose_supplier(suppliers: dict[str, Supplier]) -> Supplier:
    for supplier in suppliers.values():
        supplier.display_information()
    supplier_id = input("Supplier ID (existing or new): ").strip().upper()
    if supplier_id in suppliers:
        return suppliers[supplier_id]
    supplier = Supplier(supplier_id, input("Supplier name: "), input("Contact email: "))
    suppliers[supplier.supplier_id] = supplier
    return supplier


def main() -> None:
    try:
        inventory = load_inventory(DATA_FILE)
    except (OSError, ValueError, KeyError, TypeError, OverflowError) as error:
        print(f"Cannot load inventory: {error}")
        print("Please fix the inventory file and restart the program.")
        return

    suppliers: dict[str, Supplier] = {
        product.supplier.supplier_id: product.supplier for product in inventory.products}
    orders: dict[str, Order] = {}
    print("Orders are session-only drafts. They do not reserve or reduce stock.")
    while True:
        print("\nInventory Management System")
        print("1. Display all products")
        print("2. Add a product")
        print("3. Update stock")
        print("4. Search for a product")
        print("5. Save inventory")
        print("6. Exit")
        print("7. Remove a product")
        print("8. Create an order")
        print("9. Add a product to an order")
        print("10. Display an order and total")
        print("11. Remove an order line")
        print("12. Cancel an order")
        choice = input("Enter your choice: ").strip()

        try:
            if choice == "1":
                inventory.display_all()
            elif choice == "2":
                product_type = input("Product type (1 = physical, 2 = digital): ").strip()
                if product_type not in ("1", "2"):
                    raise ValueError("Choose 1 for physical or 2 for digital.")
                product_id = inventory.generate_product_id()
                print(f"Product ID: {product_id}")
                name = input("Product name: ")
                price = float(input("Price: "))
                stock = int(input("Stock: "))
                supplier = choose_supplier(suppliers)
                if product_type == "1":
                    weight = float(input("Weight (kg): "))
                    product = PhysicalProduct(product_id, name, price, stock, weight, supplier)
                else:
                    download_size = float(input("Download size (MB): "))
                    product = DigitalProduct(product_id, name, price, stock, download_size, supplier)
                inventory.add_product(product)
                print("Product added successfully!")
            elif choice == "3":
                product_id = input("Product ID: ")
                quantity = int(input("New stock quantity: "))
                inventory.update_stock(product_id, quantity)
                print("Stock updated successfully!")
            elif choice == "4":
                product = inventory.search_product(input("Product ID: "))
                if product is None:
                    print("Product not found.")
                else:
                    product.display_information()
            elif choice == "5":
                save_inventory(inventory, DATA_FILE)
                print("Inventory saved.")
            elif choice == "6":
                print("Saving inventory before exit...")
                save_inventory(inventory, DATA_FILE)
                print("Thank you for using Inventory Management System.")
                break
            elif choice == "7":
                removed = inventory.remove_product(input("Product ID: "))
                print(f"Removed {removed.name} from inventory. Existing order references remain valid.")
            elif choice == "8":
                order = Order(input("Order ID: "))
                if order.order_id in orders:
                    raise ValueError("An order with this ID already exists.")
                orders[order.order_id] = order
                print("Order created.")
            elif choice in ("9", "10", "11", "12"):
                order_id = input("Order ID: ").strip().upper()
                order = orders.get(order_id)
                if order is None:
                    raise ValueError("Order not found.")
                if choice == "9":
                    product = inventory.find_product(input("Product ID: "))
                    if product is None:
                        raise ValueError("Product not found.")
                    order.add_order_line(product, int(input("Quantity: ")))
                    print("Order line added.")
                elif choice == "10":
                    order.display_information()
                elif choice == "11":
                    order.display_information()
                    order.remove_order_line(int(input("Line number: ")))
                    print("Order line removed.")
                else:
                    order.cancel()
                    print("Order cancelled and its lines removed.")
            else:
                print("Please enter a choice from 1 to 12.")
        except (ValueError, OSError, OverflowError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nProgram closed. Unsaved changes were not saved.")
