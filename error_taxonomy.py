"""
Error Taxonomy for Distractor Generation

Systematic categorization of common student errors in integration,
derived from analyzing patterns in chap3_fung_mcqs.md.

Each error type includes:
- Description of the mistake
- Template for generating plausible distractors
- Applicability conditions (which types of integrals)
"""

from typing import List, Dict, Callable
from enum import Enum


class ErrorCategory(Enum):
    """High-level categories of integration errors"""
    ALGEBRAIC = "algebraic"
    CALCULUS_SPECIFIC = "calculus_specific"
    TRIGONOMETRIC = "trigonometric"
    NOTATIONAL = "notational"
    CONCEPTUAL = "conceptual"


class ErrorType:
    """Definition of a specific error pattern"""
    
    def __init__(
        self,
        error_id: str,
        name: str,
        category: ErrorCategory,
        description: str,
        example_correct: str,
        example_wrong: str,
        applicability: List[str],  # Types of integrals this applies to
        frequency: float = 0.5  # How common this error is (0-1)
    ):
        self.error_id = error_id
        self.name = name
        self.category = category
        self.description = description
        self.example_correct = example_correct
        self.example_wrong = example_wrong
        self.applicability = applicability
        self.frequency = frequency


# ============================================================================
# ALGEBRAIC ERRORS
# ============================================================================

SIGN_FLIP = ErrorType(
    error_id="alg_sign_flip",
    name="Sign Error",
    category=ErrorCategory.ALGEBRAIC,
    description="Student changes sign incorrectly (+ becomes -, - becomes +)",
    example_correct=r"-\cot(\ln x)",
    example_wrong=r"\cot(\ln x)",
    applicability=["all"],
    frequency=0.7
)

COEFFICIENT_ERROR = ErrorType(
    error_id="alg_coeff_error",
    name="Missing or Wrong Coefficient",
    category=ErrorCategory.ALGEBRAIC,
    description="Student forgets division factor (1/n, 1/a, etc) or uses wrong value",
    example_correct=r"\frac{1}{3}\tan(nx)",
    example_wrong=r"\tan(nx)",  # Missing 1/n
    applicability=["substitution", "chain_rule"],
    frequency=0.8
)

EXPONENT_OFF_BY_ONE = ErrorType(
    error_id="alg_exp_error",
    name="Exponent Off-by-One",
    category=ErrorCategory.ALGEBRAIC,
    description="Uses n+1 instead of n-1, or 1-n instead of -n",
    example_correct=r"\frac{ax^{1-n}}{1-n}",
    example_wrong=r"\frac{ax^{n-1}}{n-1}",
    applicability=["power_rule"],
    frequency=0.6
)

# ============================================================================
# CALCULUS-SPECIFIC ERRORS
# ============================================================================

CHAIN_RULE_FORGOTTEN = ErrorType(
    error_id="calc_chain_forgotten",
    name="Chain Rule Factor Missing",
    category=ErrorCategory.CALCULUS_SPECIFIC,
    description="Student integrates without including du/dx factor",
    example_correct=r"\frac{1}{2}\sin^{-1}(\frac{x^2}{2})",
    example_wrong=r"\sin^{-1}(\frac{x^2}{2})",  # Missing 1/2x from chain rule
    applicability=["substitution", "composition"],
    frequency=0.9
)

WRONG_FORMULA = ErrorType(
    error_id="calc_wrong_formula",
    name="Integration Formula Confusion",
    category=ErrorCategory.CALCULUS_SPECIFIC,
    description="Student applies wrong standard formula (e.g., sin formula for cos)",
    example_correct=r"\frac{x}{2} + \frac{\sin 2ax}{4a}",
    example_wrong=r"\frac{\cos ax}{2a}",
    applicability=["trigonometric", "exponential"],
    frequency=0.5
)

INTEGRATION_BY_PARTS_ERROR = ErrorType(
    error_id="calc_parts_error",
    name="Integration by Parts Incomplete",
    category=ErrorCategory.CALCULUS_SPECIFIC,
    description="Student forgets subtraction term or reverses u and dv",
    example_correct=r"x\sin x + \cos x",
    example_wrong=r"x\sin x",  # Missing -∫v du term
    applicability=["by_parts"],
    frequency=0.6
)

LIMITS_REVERSED = ErrorType(
    error_id="calc_limits_reversed",
    name="Definite Integral Limits Reversed",
    category=ErrorCategory.CALCULUS_SPECIFIC,
    description="Student evaluates F(a) - F(b) instead of F(b) - F(a)",
    example_correct=r"F(b) - F(a)",
    example_wrong=r"F(a) - F(b)",
    applicability=["definite_integral"],
    frequency=0.4
)

# ============================================================================
# TRIGONOMETRIC ERRORS
# ============================================================================

TRIG_IDENTITY_CONFUSION = ErrorType(
    error_id="trig_identity_confusion",
    name="Trigonometric Identity Misapplied",
    category=ErrorCategory.TRIGONOMETRIC,
    description="Student confuses sin/cos, tan/cot, sec/csc",
    example_correct=r"\sin^{-1}(\sin x - \cos x)",
    example_wrong=r"\sin^{-1}(\sin x + \cos x)",
    applicability=["trigonometric"],
    frequency=0.7
)

INVERSE_FUNCTION_ERROR = ErrorType(
    error_id="trig_inverse_error",
    name="Inverse Trigonometric Function Confusion",
    category=ErrorCategory.TRIGONOMETRIC,
    description="Student confuses sin⁻¹ with cos⁻¹, or tan⁻¹ with cot⁻¹",
    example_correct=r"\sin^{-1}((\frac{x}{a})^{3/2})",
    example_wrong=r"\cos^{-1}((\frac{x}{a})^{3/2})",
    applicability=["inverse_trig"],
    frequency=0.5
)

# ============================================================================
# NOTATIONAL ERRORS
# ============================================================================

ABSOLUTE_VALUE_MISSING = ErrorType(
    error_id="not_abs_missing",
    name="Missing Absolute Value in Logarithm",
    category=ErrorCategory.NOTATIONAL,
    description="Student writes ln(x) instead of ln|x|",
    example_correct=r"\ln|x+3|",
    example_wrong=r"\ln(x+3)",
    applicability=["logarithmic"],
    frequency=0.6
)

CONSTANT_OMITTED = ErrorType(
    error_id="not_const_omitted",
    name="Constant of Integration Missing",
    category=ErrorCategory.NOTATIONAL,
    description="Student forgets +C in indefinite integral",
    example_correct=r"\frac{x^5}{5} + 12x + c",
    example_wrong=r"\frac{x^5}{5} + 12x",
    applicability=["indefinite_integral"],
    frequency=0.4
)

# ============================================================================
# CONCEPTUAL ERRORS
# ============================================================================

DERIVATIVE_INSTEAD_OF_INTEGRAL = ErrorType(
    error_id="conc_deriv_instead",
    name="Differentiation Instead of Integration",
    category=ErrorCategory.CONCEPTUAL,
    description="Student applies derivative rule instead of anti-derivative",
    example_correct=r"\frac{x^5}{5} + 12x + c",
    example_wrong=r"5x^4 + 12",
    applicability=["basic_integral"],
    frequency=0.3
)

PROPERTY_MISAPPLICATION = ErrorType(
    error_id="conc_prop_error",
    name="Integration Property Misapplied",
    category=ErrorCategory.CONCEPTUAL,
    description="Student incorrectly applies linearity or other properties",
    example_correct=r"\int [f(x) + g(x)] dx = \int f(x)dx + \int g(x)dx",
    example_wrong=r"\int [f(x) \cdot g(x)] dx = \int f(x)dx \cdot \int g(x)dx",
    applicability=["properties"],
    frequency=0.5
)


# ============================================================================
# ERROR TAXONOMY REGISTRY
# ============================================================================

ERROR_TAXONOMY = [
    SIGN_FLIP,
    COEFFICIENT_ERROR,
    EXPONENT_OFF_BY_ONE,
    CHAIN_RULE_FORGOTTEN,
    WRONG_FORMULA,
    INTEGRATION_BY_PARTS_ERROR,
    LIMITS_REVERSED,
    TRIG_IDENTITY_CONFUSION,
    INVERSE_FUNCTION_ERROR,
    ABSOLUTE_VALUE_MISSING,
    CONSTANT_OMITTED,
    DERIVATIVE_INSTEAD_OF_INTEGRAL,
    PROPERTY_MISAPPLICATION,
]


def get_applicable_errors(integral_type: str, difficulty: str) -> List[ErrorType]:
    """
    Filter error taxonomy based on integral type and difficulty.
    
    Args:
        integral_type: Type of integral (e.g., "substitution", "trigonometric")
        difficulty: "easy", "medium", or "hard"
    
    Returns:
        List of ErrorType objects applicable to this integral
    """
    applicable = []
    
    for error in ERROR_TAXONOMY:
        # Check if error applies to this integral type
        if "all" in error.applicability or integral_type in error.applicability:
            # Filter by difficulty (harder errors for harder problems)
            if difficulty == "easy" and error.frequency >= 0.6:
                applicable.append(error)
            elif difficulty == "medium" and error.frequency >= 0.4:
                applicable.append(error)
            elif difficulty == "hard":
                applicable.append(error)
    
    return applicable


def get_error_by_category(category: ErrorCategory) -> List[ErrorType]:
    """Get all errors in a specific category"""
    return [e for e in ERROR_TAXONOMY if e.category == category]


# ============================================================================
# DISTRACTOR GENERATION TEMPLATES
# ============================================================================

DISTRACTOR_TEMPLATES = {
    "sign_flip": "Change the sign of the {component} in the answer",
    "coeff_missing": "Remove the coefficient {coefficient} from the answer",
    "coeff_wrong": "Replace coefficient {old_coeff} with {new_coeff}",
    "exponent_error": "Change exponent from {correct_exp} to {wrong_exp}",
    "chain_rule": "Remove the factor {factor} that comes from chain rule",
    "formula_swap": "Use formula for {wrong_func} instead of {correct_func}",
    "trig_identity": "Replace {correct_trig} with {wrong_trig}",
    "inverse_swap": "Use {wrong_inverse} instead of {correct_inverse}",
    "abs_value": "Remove absolute value bars from logarithm",
    "constant": "Omit the constant of integration",
}
