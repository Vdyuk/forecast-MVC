import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

type User = {
  username: string
  role: string
  name: string
}

export const UserInfo: React.FC = () => {
  const [user, setUser] = useState<User | null>(null)
  const [showMenu, setShowMenu] = useState(false)
  const navigate = useNavigate()
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const userData = localStorage.getItem('user')
    if (userData) {
      setUser(JSON.parse(userData))
    }
  }, [])

  // Закрытие меню при клике вне его
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowMenu(false)
      }
    }

    if (showMenu) {
      // Небольшая задержка для предотвращения немедленного закрытия при открытии
      const timeoutId = setTimeout(() => {
        document.addEventListener('mousedown', handleClickOutside)
      }, 100)

      return () => {
        clearTimeout(timeoutId)
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [showMenu])

  const handleLogout = () => {
    localStorage.removeItem('auth')
    localStorage.removeItem('user')
    // Принудительная перезагрузка страницы для обновления состояния
    window.location.href = '/login'
  }

  if (!user) return null

  const getRoleDisplay = (role: string) => {
    switch (role) {
      case 'dispatcher': return 'Диспетчер АО "Мосводоканал"'
      case 'analyst': return 'Аналитик ГБУ "МАЦ"'
      default: return role
    }
  }

  const handleButtonClick = () => {
    setShowMenu(!showMenu)
  }

  return (
    <div style={{ position: 'relative' }} ref={menuRef}>
      <button
        className="button ghost"
        onClick={handleButtonClick}
        style={{ display: 'flex', alignItems: 'center', gap: 8 }}
      >
        <span>👤</span>
        <span>{user.name}</span>
        <span>▼</span>
      </button>

      {showMenu && (
        <>
          {/* Фон для закрытия меню */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 9999,
              backgroundColor: 'rgba(0,0,0,0.1)'
            }}
            onClick={() => setShowMenu(false)}
          />

          {/* Выпадающее меню */}
          <div style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: 8,
            backgroundColor: 'var(--panel)',
            border: '1px solid rgba(0,0,0,0.1)',
            borderRadius: 8,
            padding: 12,
            minWidth: 200,
            zIndex: 10000,
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)'
          }} className="user-menu">
            <div style={{ marginBottom: 8, fontSize: 14, fontWeight: 'bold' }}>
              {user.name}
            </div>
            <div style={{ marginBottom: 12, fontSize: 12, color: 'var(--muted)' }}>
              {getRoleDisplay(user.role)}
            </div>
            <button
              className="button ghost"
              onClick={handleLogout}
              style={{ width: '100%', justifyContent: 'flex-start' }}
            >
              Выйти
            </button>
          </div>
        </>
      )}
    </div>
  )
}
