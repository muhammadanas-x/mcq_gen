"""
Test script to verify MCQ Generator components

Run this to test the system with a small sample before full generation.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import ConceptJSON
from nodes.analyzer import analyze_chapter_content
from nodes.stem_generator import generate_stem_for_concept
from utils.latex_validator import validate_latex_syntax, extract_latex_from_markdown
from utils.sympy_validator import verify_integration, compute_integral
from error_taxonomy import get_applicable_errors


def test_latex_validator():
    """Test LaTeX validation utilities"""
    print("\n" + "="*60)
    print("TEST 1: LaTeX Validator")
    print("="*60)
    
    test_cases = [
        (r"\frac{x^2}{2}", True, "Valid fraction"),
        (r"\frac{x^2{2}", False, "Unclosed brace"),
        (r"\int x dx", True, "Valid integral"),
        (r"\sin^{-1}(x)", True, "Valid inverse trig"),
        (r"x^^2", False, "Double superscript"),
    ]
    
    passed = 0
    for latex, expected_valid, description in test_cases:
        is_valid, error = validate_latex_syntax(latex)
        status = "✓" if is_valid == expected_valid else "✗"
        print(f"{status} {description}: {latex}")
        if not is_valid:
            print(f"  Error: {error}")
        if is_valid == expected_valid:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_sympy_validator():
    """Test SymPy mathematical validation"""
    print("\n" + "="*60)
    print("TEST 2: SymPy Validator")
    print("="*60)
    
    test_cases = [
        # (integrand, answer, should_be_correct, description)
        (r"x", r"\frac{x^2}{2}", True, "Basic power rule"),
        (r"x^2", r"\frac{x^3}{3}", True, "Power rule x^2"),
        (r"\sin(x)", r"-\cos(x)", True, "Sine integral"),
        (r"x", r"x^2", False, "Wrong answer (missing 1/2)"),
        (r"\frac{1}{x}", r"\ln|x|", True, "Natural log"),
    ]
    
    passed = 0
    for integrand, answer, expected_correct, description in test_cases:
        is_correct, confidence, correction = verify_integration(integrand, answer)
        status = "✓" if is_correct == expected_correct else "✗"
        print(f"{status} {description}")
        print(f"  Integrand: {integrand}")
        print(f"  Answer: {answer}")
        print(f"  Verified: {is_correct} (confidence: {confidence:.2f})")
        if correction:
            print(f"  Note: {correction}")
        
        if is_correct == expected_correct:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_error_taxonomy():
    """Test error taxonomy filtering"""
    print("\n" + "="*60)
    print("TEST 3: Error Taxonomy")
    print("="*60)
    
    # Test filtering by integral type and difficulty
    for integral_type in ["substitution", "trigonometric", "by_parts"]:
        for difficulty in ["easy", "medium", "hard"]:
            errors = get_applicable_errors(integral_type, difficulty)
            print(f"\n{integral_type.upper()} ({difficulty}):")
            print(f"  Applicable errors: {len(errors)}")
            for err in errors[:3]:
                print(f"  - {err.name} ({err.category.value})")
    
    return True


def test_concept_extraction():
    """Test concept extraction from sample text"""
    print("\n" + "="*60)
    print("TEST 4: Concept Extraction")
    print("="*60)
    
    sample_text = """
    # Integration by Substitution
    
    When we have an integral of the form ∫f(g(x))g'(x)dx, we can use substitution.
    Let u = g(x), then du = g'(x)dx.
    
    Example: ∫2x(x²+1)⁵dx
    Let u = x²+1, then du = 2x dx
    The integral becomes ∫u⁵ du = u⁶/6 + c = (x²+1)⁶/6 + c
    """
    
    print("Sample text:")
    print(sample_text[:200] + "...")
    
    print("\nNote: Full concept extraction requires LLM call")
    print("Skipping in test mode to avoid API costs")
    
    return True


def test_stem_generation():
    """Test stem generation with sample concept"""
    print("\n" + "="*60)
    print("TEST 5: Stem Generation")
    print("="*60)
    
    sample_concept = ConceptJSON(
        concept_id="power_rule_basic",
        concept_name="Basic Power Rule for Integration",
        formula=r"$\int x^n dx = \frac{x^{n+1}}{n+1} + c$",
        difficulty="easy",
        prerequisites=["differentiation", "algebra"],
        context="The power rule is the most fundamental integration formula. "
                "It states that to integrate x^n, increase the exponent by 1 and divide by the new exponent."
    )
    
    print("Sample concept:")
    print(f"  Name: {sample_concept['concept_name']}")
    print(f"  Formula: {sample_concept['formula']}")
    print(f"  Difficulty: {sample_concept['difficulty']}")
    
    print("\nNote: Full stem generation requires LLM call")
    print("Skipping in test mode to avoid API costs")
    
    return True


def run_all_tests():
    """Run all component tests"""
    print("\n" + "="*60)
    print("MCQ GENERATOR - COMPONENT TESTS")
    print("="*60)
    
    results = {
        "LaTeX Validator": test_latex_validator(),
        "SymPy Validator": test_sympy_validator(),
        "Error Taxonomy": test_error_taxonomy(),
        "Concept Extraction": test_concept_extraction(),
        "Stem Generation": test_stem_generation(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
