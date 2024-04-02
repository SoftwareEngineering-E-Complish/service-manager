import unittest
from unittest.mock import patch

from httpx import Response, Request
from app.utils import get_data_from_llm, _reverse_proxy

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

    
    @patch("app.utils.httpx.AsyncClient")
    async def test_reverse_proxy_success(self, mock_client):
        # Mock the response from the reverse proxy
        mock_resp = Response(
            content=b"Response Content",
            status_code=200,
            headers={"Content-Type": "application/json"},
        )
        mock_send = mock_client.return_value.send
        mock_send.return_value = mock_resp

        # Create a sample request
        request = Request("GET", "https://example.com/api", headers={"Authorization": "Bearer token"})

        # Call the method with the sample request
        response = await _reverse_proxy("backend-service", request)

        # Assert the returned values
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Response Content")
        self.assertEqual(response.headers["Content-Type"], "application/json")


    @patch("app.utils.httpx.AsyncClient")
    async def test_reverse_proxy_failure(self, mock_client):
        # Mock the response from the reverse proxy
        mock_resp = Response(
            content=b"Error",
            status_code=500,
            headers={"Content-Type": "text/plain"},
        )
        mock_send = mock_client.return_value.send
        mock_send.return_value = mock_resp

        # Create a sample request
        request = Request("POST", "https://example.com/api", headers={"Authorization": "Bearer token"})

        # Call the method with the sample request
        response = await _reverse_proxy("backend-service", request)

        # Assert the returned values
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Error")
        self.assertEqual(response.headers["Content-Type"], "text/plain")


if __name__ == "__main__":
    unittest.main()
