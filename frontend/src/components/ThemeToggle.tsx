import React from 'react'
import { useTheme } from '../contexts/ThemeContext'

export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme()

  return (
    <button
      className="button ghost"
      onClick={toggleTheme}
      style={{ display: 'flex', alignItems: 'center', gap: 8 }}
      title={`Переключить на ${theme === 'light' ? 'темную' : 'светлую'} тему`}
    >
      <span>{theme === 'light' ? '🌙' : '☀️'}</span>
    </button>
  )
}
