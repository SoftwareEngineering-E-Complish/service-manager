import unittest
from unittest.mock import patch

from httpx import Response
from fastapi import HTTPException
from app.utils import get_data_from_llm, _reverse_proxy, _reverse_auth_proxy
from starlette.requests import Request

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
        request = Request(scope={
            "type": "http",
            "method": "POST",
            "headers": [(b"authorization", b"Bearer token")],
            "path": "/api",
            "query_string": b"",
            "root_path": "",
            "client": ("127.0.0.1", 12345),
            "server": ("example.com", 443),
            "scheme": "https",
        })

        # Call the method with the sample request
        response = await _reverse_proxy("backend-service", request)

        # Assert the returned values
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content, b"Error")
        self.assertEqual(response.headers["Content-Type"], "text/plain")


    @patch("app.utils.httpx.get")
    async def test_reverse_auth_proxy_valid_token(self, mock_get):
        # Mock the response from the token verification endpoint
        mock_get.return_value.text = "true"

        # Create a sample request with a valid token
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "headers": [(b"authorization", b"Bearer valid_token")],
            "path": "/api",
            "query_string": b"",
            "root_path": "",
            "client": ("127.0.0.1", 12345),
            "server": ("example.com", 443),
            "scheme": "https",
        })

        # Call the method with the sample request
        response = await _reverse_auth_proxy("backend-service", request)

        # Assert the returned values
        self.assertEqual(response.status_code, 200)
        # Add more assertions here based on the expected behavior of _reverse_auth_proxy


    @patch("app.utils.httpx.get")
    async def test_reverse_auth_proxy_invalid_token(self, mock_get):
        # Mock the response from the token verification endpoint
        mock_get.return_value.text = "false"

        # Create a sample request with an invalid token
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "headers": [(b"authorization", b"Bearer invalid_token")],
            "path": "/api",
            "query_string": b"",
            "root_path": "",
            "client": ("127.0.0.1", 12345),
            "server": ("example.com", 443),
            "scheme": "https",
        })

        # Call the method with the sample request and assert that it raises an HTTPException
        with self.assertRaises(HTTPException) as context:
            await _reverse_auth_proxy("backend-service", request)

        # Assert the status code and detail message of the raised exception
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Invalid authorization token.")


    @patch("app.utils.httpx.get")
    async def test_reverse_auth_proxy_missing_token(self, mock_get):
        # Create a sample request without an authorization token
        request = Request(scope={
            "type": "http",
            "method": "GET",
            "headers": [(b"authorization", b"Bearer token")],
            "path": "/api",
            "query_string": b"",
            "root_path": "",
            "client": ("127.0.0.1", 12345),
            "server": ("example.com", 443),
            "scheme": "https",
        })

        # Call the method with the sample request and assert that it raises an HTTPException
        with self.assertRaises(HTTPException) as context:
            await _reverse_auth_proxy("backend-service", request)

        # Assert the status code and detail message of the raised exception
        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Request does not contain authorization token.")


if __name__ == "__main__":
    unittest.main()
