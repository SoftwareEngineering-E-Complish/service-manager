import unittest
from unittest.mock import patch

from app.utils import get_data_from_llm


class TestUtils(unittest.TestCase):
    @patch("app.utils.httpx.post")
    def test_get_data_from_llm_success(self, mock_post):
        # Mock the response from the endpoint
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "content": '{"value":"key"}'
        }

        # Call the method with sample data
        endpoint = "https://example.com/llm"
        data = {"param1": "value1", "param2": "value2"}
        status_code, llm_query = get_data_from_llm(endpoint, data)

        # Assert the returned values
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(llm_query)
        self.assertEqual(llm_query.content, '{"value":"key"}')


    @patch("app.utils.httpx.post")
    def test_get_data_from_llm_failure(self, mock_post):
        # Mock the response from the endpoint
        mock_post.return_value.status_code = 404

        # Call the method with sample data
        endpoint = "https://example.com/llm"
        data = {"param1": "value1", "param2": "value2"}
        status_code, llm_query = get_data_from_llm(endpoint, data)

        # Assert the returned values
        self.assertEqual(status_code, 404)
        self.assertIsNone(llm_query)


if __name__ == "__main__":
    unittest.main()
