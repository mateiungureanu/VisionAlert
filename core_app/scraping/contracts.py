from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

@dataclass
class ScrapedOffer:
    title: str
    source_url: str
    products: list[str] = field(default_factory=list)
    description: str = ""
    terms: str = ""
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    category_names: list[str] = field(default_factory=list)
    image_url: str | None = None
    price: str | None = None
    previous_price: str | None = None
    discount_percentage: Decimal | None = None