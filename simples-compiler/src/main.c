#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lexer.h"
#include "parser.h"
#include "codegen.h"

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) {
        fprintf(stderr, "Erro: nao foi possivel abrir '%s'\n", path);
        return NULL;
    }
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    rewind(f);
    char *buf = malloc(len + 1);
    if (!buf) { fclose(f); return NULL; }
    fread(buf, 1, len, f);
    buf[len] = '\0';
    fclose(f);
    return buf;
}

static void print_usage(void) {
    fprintf(stderr, "Uso: simplesc <arquivo.simples> [-o <saida.asm>]\n");
    fprintf(stderr, "  Compila codigo SIMPLES para NASM assembly.\n");
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        print_usage();
        return 1;
    }

    const char *input_path = NULL;
    const char *output_path = NULL;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            output_path = argv[++i];
        } else if (argv[i][0] != '-') {
            input_path = argv[i];
        }
    }

    if (!input_path) {
        fprintf(stderr, "Erro: nenhum arquivo fonte especificado\n");
        print_usage();
        return 1;
    }

    char *source = read_file(input_path);
    if (!source) return 1;

    Lexer lex;
    lexer_init(&lex, source);

    Parser parser;
    parser_init(&parser, &lex);

    ASTNode *ast = parser_parse(&parser);

    if (!ast || parser.error_count > 0) {
        fprintf(stderr, "\nCompilacao falhou com %d erro(s) sintatico(s).\n", parser.error_count);
        free(source);
        if (ast) ast_free(ast);
        return 1;
    }

    Codegen cg;
    codegen_init(&cg);

    FILE *out = stdout;
    if (output_path) {
        out = fopen(output_path, "w");
        if (!out) {
            fprintf(stderr, "Erro: nao foi possivel criar '%s'\n", output_path);
            free(source);
            ast_free(ast);
            codegen_free(&cg);
            return 1;
        }
    }

    codegen_generate(&cg, ast, out);

    if (output_path) fclose(out);

    fprintf(stdout, "\n[OK] Assembly gerado com sucesso");
    if (output_path) fprintf(stdout, ": %s", output_path);
    fprintf(stdout, "\n");

    ast_free(ast);
    codegen_free(&cg);
    free(source);
    return 0;
}
