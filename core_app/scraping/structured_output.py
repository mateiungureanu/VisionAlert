OFFER_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "scraped_offer",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "terms": {"type": "string"},
                "products": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "previous_price": {"type": ["string", "null"]},
                "price": {"type": ["string", "null"]},
                "discount_percentage": {"type": ["number", "null"]},
                "valid_from": {"type": ["string", "null"]},
                "valid_until": {"type": ["string", "null"]},
            },
            "required": [
                "title",
                "description",
                "terms",
                "products",
                "previous_price",
                "price",
                "discount_percentage",
                "valid_from",
                "valid_until",
            ],
            "additionalProperties": False,
        },
    },
}
