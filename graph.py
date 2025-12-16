"""
LangGraph Orchestration

Defines the graph structure with loopback routing for batch processing.

Graph Flow:
1. Analyzer → extracts concepts, populates queue
2. Stem Generator → processes batch (10-15 concepts)
   - If queue not empty → LOOP BACK to Stem Generator with next batch
   - If queue empty → proceed to Validator
3. Validator → verifies correctness, corrects or removes questions
4. Distractor Generator → creates 3-5 wrong options per question
5. Assembler → shuffles options, creates final formatted MCQs
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from state import MCQGeneratorState

# Import node functions
from nodes.analyzer import content_analyzer_node
from nodes.stem_generator import stem_generator_node
from nodes.validator import validator_node
from nodes.distractor_generator import distractor_generator_node
from nodes.assembler import assembler_node


def should_continue_generating(state: MCQGeneratorState) -> Literal["stem_generator", "validator"]:
    """
    Routing function: decides whether to loop back to stem generator or proceed to validator.
    
    Args:
        state: Current MCQGeneratorState
    
    Returns:
        "stem_generator" if more batches needed, "validator" if all concepts processed
    """
    if state.get("needs_more_batches", False):
        print("\n→ ROUTING: More concepts in queue, looping back to Stem Generator")
        return "stem_generator"
    else:
        print("\n→ ROUTING: All concepts processed, proceeding to Validator")
        return "validator"


def create_mcq_graph() -> StateGraph:
    """
    Create the LangGraph state graph for MCQ generation.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize graph
    workflow = StateGraph(MCQGeneratorState)
    
    # Add nodes
    workflow.add_node("analyzer", content_analyzer_node)
    workflow.add_node("stem_generator", stem_generator_node)
    workflow.add_node("validator", validator_node)
    workflow.add_node("distractor_generator", distractor_generator_node)
    workflow.add_node("assembler", assembler_node)
    
    # Define edges
    workflow.set_entry_point("analyzer")
    
    # Analyzer → Stem Generator (initial batch)
    workflow.add_edge("analyzer", "stem_generator")
    
    # Stem Generator → Conditional routing (LOOPBACK or proceed)
    workflow.add_conditional_edges(
        "stem_generator",
        should_continue_generating,
        {
            "stem_generator": "stem_generator",  # LOOPBACK
            "validator": "validator"             # PROCEED
        }
    )
    
    # Validator → Distractor Generator
    workflow.add_edge("validator", "distractor_generator")
    
    # Distractor Generator → Assembler
    workflow.add_edge("distractor_generator", "assembler")
    
    # Assembler → END
    workflow.add_edge("assembler", END)
    
    # Compile graph
    app = workflow.compile()
    
    return app


def visualize_graph(save_path: str = "mcq_generator_graph.png"):
    """
    Generate a visualization of the graph structure.
    
    Args:
        save_path: Path to save the graph image
    """
    try:
        from IPython.display import Image, display
        app = create_mcq_graph()
        
        # Get mermaid representation
        graph_image = app.get_graph().draw_mermaid_png()
        
        with open(save_path, 'wb') as f:
            f.write(graph_image)
        
        print(f"✓ Graph visualization saved to: {save_path}")
        
        return Image(graph_image)
    
    except Exception as e:
        print(f"Could not generate graph visualization: {e}")
        print("Install graphviz and pygraphviz for graph visualization")
        return None


if __name__ == "__main__":
    # Test graph creation
    print("Creating MCQ Generator Graph...")
    app = create_mcq_graph()
    print("✓ Graph created successfully!")
    
    print("\nGraph structure:")
    print("1. Analyzer (entry)")
    print("2. Stem Generator (with loopback)")
    print("   ↻ Loop if concepts_queue not empty")
    print("   → Proceed to Validator if queue empty")
    print("3. Validator")
    print("4. Distractor Generator")
    print("5. Assembler (exit)")
    
    # Try to visualize
    print("\nAttempting to visualize graph...")
    visualize_graph()
