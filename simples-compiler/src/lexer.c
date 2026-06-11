#include "lexer.h"
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>

static const char *keywords[] = {
    "programa", "inicio", "fim",
    "leia", "escreva",
    "enquanto", "faca", "fimenquanto",
    "para", "de", "ate", "passo", "fimpara",
    "se", "entao", "senao", "fimse",
    "inteiro", "real", "caractere", "booleano",
    "verdadeiro", "falso",
    "e", "ou", "nao",
    NULL
};

static TokenType keyword_tokens[] = {
    TOK_PROGRAMA, TOK_INICIO, TOK_FIM,
    TOK_LEIA, TOK_ESCREVA,
    TOK_ENQUANTO, TOK_FACA, TOK_FIMENQUANTO,
    TOK_PARA, TOK_DE, TOK_ATE, TOK_PASSO, TOK_FIMPARA,
    TOK_SE, TOK_ENTAO, TOK_SENAO, TOK_FIMSE,
    TOK_INTEIRO, TOK_REAL, TOK_CARACTERE, TOK_BOOLEANO,
    TOK_VERDADEIRO, TOK_FALSO,
    TOK_E, TOK_OU, TOK_NAO,
};

static int is_keyword(const char *s) {
    for (int i = 0; keywords[i]; i++) {
        if (strcmp(s, keywords[i]) == 0) return i;
    }
    return -1;
}

static Token make_token(Lexer *lex, TokenType type, int start, int end) {
    Token t;
    t.type = type;
    t.line = lex->line;
    int len = end - start;
    t.lexeme = malloc(len + 1);
    strncpy(t.lexeme, lex->source + start, len);
    t.lexeme[len] = '\0';
    return t;
}

static void skip_comment(Lexer *lex) {
    while (lex->source[lex->pos] && lex->source[lex->pos] != '}') {
        if (lex->source[lex->pos] == '\n') lex->line++;
        lex->pos++;
    }
    if (lex->source[lex->pos] == '}') lex->pos++;
}

static void skip_line_comment(Lexer *lex) {
    while (lex->source[lex->pos] && lex->source[lex->pos] != '\n') {
        lex->pos++;
    }
}

void lexer_init(Lexer *lex, const char *source) {
    lex->source = source;
    lex->pos = 0;
    lex->line = 1;
    lex->error_count = 0;
    lex->current = lexer_next(lex);
}

static int is_at_end(Lexer *lex) {
    return lex->source[lex->pos] == '\0';
}

static char advance(Lexer *lex) {
    return lex->source[lex->pos++];
}

static char peek(Lexer *lex) {
    return lex->source[lex->pos];
}

Token lexer_next(Lexer *lex) {
    while (!is_at_end(lex)) {
        char c = advance(lex);

        if (c == '\n') {
            lex->line++;
            continue;
        }
        if (isspace(c)) continue;

        if (c == '{') {
            skip_comment(lex);
            continue;
        }
        if (c == '/' && peek(lex) == '/') {
            advance(lex);
            skip_line_comment(lex);
            continue;
        }

        int start = lex->pos - 1;

        if (isalpha(c) || c == '_') {
            while (isalnum(peek(lex)) || peek(lex) == '_') advance(lex);
            int end = lex->pos;
            int len = end - start;
            char *buf = malloc(len + 1);
            strncpy(buf, lex->source + start, len);
            buf[len] = '\0';
            Token t = make_token(lex, TOK_IDENT, start, end);
            free(t.lexeme);
            t.lexeme = buf;
            int kw = is_keyword(t.lexeme);
            if (kw >= 0) {
                t.type = keyword_tokens[kw];
            }
            return t;
        }

        if (isdigit(c)) {
            while (isdigit(peek(lex))) advance(lex);
            return make_token(lex, TOK_NUMBER, start, lex->pos);
        }

        if (c == '"') {
            while (peek(lex) != '"' && !is_at_end(lex)) {
                if (peek(lex) == '\n') lex->line++;
                advance(lex);
            }
            if (peek(lex) == '"') advance(lex);
            return make_token(lex, TOK_STRING, start, lex->pos);
        }

        switch (c) {
            case ':':
                if (peek(lex) == '=') { advance(lex); return make_token(lex, TOK_ATRIB, start, lex->pos); }
                break;
            case '=': return make_token(lex, TOK_IGUAL, start, lex->pos);
            case '<':
                if (peek(lex) == '=') { advance(lex); return make_token(lex, TOK_MENORIG, start, lex->pos); }
                if (peek(lex) == '>') { advance(lex); return make_token(lex, TOK_DIF, start, lex->pos); }
                return make_token(lex, TOK_MENOR, start, lex->pos);
            case '>':
                if (peek(lex) == '=') { advance(lex); return make_token(lex, TOK_MAIORIG, start, lex->pos); }
                return make_token(lex, TOK_MAIOR, start, lex->pos);
            case '+': return make_token(lex, TOK_MAIS, start, lex->pos);
            case '-': return make_token(lex, TOK_MENOS, start, lex->pos);
            case '*': return make_token(lex, TOK_MULT, start, lex->pos);
            case '/': return make_token(lex, TOK_DIV, start, lex->pos);
            case '(': return make_token(lex, TOK_ABREPAR, start, lex->pos);
            case ')': return make_token(lex, TOK_FECHAPAR, start, lex->pos);
            case ',': return make_token(lex, TOK_VIRGULA, start, lex->pos);
        }

        fprintf(stderr, "Erro lexico (linha %d): caractere inesperado '%c'\n", lex->line, c);
        lex->error_count++;
    }

    return make_token(lex, TOK_EOF, lex->pos, lex->pos);
}

Token lexer_peek(Lexer *lex) {
    return lex->current;
}

void lexer_advance(Lexer *lex) {
    free(lex->current.lexeme);
    lex->current = lexer_next(lex);
}

const char *token_type_name(TokenType t) {
    static const char *names[] = {
        "EOF", "IDENT", "NUMERO", "STRING",
        "programa", "inicio", "fim",
        "leia", "escreva",
        "enquanto", "faca", "fimenquanto",
        "para", "de", "ate", "passo", "fimpara",
        "se", "entao", "senao", "fimse",
        "inteiro", "real", "caractere", "booleano",
        "verdadeiro", "falso",
        "e", "ou", "nao",
        ":=", "=", "<>",
        "<", ">", "<=", ">=",
        "+", "-", "*", "/",
        "(", ")",
        ",",
    };
    if (t < 0 || t >= (int)(sizeof(names)/sizeof(names[0]))) return "DESCONHECIDO";
    return names[t];
}
