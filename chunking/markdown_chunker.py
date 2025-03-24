import re
import json
import os
import csv
from typing import List, Dict, Tuple, Any
import hashlib

class MarkdownChunker:
    def __init__(
        self, 
        input_file: str,
        max_chunk_size: int = 1024,
        overlap_size: int = 200,
        output_format: str = "jsonl"
    ):
        """
        Initialize the chunker with settings for processing a markdown file.
        
        Args:
            input_file: Path to the markdown file
            max_chunk_size: Maximum size of each chunk in tokens (approx)
            overlap_size: Number of tokens to overlap between chunks
            output_format: Format to save chunks ('jsonl', 'csv', 'json')
        """
        self.input_file = input_file
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.output_format = output_format
        self.content = ""
        self.chunks = []
        
    def load_markdown(self) -> bool:
        """Load the markdown content from file."""
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                self.content = file.read()
            return True
        except Exception as e:
            print(f"Error loading markdown file: {e}")
            return False
    
    def is_formula(self, text: str) -> bool:
        """Check if text contains LaTeX formula."""
        # Basic check for LaTeX delimiters
        formula_patterns = [
            r'\$\$.*?\$\$',  # Display math: $$...$$
            r'\$.*?\$',      # Inline math: $...$
            r'\\begin\{equation\}.*?\\end\{equation\}',  # equation environment
            r'\\begin\{align\}.*?\\end\{align\}'         # align environment
        ]
        
        for pattern in formula_patterns:
            if re.search(pattern, text, re.DOTALL):
                return True
        return False
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in text."""
        # Simple estimation: 1 token ≈ 4 characters for English text
        # This is a rough approximation - for production, use the tokenizer
        # from your actual embedding model
        return len(text) // 4
    
    def extract_heading_structure(self) -> List[Dict[str, Any]]:
        """Extract the heading structure from markdown."""
        # Pattern to match headings in markdown
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        # Find all headings with their positions
        headings = []
        for match in heading_pattern.finditer(self.content):
            level = len(match.group(1))  # Number of # characters
            title = match.group(2).strip()
            position = match.start()
            headings.append({
                'level': level,
                'title': title,
                'position': position
            })
        
        # Add document end as the final position
        headings.append({
            'level': 0,
            'title': 'END',
            'position': len(self.content)
        })
        
        return headings
    
    def create_semantic_chunks(self) -> List[Dict[str, Any]]:
        """Create chunks based on heading structure with size constraints."""
        if not self.content:
            if not self.load_markdown():
                return []
        
        # Extract heading structure
        headings = self.extract_heading_structure()
        
        # Generate initial chunks based on headings
        initial_chunks = []
        
        for i in range(len(headings) - 1):
            current = headings[i]
            next_heading = headings[i + 1]
            
            # Extract content between current heading and next heading
            start_pos = current['position']
            end_pos = next_heading['position']
            chunk_content = self.content[start_pos:end_pos]
            
            # Build heading path (breadcrumb)
            path = []
            for h in headings[:i+1]:
                if h['level'] > 0:  # Skip the END marker
                    path.append(h['title'])
            
            # Create chunk
            chunk = {
                'content': chunk_content,
                'heading': current['title'] if current['level'] > 0 else "Document Start",
                'level': current['level'],
                'path': " > ".join(path),
                'token_count': self.estimate_tokens(chunk_content)
            }
            
            initial_chunks.append(chunk)
        
        # Further process chunks that exceed max size
        final_chunks = []
        for chunk in initial_chunks:
            if chunk['token_count'] <= self.max_chunk_size:
                # Add chunk ID
                chunk['id'] = self._generate_chunk_id(chunk['content'])
                final_chunks.append(chunk)
            else:
                # Split large chunks with overlap
                sub_chunks = self._split_large_chunk(chunk)
                final_chunks.extend(sub_chunks)
        
        return final_chunks
    
    def _generate_chunk_id(self, content: str) -> str:
        """Generate a unique ID for a chunk based on its content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    
    def _split_large_chunk(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split large chunks into smaller ones with overlap."""
        content = chunk['content']
        token_count = chunk['token_count']
        path = chunk['path']
        heading = chunk['heading']
        level = chunk['level']
        
        # If it contains formulas, try to split at paragraph boundaries
        paragraphs = re.split(r'\n\s*\n', content)
        
        sub_chunks = []
        current_chunk_text = ""
        current_token_count = 0
        
        for i, para in enumerate(paragraphs):
            para_token_count = self.estimate_tokens(para)
            
            # If adding this paragraph exceeds max size and we already have content,
            # save current chunk and start a new one with overlap
            if current_token_count + para_token_count > self.max_chunk_size and current_chunk_text:
                # Create and add the chunk
                sub_chunk = {
                    'content': current_chunk_text,
                    'heading': heading,
                    'level': level,
                    'path': path,
                    'token_count': current_token_count,
                    'id': self._generate_chunk_id(current_chunk_text),
                    'chunk_type': 'sub_chunk'
                }
                sub_chunks.append(sub_chunk)
                
                # Create overlap by including previous text up to overlap_size
                overlap_text = self._get_overlap_text(current_chunk_text)
                current_chunk_text = overlap_text + para
                current_token_count = self.estimate_tokens(current_chunk_text)
            else:
                # Add paragraph to current chunk
                if current_chunk_text:
                    current_chunk_text += "\n\n" + para
                else:
                    current_chunk_text = para
                current_token_count += para_token_count
        
        # Add the last sub-chunk if there's content left
        if current_chunk_text:
            sub_chunk = {
                'content': current_chunk_text,
                'heading': heading,
                'level': level,
                'path': path,
                'token_count': current_token_count,
                'id': self._generate_chunk_id(current_chunk_text),
                'chunk_type': 'sub_chunk'
            }
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get text for overlap from the end of a chunk."""
        # Special handling for formulas
        if self.is_formula(text):
            # If there's a formula near the end, include the whole formula
            formula_matches = list(re.finditer(r'\$\$.*?\$\$|\$.*?\$|\\begin\{.*?\}.*?\\end\{.*?\}', text, re.DOTALL))
            if formula_matches:
                last_formula = formula_matches[-1]
                formula_end = last_formula.end()
                # If formula is near the end, include everything after the last formula start
                if formula_end > len(text) - self.overlap_size:
                    return text[last_formula.start():]
        
        # Default: get last N tokens of text (approximated as characters)
        char_overlap = self.overlap_size * 4  # Rough estimate: 1 token ≈ 4 chars
        if len(text) <= char_overlap:
            return text
        return text[-char_overlap:]
    
    def process(self) -> List[Dict[str, Any]]:
        """Process the markdown file and create chunks."""
        # Create chunks
        self.chunks = self.create_semantic_chunks()
        return self.chunks
    
    def save_chunks(self, output_file: str) -> bool:
        """Save chunks to the specified output format."""
        try:
            if self.output_format == 'jsonl':
                with open(output_file, 'w', encoding='utf-8') as f:
                    for chunk in self.chunks:
                        f.write(json.dumps(chunk) + '\n')
            
            elif self.output_format == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(self.chunks, f, indent=2)
            
            elif self.output_format == 'csv':
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    # Create a minimal version for CSV (content and metadata)
                    fieldnames = ['id', 'heading', 'path', 'token_count', 'content']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for chunk in self.chunks:
                        writer.writerow({field: chunk.get(field, '') for field in fieldnames})
            
            return True
        except Exception as e:
            print(f"Error saving chunks: {e}")
            return False