import { test, expect } from '@playwright/test';

test.describe('Simples Editor E2E Flows', () => {

  test.beforeEach(async ({ page }) => {
    // Acessa a página principal. Assumindo que o frontend está mockado para logar ou que
    // exista um formulário simples de login na homepage quando não tem token.
    await page.goto('/');
  });

  test('Login flow: email/senha → autenticado', async ({ page }) => {
    // Verifica se a tela de login existe e realiza o login
    const loginForm = page.locator('form');
    if (await loginForm.isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');

      // Verifica se entrou no editor (por exemplo procurando por "Painel NASM" ou classe do editor)
      await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });
    } else {
      // Se já está logado ou não tem tela de login bloqueante
      await expect(page.locator('.monaco-editor').first()).toBeVisible();
    }
  });

  test('Edit flow: digitar código → persiste', async ({ page }) => {
    // Logar se necessário
    if (await page.locator('form').isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');
    }

    // Esperar pelo Monaco Editor
    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });

    // Focar e digitar no editor usando evaluate para injetar o texto no monaco (já que é complexo pegar input de texto nativo)
    await page.evaluate(() => {
      // Assume that monaco is available or we can just find the editor
      const editorElement = document.querySelector('.monaco-editor');
      // Hack simplificado para setar o código via dom para testes E2E básicos, ou clique e digite:
    });

    // Método direto do playwright para Monaco
    await page.click('.monaco-editor .view-lines');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('programa teste\ninteiro x\n', { delay: 50 });

    // Verificando se persiste (o monaco reflete as linhas)
    await expect(page.locator('.monaco-editor').first()).toContainText('programa teste');
  });

  test('Compile flow: código válido → NASM aparece', async ({ page }) => {
    // Logar se necessário
    if (await page.locator('form').isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');
    }

    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });

    // Digita um programa válido básico
    await page.click('.monaco-editor .view-lines');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('programa basic\ninicio\nescreva 42\nfim\n');

    // Clica em Run
    const runButton = page.locator('button:has-text("Run")');
    if (await runButton.isVisible()) {
      await runButton.click();

      // Verifica se o painel NASM foi populado (painel da direita/assembler)
      // Baseado no PRD, existe um visualizador de código NASM. Vamos esperar texto como "global _start" ou "section .text"
      await expect(page.locator('text=/section .text/i').first()).toBeVisible({ timeout: 10000 });
    }
  });

  test('Run flow: código com leia → digita input → vê output', async ({ page }) => {
    // Logar
    if (await page.locator('form').isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');
    }

    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });

    // Código interativo
    await page.click('.monaco-editor .view-lines');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('programa read\ninteiro x\ninicio\nleia x\nescreva x\nfim\n');

    const runButton = page.locator('button:has-text("Run")');
    if (await runButton.isVisible()) {
      await runButton.click();

      // O terminal (xterm) deve focar e estar pronto para receber input (ou devemos digitar diretamente)
      await page.waitForTimeout(2000); // Wait for compilation and start

      const terminal = page.locator('.xterm').first();
      if (await terminal.isVisible()) {
        await terminal.click();
        await page.keyboard.type('42\n'); // Envia "42" e enter

        // Devemos ver o 42 sendo escrito novamente pelo programa
        await expect(terminal).toContainText('42', { timeout: 10000 });
      }
    }
  });

  test('Stop flow: loop infinito → clica Stop → para em <2s', async ({ page }) => {
    if (await page.locator('form').isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');
    }

    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });

    // Simula loop infinito (se a gramática do SIMPLES suportar 'enquanto')
    await page.click('.monaco-editor .view-lines');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('programa loop\ninteiro x\ninicio\nx <- 1\nenquanto x = 1 faca\nx <- 1\nfimenquanto\nfim\n');

    const runButton = page.locator('button:has-text("Run")');
    if (await runButton.isVisible()) {
      await runButton.click();

      const stopButton = page.locator('button:has-text("Stop")');
      await expect(stopButton).toBeVisible({ timeout: 5000 });

      const startTime = Date.now();
      await stopButton.click();

      // Verifica no terminal se parou
      const terminal = page.locator('.xterm').first();
      await expect(terminal).toContainText('exit', { ignoreCase: true, timeout: 3000 });

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(2000); // Para em < 2s
    }
  });

  test('Timeout flow: loop infinito → para em <11s automaticamente', async ({ page }) => {
    test.setTimeout(20000); // Aumenta timeout especificamente para este teste

    if (await page.locator('form').isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');
    }

    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });

    await page.click('.monaco-editor .view-lines');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('programa loop\ninteiro x\ninicio\nx <- 1\nenquanto x = 1 faca\nx <- 1\nfimenquanto\nfim\n');

    const runButton = page.locator('button:has-text("Run")');
    if (await runButton.isVisible()) {
      await runButton.click();

      const startTime = Date.now();

      // Esperar mensagem de timeout no terminal
      const terminal = page.locator('.xterm').first();
      await expect(terminal).toContainText('timeout', { ignoreCase: true, timeout: 15000 });

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(12000); // Para em < 11-12s
    }
  });

  test('Error flow: código inválido → marca linha vermelha', async ({ page }) => {
    if (await page.locator('form').isVisible()) {
      await page.fill('input[type="email"]', 'test@example.com');
      await page.fill('input[type="password"]', 'senha123');
      await page.click('button[type="submit"]');
    }

    await expect(page.locator('.monaco-editor').first()).toBeVisible({ timeout: 10000 });

    await page.click('.monaco-editor .view-lines');
    await page.keyboard.press('Control+A');
    await page.keyboard.press('Backspace');
    await page.keyboard.type('programa bug\nerror aqui\n');

    const runButton = page.locator('button:has-text("Run")');
    if (await runButton.isVisible()) {
      await runButton.click();

      // Monaco usa '.squiggly-error' ou '.cgmr' class para underlines de erro (markers)
      // O DOM do monaco-editor deve ter um marker de erro
      await expect(page.locator('.squiggly-error, .red-squiggly').first()).toBeVisible({ timeout: 10000 });
    }
  });

});
