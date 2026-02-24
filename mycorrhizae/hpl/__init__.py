"""
Hypha Programming Language (HPL) Module

A biologically-inspired programming language for computational
interaction with biological systems.

Components:
- Lexer: Tokenizes HPL source code
- Interpreter: Executes HPL programs
- Builtins: Built-in functions and sensor context
- Signal Patterns: Signal Pattern Language (SPL) for pattern matching
- Devices: Device interface modules for FCI hardware
"""

from .lexer import HPLLexer, Token, TokenType
from .interpreter import HPLInterpreter
from .builtins import HPLBuiltins, SensorContext
from .signal_patterns import (
    # Types
    Signal,
    SignalUnit,
    WaveformType,
    ComparisonOp,
    # Pattern definition
    Pattern,
    PatternConstraint,
    PatternParser,
    PatternMatcher,
    # Built-in patterns
    GFST_PATTERN_LIBRARY,
    # HPL functions
    match,
    correlation,
    best_pattern,
    register_pattern,
    get_pattern_matcher,
)

__all__ = [
    # Lexer
    "HPLLexer",
    "Token",
    "TokenType",
    # Interpreter
    "HPLInterpreter",
    "HPLBuiltins",
    "SensorContext",
    # Signal Pattern Language
    "Signal",
    "SignalUnit",
    "WaveformType",
    "ComparisonOp",
    "Pattern",
    "PatternConstraint",
    "PatternParser",
    "PatternMatcher",
    "GFST_PATTERN_LIBRARY",
    # HPL pattern functions
    "match",
    "correlation",
    "best_pattern",
    "register_pattern",
    "get_pattern_matcher",
]
