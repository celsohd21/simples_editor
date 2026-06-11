#ifndef LEXER_H
#define LEXER_H

typedef enum {
    TOK_EOF, TOK_IDENT, TOK_NUMBER, TOK_STRING,
    TOK_PROGRAMA, TOK_INICIO, TOK_FIM,
    TOK_LEIA, TOK_ESCREVA,
    TOK_ENQUANTO, TOK_FACA, TOK_FIMENQUANTO,
    TOK_PARA, TOK_DE, TOK_ATE, TOK_PASSO, TOK_FIMPARA,
    TOK_SE, TOK_ENTAO, TOK_SENAO, TOK_FIMSE,
    TOK_INTEIRO, TOK_REAL, TOK_CARACTERE, TOK_BOOLEANO,
    TOK_VERDADEIRO, TOK_FALSO,
    TOK_E, TOK_OU, TOK_NAO,
    TOK_ATRIB, TOK_IGUAL, TOK_DIF,
    TOK_MENOR, TOK_MAIOR, TOK_MENORIG, TOK_MAIORIG,
    TOK_MAIS, TOK_MENOS, TOK_MULT, TOK_DIV,
    TOK_ABREPAR, TOK_FECHAPAR,
    TOK_VIRGULA,
} TokenType;

typedef struct {
    TokenType type;
    char *lexeme;
    int line;
} Token;

typedef struct {
    const char *source;
    int pos;
    int line;
    Token current;
    int error_count;
} Lexer;

void lexer_init(Lexer *lex, const char *source);
Token lexer_next(Lexer *lex);
Token lexer_peek(Lexer *lex);
void lexer_advance(Lexer *lex);
const char *token_type_name(TokenType t);

#endif
