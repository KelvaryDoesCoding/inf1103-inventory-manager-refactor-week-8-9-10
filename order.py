"""An Order owns its lines, but does not own or consume inventory products."""

import math
from order_line import OrderLine
from product import Product


class Order:
    def __init__(self, order_id: str) -> None:
        if not isinstance(order_id, str) or not order_id.strip():
            raise ValueError("Order ID cannot be empty.")
        self.__order_id: str = order_id.strip().upper()
        self.__order_lines: list[OrderLine] = []
        self.__cancelled: bool = False

    @property
    def order_id(self) -> str:
        return self.__order_id

    @property
    def order_lines(self) -> tuple[OrderLine, ...]:
        return tuple(self.__order_lines)

    @property
    def cancelled(self) -> bool:
        return self.__cancelled

    def add_order_line(self, product: Product, quantity: int) -> None:
        if self.cancelled:
            raise ValueError("Cannot add lines to a cancelled order.")
        line = OrderLine(product, quantity)
        total = self.calculate_total() + line.calculate_subtotal()
        if not math.isfinite(total):
            raise ValueError("Order total is too large.")
        self.__order_lines.append(line)

    def remove_order_line(self, line_number: int) -> None:
        """Use the one-based number displayed by display_information()."""
        if type(line_number) is not int or not 1 <= line_number <= len(self.__order_lines):
            raise ValueError("Order line number does not exist.")
        del self.__order_lines[line_number - 1]

    def cancel(self) -> None:
        self.__order_lines.clear()
        self.__cancelled = True

    def calculate_total(self) -> float:
        return sum((line.calculate_subtotal() for line in self.__order_lines), 0.0)

    def display_information(self) -> None:
        print(f"Order {self.order_id}" + (" (cancelled)" if self.cancelled else ""))
        for number, line in enumerate(self.__order_lines, 1):
            print(f"{number}. {line.product.product_id} {line.product.name} | "
                  f"Quantity: {line.quantity} | Subtotal: ${line.calculate_subtotal():.2f}")
        print(f"Total: ${self.calculate_total():.2f}")
