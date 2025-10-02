import React, { useEffect, useState } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import axios from 'axios'
import { DashboardPage } from './dashboard/DashboardPage'
import { StatusListPage } from './status/StatusListPage'
import { HouseDetailPage } from './house/HouseDetailPage'
import { LoginPage } from './auth/LoginPage'
import { UserInfo } from './auth/UserInfo'
import { ThemeProvider } from '../contexts/ThemeContext'
import { ThemeToggle } from '../components/ThemeToggle'
import { HouseSummaryPage } from './house/HouseSummaryPage'

type ModelRelearn = {
  id: number
  date: string
  model_name: string
  status_relearn: string
}

type HouseOption = {
  id_house: number
  unom: number
  simple_address: string
}

const apiBase = () => (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')

const AppContent: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [loading, setLoading] = useState(true)
  const [showHistoryModal, setShowHistoryModal] = useState(false)
  const [showIncidentModal, setShowIncidentModal] = useState(false)
  const [modelHistory, setModelHistory] = useState<ModelRelearn[]>([])
  const [houseOptions, setHouseOptions] = useState<HouseOption[]>([])
  const [selectedHouse, setSelectedHouse] = useState<number | null>(null)
  const [newIncidentStatus, setNewIncidentStatus] = useState<string>('New')
  const [newHouseHealth, setNewHouseHealth] = useState<string>('Green')
  const [searchQuery, setSearchQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)

  const location = useLocation()

  const loadModelHistory = () => {
    axios.get(`${apiBase()}/api/model-relearn/history`)
      .then(r => setModelHistory(r.data))
      .catch(console.error)
  }

  const loadHouseOptions = () => {
    axios.get(`${apiBase()}/api/v2/houses/options`)
      .then(r => setHouseOptions(r.data))
      .catch(console.error)
  }

  useEffect(() => {
    const auth = localStorage.getItem('auth')
    setIsAuthenticated(!!auth)
    setLoading(false)
    if (showHistoryModal) loadModelHistory()
    if (showIncidentModal) loadHouseOptions()
  }, [showHistoryModal, showIncidentModal])

  const handleCreateIncident = () => {
    if (!selectedHouse) return
    axios.post(`${apiBase()}/api/v2/incidents/create`, { 
      id_house: selectedHouse,
      status_incident: newIncidentStatus,
      house_health: newHouseHealth
    })
      .then(() => {
        alert('Инцидент создан успешно!')
        resetIncidentModal()
        window.location.reload();
      })
      .catch(error => {
        console.error("Ошибка при создании инцидента (v2):", error);
        if (error.response && error.response.status === 404) {
          alert('Ошибка: ' + error.response.data.detail);
        } else {
          alert('Произошла ошибка при создании инцидента (v2). Проверьте консоль.');
        }
      })
  }

  const resetIncidentModal = () => {
    setShowIncidentModal(false)
    setSelectedHouse(null)
    setNewIncidentStatus('New')
    setNewHouseHealth('Green')
    setSearchQuery('')
    setShowDropdown(false)
  }

  const statusApiMapping: { [key: string]: string } = {
    'Новый': 'New',
    'В работе': 'Work',
    'В ремонте': 'Repair',
    'Решен': 'Resolved'
  }

  const healthApiMapping: { [key: string]: string } = {
    'Критический инцидент': 'Red',
    'Предупреждение': 'Yellow',
    'Нет проблем': 'Green'
  }

  const filteredOptions = houseOptions.filter(house =>
    house.simple_address.toLowerCase().includes(searchQuery.toLowerCase()) ||
    house.unom.toString().includes(searchQuery)
  )

  const handleOptionClick = (house: HouseOption) => {
    setSelectedHouse(house.id_house)
    setSearchQuery(`${house.simple_address} (УНОМ: ${house.unom})`)
    setShowDropdown(false)
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'var(--bg)'
      }}>
        <div style={{ color: 'var(--muted)' }}>Загрузка...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <div>
      <div className="panel" style={{ borderRadius: 0 }}>
        <div className="container topbar">
          <div className="title">
            <Link
              to="/r/lublino"
              style={{
                textDecoration: 'none',
                color: 'inherit',
                cursor: 'pointer',
                fontSize: '1.1rem'
              }}
            >
              Мониторинг системы водоснабжения - район Люблино
            </Link>
          </div>
          <div style={{ 
            display: 'flex', 
            gap: 12, 
            alignItems: 'center',
            flexWrap: 'wrap',
            justifyContent: 'flex-end'
          }}>

            <button className="button" onClick={() => setShowIncidentModal(true)}>
              Создать инцидент
            </button>
            <button className="button" onClick={() => setShowHistoryModal(true)}>
              История обучения модели
            </button>
            <ThemeToggle />
            <UserInfo />
          </div>
        </div>
      </div>
      <div className="container" style={{ paddingTop: 16 }}>
        <Routes>
          <Route path="/" element={<DashboardPage regionId="lublino" />} />
          <Route path="/r/:regionId" element={<DashboardPage />} />
          <Route path="/house-summary/:houseId" element={<HouseSummaryPage />} />
          <Route path="/r/:regionId/list/:status" element={<StatusListPage />} />
          <Route path="/house/:houseId" element={<HouseDetailPage />} />
        </Routes>
      </div>

      {/* Модалка истории обучения */}
      {showHistoryModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowHistoryModal(false)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            className="modal"
            onClick={e => e.stopPropagation()}
            style={{
              backgroundColor: 'var(--bg)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              padding: '20px',
              maxWidth: '95vw',
              width: '90%',
              maxHeight: '80vh',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
            }}
          >
            <h3 style={{ margin: '0 0 15px 0', fontSize: '1.3rem' }}>История обучения</h3>
            <div style={{
              flex: 1,
              overflow: 'auto',
              marginBottom: '15px',
              maxHeight: '400px',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '4px'
            }}>
              <table className="table" style={{ margin: 0, width: '100%' }}>
                <thead style={{ position: 'sticky', top: 0, backgroundColor: 'var(--bg)' }}>
                  <tr>
                    <th style={{ padding: '10px 8px' }}>Дата</th>
                    <th style={{ padding: '10px 8px' }}>Модель</th>
                    <th style={{ padding: '10px 8px' }}>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {modelHistory.map(record => (
                    <tr key={record.id}>
                      <td style={{ padding: '10px 8px' }}>
                        {record.date ? new Date(record.date).toLocaleDateString('ru-RU', {
                          day: '2-digit',
                          month: '2-digit',
                          year: 'numeric'
                        }) : 'Не указана'}
                      </td>
                      <td style={{ padding: '10px 8px' }}>{record.model_name}</td>
                      <td style={{ padding: '10px 8px' }}>{record.status_relearn}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: 'flex', gap: '10px', flexShrink: 0, flexWrap: 'wrap' }}>
              <button className="button" onClick={() => {
                const modelName = `model_${Date.now()}`
                axios.post(`${apiBase()}/api/model-relearn/start`, {
                  model_name: modelName,
                  status_relearn: 'started'
                })
                  .then(() => {
                    alert('Переобучение модели запущено!')
                    loadModelHistory()
                  })
                  .catch(console.error)
              }}>
                Переобучить
              </button>
              <button className="button" onClick={() => setShowHistoryModal(false)}>
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модалка внесения инцидента */}
      {showIncidentModal && (
        <div
          className="modal-overlay"
          onClick={resetIncidentModal}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            className="modal"
            onClick={e => e.stopPropagation()}
            style={{
              backgroundColor: 'var(--bg)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              padding: '20px',
              maxWidth: '95vw',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
            }}
          >
            <h3 style={{ margin: '0 0 15px 0', fontSize: '1.3rem' }}>Создать инцидент</h3>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Выберите дом:</label>
              <div style={{ position: 'relative', width: '100%' }}>
                <input
                  className="input"
                  placeholder="Поиск по адресу или УНОМ..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setSelectedHouse(null);
                    setShowDropdown(true);
                  }}
                  onFocus={() => setShowDropdown(true)}
                  style={{ width: '100%' }}
                />
                {showDropdown && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '100%',
                      left: 0,
                      right: 0,
                      backgroundColor: 'var(--bg)',
                      border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '4px',
                      zIndex: 1001,
                      maxHeight: '200px',
                      overflowY: 'auto',
                    }}
                  >
                    {filteredOptions.length > 0 ? (
                      filteredOptions.map(house => (
                        <div
                          key={house.id_house}
                          onClick={() => handleOptionClick(house)}
                          style={{
                            padding: '12px',
                            cursor: 'pointer',
                            borderBottom: '1px solid rgba(255,255,255,0.05)',
                          }}
                          onMouseDown={(e) => e.preventDefault()}
                        >
                          {house.simple_address} (УНОМ: {house.unom})
                        </div>
                      ))
                    ) : (
                      <div style={{ padding: '12px', textAlign: 'center', color: 'var(--muted)' }}>
                        Нет совпадений
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Статус инцидента:</label>
              <select
                className="select"
                value={newIncidentStatus}
                onChange={e => setNewIncidentStatus(statusApiMapping[e.target.value] || e.target.value)}
                style={{ width: '100%' }}
              >
                <option value="New">Новый</option>
                <option value="Work">В работе</option>
                <option value="Repair">В ремонте</option>
                <option value="Resolved">Решен</option>
              </select>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '8px' }}>Состояние дома:</label>
              <select
                className="select"
                value={newHouseHealth}
                onChange={e => setNewHouseHealth(healthApiMapping[e.target.value] || e.target.value)}
                style={{ width: '100%' }}
              >
                <option value="Red">Критический инцидент</option>
                <option value="Yellow">Предупреждение</option>
                <option value="Green">Нет проблем</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button className="button" onClick={handleCreateIncident} disabled={!selectedHouse}>
                Добавить
              </button>
              <button className="button" onClick={resetIncidentModal}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      
    </div>
  )
}

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}