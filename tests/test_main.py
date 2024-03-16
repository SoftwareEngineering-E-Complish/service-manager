import unittest
from unittest.mock import patch

from app.main import list_properties
from app.models import LLMQuery

from fastapi import HTTPException


class TestApp(unittest.IsolatedAsyncioTestCase):
    @patch("app.main.fetch_json")
    @patch("app.main.get_data_from_llm")
    async def test_list_properties_success(self, mock_get_data_from_llm, mock_fetch_json):
        # Mock the fetch_json and get_data_from_llm functions
        mock_fetch_json.return_value = {"param1": "value1", "param2": "value2"}
        mock_get_data_from_llm.return_value = (
            200,
            LLMQuery(content='{"param1": "value1", "param2": "value2"}'),
        )

        # Call the list_properties function
        result = await list_properties("user_query")

        # Assert the returned value
        self.assertEqual(result, {"param1": "value1", "param2": "value2"})

    @patch("app.main.fetch_json")
    @patch("app.main.get_data_from_llm")
    async def test_list_properties_inventory_service_error(
        self, mock_get_data_from_llm, mock_fetch_json
    ):
        # Mock the fetch_json and get_data_from_llm functions
        mock_fetch_json.return_value = None
        mock_get_data_from_llm.return_value = (
            200,
            LLMQuery(content='{"param1": "value1", "param2": "value2"}'),
        )

        # Call the list_properties function and expect an exception
        with self.assertRaises(HTTPException) as cm:
            await list_properties("user_query")

        # Assert the exception status code and detail
        self.assertEqual(cm.exception.status_code, 500)
        self.assertEqual(
            cm.exception.detail,
            "Something went wrong with the inventory service. Initial request failed.",
        )

    @patch("app.main.fetch_json")
    @patch("app.main.get_data_from_llm")
    async def test_list_properties_llm_service_error(
        self, mock_get_data_from_llm, mock_fetch_json
    ):
        # Mock the fetch_json and get_data_from_llm functions
        mock_fetch_json.return_value = {"param1": "value1", "param2": "value2"}
        mock_get_data_from_llm.return_value = (500, None)

        # Call the list_properties function and expect an exception
        with self.assertRaises(HTTPException) as cm:
            await list_properties("user_query")

        # Assert the exception status code and detail
        self.assertEqual(cm.exception.status_code, 500)
        self.assertEqual(
            cm.exception.detail, "Something went wrong with the LLM service."
        )


if __name__ == "__main__":
    unittest.main()
