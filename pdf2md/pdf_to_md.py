import pdfplumber
import re
import os
from tqdm import tqdm

class PdfToMarkdownConverter:
    def __init__(self, pdf_path, output_md_path):
        self.pdf_path = pdf_path
        self.output_md_path = output_md_path

    def is_heading(self, text, prev_text=""):
        text = text.strip()
        if not text or len(text) > 100:
            return False
        if text.isupper() or (prev_text.strip() == "" and len(text) < 50):
            return True
        return False

    def format_formula(self, text):
        formula_pattern = r'(\b\w+\^\d+|\bsqrt\(.+?\)|[\w\d]+/[\/\w\d]+)'
        if re.search(formula_pattern, text):
            return f"${text}$"
        return text

    def convert(self):
        try:
            if not os.path.exists(self.pdf_path):
                raise FileNotFoundError(f"PDF file '{self.pdf_path}' not found!")

            markdown_content = "# Converted PDF Book\n\n"
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                prev_text = ""

                with tqdm(total=total_pages, desc="Converting PDF to Markdown", unit="page") as pbar:
                    for page_num, page in enumerate(pdf.pages, 1):
                        text = page.extract_text() or ""
                        lines = text.split("\n")
                        tables = page.extract_tables() or []
                        table_content = ""

                        page_text = f"## Page {page_num}\n\n"
                        for line in lines:
                            line = line.strip()
                            if not line:
                                page_text += "\n"
                                continue
                            if self.is_heading(line, prev_text):
                                page_text += f"### {line}\n\n"
                            else:
                                formatted_line = self.format_formula(line)
                                page_text += f"{formatted_line}  \n"
                            prev_text = line

                        if tables:
                            table_content += "### Tables\n\n"
                            for table in tables:
                                if not table or not table[0]:
                                    continue
                                header = [str(cell or "") for cell in table[0]]
                                table_md = "| " + " | ".join(header) + " |\n"
                                table_md += "| " + " | ".join(["---"] * len(header)) + " |\n"
                                for row in table[1:]:
                                    row = [str(cell or "") for cell in row]
                                    table_md += "| " + " | ".join(row) + " |\n"
                                table_content += table_md + "\n\n"

                        markdown_content += page_text + table_content
                        pbar.update(1)  

            with open(self.output_md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(markdown_content)
            print(f"\nConversion complete! Markdown file saved as: {self.output_md_path}")
            return True
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            return False

if __name__ == "__main__":
    converter = PdfToMarkdownConverter("book.pdf", "book.md")
    converter.convert()