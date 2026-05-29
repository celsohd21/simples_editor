import { useState } from 'react'
import './App.css'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/health`, {
        method: 'GET',
      })

      if (response.ok) {
        setIsAuthenticated(true)
        setEmail('')
        setPassword('')
      } else {
        setError('Falha ao conectar com o backend')
      }
    } catch (err) {
      setError('Erro de conexão: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="login-container">
        <div className="login-box">
          <h1>🖥️ Simples Editor</h1>
          <p>IDE Web para linguagem SIMPLES</p>
          
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input
                id="email"
                type="email"
                placeholder="seu@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Senha:</label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" disabled={loading}>
              {loading ? 'Conectando...' : 'Entrar'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="editor-container">
      <header className="header">
        <h1>📝 Simples Editor</h1>
        <button onClick={() => setIsAuthenticated(false)}>Sair</button>
      </header>

      <main className="main-content">
        <div className="panels">
          <div className="panel editor-panel">
            <h2>Editor SIMPLES</h2>
            <p style={{ padding: '20px', color: '#888' }}>
              Editor de código será renderizado aqui (Sprint 2)
            </p>
          </div>

          <div className="panel nasm-panel">
            <h2>Painel NASM</h2>
            <p style={{ padding: '20px', color: '#888' }}>
              Assembly gerado será exibido aqui (Sprint 2)
            </p>
          </div>
        </div>

        <div className="panel terminal-panel">
          <h2>Terminal</h2>
          <p style={{ padding: '20px', color: '#888' }}>
            Terminal interativo será aqui (Sprint 4)
          </p>
        </div>
      </main>

      <footer className="footer">
        <p>Backend Health: <span id="health-status">✅ OK</span></p>
      </footer>
    </div>
  )
}

export default App
