import { useState, useEffect, useRef } from 'react'
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels'
import Editor from './Editor'
import './EditorPage.css'

/**
 * Página principal com o Monaco Editor integrado.
 * Componentes da página:
 * - Editor de código (esquerda)
 * - Painel NASM (direita) - placeholder para Sprint 2
 * - Terminal (inferior) - placeholder para Sprint 4
 */
export default function EditorPage({ onLogout }) {
  const [code, setCode] = useState(
    `// Bem-vindo ao Simples Editor!\n// Escreva código SIMPLES aqui\n\nleia x\nescreva x\n`
  )
  const [savedCode, setSavedCode] = useState(code)
  const [isRunning, setIsRunning] = useState(false)
  const [namsCollapsed, setNasmCollapsed] = useState(false)
  const resizerRef = useRef(null)

  // Salva o código em localStorage
  useEffect(() => {
    const handleSave = (e) => {
      setSavedCode(code)
      console.log('Código salvo:', code)
      // TODO: Salvar no backend/banco de dados (Sprint 3)
    }
    window.addEventListener('editor:save', handleSave)
    return () => window.removeEventListener('editor:save', handleSave)
  }, [code])

  const handleRun = () => {
    setIsRunning(true)
    console.log('Executando código:', code)
    // TODO: Enviar para backend para compilação (Sprint 3)
    setTimeout(() => setIsRunning(false), 2000)
  }

  const handleClear = () => {
    if (confirm('Deseja limpar o editor?')) {
      setCode('')
    }
  }

  const handleReset = () => {
    if (confirm('Deseja restaurar o código de exemplo?')) {
      setCode(`// Bem-vindo ao Simples Editor!\n// Escreva código SIMPLES aqui\n\nleia x\nescreva x\n`)
    }
  }

  const handleResizerDoubleClick = () => {
    setNasmCollapsed(!namsCollapsed)
  }

  const handleLogout = () => {
    onLogout()
  }

  return (
    <div className="editor-page">
      {/* Header */}
      <header className="editor-header">
        <div className="header-left">
          <h1>Simples Editor</h1>
          <span className="status-badge">Pronto</span>
        </div>
        <div className="header-right">
          <button
            className="btn btn-primary"
            onClick={handleRun}
            disabled={isRunning}
            title="Ctrl+Enter ou clique aqui"
          >
            {isRunning ? '▌ Executando...' : '▶ Run'}
          </button>
          <button className="btn btn-secondary" onClick={handleClear} title="Limpa o editor">
            Limpar
          </button>
          <button className="btn btn-secondary" onClick={handleReset} title="Restaura exemplo">
            Reset
          </button>
          <button className="btn btn-logout" onClick={handleLogout} title="Fazer logout">
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="editor-main">
        <PanelGroup direction="vertical">
          {/* Top: Editor + NASM (Horizontal Layout) */}
          <Panel defaultSize={70} minSize={40}>
            <PanelGroup direction="horizontal">
              {/* Left Panel - Editor */}
              <Panel defaultSize={40} minSize={30}>
                <div className="editor-container">
                  <div className="panel-header">
                    <span>📝 Editor</span>
                    <span className="file-name">código.simples</span>
                  </div>
                  <Editor
                    value={code}
                    onChange={setCode}
                    language="simples"
                    theme="vs-dark"
                    readOnly={false}
                    minimap={true}
                  />
                </div>
              </Panel>

              {/* Resizer with Double-Click Handler */}
              <PanelResizeHandle 
                className="resizer" 
                ref={resizerRef}
                onDoubleClick={handleResizerDoubleClick}
              />

              {/* Right Panel - NASM */}
              <Panel 
                defaultSize={60} 
                minSize={namsCollapsed ? 0 : 20}
                collapsible={true}
                onCollapse={() => setNasmCollapsed(true)}
                onExpand={() => setNasmCollapsed(false)}
              >
                <div className="nasm-container">
                  <div className="panel-header">
                    <span>⚙️ NASM Assembly</span>
                  </div>
                  <div className="nasm-content">
                    <p className="placeholder-text">NASM será exibido aqui após compilação</p>
                    <p className="placeholder-hint">(Dê double-click no separador para colapsar)</p>
                  </div>
                </div>
              </Panel>
            </PanelGroup>
          </Panel>

          {/* Vertical Resizer between Editor+NASM and Terminal */}
          <PanelResizeHandle className="resizer resizer-vertical" />

          {/* Bottom Panel - Terminal */}
          <Panel defaultSize={30} minSize={10}>
            <div className="terminal-container">
              <div className="panel-header">
                <span>💻 Terminal</span>
              </div>
              <div className="terminal-content">
                <p className="placeholder-text">Terminal será exibido aqui após execução</p>
                <p className="placeholder-hint">(Sprint 4 - WebSocket + xterm.js)</p>
              </div>
            </div>
          </Panel>
        </PanelGroup>
      </main>

      {/* Status Bar */}
      <div className="status-bar">
        <span>Linhas: {code.split('\n').length}</span>
        <span>•</span>
        <span>Caracteres: {code.length}</span>
        <span>•</span>
        <span>Salvo: {savedCode === code ? 'Sim ✓' : 'Não ✗'}</span>
        <span className="status-right">UTF-8 • CRLF • Simples</span>
      </div>
    </div>
  )
}
