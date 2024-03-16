import unittest
from unittest.mock import patch

from app.utils import get_data_from_llm


class TestUtils(unittest.TestCase):
    @patch("app.utils.httpx.post")
    def test_get_data_from_llm_success(self, mock_post):
        # Mock the response from the endpoint
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "propertyId": 1,
            "title": "Luxury Apartment in Zurich",
            "description": "This is a luxury apartment located in the heart of Zurich.",
            "price": 2000000,
            "location": "Zurich",
            "bedrooms": 3,
            "bathrooms": 2,
            "square_meters": 100,
            "year_built": 2000,
            "property_type": "Apartment",
            "done": True,
        }

        # Call the method with sample data
        endpoint = "https://example.com/llm"
        data = {"param1": "value1", "param2": "value2"}
        status_code, llm_query = get_data_from_llm(endpoint, data)

        # Assert the returned values
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(llm_query)
        self.assertEqual(llm_query.propertyId, 1)
        self.assertEqual(llm_query.title, "Luxury Apartment in Zurich")
        self.assertEqual(
            llm_query.description,
            "This is a luxury apartment located in the heart of Zurich.",
        )
        self.assertEqual(llm_query.price, 2000000)
        self.assertEqual(llm_query.location, "Zurich")
        self.assertEqual(llm_query.bedrooms, 3)
        self.assertEqual(llm_query.bathrooms, 2)
        self.assertEqual(llm_query.square_meters, 100)
        self.assertEqual(llm_query.year_built, 2000)
        self.assertEqual(llm_query.property_type, "Apartment")
        self.assertEqual(llm_query.done, True)

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
