import unittest
from pathlib import Path

from src.pdf_table_extractor import scan_pdf_folder


class PdfScanTest(unittest.TestCase):
    def test_current_sample_folder_has_expected_pdfs(self):
        folder = Path(__file__).resolve().parents[1] / "test_pdf_folder"
        if not folder.exists():
            self.skipTest("Sample PDF folder not present")
        self.assertEqual(len(scan_pdf_folder(folder)), 33)


if __name__ == "__main__":
    unittest.main()
