"""
Hypha Programming Language (HPL) Module

A biologically-inspired programming language for computational
interaction with biological systems.
"""

from .lexer import HPLLexer, Token, TokenType
from .interpreter import HPLInterpreter
from .builtins import HPLBuiltins, SensorContext

__all__ = [
    "HPLLexer",
    "Token",
    "TokenType",
    "HPLInterpreter",
    "HPLBuiltins",
    "SensorContext",
]
