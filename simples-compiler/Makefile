CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2
SRCDIR = src
OBJDIR = obj

SRCS = $(SRCDIR)/main.c $(SRCDIR)/lexer.c $(SRCDIR)/parser.c $(SRCDIR)/codegen.c $(SRCDIR)/ast.c
OBJS = $(SRCS:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
TARGET = simplesc

.PHONY: all clean test install

all: $(TARGET)

$(OBJDIR):
	mkdir -p $(OBJDIR)

$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) -o $(TARGET)

clean:
	rm -rf $(OBJDIR) $(TARGET)

test: $(TARGET)
	@echo "=== Testando compilacao SIMPLES ==="
	@$(CC) $(CFLAGS) -c $(SRCDIR)/ast.c -o /dev/null && echo "[OK] ast.c compila"
	@$(CC) $(CFLAGS) -c $(SRCDIR)/lexer.c -o /dev/null && echo "[OK] lexer.c compila"
	@$(CC) $(CFLAGS) -c $(SRCDIR)/parser.c -o /dev/null && echo "[OK] parser.c compila"
	@$(CC) $(CFLAGS) -c $(SRCDIR)/codegen.c -o /dev/null && echo "[OK] codegen.c compila"
	@$(CC) $(CFLAGS) -c $(SRCDIR)/main.c -o /dev/null && echo "[OK] main.c compila"
	@echo "[OK] Todos os modulos compilam"

install: $(TARGET)
	cp $(TARGET) /usr/local/bin/$(TARGET)
