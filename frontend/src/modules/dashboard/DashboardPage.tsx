import React, { useEffect, useMemo, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { GlobalChatWidget } from '../../components/RegionChatWidget'
import { GrafanaChartStable } from '../../components/GrafanaCharStable'

type DashboardMetrics = {
  region_id: string
  region_name: string
  counts: { red: number, yellow: number, green: number, in_work: number, total_current_failures: number, processed_current?: number }
  period_days: number
}

type HouseOption = {
  id_house: number
  unom: number
  simple_address: string
}

// Add forecast type
type ForecastData = {
  v1: number
  v2: number
}

const apiBase = () => (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')

export const DashboardPage: React.FC<{ regionId?: string }> = ({ regionId }) => {
  const params = useParams()
  const navigate = useNavigate()
  const rid = regionId || params.regionId || 'lublino'
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [llmContext, setLlmContext] = useState<any>(null)
  const [forecastData, setForecastData] = useState<ForecastData | null>(null) // Add forecast state

  // Состояния для селекта с поиском
  const [houseOptions, setHouseOptions] = useState<HouseOption[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedHouse, setSelectedHouse] = useState<number | null>(null)

  useEffect(() => {
    const base = apiBase()
    axios.get(`${base}/api/regions/${rid}/dashboard`, { params: { days: 14 } })
      .then(r => setMetrics(r.data))
      .catch(() => {
        // fallback minimal metrics so UI is not empty
        setMetrics({ region_id: rid as string, region_name: '—', counts: { red: 2, yellow: 4, green: 10, in_work: 1, total_current_failures: 6, processed_current: 2 }, period_days: 14 })
      })
    axios.get(`${base}/api/regions/${rid}/llm-context`).then(r => setLlmContext(r.data)).catch(() => setLlmContext({ region: rid, houses: [] }))

    // Загрузка опций домов для селекта
    axios.get(`${base}/api/v2/houses/options`)
      .then(r => setHouseOptions(r.data))
      .catch(console.error)

    // Fetch forecast data (no region_id needed)
    axios.get(`${base}/api/forecast-overall`)
      .then(response => setForecastData(response.data))
      .catch(error => console.error("Error fetching forecast ", error))
  }, [rid])

  const hiddenBlock = useMemo(() => {
    return (
      <div style={{ display: 'none' }} id="llm-context-block" data-json={JSON.stringify(llmContext || {})}></div>
    )
  }, [llmContext])

  // Фильтрация опций на основе поискового запроса
  const filteredOptions = houseOptions.filter(house =>
    house.simple_address.toLowerCase().includes(searchQuery.toLowerCase()) ||
    house.unom.toString().includes(searchQuery)
  )

  // Обработчик клика по опции
  const handleOptionClick = (house: HouseOption) => {
    setSelectedHouse(house.id_house)
    setSearchQuery(`${house.simple_address} (УНОМ: ${house.unom})`)
    setShowDropdown(false)
  }

  // Обработчик перехода к дому
  const handleGoToHouse = () => {
    if (selectedHouse) {
      navigate(`/house-summary/${selectedHouse}`)
    }
  }

  return (
    <div>
      {hiddenBlock}
      <h2>Оперативная ситуация</h2>
      <div className="row cols-4">
        <div className="panel card">
          <div className="label fs-16">Критический инцидент</div>
          <div className="value center" style={{ color: 'var(--red)' }}>{metrics?.counts.red ?? '—'}</div>
          <Link to={`/r/${rid}/list/red`} className="button center">Открыть список</Link>
        </div>
        <div className="panel card">
          <div className="label fs-16">Предупреждение</div>
          <div className="value center" style={{ color: 'var(--yellow)' }}>{metrics?.counts.yellow ?? '—'}</div>
          <Link to={`/r/${rid}/list/yellow`} className="button center">Открыть список</Link>
        </div>
        <div className="panel card">
          <div className="label fs-16">Нет проблем</div>
          <div className="value center" style={{ color: 'var(--green)' }}>{metrics?.counts.green ?? '—'}</div>
        </div>
        <div className="panel card">
          <div className="label fs-16">В работе</div>
          <div className="value center" style={{ color: 'var(--primary)' }}>{metrics?.counts.in_work ?? '—'}</div>
          <Link to={`/r/${rid}/list/in_work`} className="button center">Открыть список</Link>
        </div>
      </div>
      <div>
        <h3>Прогноз по модели:</h3>
        <div>
          Объем утечки {forecastData ? forecastData.v1.toFixed(1) : '—'} м<sup>3</sup> в сутки,
          рост {forecastData ? forecastData.v2.toFixed(1) : '—'}% в день
        </div>
      </div>
      <h3>Перейти к сводной информации дома</h3>
      <div className="panel card" style={{ marginBottom: '20px' }}>
        <div style={{ position: 'relative', width: '100%' }}>
          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <input
                className="input"
                placeholder="Поиск по адресу..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value)
                  setSelectedHouse(null)
                  setShowDropdown(true)
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
                          padding: '8px',
                          cursor: 'pointer',
                          borderBottom: '1px solid rgba(255,255,255,0.05)',
                        }}
                        onMouseDown={(e) => e.preventDefault()}
                      >
                        {house.simple_address} (УНОМ: {house.unom})
                      </div>
                    ))
                  ) : (
                    <div style={{ padding: '8px', textAlign: 'center', color: 'var(--muted)' }}>
                      Нет совпадений
                    </div>
                  )}
                </div>
              )}
            </div>
            <button
              className="button"
              onClick={handleGoToHouse}
              disabled={!selectedHouse}
              style={{ alignSelf: 'flex-start' }}
            >
              Перейти
            </button>
          </div>
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px',
        marginBottom: '20px'
      }}>
        <GrafanaChartStable
          baseUrl="http://158.255.3.5:3000/d-solo/adcj78z?orgId=1&timezone=browser&showCategory=Thresholds&__feature.dashboardSceneSolo=true"
          panelId="panel-2"
          from="now-31d"
          to="now"
        />
        <GrafanaChartStable
          baseUrl="http://158.255.3.5:3000/d-solo/adcj78z?orgId=1&timezone=browser&__feature.dashboardSceneSolo=true"
          panelId="panel-1"
          from="now"
          to="now"
        />
      </div>

      <GlobalChatWidget />
    </div>
  )
}