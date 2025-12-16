"""
Example usage and quick start guide for MCQ Generator
"""

from main import MCQGenerator

# Example 1: Generate from chapter content
def example_from_chapter():
    """Generate MCQs from chapter3.md"""
    print("Example 1: Generating MCQs from chapter content")
    print("="*60)
    
    generator = MCQGenerator(
        llm_provider="gemini",  # or "anthropic", "openai"
        model="gemini-2.5-pro",
        batch_size=10  # Start with smaller batches for testing
    )
    
    mcqs = generator.generate_from_file(
        input_path="../chapter3.md",
        input_type="chapter",
        output_path="generated_mcqs_from_chapter.md",
        include_explanations=True
    )
    
    print(f"\n✓ Generated {len(mcqs)} MCQs from chapter content")
    return mcqs


# Example 2: Generate from existing MCQs
def example_from_mcqs():
    """Generate similar MCQs from chap3_fung_mcqs.md"""
    print("\nExample 2: Generating MCQs from existing MCQ patterns")
    print("="*60)
    
    generator = MCQGenerator(
        llm_provider="gemini",
        model="gemini-2.5-pro",
        batch_size=15
    )
    
    mcqs = generator.generate_from_file(
        input_path="../chap3_fung_mcqs.md",
        input_type="mcqs",
        output_path="generated_mcqs_from_existing.md",
        include_explanations=True
    )
    
    print(f"\n✓ Generated {len(mcqs)} MCQs based on existing patterns")
    return mcqs


# Example 3: Access individual MCQ data
def example_access_data(mcqs):
    """Show how to access generated MCQ data"""
    print("\nExample 3: Accessing MCQ data")
    print("="*60)
    
    if not mcqs:
        print("No MCQs provided")
        return
    
    # Access first MCQ
    mcq = mcqs[0]
    
    print(f"Question {mcq['question_number']}:")
    print(f"  Stem: {mcq['stem']}")
    print(f"  Difficulty: {mcq['metadata']['difficulty']}")
    print(f"  Integral Type: {mcq['metadata']['integral_type']}")
    print(f"\n  Options:")
    for key, value in mcq['options'].items():
        marker = " ← CORRECT" if key == mcq['correct_answer'] else ""
        print(f"    ({key}) {value}{marker}")
    
    print(f"\n  Validation Score: {mcq['metadata']['validation_score']:.2f}")
    print(f"  Was Corrected: {mcq['metadata']['was_corrected']}")


# Example 4: Quick test run with minimal concepts
def example_quick_test():
    """Quick test with small batch to verify setup"""
    print("\nExample 4: Quick test run (small batch)")
    print("="*60)
    print("This will generate a small number of MCQs to verify your setup")
    print("Use this before running full generation")
    
    generator = MCQGenerator(
        llm_provider="gemini",
        model="gemini-2.5-pro",
        batch_size=5  # Very small batch for testing
    )
    
    # You could create a small sample file for testing
    # For now, we'll show the structure
    print("\nTo run quick test:")
    print("1. Create a small sample file (sample_content.md) with 2-3 concepts")
    print("2. Run:")
    print('   mcqs = generator.generate_from_file(')
    print('       input_path="sample_content.md",')
    print('       input_type="chapter",')
    print('       output_path="test_output.md"')
    print('   )')


if __name__ == "__main__":
    import sys
    import os
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("⚠ Warning: .env file not found")
        print("Please copy .env.example to .env and add your API keys")
        print("\ncp .env.example .env")
        print("# Then edit .env with your API keys")
        sys.exit(1)
    
    # Check if input files exist
    chapter_exists = os.path.exists("../chapter3.md")
    mcqs_exist = os.path.exists("../chap3_fung_mcqs.md")
    
    print("MCQ Generator - Example Usage")
    print("="*60)
    print("\nAvailable examples:")
    print("1. Generate from chapter content (chapter3.md)")
    print("2. Generate from existing MCQs (chap3_fung_mcqs.md)")
    print("3. Access MCQ data programmatically")
    print("4. Quick test run")
    
    if not (chapter_exists or mcqs_exist):
        print("\n⚠ Warning: Input files not found in parent directory")
        print("Make sure chapter3.md or chap3_fung_mcqs.md exist")
        example_quick_test()
    else:
        print("\n" + "="*60)
        print("Ready to run examples!")
        print("Uncomment the example you want to run below:")
        print("="*60)
        
        # Uncomment to run:
        # mcqs = example_from_chapter()
        # mcqs = example_from_mcqs()
        # example_access_data(mcqs)
        example_quick_test()
