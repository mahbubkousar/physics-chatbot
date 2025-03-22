from pdf2md.pdf_to_md import PdfToMarkdownConverter

def run_project():
    print("Physics Chatbot Project")
    print("-----------------------")

    # Convert PDF to Markdown
    pdf_path = "resources/book.pdf"
    md_path = "resources/book.md"
    pdf_converter = PdfToMarkdownConverter(pdf_path, md_path)
    if pdf_converter.convert():
        print("PDF to Markdown task completed successfully!")
    else:
        print("PDF to Markdown task failed!")
        return  


    print("Project completed!")

if __name__ == "__main__":
    run_project()