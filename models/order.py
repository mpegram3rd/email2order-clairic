import datetime
from dataclasses import dataclass, field
from typing import List
from datetime import date


@dataclass
class Item:
    id: str
    name: str
    quantity: int
    price: float


@dataclass
class Order:
    contact_name: str
    contact_phone: str
    company: str
    attention: str
    street_address: str
    city: str
    state: str
    zip_code: str
    delivery_date: date
    items: List[Item] = field(default_factory=list)

