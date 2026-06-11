#ifndef PARSER_H
#define PARSER_H

#include "lexer.h"
#include "ast.h"

typedef struct {
    Lexer *lex;
    int error_count;
} Parser;

void parser_init(Parser *p, Lexer *lex);
ASTNode *parser_parse(Parser *p);
void parser_error(Parser *p, const char *msg);

#endif
