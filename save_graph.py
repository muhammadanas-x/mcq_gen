#!/usr/bin/env python3
"""
Script to save the MCQ Generator graph structure as an image.

This script generates a visual representation of the LangGraph workflow
and saves it as a PNG file.
"""

import sys
import os
from graph import create_mcq_graph


def print_graph_structure():
    """Print a detailed text representation of the graph structure."""
    print("\n" + "="*70)
    print("MCQ GENERATOR GRAPH STRUCTURE")
    print("="*70)
    print("\nNodes:")
    print("  1. analyzer           - Extracts concepts from content")
    print("  2. stem_generator     - Generates question stems (batch processing)")
    print("  3. validator          - Validates and corrects questions")
    print("  4. distractor_generator - Creates wrong answer options")
    print("  5. assembler          - Final assembly and formatting")
    print("\nEdges:")
    print("  START → analyzer")
    print("  analyzer → stem_generator")
    print("  stem_generator → [CONDITIONAL ROUTING]")
    print("    ├─ if needs_more_batches == True  → stem_generator (LOOP)")
    print("    └─ if needs_more_batches == False → validator")
    print("  validator → distractor_generator")
    print("  distractor_generator → assembler")
    print("  assembler → END")
    print("\nConditional Node Details:")
    print("  Function: should_continue_generating()")
    print("  Condition: state['needs_more_batches']")
    print("  Routes to:")
    print("    - 'stem_generator' when True (processes next batch)")
    print("    - 'validator' when False (all concepts processed)")
    print("="*70 + "\n")


def save_graph_image(output_path: str = "mcq_generator_graph.png"):
    """
    Generate and save the graph structure visualization.
    
    Args:
        output_path: Path where the graph image will be saved
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print("Creating MCQ Generator Graph...")
        app = create_mcq_graph()
        print("✓ Graph created successfully!")
        
        # Print detailed structure
        print_graph_structure()
        
        print(f"Generating visualization to: {output_path}...")
        
        # Get graph object
        graph_obj = app.get_graph()
        graph_image = None
        method_used = None
        
        # Method 1: Try draw_ascii for terminal display
        try:
            print("\nASCII Representation:")
            print(graph_obj.draw_ascii())
        except Exception as e:
            print(f"ASCII drawing not available: {e}")
        
        # Method 2: Save mermaid text (most detailed)
        try:
            mermaid_text = graph_obj.draw_mermaid()
            mermaid_path = output_path.replace('.png', '.mmd')
            with open(mermaid_path, 'w') as f:
                f.write(mermaid_text)
            print(f"\n✓ Mermaid diagram saved to: {mermaid_path}")
            print(f"  (View at https://mermaid.live/ for full conditional routing)")
        except Exception as e:
            print(f"Could not save mermaid text: {e}")
        
        # Method 3: Try draw_png (best quality with pygraphviz)
        try:
            print("\nAttempting to generate PNG with pygraphviz...")
            graph_image = graph_obj.draw_png()
            method_used = "draw_png (pygraphviz)"
        except Exception as e1:
            print(f"  pygraphviz method failed: {e1}")
            
            # Method 4: Fallback to draw_mermaid_png
            try:
                print("  Falling back to draw_mermaid_png()...")
                graph_image = graph_obj.draw_mermaid_png()
                method_used = "draw_mermaid_png"
                print("  ⚠ Warning: mermaid_png may not show conditional routing clearly")
                print("    Check the .mmd file or use pygraphviz for better visualization")
            except Exception as e2:
                print(f"  Mermaid PNG method also failed: {e2}")
                print("\n✗ Could not generate PNG image")
                print("   However, mermaid diagram (.mmd) was saved successfully")
                return True  # Still consider it success if we have .mmd file
        
        # Save PNG if we got it
        if graph_image:
            with open(output_path, 'wb') as f:
                f.write(graph_image)
            print(f"\n✓ Graph visualization saved to: {output_path}")
            print(f"  Method used: {method_used}")
        
        return True
        
    except ImportError as e:
        print(f"\n✗ Error: Missing required dependencies")
        print(f"  {e}")
        print("\nFor better visualization, install:")
        print("  1. System graphviz: brew install graphviz")
        print("  2. Python binding: pip install pygraphviz")
        return False
        
    except Exception as e:
        print(f"\n✗ Error generating graph visualization: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Allow custom output path from command line
    output_path = sys.argv[1] if len(sys.argv) > 1 else "mcq_generator_graph.png"
    
    success = save_graph_image(output_path)
    sys.exit(0 if success else 1)
