"""Unit tests for document loading and ingestion."""

import unittest
from pathlib import Path
from core.ingestion.loader import DocumentLoader, Document

class TestDocumentLoader(unittest.TestCase):
    def setUp(self):
        self.loader = DocumentLoader()

    def test_clean_text(self):
        dirty = "Cardio- \nvascular disease\r\nis a major\n\n\n\nrisk factor.  "
        cleaned = self.loader.clean_text(dirty)
        self.assertIn("Cardiovascular", cleaned)
        self.assertNotIn("\r", cleaned)
        self.assertNotIn("\n\n\n", cleaned)

    def test_load_text_file(self):
        test_path = Path("/home/prak05/MediScribe/materials/sample_data/clinical_guidelines_sample.md")
        if test_path.exists():
            docs = self.loader.load_file(test_path)
            self.assertGreater(len(docs), 0)
            self.assertEqual(docs[0].source, "clinical_guidelines_sample.md")
            self.assertIn("Diabetic Ketoacidosis", docs[0].text)

if __name__ == "__main__":
    unittest.main()
