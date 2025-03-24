import re
import json
import os
import csv
from typing import List, Dict, Tuple, Any
import hashlib

def __init__(
    self, 
    input_file: str,
    max_chunk_size: int = 1024,
    overlap_size: int = 200,
    min_chunk_size: int = 100,
    output_format: str = "jsonl"
):
    """
    Initialize the chunker with settings for processing a markdown file.
    
    Args:
        input_file: Path to the markdown file
        max_chunk_size: Maximum size of each chunk in tokens (approx)
        overlap_size: Number of tokens to overlap between chunks
        min_chunk_size: Minimum size for a chunk (smaller chunks will be merged)
        output_format: Format to save chunks ('jsonl', 'csv', 'json')
    """
    self.input_file = input_file
    self.max_chunk_size = int(max_chunk_size)
    self.overlap_size = int(overlap_size)
    self.min_chunk_size = int(min_chunk_size)
    self.output_format = output_format
    self.content = ""
    self.chunks = []

class MarkdownChunker:
    def __init__(
        self, 
        input_file: str,
        max_chunk_size: int = 1024,
        overlap_size: int = 200,
        min_chunk_size: int = 100,  # Added minimum chunk size parameter
        output_format: str = "jsonl"
    ):
        """
        Initialize the chunker with settings for processing a markdown file.
        
        Args:
            input_file: Path to the markdown file
            max_chunk_size: Maximum size of each chunk in tokens (approx)
            overlap_size: Number of tokens to overlap between chunks
            min_chunk_size: Minimum size for a chunk (smaller chunks will be merged)
            output_format: Format to save chunks ('jsonl', 'csv', 'json')
        """
        self.input_file = input_file
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = int(min_chunk_size)
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
        # Enhanced formula detection patterns
        formula_patterns = [
            r'\$\$[\s\S]*?\$\$',                         # Display math: $$...$$
            r'\$[^$\n]+?\$',                             # Inline math: $...$
            r'\\begin\{equation\}[\s\S]*?\\end\{equation\}',  # equation environment
            r'\\begin\{align\}[\s\S]*?\\end\{align\}',        # align environment
            r'\\begin\{eqnarray\}[\s\S]*?\\end\{eqnarray\}',  # eqnarray environment
            r'\\begin\{gathered\}[\s\S]*?\\end\{gathered\}',  # gathered environment
            r'\\begin\{cases\}[\s\S]*?\\end\{cases\}'         # cases environment
        ]
        
        for pattern in formula_patterns:
            if re.search(pattern, text, re.DOTALL):
                return True
        return False
    
    def extract_formula_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """Extract the start and end positions of all formulas in text."""
        formula_patterns = [
            (r'\$\$([\s\S]*?)\$\$', 0),                             # Display math
            (r'\$([^$\n]+?)\$', 0),                                 # Inline math
            (r'\\begin\{equation\}([\s\S]*?)\\end\{equation\}', 0), # equation
            (r'\\begin\{align\}([\s\S]*?)\\end\{align\}', 0),       # align
            (r'\\begin\{eqnarray\}([\s\S]*?)\\end\{eqnarray\}', 0), # eqnarray
            (r'\\begin\{gathered\}([\s\S]*?)\\end\{gathered\}', 0), # gathered
            (r'\\begin\{cases\}([\s\S]*?)\\end\{cases\}', 0)        # cases
        ]
        
        boundaries = []
        for pattern, group_idx in formula_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                boundaries.append((match.start(), match.end()))
        
        # Sort by start position
        return sorted(boundaries)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in text."""
        # Simple estimation: 1 token ≈ 4 characters for English text
        # This is a rough approximation - for production, use the tokenizer
        # from your actual embedding model
        return max(1, len(text) // 4)  # Ensure at least 1 token
    
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
        
        # Add document start as the initial position if no headings at start
        if not headings or headings[0]['position'] > 0:
            headings.insert(0, {
                'level': 0,
                'title': 'Document Start',
                'position': 0
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
            
            # Skip empty chunks
            if not chunk_content.strip():
                continue
                
            # Build heading path (breadcrumb)
            path = []
            for h in headings[:i+1]:
                if h['level'] > 0:  # Skip non-heading markers
                    path.append(h['title'])
            
            # Create chunk
            chunk = {
                'content': chunk_content,
                'heading': current['title'] if current['level'] > 0 else "Document Start",
                'level': current['level'],
                'path': " > ".join(path) if path else "Root",
                'token_count': self.estimate_tokens(chunk_content),
                'start_pos': start_pos,
                'end_pos': end_pos
            }
            
            initial_chunks.append(chunk)
        
        # Further process chunks that exceed max size
        large_chunks_processed = []
        for chunk in initial_chunks:
            if chunk['token_count'] <= self.max_chunk_size:
                large_chunks_processed.append(chunk)
            else:
                # Split large chunks with overlap
                sub_chunks = self._split_large_chunk(chunk)
                large_chunks_processed.extend(sub_chunks)
        
        # Post-process: merge small chunks together when possible
        final_chunks = self._merge_small_chunks(large_chunks_processed)
        
        # Add chunk IDs and clean up temporary fields
        for chunk in final_chunks:
            chunk['id'] = self._generate_chunk_id(chunk['content'])
            # Remove temporary fields used for processing
            if 'start_pos' in chunk:
                del chunk['start_pos']
            if 'end_pos' in chunk:
                del chunk['end_pos']
            
        return final_chunks
    
    def _generate_chunk_id(self, content: str) -> str:
        """Generate a unique ID for a chunk based on its content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    
    def _split_large_chunk(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split large chunks into smaller ones with overlap, respecting formulas."""
        content = chunk['content']
        token_count = chunk['token_count']
        path = chunk['path']
        heading = chunk['heading']
        level = chunk['level']
        
        # Extract all formula boundaries
        formula_boundaries = self.extract_formula_boundaries(content)
        
        # First try to split at paragraph boundaries
        paragraphs = []
        last_pos = 0
        
        # Split by paragraphs but keep formulas intact
        para_pattern = re.compile(r'\n\s*\n')
        for match in para_pattern.finditer(content):
            para_end = match.start()
            
            # Check if we're inside a formula
            in_formula = False
            for start, end in formula_boundaries:
                if start <= para_end <= end:
                    in_formula = True
                    break
            
            if not in_formula:
                # Safe to split here
                paragraph = content[last_pos:para_end].strip()
                if paragraph:
                    paragraphs.append(paragraph)
                last_pos = match.end()
        
        # Add the final paragraph
        final_para = content[last_pos:].strip()
        if final_para:
            paragraphs.append(final_para)
        
        # If no paragraphs were found or only one paragraph, split by sentences or fixed size
        if len(paragraphs) <= 1 and token_count > self.max_chunk_size:
            return self._split_by_sentences(chunk, formula_boundaries)
        
        # Now process the paragraphs into chunks
        sub_chunks = []
        current_chunk_text = ""
        current_token_count = 0
        current_start_pos = chunk['start_pos']
        
        for para in paragraphs:
            para_token_count = self.estimate_tokens(para)
            
            # If this single paragraph exceeds max size, split it further
            if para_token_count > self.max_chunk_size:
                if current_chunk_text:
                    # Save current accumulated chunk
                    sub_chunk = {
                        'content': current_chunk_text,
                        'heading': heading,
                        'level': level,
                        'path': path,
                        'token_count': current_token_count,
                        'start_pos': current_start_pos,
                        'end_pos': current_start_pos + len(current_chunk_text)
                    }
                    sub_chunks.append(sub_chunk)
                    current_chunk_text = ""
                    current_token_count = 0
                
                # Create a temporary chunk for this paragraph and split it
                para_chunk = {
                    'content': para,
                    'heading': heading,
                    'level': level,
                    'path': path,
                    'token_count': para_token_count,
                    'start_pos': content.find(para, current_start_pos) + chunk['start_pos'],
                    'end_pos': content.find(para, current_start_pos) + len(para) + chunk['start_pos']
                }
                para_sub_chunks = self._split_by_sentences(para_chunk, formula_boundaries)
                sub_chunks.extend(para_sub_chunks)
                
                # Update the start position for the next paragraph
                current_start_pos = para_chunk['end_pos']
                continue
            
            # If adding this paragraph would exceed max size, save current chunk and start new one
            if current_token_count + para_token_count > self.max_chunk_size and current_chunk_text:
                # Save current chunk
                sub_chunk = {
                    'content': current_chunk_text,
                    'heading': heading,
                    'level': level,
                    'path': path,
                    'token_count': current_token_count,
                    'start_pos': current_start_pos,
                    'end_pos': current_start_pos + len(current_chunk_text)
                }
                sub_chunks.append(sub_chunk)
                
                # Create overlap by including previous text up to overlap_size
                overlap_text = self._get_overlap_text(current_chunk_text)
                current_chunk_text = overlap_text
                current_token_count = self.estimate_tokens(overlap_text)
                current_start_pos = sub_chunk['end_pos'] - len(overlap_text)
            
            # Add paragraph to current chunk
            if current_chunk_text:
                current_chunk_text += "\n\n" + para
            else:
                current_chunk_text = para
            current_token_count = self.estimate_tokens(current_chunk_text)
        
        # Add the last sub-chunk if there's content left
        if current_chunk_text:
            sub_chunk = {
                'content': current_chunk_text,
                'heading': heading,
                'level': level,
                'path': path,
                'token_count': current_token_count,
                'start_pos': current_start_pos,
                'end_pos': current_start_pos + len(current_chunk_text)
            }
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _split_by_sentences(self, chunk: Dict[str, Any], formula_boundaries: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Split chunk by sentences when paragraphs are too large."""
        content = chunk['content']
        path = chunk['path']
        heading = chunk['heading']
        level = chunk['level']
        start_pos = chunk['start_pos']
        
        # Function to check if position is within a formula
        def in_formula(pos):
            rel_pos = start_pos + pos  # Position relative to the document
            for f_start, f_end in formula_boundaries:
                if f_start <= rel_pos <= f_end:
                    return True
            return False
        
        # Pattern for sentence endings
        sentence_pattern = re.compile(r'(?<=[.!?])\s+')
        
        sub_chunks = []
        current_chunk_text = ""
        current_token_count = 0
        current_start = 0
        
        # Get sentence boundaries
        sentence_boundaries = []
        for match in sentence_pattern.finditer(content):
            if not in_formula(match.start()):
                sentence_boundaries.append(match.start())
        
        # Add the end of content as final boundary
        sentence_boundaries.append(len(content))
        
        # Process sentences into chunks
        last_boundary = 0
        for boundary in sentence_boundaries:
            sentence = content[last_boundary:boundary].strip()
            sentence_token_count = self.estimate_tokens(sentence)
            
            # If a single sentence exceeds max size, split it by a fixed size
            if sentence_token_count > self.max_chunk_size:
                if current_chunk_text:
                    # Save current chunk
                    sub_chunk = {
                        'content': current_chunk_text,
                        'heading': heading,
                        'level': level,
                        'path': path,
                        'token_count': current_token_count,
                        'start_pos': start_pos + current_start,
                        'end_pos': start_pos + current_start + len(current_chunk_text)
                    }
                    sub_chunks.append(sub_chunk)
                    current_chunk_text = ""
                    current_token_count = 0
                
                # Split the sentence by fixed size, respecting token limit
                chars_per_chunk = self.max_chunk_size * 4  # Approximate
                for i in range(0, len(sentence), chars_per_chunk):
                    chunk_text = sentence[i:i + chars_per_chunk]
                    if i > 0:
                        # Add overlap from previous chunk
                        overlap_size_chars = min(self.overlap_size * 4, len(chunk_text))
                        chunk_text = sentence[i - overlap_size_chars:i + chars_per_chunk]
                    
                    sub_chunk = {
                        'content': chunk_text,
                        'heading': heading,
                        'level': level,
                        'path': path,
                        'token_count': self.estimate_tokens(chunk_text),
                        'start_pos': start_pos + last_boundary + i,
                        'end_pos': start_pos + last_boundary + i + len(chunk_text)
                    }
                    sub_chunks.append(sub_chunk)
            else:
                # If adding this sentence would exceed max size, save current chunk and start new one
                if current_token_count + sentence_token_count > self.max_chunk_size and current_chunk_text:
                    # Save current chunk
                    sub_chunk = {
                        'content': current_chunk_text,
                        'heading': heading,
                        'level': level,
                        'path': path,
                        'token_count': current_token_count,
                        'start_pos': start_pos + current_start,
                        'end_pos': start_pos + current_start + len(current_chunk_text)
                    }
                    sub_chunks.append(sub_chunk)
                    
                    # Create overlap by including previous text up to overlap_size
                    overlap_text = self._get_overlap_text(current_chunk_text)
                    current_chunk_text = overlap_text
                    current_token_count = self.estimate_tokens(overlap_text)
                    current_start = current_start + len(current_chunk_text) - len(overlap_text)
                
                # Add sentence to current chunk
                if current_chunk_text:
                    current_chunk_text += " " + sentence
                else:
                    current_chunk_text = sentence
                    current_start = last_boundary
                current_token_count = self.estimate_tokens(current_chunk_text)
            
            last_boundary = boundary
        
        # Add the last sub-chunk if there's content left
        if current_chunk_text:
            sub_chunk = {
                'content': current_chunk_text,
                'heading': heading,
                'level': level,
                'path': path,
                'token_count': current_token_count,
                'start_pos': start_pos + current_start,
                'end_pos': start_pos + current_start + len(current_chunk_text)
            }
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _merge_small_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge adjacent small chunks together up to min_chunk_size."""
        if not chunks:
            return []
        
        # Sort chunks by position
        sorted_chunks = sorted(chunks, key=lambda x: x['start_pos'])
        
        merged_chunks = []
        current_chunk = sorted_chunks[0].copy()
        
        for i in range(1, len(sorted_chunks)):
            next_chunk = sorted_chunks[i]
            
            # If current chunk is below min size and same heading level, try to merge
            if (current_chunk['token_count'] < self.min_chunk_size and 
                current_chunk['level'] == next_chunk['level'] and
                current_chunk['path'] == next_chunk['path']):
                
                # Check if merging wouldn't exceed max size
                combined_tokens = current_chunk['token_count'] + next_chunk['token_count']
                if combined_tokens <= self.max_chunk_size:
                    # Merge the chunks
                    current_chunk['content'] += "\n\n" + next_chunk['content']
                    current_chunk['token_count'] = combined_tokens
                    current_chunk['end_pos'] = next_chunk['end_pos']
                    continue
            
            # If we can't merge, save current chunk and start a new one
            merged_chunks.append(current_chunk)
            current_chunk = next_chunk.copy()
        
        # Add the last chunk
        merged_chunks.append(current_chunk)
        
        return merged_chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get text for overlap from the end of a chunk."""
        # Handle formula-specific overlap needs
        formula_boundaries = self.extract_formula_boundaries(text)
        
        # If there's a formula near the end, include the whole formula
        if formula_boundaries:
            for start, end in reversed(formula_boundaries):
                # If formula ends in the last part of the text
                if end > len(text) - (self.overlap_size * 4):
                    # Include from the start of the last formula to the end
                    return text[start:]
        
        # Default: get last N tokens of text (approximated as characters)
        char_overlap = self.overlap_size * 4  # Rough estimate: 1 token ≈ 4 chars
        if len(text) <= char_overlap:
            return text
        
        # Try to find paragraph or sentence boundary for cleaner overlap
        overlap_text = text[-char_overlap:]
        para_match = re.search(r'\n\s*\n', overlap_text)
        if para_match:
            # Start from paragraph boundary within overlap zone
            return overlap_text[para_match.end():]
        
        sentence_match = re.search(r'(?<=[.!?])\s+', overlap_text)
        if sentence_match:
            # Start from sentence boundary within overlap zone
            return overlap_text[sentence_match.end():]
        
        return overlap_text
    
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