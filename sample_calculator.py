"""
Sample calculator module for testing the test generator.

This module provides basic calculator functions and a Calculator class
to demonstrate test generation capabilities.
"""

from typing import List


def add(a: float, b: float) -> float:
    """
    Add two numbers.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    return a + b


def subtract(a: float, b: float) -> float:
    """
    Subtract b from a.
    
    Args:
        a: First number
        b: Number to subtract
    
    Returns:
        Difference of a and b
    """
    return a - b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """
    Divide a by b.
    
    Args:
        a: Numerator
        b: Denominator
    
    Returns:
        Quotient of a and b
    
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def calculate_average(numbers: List[float]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: List of numbers
    
    Returns:
        Average value
    
    Raises:
        ValueError: If list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


class Calculator:
    """
    A simple calculator class with memory feature.
    
    Attributes:
        memory: Stored value in memory
    """
    
    def __init__(self, initial_value: float = 0.0):
        """
        Initialize calculator.
        
        Args:
            initial_value: Initial memory value
        """
        self.memory = initial_value
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers and store in memory."""
        result = a + b
        self.memory = result
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a and store in memory."""
        result = a - b
        self.memory = result
        return result
    
    def get_memory(self) -> float:
        """Get current memory value."""
        return self.memory
    
    def clear_memory(self) -> None:
        """Clear memory."""
        self.memory = 0.0
    
    def add_to_memory(self, value: float) -> float:
        """
        Add value to memory.
        
        Args:
            value: Value to add
        
        Returns:
            New memory value
        """
        self.memory += value
        return self.memory
    
    def __str__(self) -> str:
        """String representation."""
        return f"Calculator(memory={self.memory})"
    
    def __repr__(self) -> str:
        """Representation."""
        return f"Calculator({self.memory})"


class ScientificCalculator(Calculator):
    """Scientific calculator with advanced operations."""
    
    def power(self, base: float, exponent: float) -> float:
        """
        Calculate base raised to exponent.
        
        Args:
            base: Base number
            exponent: Exponent
        
        Returns:
            Result of base^exponent
        """
        result = base ** exponent
        self.memory = result
        return result
    
    def square_root(self, number: float) -> float:
        """
        Calculate square root.
        
        Args:
            number: Number to calculate square root of
        
        Returns:
            Square root of number
        
        Raises:
            ValueError: If number is negative
        """
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        
        result = number ** 0.5
        self.memory = result
        return result
