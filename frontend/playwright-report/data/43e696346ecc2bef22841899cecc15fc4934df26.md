# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: simples-editor.spec.js >> Simples Editor E2E Flows >> Compile flow: código válido → NASM aparece
- Location: e2e/simples-editor.spec.js:55:3

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost/
Call log:
  - navigating to "http://localhost/", waiting until "load"

```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   |
  3   | test.describe('Simples Editor E2E Flows', () => {
  4   |
  5   |   test.beforeEach(async ({ page }) => {
  6   |     // Acessa a página principal. Assumindo que o frontend está mockado para logar ou que
  7   |     // exista um formulário simples de login na homepage quando não tem token.
> 8   |     await page.goto('/');
      |                ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost/
  9   |   });
  10  |
  11  |   test('Login flow: email/senha → autenticado', async ({ page }) => {
  12  |     // Verifica se a tela de login existe e realiza o login
  13  |     const loginForm = page.locator('form');
  14  |     if (await loginForm.isVisible()) {
  15  |       await page.fill('input[type="email"]', 'test@example.com');
  16  |       await page.fill('input[type="password"]', 'senha123');
  17  |       await page.click('button[type="submit"]');
  18  |
  19  |       // Verifica se entrou no editor (por exemplo procurando por "Painel NASM" ou classe do editor)
  20  |       await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  21  |     } else {
  22  |       // Se já está logado ou não tem tela de login bloqueante
  23  |       await expect(page.locator('.monaco-editor').first()).toBeVisible();
  24  |     }
  25  |   });
  26  |
  27  |   test('Edit flow: digitar código → persiste', async ({ page }) => {
  28  |     // Logar se necessário
  29  |     if (await page.locator('form').isVisible()) {
  30  |       await page.fill('input[type="email"]', 'test@example.com');
  31  |       await page.fill('input[type="password"]', 'senha123');
  32  |       await page.click('button[type="submit"]');
  33  |     }
  34  |
  35  |     // Esperar pelo Monaco Editor
  36  |     await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  37  |
  38  |     // Focar e digitar no editor usando evaluate para injetar o texto no monaco (já que é complexo pegar input de texto nativo)
  39  |     await page.evaluate(() => {
  40  |       // Assume that monaco is available or we can just find the editor
  41  |       const editorElement = document.querySelector('.monaco-editor');
  42  |       // Hack simplificado para setar o código via dom para testes E2E básicos, ou clique e digite:
  43  |     });
  44  |
  45  |     // Método direto do playwright para Monaco
  46  |     await page.click('.monaco-editor .view-lines');
  47  |     await page.keyboard.press('Control+A');
  48  |     await page.keyboard.press('Backspace');
  49  |     await page.keyboard.type('programa teste\ninteiro x\n', { delay: 50 });
  50  |
  51  |     // Verificando se persiste (o monaco reflete as linhas)
  52  |     await expect(page.locator('.monaco-editor').first()).toContainText('programa teste');
  53  |   });
  54  |
  55  |   test('Compile flow: código válido → NASM aparece', async ({ page }) => {
  56  |     // Logar se necessário
  57  |     if (await page.locator('form').isVisible()) {
  58  |       await page.fill('input[type="email"]', 'test@example.com');
  59  |       await page.fill('input[type="password"]', 'senha123');
  60  |       await page.click('button[type="submit"]');
  61  |     }
  62  |
  63  |     await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  64  |
  65  |     // Digita um programa válido básico
  66  |     await page.click('.monaco-editor .view-lines');
  67  |     await page.keyboard.press('Control+A');
  68  |     await page.keyboard.press('Backspace');
  69  |     await page.keyboard.type('programa basic\ninicio\nescreva 42\nfim\n');
  70  |
  71  |     // Clica em Run
  72  |     const runButton = page.locator('button:has-text("Run")');
  73  |     if (await runButton.isVisible()) {
  74  |       await runButton.click();
  75  |
  76  |       // Verifica se o painel NASM foi populado (painel da direita/assembler)
  77  |       // Baseado no PRD, existe um visualizador de código NASM. Vamos esperar texto como "global _start" ou "section .text"
  78  |       await expect(page.locator('text=/section .text/i').first()).toBeVisible({ timeout: 10000 });
  79  |     }
  80  |   });
  81  |
  82  |   test('Run flow: código com leia → digita input → vê output', async ({ page }) => {
  83  |     // Logar
  84  |     if (await page.locator('form').isVisible()) {
  85  |       await page.fill('input[type="email"]', 'test@example.com');
  86  |       await page.fill('input[type="password"]', 'senha123');
  87  |       await page.click('button[type="submit"]');
  88  |     }
  89  |
  90  |     await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
  91  |
  92  |     // Código interativo
  93  |     await page.click('.monaco-editor .view-lines');
  94  |     await page.keyboard.press('Control+A');
  95  |     await page.keyboard.press('Backspace');
  96  |     await page.keyboard.type('programa read\ninteiro x\ninicio\nleia x\nescreva x\nfim\n');
  97  |
  98  |     const runButton = page.locator('button:has-text("Run")');
  99  |     if (await runButton.isVisible()) {
  100 |       await runButton.click();
  101 |
  102 |       // O terminal (xterm) deve focar e estar pronto para receber input (ou devemos digitar diretamente)
  103 |       await page.waitForTimeout(2000); // Wait for compilation and start
  104 |
  105 |       const terminal = page.locator('.xterm').first();
  106 |       if (await terminal.isVisible()) {
  107 |         await terminal.click();
  108 |         await page.keyboard.type('42\n'); // Envia "42" e enter
```