from unittest.mock import patch

import requests
from django.test import SimpleTestCase

from core_app.scraping.scrapers.cinemacity import (
    LMStudioUnavailableError,
    _extract_offer_with_llm,
)
from core_app.scraping.structured_output import OFFER_RESPONSE_FORMAT


class CinemaCityLLMTests(SimpleTestCase):
    @patch.dict(
        "os.environ",
        {
            "LM_STUDIO_BASE_URL": "http://localhost:1235/v1",
            "LM_STUDIO_MODEL": "qwen3.5-9b",
        },
    )
    @patch("core_app.scraping.scrapers.cinemacity.requests.post")
    def test_connection_error_explains_how_to_start_lm_studio(self, post):
        post.side_effect = requests.ConnectionError("connection refused")

        with self.assertRaisesRegex(
            LMStudioUnavailableError,
            "Start its local server and load the configured model",
        ):
            _extract_offer_with_llm(
                "Offer text",
                "https://www.cinemacity.ro/offers/example",
                "Listing title",
                "Page title",
            )

        self.assertEqual(
            post.call_args.args[0],
            "http://localhost:1235/v1/chat/completions",
        )
        self.assertEqual(post.call_args.kwargs["json"]["model"], "qwen3.5-9b")
        self.assertEqual(
            post.call_args.kwargs["json"]["response_format"],
            OFFER_RESPONSE_FORMAT,
        )
        self.assertEqual(
            OFFER_RESPONSE_FORMAT["type"],
            "json_schema",
        )
        properties = OFFER_RESPONSE_FORMAT["json_schema"]["schema"]["properties"]
        self.assertEqual(properties["previous_price"], {"type": ["string", "null"]})
        self.assertEqual(properties["price"], {"type": ["string", "null"]})
        self.assertEqual(
            properties["discount_percentage"],
            {"type": ["number", "null"]},
        )
