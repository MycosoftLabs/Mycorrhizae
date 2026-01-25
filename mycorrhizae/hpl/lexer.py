"""
HPL Lexer - Hypha Programming Language Tokenizer

Tokenizes HPL source code into a stream of tokens for the interpreter.
HPL uses biological metaphors for programming constructs:
- spawn: Create a new process/agent
- branch: Conditional branching
- sense: Read sensor data
- emit: Output data/signals
- fruit: Produce final output
- decay: Clean up resources
- grow: Accumulate/loop
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    """Token types in HPL."""
    # Keywords (biological metaphors)
    SPAWN = auto()      # spawn - create process
    BRANCH = auto()     # branch - conditional
    SENSE = auto()      # sense - read input
    EMIT = auto()       # emit - output signal
    FRUIT = auto()      # fruit - final output
    DECAY = auto()      # decay - cleanup
    GROW = auto()       # grow - loop/accumulate
    HYPHA = auto()      # hypha - variable
    MYCELIUM = auto()   # mycelium - collection
    SUBSTRATE = auto()  # substrate - environment
    ENZYME = auto()     # enzyme - function
    
    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    EQ = auto()         # ==
    NE = auto()         # !=
    LT = auto()         # <
    GT = auto()         # >
    LE = auto()         # <=
    GE = auto()         # >=
    ASSIGN = auto()     # =
    ARROW = auto()      # ->
    
    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    DOT = auto()
    
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Special
    COMMENT = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    """A token from HPL source code."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:{self.column})"


# Keyword mapping
KEYWORDS = {
    "spawn": TokenType.SPAWN,
    "branch": TokenType.BRANCH,
    "sense": TokenType.SENSE,
    "emit": TokenType.EMIT,
    "fruit": TokenType.FRUIT,
    "decay": TokenType.DECAY,
    "grow": TokenType.GROW,
    "hypha": TokenType.HYPHA,
    "mycelium": TokenType.MYCELIUM,
    "substrate": TokenType.SUBSTRATE,
    "enzyme": TokenType.ENZYME,
}


class HPLLexer:
    """
    Lexer for the Hypha Programming Language.
    
    Tokenizes HPL source code into a stream of tokens.
    """
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    @property
    def current_char(self) -> Optional[str]:
        """Get current character or None if at end."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek(self, offset: int = 1) -> Optional[str]:
        """Peek at character ahead."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> Optional[str]:
        """Advance to next character."""
        char = self.current_char
        self.pos += 1
        
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def add_token(self, token_type: TokenType, value: str) -> None:
        """Add a token to the stream."""
        self.tokens.append(Token(
            type=token_type,
            value=value,
            line=self.line,
            column=self.column - len(value),
        ))
    
    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char and self.current_char in " \t\r":
            self.advance()
    
    def read_number(self) -> str:
        """Read a numeric literal."""
        start = self.pos
        has_dot = False
        
        while self.current_char and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                if has_dot:
                    break
                has_dot = True
            self.advance()
        
        return self.source[start:self.pos]
    
    def read_string(self, quote: str) -> str:
        """Read a string literal."""
        self.advance()  # Skip opening quote
        start = self.pos
        
        while self.current_char and self.current_char != quote:
            if self.current_char == "\\":
                self.advance()  # Skip escape
            self.advance()
        
        value = self.source[start:self.pos]
        self.advance()  # Skip closing quote
        
        return value
    
    def read_identifier(self) -> str:
        """Read an identifier or keyword."""
        start = self.pos
        
        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            self.advance()
        
        return self.source[start:self.pos]
    
    def read_comment(self) -> str:
        """Read a comment (# to end of line)."""
        start = self.pos
        
        while self.current_char and self.current_char != "\n":
            self.advance()
        
        return self.source[start:self.pos]
    
    def tokenize(self) -> List[Token]:
        """Tokenize the entire source code."""
        while self.current_char:
            self.skip_whitespace()
            
            if not self.current_char:
                break
            
            char = self.current_char
            
            # Newline
            if char == "\n":
                self.add_token(TokenType.NEWLINE, char)
                self.advance()
            
            # Comment
            elif char == "#":
                comment = self.read_comment()
                self.add_token(TokenType.COMMENT, comment)
            
            # Number
            elif char.isdigit():
                number = self.read_number()
                self.add_token(TokenType.NUMBER, number)
            
            # String
            elif char in "\"'":
                string = self.read_string(char)
                self.add_token(TokenType.STRING, string)
            
            # Identifier/Keyword
            elif char.isalpha() or char == "_":
                ident = self.read_identifier()
                token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
                self.add_token(token_type, ident)
            
            # Operators
            elif char == "+":
                self.add_token(TokenType.PLUS, char)
                self.advance()
            elif char == "-":
                if self.peek() == ">":
                    self.advance()
                    self.advance()
                    self.add_token(TokenType.ARROW, "->")
                else:
                    self.add_token(TokenType.MINUS, char)
                    self.advance()
            elif char == "*":
                self.add_token(TokenType.STAR, char)
                self.advance()
            elif char == "/":
                self.add_token(TokenType.SLASH, char)
                self.advance()
            elif char == "%":
                self.add_token(TokenType.PERCENT, char)
                self.advance()
            elif char == "=":
                if self.peek() == "=":
                    self.advance()
                    self.advance()
                    self.add_token(TokenType.EQ, "==")
                else:
                    self.add_token(TokenType.ASSIGN, char)
                    self.advance()
            elif char == "!":
                if self.peek() == "=":
                    self.advance()
                    self.advance()
                    self.add_token(TokenType.NE, "!=")
                else:
                    self.advance()  # Skip unknown
            elif char == "<":
                if self.peek() == "=":
                    self.advance()
                    self.advance()
                    self.add_token(TokenType.LE, "<=")
                else:
                    self.add_token(TokenType.LT, char)
                    self.advance()
            elif char == ">":
                if self.peek() == "=":
                    self.advance()
                    self.advance()
                    self.add_token(TokenType.GE, ">=")
                else:
                    self.add_token(TokenType.GT, char)
                    self.advance()
            
            # Delimiters
            elif char == "(":
                self.add_token(TokenType.LPAREN, char)
                self.advance()
            elif char == ")":
                self.add_token(TokenType.RPAREN, char)
                self.advance()
            elif char == "{":
                self.add_token(TokenType.LBRACE, char)
                self.advance()
            elif char == "}":
                self.add_token(TokenType.RBRACE, char)
                self.advance()
            elif char == "[":
                self.add_token(TokenType.LBRACKET, char)
                self.advance()
            elif char == "]":
                self.add_token(TokenType.RBRACKET, char)
                self.advance()
            elif char == ",":
                self.add_token(TokenType.COMMA, char)
                self.advance()
            elif char == ":":
                self.add_token(TokenType.COLON, char)
                self.advance()
            elif char == ";":
                self.add_token(TokenType.SEMICOLON, char)
                self.advance()
            elif char == ".":
                self.add_token(TokenType.DOT, char)
                self.advance()
            
            else:
                # Unknown character - skip
                self.advance()
        
        self.add_token(TokenType.EOF, "")
        return self.tokens
