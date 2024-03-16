import unittest

from app.models import LLMQuery


class TestLLMQuery(unittest.TestCase):
    def test_get_parsed_params(self):
        # Create an instance of LLMQuery
        llm_query = LLMQuery(
            content='{"param1": "value1", "param2": "value2", "param3": null}'
        )

        # Call the get_parsed_params method
        parsed_params = llm_query.get_parsed_params()

        # Assert the returned value
        self.assertEqual(parsed_params, {"param1": "value1", "param2": "value2"})

    def test_get_parsed_params_with_empty_content(self):
        # Create an instance of LLMQuery with empty content
        llm_query = LLMQuery(content="{}")

        # Call the get_parsed_params method
        parsed_params = llm_query.get_parsed_params()

        # Assert the returned value
        self.assertEqual(parsed_params, {})

    def test_get_parsed_params_with_none_content(self):
        # Create an instance of LLMQuery with None content
        llm_query = LLMQuery(content='')

        # Call the get_parsed_params method
        parsed_params = llm_query.get_parsed_params()

        # Assert the returned value
        self.assertEqual(parsed_params, {})


if __name__ == "__main__":
    unittest.main()
