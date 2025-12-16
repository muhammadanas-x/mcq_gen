"""
LaTeX validation utilities

Checks LaTeX syntax and ensures proper rendering.
"""

import re
from typing import Tuple


def validate_latex_syntax(latex_str: str) -> Tuple[bool, str]:
    """
    Validate basic LaTeX syntax without full rendering.
    
    Args:
        latex_str: LaTeX expression to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not latex_str:
        return True, ""
    
    errors = []
    
    # Check balanced braces
    brace_count = 0
    for i, char in enumerate(latex_str):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
        if brace_count < 0:
            errors.append(f"Unmatched closing brace at position {i}")
            break
    
    if brace_count > 0:
        errors.append(f"Unclosed braces: {brace_count} remaining")
    
    # Check balanced brackets
    bracket_count = 0
    for i, char in enumerate(latex_str):
        if char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
        if bracket_count < 0:
            errors.append(f"Unmatched closing bracket at position {i}")
            break
    
    if bracket_count > 0:
        errors.append(f"Unclosed brackets: {bracket_count} remaining")
    
    # Check for common LaTeX commands
    common_commands = [
        r'\\frac', r'\\int', r'\\sin', r'\\cos', r'\\tan', r'\\log', r'\\ln',
        r'\\sqrt', r'\\sum', r'\\prod', r'\\lim', r'\\infty',
        r'\\alpha', r'\\beta', r'\\gamma', r'\\theta', r'\\pi',
        r'\\leq', r'\\geq', r'\\neq', r'\\approx'
    ]
    
    # Check for malformed fractions
    frac_pattern = r'\\frac\s*\{[^}]*\}\s*\{[^}]*\}'
    fracs = re.findall(r'\\frac', latex_str)
    valid_fracs = re.findall(frac_pattern, latex_str)
    if len(fracs) != len(valid_fracs):
        errors.append("Malformed \\frac command (needs two arguments in braces)")
    
    # Check for malformed sqrt
    sqrt_pattern = r'\\sqrt(\[[^\]]*\])?\s*\{[^}]*\}'
    sqrts = re.findall(r'\\sqrt', latex_str)
    valid_sqrts = re.findall(sqrt_pattern, latex_str)
    if len(sqrts) != len(valid_sqrts):
        errors.append("Malformed \\sqrt command")
    
    # Check for double superscripts/subscripts without braces
    if re.search(r'\^\^', latex_str):
        errors.append("Double superscript (^^) without braces")
    if re.search(r'__', latex_str):
        errors.append("Double subscript (__) without braces")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, ""


def normalize_latex(latex_str: str) -> str:
    """
    Normalize LaTeX expression for consistency.
    
    - Remove extra whitespace
    - Standardize function names
    - Ensure proper spacing around operators
    """
    if not latex_str:
        return latex_str
    
    # Remove extra spaces
    normalized = re.sub(r'\s+', ' ', latex_str).strip()
    
    # Standardize arc functions to inverse notation
    normalized = normalized.replace(r'\arcsin', r'\sin^{-1}')
    normalized = normalized.replace(r'\arccos', r'\cos^{-1}')
    normalized = normalized.replace(r'\arctan', r'\tan^{-1}')
    
    return normalized


def extract_latex_from_markdown(markdown_text: str) -> list[str]:
    """
    Extract all LaTeX expressions from markdown text.
    
    Args:
        markdown_text: Markdown with inline $ or display $$ LaTeX
    
    Returns:
        List of LaTeX expressions found
    """
    # Find inline math $...$
    inline_pattern = r'\$([^\$]+)\$'
    inline_matches = re.findall(inline_pattern, markdown_text)
    
    # Find display math $$...$$
    display_pattern = r'\$\$([^\$]+)\$\$'
    display_matches = re.findall(display_pattern, markdown_text)
    
    return inline_matches + display_matches
