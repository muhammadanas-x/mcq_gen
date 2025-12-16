"""
SymPy Integration Utilities - IMPROVED VERSION

Mathematical validation using symbolic computation with robust LaTeX parsing.
"""

import sympy as sp
from sympy import symbols, integrate, diff, simplify, latex, sympify, parse_expr
from typing import Tuple, Optional
import re


def latex_to_sympy(latex_expr: str) -> Optional[sp.Expr]:
    """
    Convert LaTeX expression to SymPy expression with robust parsing.
    
    Args:
        latex_expr: LaTeX string (without $ delimiters)
    
    Returns:
        SymPy expression or None if parsing fails
    """
    try:
        cleaned = latex_expr.strip().replace('$', '')
        
        # Remove spacing and formatting commands
        for cmd in [r'\,', r'\:', r'\;', r'\!', r'\ ']:
            cleaned = cleaned.replace(cmd, ' ')
        
        # Handle \left and \right
        cleaned = re.sub(r'\\left\(', '(', cleaned)
        cleaned = re.sub(r'\\right\)', ')', cleaned)
        cleaned = cleaned.replace(r'\left', '').replace(r'\right', '')
        
        # Remove constants at the end
        cleaned = re.sub(r'\s*\+\s*[CcKk]\s*$', '', cleaned)
        
        # Replace fractions (handle nesting)
        for _ in range(3):
            cleaned = re.sub(r'\\frac\{([^{}]*)\}\{([^{}]*)\}', r'((\1)/(\2))', cleaned)
        
        # Replace sqrt
        for _ in range(2):
            cleaned = re.sub(r'\\sqrt\{([^{}]+)\}', r'sqrt(\1)', cleaned)
        
        # Replace absolute values
        cleaned = re.sub(r'\|([^|]+)\|', r'Abs(\1)', cleaned)
        
        # Operators
        cleaned = cleaned.replace(r'\cdot', '*').replace(r'\times', '*')
        
        # Trig powers: \sin^{2}(x) -> sin(x)**2
        cleaned = re.sub(r'\\sin\^\{(\d+)\}\(([^)]+)\)', r'sin(\2)**\1', cleaned)
        cleaned = re.sub(r'\\cos\^\{(\d+)\}\(([^)]+)\)', r'cos(\2)**\1', cleaned)
        cleaned = re.sub(r'\\tan\^\{(\d+)\}\(([^)]+)\)', r'tan(\2)**\1', cleaned)
        cleaned = re.sub(r'\\sec\^\{(\d+)\}\(([^)]+)\)', r'sec(\2)**\1', cleaned)
        cleaned = re.sub(r'\\csc\^\{(\d+)\}\(([^)]+)\)', r'csc(\2)**\1', cleaned)
        cleaned = re.sub(r'\\cot\^\{(\d+)\}\(([^)]+)\)', r'cot(\2)**\1', cleaned)
        
        # Trig without args: \sin^2 x -> sin(x)**2
        cleaned = re.sub(r'\\sin\^\{(\d+)\}\s+([a-zA-Z0-9]+)', r'sin(\2)**\1', cleaned)
        cleaned = re.sub(r'\\cos\^\{(\d+)\}\s+([a-zA-Z0-9]+)', r'cos(\2)**\1', cleaned)
        cleaned = re.sub(r'\\tan\^\{(\d+)\}\s+([a-zA-Z0-9]+)', r'tan(\2)**\1', cleaned)
        
        # Regular trig with args
        cleaned = re.sub(r'\\sin\(([^)]+)\)', r'sin(\1)', cleaned)
        cleaned = re.sub(r'\\cos\(([^)]+)\)', r'cos(\1)', cleaned)
        cleaned = re.sub(r'\\tan\(([^)]+)\)', r'tan(\1)', cleaned)
        cleaned = re.sub(r'\\sec\(([^)]+)\)', r'sec(\1)', cleaned)
        cleaned = re.sub(r'\\csc\(([^)]+)\)', r'csc(\1)', cleaned)
        cleaned = re.sub(r'\\cot\(([^)]+)\)', r'cot(\1)', cleaned)
        
        # Basic trig
        cleaned = cleaned.replace(r'\sin', 'sin')
        cleaned = cleaned.replace(r'\cos', 'cos')
        cleaned = cleaned.replace(r'\tan', 'tan')
        cleaned = cleaned.replace(r'\sec', 'sec')
        cleaned = cleaned.replace(r'\csc', 'csc')
        cleaned = cleaned.replace(r'\cot', 'cot')
        
        # Inverse trig
        cleaned = re.sub(r'\\sin\^\{-1\}', 'asin', cleaned)
        cleaned = re.sub(r'\\cos\^\{-1\}', 'acos', cleaned)
        cleaned = re.sub(r'\\tan\^\{-1\}', 'atan', cleaned)
        
        # Log functions
        cleaned = re.sub(r'\\ln\(([^)]+)\)', r'log(\1)', cleaned)
        cleaned = cleaned.replace(r'\ln', 'log')
        cleaned = cleaned.replace(r'\log', 'log')
        
        # Exponentials and constants
        cleaned = cleaned.replace(r'\exp', 'exp')
        cleaned = cleaned.replace(r'\pi', 'pi')
        
        # Implicit multiplication: 7x -> 7*x
        cleaned = re.sub(r'(\d+)([a-zA-Z])', r'\1*\2', cleaned)
        
        # Clean spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Parse
        x = symbols('x')
        expr = parse_expr(cleaned, local_dict={'x': x, 'e': sp.E, 'pi': sp.pi}, transformations='all')
        return expr
    
    except:
        return None


def verify_integration(integrand_latex: str, answer_latex: str, variable: str = 'x') -> Tuple[bool, float, Optional[str]]:
    """
    Verify that answer is correct by differentiating and comparing to integrand.
    
    Args:
        integrand_latex: The function being integrated (LaTeX)
        answer_latex: The proposed integral result (LaTeX)
        variable: Variable of integration (default 'x')
    
    Returns:
        (is_correct, confidence_score, correction_or_error_message)
    """
    try:
        var = symbols(variable)
        
        integrand = latex_to_sympy(integrand_latex)
        answer = latex_to_sympy(answer_latex)
        
        if integrand is None:
            return False, 0.0, "Could not parse integrand"
        if answer is None:
            return False, 0.0, "Could not parse answer"
        
        # Differentiate the answer
        derivative = diff(answer, var)
        derivative_simplified = simplify(derivative)
        
        # Compare with integrand
        difference = simplify(integrand - derivative_simplified)
        
        if difference == 0:
            return True, 1.0, None
        
        # Try harder simplification
        expanded_diff = simplify(difference.expand())
        if expanded_diff == 0:
            return True, 0.95, None
        
        # Check trig identities
        trig_simplified = simplify(difference.rewrite(sp.sin))
        if trig_simplified == 0:
            return True, 0.9, None
        
        # If not equal, try to compute correct answer
        try:
            correct_answer = integrate(integrand, var)
            correct_latex = f"${latex(correct_answer)} + c$"
            return False, 0.0, f"Correct answer: {correct_latex}"
        except:
            return False, 0.0, f"Derivative {derivative_simplified} doesn't match integrand {integrand}"
    
    except Exception as e:
        return False, 0.0, f"Validation error: {str(e)}"


def compute_integral(integrand_latex: str, variable: str = 'x', 
                     definite: bool = False, lower_bound: Optional[str] = None, 
                     upper_bound: Optional[str] = None) -> Optional[str]:
    """
    Compute integral using SymPy.
    
    Args:
        integrand_latex: Function to integrate (LaTeX)
        variable: Variable of integration
        definite: Whether it's a definite integral
        lower_bound: Lower limit (LaTeX) if definite
        upper_bound: Upper limit (LaTeX) if definite
    
    Returns:
        LaTeX string of result or None if computation fails
    """
    try:
        var = symbols(variable)
        integrand = latex_to_sympy(integrand_latex)
        
        if integrand is None:
            return None
        
        if definite and lower_bound and upper_bound:
            lower = latex_to_sympy(lower_bound)
            upper = latex_to_sympy(upper_bound)
            
            if lower is None or upper is None:
                return None
            
            result = integrate(integrand, (var, lower, upper))
        else:
            result = integrate(integrand, var)
        
        result_simplified = simplify(result)
        latex_result = latex(result_simplified)
        
        return f"${latex_result}$" if not definite else f"${latex_result}$"
    
    except Exception as e:
        return None


def extract_integrand_from_question(question_stem: str) -> Optional[str]:
    """
    Extract integrand from question text.
    
    Args:
        question_stem: Full question text
    
    Returns:
        LaTeX string of integrand or None
    """
    # Look for ∫...dx pattern or \int ... dx pattern
    patterns = [
        r'\$\\int\s+(.+?)\s+dx\$',  # \int f(x) dx
        r'\$\\int\s+(.+?)\s+\\,\s*dx\$',  # \int f(x) \, dx
        r'\$\\int_\{[^}]+\}\^\{[^}]+\}\s+(.+?)\s+\\,?\s*dx\$',  # \int_a^b f(x) dx
        r'∫\s*(.+?)\s*dx',  # Unicode integral
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question_stem)
        if match:
            return match.group(1).strip()
    
    return None
