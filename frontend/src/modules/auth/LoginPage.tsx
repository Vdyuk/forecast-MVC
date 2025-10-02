import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ThemeToggle } from '../../components/ThemeToggle'

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()

    // Простая аутентификация для демо
    if (username === 'admin' && password === 'admin') {
      localStorage.setItem('auth', 'true')
      localStorage.setItem('user', JSON.stringify({
        username: 'admin',
        role: 'dispatcher',
        name: 'Диспетчер АО "Мосводоканал"'
      }))
      // Принудительная перезагрузка страницы для обновления состояния
      window.location.href = '/'
    } else {
      setError('Неверные учетные данные')
    }
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'var(--bg)'
    }}>
      <div className="panel" style={{ width: 400, padding: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <div className="title" style={{ fontSize: 24 }}>
            Мониторинг системы водоснабжения
          </div>
          <ThemeToggle />
        </div>
        <div style={{ textAlign: 'center', marginBottom: 24, color: 'var(--muted)' }}>
          Вход в систему
        </div>

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>Логин</label>
            <input
              className="input"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Введите логин"
              required
              style={{ width: '100%' }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', marginBottom: 8 }}>Пароль</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Введите пароль"
              required
              style={{ width: '100%' }}
            />
          </div>

          {error && (
            <div style={{ color: 'var(--red)', marginBottom: 16, textAlign: 'center' }}>
              {error}
            </div>
          )}

          <button className="button primary" type="submit" style={{ width: '100%' }}>
            Войти
          </button>
        </form>

        <div style={{ marginTop: 24, padding: 16, backgroundColor: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
          <div style={{ fontSize: 14, color: 'var(--muted)', marginBottom: 8 }}>Демо-аккаунт Диспетчера МВК:</div>
          <div style={{ fontSize: 12, color: 'var(--muted)' }}>
            <div>Логин: admin</div>
            <div>Пароль: admin</div>
          </div>
        </div>
      </div>
    </div>
  )
}
