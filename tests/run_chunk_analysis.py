# tests/run_chunk_analysis.py
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.chunk_analyzer import ChunkAnalyzer

def run_analysis():
    """Run analysis on the chunked data"""
    # Define paths
    chunks_file = os.path.join(project_root, "resources", "chunks.jsonl")
    output_dir = os.path.join(project_root, "tests", "output")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Analyzing chunks from: {chunks_file}")
    
    # Initialize analyzer
    analyzer = ChunkAnalyzer(chunks_file)
    
    # Generate and save report
    report_path = os.path.join(output_dir, "chunk_analysis_report.md")
    if analyzer.save_report(report_path):
        print(f"Analysis report saved to: {report_path}")
    else:
        print("Failed to save analysis report")
    
    # Export statistics as JSON
    stats_path = os.path.join(output_dir, "chunk_stats.json")
    if analyzer.export_stats_json(stats_path):
        print(f"Statistics exported to: {stats_path}")
    else:
        print("Failed to export statistics")
    
    # Generate visualizations
    vis_dir = os.path.join(output_dir, "visualizations")
    if analyzer.create_visualizations(vis_dir):
        print(f"Visualizations saved to: {vis_dir}")
    else:
        print("Failed to create visualizations")
    
    # Print summary to console
    if analyzer.stats:
        stats = analyzer.stats
        print("\nChunk Analysis Summary:")
        print("=" * 50)
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Average tokens per chunk: {stats['token_count']['avg']:.2f}")
        print(f"Token count range: {stats['token_count']['min']} - {stats['token_count']['max']}")
        print(f"Standard deviation: {stats['token_count']['stdev']:.2f}")
        
        # Print recommendations
        print("\nKey Recommendations:")
        print("-" * 50)
        if stats['token_count']['max'] > 1500:
            print("- Consider reducing max_chunk_size as some chunks are quite large")
        
        if stats['token_count']['avg'] < 400:
            print("- Consider increasing max_chunk_size as chunks are relatively small on average")
        
        if stats['token_count']['stdev'] > stats['token_count']['avg'] * 0.5:
            print("- High variation in chunk sizes - may need to refine chunking strategy")
        
        sub_chunk_count = stats['chunk_types'].get('sub_chunk', 0)
        if sub_chunk_count / stats['total_chunks'] > 0.5:
            print("- Many sections were split into sub-chunks, consider restructuring document")
    else:
        print("No statistics available. Analysis may have failed.")

if __name__ == "__main__":
    run_analysis()