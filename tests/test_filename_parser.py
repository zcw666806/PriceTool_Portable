import unittest

from src.filename_parser import parse_pdf_filename


class FilenameParserTest(unittest.TestCase):
    def test_standard_name(self):
        parsed = parse_pdf_filename("ATH Price Alba 7286_2026.2 USD.pdf")
        self.assertEqual(parsed["supplier"], "ATH")
        self.assertEqual(parsed["product_name"], "Alba")
        self.assertEqual(parsed["product_codes"], ["7286"])
        self.assertEqual(parsed["version"], "2026.2")
        self.assertEqual(parsed["currency"], "USD")
        self.assertFalse(parsed["needs_review"])

    def test_code_range(self):
        parsed = parse_pdf_filename("ATH Price Atlantis 7112-7162_2026.2 USD.pdf")
        self.assertEqual(parsed["product_name"], "Atlantis")
        self.assertEqual(parsed["product_code_raw"], "7112-7162")
        self.assertEqual(parsed["product_codes"], ["7112", "7162"])

    def test_missing_code(self):
        parsed = parse_pdf_filename("HYD Price Lounge Chairs_2026.1 USD.pdf")
        self.assertEqual(parsed["supplier"], "HYD")
        self.assertEqual(parsed["product_name"], "Lounge Chairs")
        self.assertEqual(parsed["product_codes"], [])
        self.assertTrue(parsed["needs_review"])


if __name__ == "__main__":
    unittest.main()
