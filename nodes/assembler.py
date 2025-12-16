"""
MCQ Assembly Node

Assembles complete MCQs with shuffled options and comprehensive explanations.
Exports to formatted markdown matching the style of chap3_fung_mcqs.md.
"""

import random
from typing import Dict, List
from state import MCQGeneratorState, CompleteMCQ, Distractor


def shuffle_options(correct_answer: str, distractors: List[Distractor]) -> Dict:
    """
    Shuffle correct answer and distractors into options a, b, c, d.
    
    Args:
        correct_answer: LaTeX string for correct answer
        distractors: List of 3 Distractor objects
    
    Returns:
        {
            'options': {'a': '...', 'b': '...', 'c': '...', 'd': '...'},
            'correct_key': 'a'|'b'|'c'|'d',
            'explanations': {'a': '...', 'b': '...', ...}
        }
    """
    # Create list of all options with metadata
    all_options = [
        {
            'text': correct_answer,
            'is_correct': True,
            'explanation': 'This is the correct answer.'
        }
    ]
    
    for dist in distractors:
        all_options.append({
            'text': dist['option_text'],
            'is_correct': False,
            'explanation': dist['explanation']
        })
    
    # Shuffle
    random.shuffle(all_options)
    
    # Ensure we have exactly 4 options
    if len(all_options) < 4:
        # Generate unique filler options
        filler_templates = [
            '$\\text{None of these}$',
            '$\\text{Cannot be determined}$',
            '$\\text{The integral does not exist}$',
            '$\\text{Insufficient information}$'
        ]
        
        needed = 4 - len(all_options)
        for i in range(needed):
            all_options.append({
                'text': filler_templates[i] if i < len(filler_templates) else f'$\\text{{Option {i+1}}}$',
                'is_correct': False,
                'explanation': 'This is a filler option.'
            })
    
    all_options = all_options[:4]
    
    # Map to a, b, c, d
    option_keys = ['a', 'b', 'c', 'd']
    options = {}
    explanations = {}
    correct_key = None
    
    for key, option in zip(option_keys, all_options):
        options[key] = option['text']
        explanations[key] = option['explanation']
        if option['is_correct']:
            correct_key = key
    
    return {
        'options': options,
        'correct_key': correct_key,
        'explanations': explanations
    }


def format_mcq_markdown(mcq: CompleteMCQ, include_explanations: bool = True) -> str:
    """
    Format a single MCQ in markdown style matching chap3_fung_mcqs.md.
    
    Args:
        mcq: CompleteMCQ object
        include_explanations: Whether to include explanation section
    
    Returns:
        Formatted markdown string
    """
    lines = []
    
    # Question number and stem
    lines.append(f"**{mcq['question_number']}. {mcq['stem']}**")
    
    # Options
    for key in ['a', 'b', 'c', 'd']:
        option_text = mcq['options'][key]
        
        # Mark correct answer with bold
        if key == mcq['correct_answer']:
            lines.append(f"   *   **({key}) {option_text}**")
        else:
            lines.append(f"   *   ({key}) {option_text}")
    
    # Add explanation section if requested
    if include_explanations:
        lines.append("")
        lines.append("   **Explanation:**")
        lines.append(f"   - **Correct ({mcq['correct_answer']}):** {mcq['explanation']['correct']}")
        
        for key in ['a', 'b', 'c', 'd']:
            if key != mcq['correct_answer']:
                lines.append(f"   - **({key}):** {mcq['explanation'][key]}")
    
    lines.append("")  # Blank line between questions
    
    return "\n".join(lines)


def assembler_node(state: MCQGeneratorState) -> Dict:
    """
    LangGraph node that assembles complete MCQs and formats for export.
    
    Args:
        state: Current MCQGeneratorState
    
    Returns:
        Updated state: final_mcqs, metrics
    """
    print("\n" + "="*60)
    print("MCQ ASSEMBLY NODE")
    print("="*60)
    
    questions_with_distractors = state["questions_with_distractors"]
    print(f"Assembling {len(questions_with_distractors)} complete MCQs")
    
    # Handle empty case
    if len(questions_with_distractors) == 0:
        print("\n⚠ No questions available for assembly!")
        print("⚠ All questions failed validation. Consider:")
        print("  1. Using a different model (try gemini-1.5-pro instead of 2.5-pro)")
        print("  2. Checking input content quality")
        print("  3. Adjusting validation strictness")
        
        return {
            "final_mcqs": [],
            "metrics": {
                **state.get("metrics", {}),
                "final_mcqs_count": 0,
                "difficulty_distribution": {}
            }
        }
    
    final_mcqs = []
    
    for i, question_data in enumerate(questions_with_distractors):
        print(f"\n[{i+1}/{len(questions_with_distractors)}] Assembling MCQ {i+1}")
        
        # Shuffle options
        shuffled = shuffle_options(
            question_data['correct_answer'],
            question_data['distractors']
        )
        
        # Create explanation dict
        explanations = {
            'correct': f"This is the correct answer. {question_data.get('reasoning', 'Apply the appropriate integration technique.')}"
        }
        explanations.update(shuffled['explanations'])
        
        # Create CompleteMCQ
        mcq = CompleteMCQ(
            question_number=i + 1,
            concept_id=question_data['concept_id'],
            stem=question_data['stem'],
            options=shuffled['options'],
            correct_answer=shuffled['correct_key'],
            explanation=explanations,
            metadata={
                'difficulty': question_data['difficulty'],
                'validation_score': question_data['validation_score'],
                'was_corrected': question_data['was_corrected'],
                'integral_type': question_data.get('generation_metadata', {}).get('integral_type', 'general')
            }
        )
        
        final_mcqs.append(mcq)
        
        print(f"  ✓ Assembled with options: {', '.join(shuffled['options'].keys())}")
        print(f"  ✓ Correct answer: ({shuffled['correct_key']})")
    
    print(f"\n" + "="*60)
    print(f"ASSEMBLY SUMMARY")
    print(f"="*60)
    print(f"✓ Total MCQs assembled: {len(final_mcqs)}")
    
    # Calculate difficulty distribution
    difficulty_counts = {}
    for mcq in final_mcqs:
        diff = mcq['metadata']['difficulty']
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    print(f"✓ Difficulty distribution:")
    for diff, count in difficulty_counts.items():
        print(f"  - {diff}: {count} ({count/len(final_mcqs)*100:.1f}%)")
    
    return {
        "final_mcqs": final_mcqs,
        "metrics": {
            **state.get("metrics", {}),
            "final_mcqs_count": len(final_mcqs),
            "difficulty_distribution": difficulty_counts
        }
    }


def export_mcqs_to_markdown(mcqs: List[CompleteMCQ], output_path: str, 
                           include_explanations: bool = True, 
                           title: str = "Generated MCQs") -> None:
    """
    Export complete MCQs to markdown file.
    
    Args:
        mcqs: List of CompleteMCQ objects
        output_path: Path to output file
        include_explanations: Whether to include explanations
        title: Title for the markdown document
    """
    lines = [
        f"### {title}",
        "#### PRACTICE EXERCISE",
        ""
    ]
    
    for mcq in mcqs:
        mcq_text = format_mcq_markdown(mcq, include_explanations)
        lines.append(mcq_text)
    
    # Add footer with metadata
    lines.extend([
        "",
        "---",
        f"**Generated Questions:** {len(mcqs)}",
        f"**Difficulty Distribution:**",
    ])
    
    difficulty_counts = {}
    for mcq in mcqs:
        diff = mcq['metadata']['difficulty']
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    for diff, count in sorted(difficulty_counts.items()):
        lines.append(f"- {diff.capitalize()}: {count} questions")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\n✓ Exported {len(mcqs)} MCQs to: {output_path}")
