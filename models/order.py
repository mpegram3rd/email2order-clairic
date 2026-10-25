import datetime
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, date


@dataclass
class Item:
    id: str
    name: str
    quantity: int
    price: float


@dataclass
class Order:
    contact_name: str | None
    contact_phone: str | None
    company: str | None
    attention: str | None
    street_address: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    delivery_date: date | None
    items: List[Item] = field(default_factory=list)

    @classmethod
    def extract_value(cls, data: dict) -> str | None:
        """
        Extracts the value from the given data dictionary first checking
        the "value" field.  If not found in the value field, the guess field is checked.
        If the confidence is greater than 0.5, the guess is returned.

        :param data: The data dictionary containing the value and confidence information.
        :return: The extracted value if available, otherwise None.
        """
        value = None
        if data["value"]:
            value = data["value"]
        elif data["guess"] and data["confidence"] > 0.5:
            value = data["guess"]
        return value

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        new_order = cls(
            contact_name=cls.extract_value(data["contact_name"]),
            contact_phone=cls.extract_value(data["contact_phone"]),
            company=cls.extract_value(data["recipient_company"]),
            attention=cls.extract_value(data["recipient_attention"]),
            street_address=cls.extract_value(data["recipient_street_address"]),
            city=cls.extract_value(data["recipient_city"]),
            state=cls.extract_value(data["recipient_state"]),
            zip_code=cls.extract_value(data["recipient_zip_code"]),
            delivery_date=None
        )
        raw_value = cls.extract_value(data["expected_delivery_date"])
        if raw_value is not None:
            new_order.delivery_date = datetime.strptime(raw_value,  "%Y-%m-%d").date()

        return new_order

