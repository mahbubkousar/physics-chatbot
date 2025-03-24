# tests/chunk_analyzer.py
import json
import os
import sys
import statistics
import matplotlib.pyplot as plt
from collections import Counter
import argparse
from typing import Dict, List, Any

class ChunkAnalyzer:
    def __init__(self, chunks_file: str):
        """
        Initialize the analyzer with the path to the chunks file.
        
        Args:
            chunks_file: Path to the JSONL file containing chunks
        """
        self.chunks_file = chunks_file
        self.chunks = []
        self.stats = {}
        
    def load_chunks(self) -> bool:
        """Load chunks from the JSONL file."""
        try:
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                self.chunks = [json.loads(line) for line in f]
            return True
        except Exception as e:
            print(f"Error loading chunks file: {e}")
            return False
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze the chunks and generate statistics."""
        if not self.chunks and not self.load_chunks():
            return {}
        
        # Count chunks
        total_chunks = len(self.chunks)
        
        # Analyze token counts
        token_counts = [chunk.get('token_count', 0) for chunk in self.chunks]
        
        # Analyze content length
        content_lengths = [len(chunk.get('content', '')) for chunk in self.chunks]
        
        # Analyze heading levels
        heading_levels = [chunk.get('level', 0) for chunk in self.chunks]
        level_counter = Counter(heading_levels)
        
        # Analyze chunk types
        chunk_types = [chunk.get('chunk_type', 'main_chunk') for chunk in self.chunks]
        type_counter = Counter(chunk_types)
        
        # Count total tokens
        total_tokens = sum(token_counts)
        
        # Calculate statistics
        stats = {
            'total_chunks': total_chunks,
            'total_tokens': total_tokens,
            'token_count': {
                'min': min(token_counts) if token_counts else 0,
                'max': max(token_counts) if token_counts else 0,
                'avg': statistics.mean(token_counts) if token_counts else 0,
                'median': statistics.median(token_counts) if token_counts else 0,
                'stdev': statistics.stdev(token_counts) if len(token_counts) > 1 else 0
            },
            'content_length': {
                'min': min(content_lengths) if content_lengths else 0,
                'max': max(content_lengths) if content_lengths else 0,
                'avg': statistics.mean(content_lengths) if content_lengths else 0,
                'median': statistics.median(content_lengths) if content_lengths else 0,
                'stdev': statistics.stdev(content_lengths) if len(content_lengths) > 1 else 0
            },
            'heading_levels': dict(level_counter),
            'chunk_types': dict(type_counter)
        }
        
        self.stats = stats
        return stats
    
    def generate_report(self) -> str:
        """Generate a text report of the analysis."""
        if not self.stats:
            self.analyze()
        
        if not self.stats:
            return "No data available for analysis."
        
        report = []
        report.append("# Chunk Analysis Report")
        report.append("\n## General Statistics")
        report.append(f"- Total chunks: {self.stats['total_chunks']}")
        report.append(f"- Total tokens: {self.stats['total_tokens']}")
        report.append(f"- Average tokens per chunk: {self.stats['token_count']['avg']:.2f}")
        
        report.append("\n## Token Count Statistics")
        report.append(f"- Minimum: {self.stats['token_count']['min']}")
        report.append(f"- Maximum: {self.stats['token_count']['max']}")
        report.append(f"- Average: {self.stats['token_count']['avg']:.2f}")
        report.append(f"- Median: {self.stats['token_count']['median']}")
        report.append(f"- Standard Deviation: {self.stats['token_count']['stdev']:.2f}")
        
        report.append("\n## Content Length Statistics (characters)")
        report.append(f"- Minimum: {self.stats['content_length']['min']}")
        report.append(f"- Maximum: {self.stats['content_length']['max']}")
        report.append(f"- Average: {self.stats['content_length']['avg']:.2f}")
        report.append(f"- Median: {self.stats['content_length']['median']}")
        report.append(f"- Standard Deviation: {self.stats['content_length']['stdev']:.2f}")
        
        report.append("\n## Heading Level Distribution")
        for level, count in sorted(self.stats['heading_levels'].items()):
            level_name = "Document Start" if level == 0 else f"Level {level}"
            report.append(f"- {level_name}: {count} chunks ({count/self.stats['total_chunks']*100:.1f}%)")
        
        report.append("\n## Chunk Type Distribution")
        for chunk_type, count in sorted(self.stats['chunk_types'].items()):
            report.append(f"- {chunk_type}: {count} chunks ({count/self.stats['total_chunks']*100:.1f}%)")
        
        report.append("\n## Recommendations")
        avg_tokens = self.stats['token_count']['avg']
        max_tokens = self.stats['token_count']['max']
        
        if max_tokens > 1500:
            report.append("- Consider reducing max_chunk_size as some chunks are quite large")
        
        if avg_tokens < 400:
            report.append("- Consider increasing max_chunk_size as chunks are relatively small on average")
        
        std_dev = self.stats['token_count']['stdev']
        if std_dev > avg_tokens * 0.5:
            report.append("- High variation in chunk sizes - may need to refine chunking strategy")
            
        sub_chunk_count = self.stats['chunk_types'].get('sub_chunk', 0)
        if sub_chunk_count / self.stats['total_chunks'] > 0.5:
            report.append("- Many large sections were split into sub-chunks, consider restructuring document")
        
        return "\n".join(report)
    
    def create_visualizations(self, output_dir: str) -> bool:
        """Create visualizations of chunk statistics and save to output directory."""
        if not self.stats:
            self.analyze()
        
        if not self.stats:
            return False
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Plot 1: Token Count Distribution
            plt.figure(figsize=(10, 6))
            token_counts = [chunk.get('token_count', 0) for chunk in self.chunks]
            plt.hist(token_counts, bins=20, color='skyblue', edgecolor='black')
            plt.title('Distribution of Token Counts')
            plt.xlabel('Token Count')
            plt.ylabel('Number of Chunks')
            plt.axvline(self.stats['token_count']['avg'], color='red', linestyle='--', 
                       label=f"Average: {self.stats['token_count']['avg']:.1f}")
            plt.axvline(self.stats['token_count']['median'], color='green', linestyle='--', 
                       label=f"Median: {self.stats['token_count']['median']}")
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'token_distribution.png'))
            plt.close()
            
            # Plot 2: Heading Level Distribution
            plt.figure(figsize=(10, 6))
            levels = []
            counts = []
            for level, count in sorted(self.stats['heading_levels'].items()):
                level_name = "Doc Start" if level == 0 else f"Level {level}"
                levels.append(level_name)
                counts.append(count)
            
            plt.bar(levels, counts, color='lightgreen', edgecolor='black')
            plt.title('Distribution of Heading Levels')
            plt.xlabel('Heading Level')
            plt.ylabel('Number of Chunks')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'heading_distribution.png'))
            plt.close()
            
            # Plot 3: Chunk Types
            plt.figure(figsize=(10, 6))
            types = []
            type_counts = []
            for chunk_type, count in sorted(self.stats['chunk_types'].items()):
                types.append(chunk_type)
                type_counts.append(count)
            
            plt.bar(types, type_counts, color='salmon', edgecolor='black')
            plt.title('Distribution of Chunk Types')
            plt.xlabel('Chunk Type')
            plt.ylabel('Number of Chunks')
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'chunk_types.png'))
            plt.close()
            
            return True
        except Exception as e:
            print(f"Error creating visualizations: {e}")
            return False
        
    def save_report(self, output_file: str) -> bool:
        """Save the analysis report to a file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.generate_report())
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
            
    def export_stats_json(self, output_file: str) -> bool:
        """Export statistics as JSON for further analysis."""
        if not self.stats:
            self.analyze()
            
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting stats: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Analyze chunked documents')
    parser.add_argument('chunks_file', help='Path to the JSONL file containing chunks')
    parser.add_argument('--output-dir', '-o', default='tests/output', 
                        help='Directory to save analysis outputs')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize analyzer
    analyzer = ChunkAnalyzer(args.chunks_file)
    
    # Generate and save report
    report_path = os.path.join(args.output_dir, 'chunk_analysis_report.md')
    if analyzer.save_report(report_path):
        print(f"Analysis report saved to {report_path}")
    
    # Export statistics as JSON
    stats_path = os.path.join(args.output_dir, 'chunk_stats.json')
    if analyzer.export_stats_json(stats_path):
        print(f"Statistics exported to {stats_path}")
    
    # Generate visualizations
    vis_dir = os.path.join(args.output_dir, 'visualizations')
    if analyzer.create_visualizations(vis_dir):
        print(f"Visualizations saved to {vis_dir}")
    
    print("\nSummary of analysis:")
    print(f"- Total chunks: {analyzer.stats.get('total_chunks', 'N/A')}")
    print(f"- Average tokens per chunk: {analyzer.stats.get('token_count', {}).get('avg', 'N/A'):.2f}")
    print(f"- Max token count: {analyzer.stats.get('token_count', {}).get('max', 'N/A')}")
    print("See the full report for more details.")

if __name__ == "__main__":
    main()