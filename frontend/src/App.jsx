import { useState, useEffect } from 'react'
import LoginPage from './pages/LoginPage'
import EditorPage from './components/EditorPage'
import { registerSimplesLanguage, registerSimplesAutocomplete } from './languages/simples'
import './App.css'

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [loading, setLoading] = useState(true)

  // Registra a linguagem SIMPLES ao carregar
  useEffect(() => {
    registerSimplesLanguage()
    registerSimplesAutocomplete()
  }, [])

  // Verifica se há token salvo ao carregar
  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      setIsLoggedIn(true)
    }
    setLoading(false)
  }, [])

  const handleLogin = (token) => {
    localStorage.setItem('auth_token', token)
    setIsLoggedIn(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    setIsLoggedIn(false)
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner"></div>
        <p>Carregando...</p>
      </div>
    )
  }

  return isLoggedIn ? <EditorPage onLogout={handleLogout} /> : <LoginPage onLogin={handleLogin} />
}

export default App
