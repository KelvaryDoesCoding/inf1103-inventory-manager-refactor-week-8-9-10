"""A supplier exists independently of the products it supplies."""


class Supplier:
    def __init__(self, supplier_id: str, name: str, contact_email: str) -> None:
        for value in (supplier_id, name, contact_email):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Supplier ID, name and contact email cannot be empty.")
        self.__supplier_id: str = supplier_id.strip().upper()
        self.__name: str = name.strip()
        self.__contact_email: str = contact_email.strip()

    @property
    def supplier_id(self) -> str:
        return self.__supplier_id

    @property
    def name(self) -> str:
        return self.__name

    @property
    def contact_email(self) -> str:
        return self.__contact_email

    def display_information(self) -> None:
        print(f"Supplier: {self.supplier_id} | {self.name} | {self.contact_email}")
