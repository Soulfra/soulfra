#!/usr/bin/env python3
"""
Test Voice-to-Graph Pipeline with REAL Voice File

Proves end-to-end:
1. Load real audio file (.wav or .webm)
2. Transcribe with Whisper
3. Extract wordmap
4. Add fuzzy semantic relationships
5. Compute graph layout
6. Render interactive HTML
7. Benchmark performance
"""

import sys
import os
from pathlib import Path

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'optional'))

import time
import json
from datetime import datetime

# Import our modules
from content_parser import ContentParser
from fuzzy_semantic_extractor import FuzzySemanticExtractor
from canvas_visualizer import CanvasVisualizer

# Import Whisper
import whisper

def transcribe_audio(audio_path: str, model_name: str = 'base') -> str:
    """
    Transcribe audio file using Whisper

    Args:
        audio_path: Path to audio file
        model_name: Whisper model (tiny, base, small, medium, large)

    Returns:
        Transcript text
    """
    print(f"\n🎤 Transcribing audio with Whisper ({model_name})...")
    start = time.time()

    # Load model
    model = whisper.load_model(model_name)

    # Transcribe
    result = model.transcribe(audio_path)

    elapsed = time.time() - start
    transcript = result['text']

    print(f"   ✅ Transcription complete in {elapsed:.2f}s")
    print(f"   📝 Transcript: {transcript[:100]}...")

    return transcript


def voice_to_graph_pipeline(audio_path: str, output_dir: Path):
    """
    Full pipeline: Audio → Graph visualization

    Args:
        audio_path: Path to audio file
        output_dir: Where to save outputs
    """
    print("=" * 80)
    print("🚀 VOICE-TO-GRAPH PIPELINE - REAL AUDIO TEST")
    print("=" * 80)

    output_dir.mkdir(parents=True, exist_ok=True)

    # =================================================================
    # Step 1: Transcribe audio
    # =================================================================
    transcript_start = time.time()
    transcript = transcribe_audio(audio_path, model_name='base')
    transcription_time = time.time() - transcript_start

    # Save transcript
    transcript_path = output_dir / 'transcript.txt'
    with open(transcript_path, 'w') as f:
        f.write(transcript)

    print(f"\n   📄 Saved transcript to {transcript_path}")

    # =================================================================
    # Step 2: Parse transcript → Wordmap
    # =================================================================
    print("\n🧠 Parsing transcript into wordmap...")
    parse_start = time.time()

    parser = ContentParser()
    graph = parser.parse(transcript, 'voice_transcript', metadata={
        'audio_file': audio_path,
        'timestamp': datetime.now().isoformat()
    })

    parse_time = time.time() - parse_start

    print(f"   ✅ Wordmap extracted in {parse_time:.3f}s")
    print(f"   📊 Nodes: {len(graph['nodes'])}, Edges: {len(graph['edges'])}")

    # Show top words
    top_words = sorted(graph['nodes'], key=lambda n: n.get('frequency', 0), reverse=True)[:10]
    print(f"\n   🔤 Top 10 words:")
    for i, node in enumerate(top_words, 1):
        print(f"      {i}. {node['label']}: {node['frequency']} times")

    # =================================================================
    # Step 3: Add fuzzy semantic relationships
    # =================================================================
    print("\n✨ Extracting fuzzy semantics...")
    semantic_start = time.time()

    extractor = FuzzySemanticExtractor()
    semantic_nodes, semantic_edges = extractor.extract_graph_semantics(
        nodes=graph['nodes'],
        max_words=15  # Top 15 words
    )

    graph['nodes'].extend(semantic_nodes)
    graph['edges'].extend(semantic_edges)

    semantic_time = time.time() - semantic_start

    print(f"   ✅ Semantics extracted in {semantic_time:.3f}s")
    print(f"   📊 Added {len(semantic_nodes)} semantic nodes, {len(semantic_edges)} semantic edges")

    # Show sample relationships
    print(f"\n   🔗 Sample semantic relationships:")
    for edge in semantic_edges[:8]:
        print(f"      {edge['source']} --[{edge['type']}]→ {edge['target']}")

    # =================================================================
    # Step 4: Compute graph layout
    # =================================================================
    print("\n🧲 Computing force-directed layout...")
    layout_start = time.time()

    viz = CanvasVisualizer(width=1000, height=800)
    positions = viz.layout_force_directed(
        nodes=graph['nodes'],
        edges=graph['edges'],
        iterations=100
    )

    layout_time = time.time() - layout_start

    print(f"   ✅ Layout computed in {layout_time:.3f}s")

    # =================================================================
    # Step 5: Render visualizations
    # =================================================================
    print("\n🎨 Rendering visualizations...")
    render_start = time.time()

    # HTML (interactive)
    html_path = output_dir / 'graph.html'
    viz.render_html_interactive(graph['nodes'], graph['edges'], positions, str(html_path))

    # SVG (static)
    svg_path = output_dir / 'graph.svg'
    viz.render_svg(graph['nodes'], graph['edges'], positions, str(svg_path))

    # JSON (data)
    json_path = output_dir / 'graph.json'
    viz.export_json(graph['nodes'], graph['edges'], positions, str(json_path))

    render_time = time.time() - render_start

    print(f"   ✅ Visualizations rendered in {render_time:.3f}s")

    # =================================================================
    # Step 6: Performance Report
    # =================================================================
    total_time = transcription_time + parse_time + semantic_time + layout_time + render_time

    print("\n" + "=" * 80)
    print("📊 PERFORMANCE REPORT")
    print("=" * 80)
    print(f"\n⏱️  Pipeline Timing:")
    print(f"   1. Transcription (Whisper):  {transcription_time:.3f}s")
    print(f"   2. Wordmap parsing:           {parse_time:.3f}s")
    print(f"   3. Semantic extraction:       {semantic_time:.3f}s")
    print(f"   4. Graph layout:              {layout_time:.3f}s")
    print(f"   5. Rendering (HTML/SVG/JSON): {render_time:.3f}s")
    print(f"   " + "-" * 50)
    print(f"   TOTAL:                        {total_time:.3f}s")

    print(f"\n📁 Outputs:")
    print(f"   - Transcript:      {transcript_path}")
    print(f"   - Interactive:     {html_path}")
    print(f"   - Static SVG:      {svg_path}")
    print(f"   - Graph data:      {json_path}")

    print(f"\n🌐 Open {html_path} in your browser to explore!")

    # Generate summary report
    report = f"""# Voice-to-Graph Pipeline Test - Real Audio

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Input
- **Audio File:** {audio_path}
- **File Size:** {Path(audio_path).stat().st_size:,} bytes
- **Transcript Length:** {len(transcript.split())} words

## Pipeline Performance
1. **Transcription (Whisper):** {transcription_time:.3f}s
2. **Wordmap Parsing:** {parse_time:.3f}s
3. **Semantic Extraction:** {semantic_time:.3f}s
4. **Graph Layout:** {layout_time:.3f}s
5. **Rendering:** {render_time:.3f}s

**Total Pipeline Time:** {total_time:.3f}s

## Results
- **Total Nodes:** {len(graph['nodes'])} ({len(semantic_nodes)} semantic)
- **Total Edges:** {len(graph['edges'])} ({len(semantic_edges)} semantic)

### Top Words
"""

    for i, node in enumerate(top_words, 1):
        report += f"{i}. **{node['label']}** ({node['frequency']}x)\n"

    report += f"""

### Sample Semantic Relationships
"""

    for edge in semantic_edges[:10]:
        report += f"- {edge['source']} --[{edge['type']}]→ {edge['target']}\n"

    report += f"""

## Transcript

```
{transcript}
```

## Outputs
- [Interactive Graph]({html_path.name})
- [Static SVG]({svg_path.name})
- [Graph Data]({json_path.name})

## ✅ PROOF: Full pipeline works with real audio!
"""

    report_path = output_dir / 'REPORT.md'
    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n📄 Full report saved to {report_path}")
    print("\n" + "=" * 80)
    print("✅ PIPELINE TEST COMPLETE!")
    print("=" * 80)


if __name__ == '__main__':
    # Test with sample_5.wav (larger file, more content)
    audio_file = Path(__file__).parent.parent / 'voice_samples' / 'sample_5.wav'

    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        print("\n📁 Available audio files:")
        samples_dir = Path(__file__).parent.parent / 'voice_samples'
        if samples_dir.exists():
            for f in sorted(samples_dir.glob('*.wav')):
                print(f"   - {f.name}")
        sys.exit(1)

    # Run pipeline
    output_dir = Path(__file__).parent.parent / 'data' / 'voice_to_graph_test'

    voice_to_graph_pipeline(str(audio_file), output_dir)
