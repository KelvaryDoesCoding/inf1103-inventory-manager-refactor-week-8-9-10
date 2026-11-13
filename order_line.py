"""An Order creates and owns its lines; each line only refers to a Product."""

import math
from product import Product


class OrderLine:
    def __init__(self, product: Product, quantity: int) -> None:
        if not isinstance(product, Product):
            raise TypeError("Order lines require a Product object.")
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("Order quantity must be a positive whole number.")
        self.__product: Product = product
        self.__quantity: int = quantity
        self.calculate_subtotal()

    @property
    def product(self) -> Product:
        return self.__product

    @property
    def quantity(self) -> int:
        return self.__quantity

    def calculate_subtotal(self) -> float:
        subtotal = self.product.price * self.quantity
        if not math.isfinite(subtotal):
            raise ValueError("Order subtotal is too large.")
        return subtotal
