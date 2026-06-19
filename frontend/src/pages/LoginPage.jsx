import { useState } from 'react'

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isSignUp, setIsSignUp] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const endpoint = isSignUp ? '/api/auth/signup' : '/api/auth/login'
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (response.ok) {
        onLogin(data.access_token)
      } else {
        setError(data.error || 'Erro na autenticação')
      }
    } catch (err) {
      setError('Erro ao conectar ao servidor: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <div className="auth-brand-panel">
          <div className="brand-badge">Simples Editor</div>
          <h1>Compilador<br />de Linguagem<br />SIMPLES</h1>
          <p>
            Editor online para a linguagem SIMPLES — escreva, compile e execute
            seus programas diretamente no navegador. Com suporte a NASM, terminal
            interativo e sandbox seguro.
          </p>
          <div className="feature-list">
            <article>
              <span>Editor</span>
              <h2>Monaco Editor</h2>
              <p>Syntax highlighting, autocomplete e marcadores de erro.</p>
            </article>
            <article>
              <span>Terminal</span>
              <h2>Interativo</h2>
              <p>Terminal xterm.js com suporte a stdin via WebSocket.</p>
            </article>
            <article>
              <span>Sandbox</span>
              <h2>Seguro</h2>
              <p>Execução isolada em container Docker com 9 camadas de segurança.</p>
            </article>
          </div>
        </div>

        <div className="auth-form-panel">
          <div className="auth-card">
            <div className="auth-card-header">
              <p className="eyebrow">Bem-vindo</p>
              <h2>{isSignUp ? 'Criar Conta' : 'Entrar'}</h2>
              <p>
                {isSignUp
                  ? 'Preencha os dados abaixo para criar sua conta.'
                  : 'Acesse sua conta para continuar.'}
              </p>
            </div>

            <form className="login-form" onSubmit={handleSubmit}>
              <div className="field-group">
                <span>Email</span>
                <input
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <div className="field-group">
                <span>Senha</span>
                <input
                  type="password"
                  placeholder="Mínimo 6 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  disabled={loading}
                />
              </div>

              {error && <div className="status-message">{error}</div>}

              <button type="submit" disabled={loading} className="primary-button">
                {loading ? 'Carregando...' : isSignUp ? 'Criar Conta' : 'Entrar'}
              </button>
            </form>

            <div className="card-footer">
              <p>
                {isSignUp ? 'Já tem uma conta? ' : 'Não tem uma conta? '}
                <button
                  type="button"
                  className="text-button"
                  onClick={() => {
                    setIsSignUp(!isSignUp)
                    setError('')
                  }}
                  disabled={loading}
                >
                  {isSignUp ? 'Entrar' : 'Criar Conta'}
                </button>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
