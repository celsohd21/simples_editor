#ifndef CODEGEN_H
#define CODEGEN_H

#include <stdio.h>
#include "ast.h"

typedef struct {
    int offset;
} VarEntry;

typedef struct {
    VarEntry *vars;
    char **names;
    int count;
    int capacity;
    int stack_offset;
    int string_count;
    int label_count;
} Codegen;

void codegen_init(Codegen *cg);
void codegen_free(Codegen *cg);
void codegen_generate(Codegen *cg, ASTNode *node, FILE *out);
int codegen_error_count(Codegen *cg);

#endif
