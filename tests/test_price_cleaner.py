import unittest

from src.price_cleaner import clean_price


class PriceCleanerTest(unittest.TestCase):
    def test_split_digits(self):
        self.assertEqual(clean_price("8 65")["price"], 865)
        self.assertEqual(clean_price("6 90")["price"], 690)

    def test_comma_with_spaces(self):
        self.assertEqual(clean_price("1 ,005")["price"], 1005)
        self.assertEqual(clean_price("1 ,100")["price"], 1100)

    def test_blank(self):
        result = clean_price("-")
        self.assertIsNone(result["price"])
        self.assertTrue(result["needs_review"])

    def test_out_of_range(self):
        result = clean_price("50")
        self.assertEqual(result["price"], 50)
        self.assertTrue(result["needs_review"])


if __name__ == "__main__":
    unittest.main()
