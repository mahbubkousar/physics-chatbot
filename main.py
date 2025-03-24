import os
from pdf2md.pdf_to_md import PdfToMarkdownConverter
from chunking.chunker import chunk_markdown_file

def run_project():
    print("Physics Chatbot Project")
    print("-----------------------")

    # File paths
    pdf_path = "resources/book.pdf"
    md_path = "resources/book.md"
    chunks_path = "resources/chunks.jsonl"
    
    # Step 1: PDF to Markdown conversion
    if os.path.exists(md_path):
        print("Markdown file already exists. Skipping conversion.")
    else:
        print("Converting PDF to Markdown...")
        pdf_converter = PdfToMarkdownConverter(pdf_path, md_path)
        if pdf_converter.convert():
            print("PDF to Markdown task completed successfully!")
        else:
            print("PDF to Markdown task failed!")
            return
    
    # Step 2: Chunk the markdown file
    if os.path.exists(chunks_path):
        print("Chunks file already exists. Skipping chunking.")
    else:
        print("Chunking Markdown file...")
        # Set parameters for chunking
        max_chunk_size = 1024  # ~1024 tokens max per chunk
        overlap_size = 200     # ~200 tokens overlap
        min_chunk_size = 100   # ~100 tokens minimum per chunk
        output_format = "jsonl"  # JSONL format for chunks
        
        if chunk_markdown_file(
            input_file=md_path,
            output_file=chunks_path,
            max_chunk_size=max_chunk_size,
            overlap_size=overlap_size,
            min_chunk_size=min_chunk_size,
            output_format=output_format
        ):
            print("Markdown chunking completed successfully!")
        else:
            print("Markdown chunking failed!")
            return

    print("Project completed!")

if __name__ == "__main__":
    run_project()