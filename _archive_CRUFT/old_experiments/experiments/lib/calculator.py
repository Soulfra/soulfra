#!/usr/bin/env python3
"""
Calculator - From Scratch Math Operations (Zero Dependencies)

Builds a calculator from primitives to teach the tier system.
No eval(), no external libraries - just basic operators.

Philosophy: Show how complex operations build from simple ones.

Tier System:
TIER 0: Numbers (int, float)
TIER 1: Basic ops (+, -, *, /)
TIER 2: Functions (sqrt, pow, abs)
TIER 3: Expressions (parse and evaluate)
TIER 4: Complex calculations (statistics, trigonometry)

Usage:
    from lib.calculator import calculate, parse_expression

    result = calculate('+', 5, 3)  # 8
    result = parse_expression('2 + 3 * 4')  # 14
"""

import re
from typing import Union, List


# ==============================================================================
# TIER 1: BASIC OPERATIONS
# ==============================================================================

def add(a: float, b: float) -> float:
    """Addition"""
    return a + b


def subtract(a: float, b: float) -> float:
    """Subtraction"""
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiplication"""
    return a * b


def divide(a: float, b: float) -> float:
    """Division (handles divide by zero)"""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def calculate(operator: str, a: float, b: float) -> float:
    """
    Calculate using basic operators

    Args:
        operator: One of +, -, *, /
        a: First number
        b: Second number

    Returns:
        Result

    Example:
        >>> calculate('+', 5, 3)
        8.0
    """
    ops = {
        '+': add,
        '-': subtract,
        '*': multiply,
        '/': divide,
    }

    if operator not in ops:
        raise ValueError(f"Unknown operator: {operator}")

    return ops[operator](a, b)


# ==============================================================================
# TIER 2: FUNCTIONS
# ==============================================================================

def sqrt(n: float) -> float:
    """
    Square root using Newton's method (from scratch)

    No math.sqrt needed - we build it ourselves!
    """
    if n < 0:
        raise ValueError("Cannot take square root of negative number")

    if n == 0:
        return 0.0

    # Newton's method: x_{n+1} = (x_n + n/x_n) / 2
    guess = n / 2.0
    for _ in range(50):  # Iterations
        guess = (guess + n / guess) / 2.0

    return guess


def power(base: float, exponent: int) -> float:
    """
    Power function (from scratch)

    No ** operator - we build it ourselves!
    """
    if exponent == 0:
        return 1.0

    if exponent < 0:
        return 1.0 / power(base, -exponent)

    result = 1.0
    for _ in range(exponent):
        result *= base

    return result


def absolute(n: float) -> float:
    """Absolute value"""
    return n if n >= 0 else -n


# ==============================================================================
# TIER 3: EXPRESSION PARSING
# ==============================================================================

def parse_expression(expr: str) -> float:
    """
    Parse and evaluate a mathematical expression

    Supports:
    - Basic operators: +, -, *, /
    - Parentheses: (2 + 3) * 4
    - Order of operations (PEMDAS)

    Args:
        expr: Mathematical expression as string

    Returns:
        Result

    Example:
        >>> parse_expression('2 + 3 * 4')
        14.0
        >>> parse_expression('(2 + 3) * 4')
        20.0
    """
    # Remove whitespace
    expr = expr.replace(' ', '')

    # Tokenize
    tokens = _tokenize(expr)

    # Parse and evaluate
    return _evaluate(tokens)


def _tokenize(expr: str) -> List[str]:
    """Convert expression string to tokens"""
    tokens = []
    current_number = ''

    for char in expr:
        if char.isdigit() or char == '.':
            current_number += char
        elif char in '+-*/()':
            if current_number:
                tokens.append(current_number)
                current_number = ''
            tokens.append(char)
        else:
            raise ValueError(f"Invalid character: {char}")

    if current_number:
        tokens.append(current_number)

    return tokens


def _evaluate(tokens: List[str]) -> float:
    """
    Evaluate tokenized expression

    Uses recursive descent parsing for order of operations
    """
    # Convert to numbers/operators
    for i in range(len(tokens)):
        if tokens[i] not in '+-*/()':
            tokens[i] = float(tokens[i])

    # Handle parentheses first
    while '(' in tokens:
        # Find innermost parentheses
        start = -1
        for i in range(len(tokens)):
            if tokens[i] == '(':
                start = i
            elif tokens[i] == ')':
                # Evaluate contents
                result = _evaluate_simple(tokens[start+1:i])
                tokens = tokens[:start] + [result] + tokens[i+1:]
                break

    return _evaluate_simple(tokens)


def _evaluate_simple(tokens: List) -> float:
    """Evaluate expression without parentheses (handles order of operations)"""
    # First pass: * and /
    i = 0
    while i < len(tokens):
        if tokens[i] == '*':
            result = tokens[i-1] * tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        elif tokens[i] == '/':
            result = tokens[i-1] / tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        else:
            i += 1

    # Second pass: + and -
    i = 0
    while i < len(tokens):
        if tokens[i] == '+':
            result = tokens[i-1] + tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        elif tokens[i] == '-':
            result = tokens[i-1] - tokens[i+1]
            tokens = tokens[:i-1] + [result] + tokens[i+2:]
        else:
            i += 1

    return tokens[0]


# ==============================================================================
# TIER 4: STATISTICS
# ==============================================================================

def mean(numbers: List[float]) -> float:
    """Calculate average"""
    if not numbers:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(numbers) / len(numbers)


def median(numbers: List[float]) -> float:
    """Calculate median"""
    if not numbers:
        raise ValueError("Cannot calculate median of empty list")

    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)

    if n % 2 == 0:
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        return sorted_numbers[n//2]


# ==============================================================================
# TESTING
# ==============================================================================

if __name__ == '__main__':
    print("🧪 Testing Calculator (From Scratch)\n")

    # Test TIER 1: Basic ops
    print("TIER 1: Basic Operations")
    print(f"  5 + 3 = {calculate('+', 5, 3)}")
    print(f"  5 - 3 = {calculate('-', 5, 3)}")
    print(f"  5 * 3 = {calculate('*', 5, 3)}")
    print(f"  6 / 2 = {calculate('/', 6, 2)}")
    print()

    # Test TIER 2: Functions
    print("TIER 2: Functions (from scratch)")
    print(f"  sqrt(16) = {sqrt(16)}")
    print(f"  sqrt(2) ≈ {sqrt(2):.10f}")
    print(f"  power(2, 8) = {power(2, 8)}")
    print(f"  abs(-5) = {absolute(-5)}")
    print()

    # Test TIER 3: Expression parsing
    print("TIER 3: Expression Parsing")
    print(f"  2 + 3 * 4 = {parse_expression('2 + 3 * 4')}")
    print(f"  (2 + 3) * 4 = {parse_expression('(2 + 3) * 4')}")
    print(f"  10 / 2 + 3 = {parse_expression('10 / 2 + 3')}")
    print()

    # Test TIER 4: Statistics
    print("TIER 4: Statistics")
    numbers = [1, 2, 3, 4, 5]
    print(f"  mean({numbers}) = {mean(numbers)}")
    print(f"  median({numbers}) = {median(numbers)}")
    print()

    print("✅ Calculator tests complete!")
    print("\n💡 All built from scratch - no math lib, no eval()!")
