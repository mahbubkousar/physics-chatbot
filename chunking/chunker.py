# chunking/chunker.py
from .markdown_chunker import MarkdownChunker

def chunk_markdown_file(
    input_file: str,
    output_file: str,
    max_chunk_size: int = 1024,
    overlap_size: int = 200,
    min_chunk_size: int = 100,  # Added minimum chunk size parameter
    output_format: str = "jsonl"
) -> bool:
    """
    Chunk a markdown file using the hybrid semantic chunking approach.
    
    Args:
        input_file: Path to the markdown file
        output_file: Path to save the chunked output
        max_chunk_size: Maximum size of each chunk in tokens
        overlap_size: Number of tokens to overlap between chunks
        min_chunk_size: Minimum size for a chunk (smaller chunks will be merged)
        output_format: Format to save chunks ('jsonl', 'csv', 'json')
        
    Returns:
        bool: True if chunking was successful, False otherwise
    """
    chunker = MarkdownChunker(
        input_file=input_file,
        max_chunk_size=max_chunk_size,
        overlap_size=overlap_size,
        min_chunk_size=int(min_chunk_size),
        output_format=output_format
    )
    
    # Process the markdown file
    chunks = chunker.process()
    
    if not chunks:
        return False
    
    # Save the chunks
    return chunker.save_chunks(output_file)