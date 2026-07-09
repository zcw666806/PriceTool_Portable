import unittest

from src.normalizer import normalize_size


class SizeMappingTest(unittest.TestCase):
    def test_common_sizes(self):
        self.assertEqual(normalize_size("1 SEATER")["size"], "1S")
        self.assertEqual(normalize_size("2-Seater")["size"], "2S")
        self.assertEqual(normalize_size("FOOTSTOOL")["size"], "FOOTSTOOL")
        self.assertEqual(normalize_size("LHF/RHF SINGLE ARM")["size"], "LHF/RHF SINGLE ARM")


if __name__ == "__main__":
    unittest.main()
