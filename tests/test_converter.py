import unittest
import os
from pdf2md.pdf_to_md import PdfToMarkdownConverter

class TestPdfToMarkdownConverter(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.test_pdf = "resources/book.pdf"
        self.test_md = "resources/book.md"
        self.invalid_pdf = "resources/nonexistent.pdf"
        
        # Check if a real test PDF exists
        self.has_test_pdf = os.path.exists(self.test_pdf) and os.path.getsize(self.test_pdf) > 0
        
        # Clean up output file if it exists
        if os.path.exists(self.test_md):
            os.remove(self.test_md)

    def tearDown(self):
        """Clean up after each test."""
        if os.path.exists(self.test_md):
            os.remove(self.test_md)

    @unittest.skipUnless(os.path.exists("resources/book.pdf"), "Test PDF not found; skipping file-based test")
    def test_successful_conversion(self):
        """Test that a valid PDF is converted to Markdown successfully."""
        converter = PdfToMarkdownConverter(self.test_pdf, self.test_md)
        result = converter.convert()
        self.assertTrue(result, "Conversion should return True on success")
        self.assertTrue(os.path.exists(self.test_md), "Markdown file should be created")
        
        with open(self.test_md, 'r', encoding='utf-8') as md_file:
            content = md_file.read()
            self.assertIn("# Converted PDF Book", content, "Markdown should have title")
            self.assertIn("## Page 1", content, "Markdown should have page heading")

    def test_missing_pdf(self):
        """Test that conversion fails gracefully with a missing PDF."""
        converter = PdfToMarkdownConverter(self.invalid_pdf, self.test_md)
        result = converter.convert()
        self.assertFalse(result, "Conversion should return False for missing PDF")
        self.assertFalse(os.path.exists(self.test_md), "No Markdown file should be created")

    def test_heading_detection(self):
        """Test the is_heading method for correct identification."""
        converter = PdfToMarkdownConverter(self.test_pdf, self.test_md)
        self.assertTrue(converter.is_heading("INTRODUCTION", ""), "All caps should be a heading")
        self.assertTrue(converter.is_heading("Short Title", ""), "Short text after empty line should be a heading")
        self.assertFalse(converter.is_heading("This is a very long sentence that should not be a heading because it exceeds the length limit", ""), "Long text should not be a heading")
        self.assertFalse(converter.is_heading("Normal text", "Previous text"), "Regular text should not be a heading")

    def test_formula_formatting(self):
        """Test the format_formula method for correct Markdown math wrapping."""
        converter = PdfToMarkdownConverter(self.test_pdf, self.test_md)
        self.assertEqual(converter.format_formula("x^2 + y^2"), "$x^2 + y^2$", "Formula should be wrapped in $")
        self.assertEqual(converter.format_formula("sqrt(x)"), "$sqrt(x)$", "Square root should be wrapped in $")
        self.assertEqual(converter.format_formula("a/b"), "$a/b$", "Fraction should be wrapped in $")
        self.assertEqual(converter.format_formula("Plain text"), "Plain text", "Non-formula text should remain unchanged")

if __name__ == "__main__":
    unittest.main()