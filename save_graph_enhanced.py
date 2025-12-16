#!/usr/bin/env python3
"""
Enhanced script to save the MCQ Generator graph structure with proper conditional node labeling.

This script creates a detailed visualization showing the conditional routing logic.
"""

import sys
import os


def create_enhanced_mermaid():
    """Create an enhanced mermaid diagram with proper conditional labels."""
    mermaid_content = """%%{init: {'theme':'base', 'themeVariables': { 'primaryColor':'#f2f0ff','primaryTextColor':'#000','primaryBorderColor':'#7C3AED','lineColor':'#7C3AED','secondaryColor':'#FEF3C7','tertiaryColor':'#fff'}}}%%
graph TD
    Start([START]):::startEnd
    Analyzer[Analyzer<br/>Extract Concepts]:::node
    StemGen[Stem Generator<br/>Generate Questions<br/>Batch: 10-15 concepts]:::node
    Condition{needs_more_batches?<br/>Check Queue}:::condition
    Validator[Validator<br/>Verify & Correct]:::node
    DistractorGen[Distractor Generator<br/>Create Wrong Options]:::node
    Assembler[Assembler<br/>Shuffle & Format]:::node
    End([END]):::startEnd
    
    Start --> Analyzer
    Analyzer --> StemGen
    StemGen --> Condition
    Condition -->|True<br/>Queue not empty| StemGen
    Condition -->|False<br/>Queue empty| Validator
    Validator --> DistractorGen
    DistractorGen --> Assembler
    Assembler --> End
    
    classDef startEnd fill:#bfb6fc,stroke:#7C3AED,stroke-width:3px,color:#000
    classDef node fill:#f2f0ff,stroke:#7C3AED,stroke-width:2px,color:#000
    classDef condition fill:#FEF3C7,stroke:#F59E0B,stroke-width:3px,color:#000,font-weight:bold
    
    %% Add notes
    note1[Loop back for<br/>next batch]:::note
    note2[All concepts<br/>processed]:::note
    
    classDef note fill:#E0F2FE,stroke:#0EA5E9,stroke-width:1px,stroke-dasharray: 5 5,color:#000,font-size:11px
"""
    return mermaid_content


def create_enhanced_png_with_graphviz():
    """Create a PNG using graphviz with proper conditional node."""
    dot_content = """digraph MCQGenerator {
    // Graph settings
    rankdir=TB;
    node [shape=box, style="rounded,filled", fillcolor="#f2f0ff", fontname="Arial", fontsize=11];
    edge [fontname="Arial", fontsize=10];
    
    // Start/End nodes
    start [label="START", shape=oval, fillcolor="#bfb6fc", fontsize=12, penwidth=2];
    end [label="END", shape=oval, fillcolor="#bfb6fc", fontsize=12, penwidth=2];
    
    // Regular nodes
    analyzer [label="Analyzer\\nExtract Concepts"];
    stem_gen [label="Stem Generator\\nGenerate Questions\\n(Batch: 10-15 concepts)"];
    validator [label="Validator\\nVerify & Correct"];
    distractor_gen [label="Distractor Generator\\nCreate Wrong Options"];
    assembler [label="Assembler\\nShuffle & Format"];
    
    // Conditional node (diamond shape)
    condition [label="needs_more_batches?\\nCheck Queue Status", shape=diamond, fillcolor="#FEF3C7", penwidth=2, color="#F59E0B"];
    
    // Edges
    start -> analyzer;
    analyzer -> stem_gen;
    stem_gen -> condition;
    condition -> stem_gen [label="True\\n(Queue not empty)", color="#DC2626", fontcolor="#DC2626", penwidth=2];
    condition -> validator [label="False\\n(Queue empty)", color="#16A34A", fontcolor="#16A34A", penwidth=2];
    validator -> distractor_gen;
    distractor_gen -> assembler;
    assembler -> end;
    
    // Invisible edges for better layout
    {rank=same; condition; stem_gen;}
}
"""
    return dot_content


def save_all_formats(base_name: str = "mcq_generator_graph_full"):
    """
    Save the graph in multiple formats for maximum clarity.
    
    Args:
        base_name: Base filename without extension
    """
    print("="*70)
    print("ENHANCED MCQ GENERATOR GRAPH VISUALIZATION")
    print("="*70)
    
    # 1. Save enhanced mermaid diagram
    mermaid_path = f"{base_name}.mmd"
    try:
        with open(mermaid_path, 'w') as f:
            f.write(create_enhanced_mermaid())
        print(f"\n✓ Enhanced Mermaid diagram saved to: {mermaid_path}")
        print(f"  View at: https://mermaid.live/")
        print(f"  This version shows the conditional node properly!")
    except Exception as e:
        print(f"✗ Could not save mermaid: {e}")
    
    # 2. Save graphviz DOT file
    dot_path = f"{base_name}.dot"
    try:
        with open(dot_path, 'w') as f:
            f.write(create_enhanced_png_with_graphviz())
        print(f"\n✓ Graphviz DOT file saved to: {dot_path}")
    except Exception as e:
        print(f"✗ Could not save DOT file: {e}")
    
    # 3. Try to generate PNG from DOT using graphviz
    png_path = f"{base_name}.png"
    try:
        import subprocess
        result = subprocess.run(
            ['dot', '-Tpng', dot_path, '-o', png_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"\n✓ PNG image generated: {png_path}")
            print(f"  This shows the full conditional routing with labels!")
        else:
            print(f"\n✗ Could not generate PNG: {result.stderr}")
            print(f"  Install graphviz: brew install graphviz")
    except FileNotFoundError:
        print(f"\n⚠ graphviz 'dot' command not found")
        print(f"  Install it with: brew install graphviz")
        print(f"  Then run: dot -Tpng {dot_path} -o {png_path}")
    except Exception as e:
        print(f"\n✗ Error generating PNG: {e}")
    
    # 4. Generate PNG from Mermaid (if mmdc is available)
    try:
        import subprocess
        mermaid_png = f"{base_name}_mermaid.png"
        result = subprocess.run(
            ['mmdc', '-i', mermaid_path, '-o', mermaid_png, '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"\n✓ Mermaid PNG generated: {mermaid_png}")
        else:
            print(f"\n⚠ Mermaid CLI not available (optional)")
            print(f"  Install with: npm install -g @mermaid-js/mermaid-cli")
    except FileNotFoundError:
        pass  # mmdc is optional
    except Exception:
        pass
    
    # 5. Print text representation
    print("\n" + "="*70)
    print("TEXT REPRESENTATION")
    print("="*70)
    print("""
    START
      ↓
    ┌─────────────────────┐
    │  Analyzer           │
    │  Extract Concepts   │
    └─────────────────────┘
      ↓
    ┌─────────────────────────────────┐
    │  Stem Generator                 │
    │  Generate Questions             │
    │  (Batch: 10-15 concepts)        │
    └─────────────────────────────────┘
      ↓
    ╱───────────────────────╲
   ╱ needs_more_batches?    ╲
  ╱  Check Queue Status      ╲
  ╲                          ╱
   ╲────────┬────────────────╱
            │
      ┌─────┴─────┐
      │           │
   [True]      [False]
 Queue not   Queue empty
   empty         │
      │          ↓
      │    ┌─────────────────────┐
      │    │  Validator          │
      │    │  Verify & Correct   │
      │    └─────────────────────┘
      │          ↓
      │    ┌──────────────────────────────┐
      │    │  Distractor Generator        │
      │    │  Create Wrong Options        │
      │    └──────────────────────────────┘
      │          ↓
      │    ┌─────────────────────┐
      │    │  Assembler          │
      │    │  Shuffle & Format   │
      │    └─────────────────────┘
      │          ↓
      │        END
      │
      └──────────┘ (LOOP BACK)
    """)
    print("="*70)
    
    print("\n✓ Graph structure saved successfully!")
    print(f"\nFiles created:")
    print(f"  • {mermaid_path} - Enhanced mermaid diagram with conditional node")
    print(f"  • {dot_path} - Graphviz source file")
    if os.path.exists(png_path):
        print(f"  • {png_path} - PNG visualization with conditional routing")
    print(f"\nThe conditional routing is now clearly visible!")
    
    return True


if __name__ == "__main__":
    base_name = sys.argv[1] if len(sys.argv) > 1 else "mcq_generator_graph_full"
    save_all_formats(base_name)
