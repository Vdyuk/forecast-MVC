import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { LLMChatWidget } from '../../components/LLMChatWidget'
import { GrafanaChart } from '../../components/GrafanaChart'
import { GrafanaTable } from '../../components/GrafanaTable'

type HouseDetail = {
  house_id: string
  address: string
  simple_address?: string
  region: string
  status: 'red' | 'yellow' | 'green' | 'in_work'
  incident_status: string
  last_failure_date?: string
  status_valid_until?: string
  status_reason?: string
  fias?: string
  unom?: string
  nreg?: string
}

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

export const HouseDetailPage: React.FC = () => {
  const { houseId } = useParams()
  const [data, setData] = useState<HouseDetail | null>(null)
  const [status, setStatus] = useState<'red' | 'yellow' | 'green' | 'in_work'>('in_work') // Состояние для других частей приложения
  const [incidentStatus, setIncidentStatus] = useState<string>('Новый')

  // === НОВЫЕ СОСТОЯНИЯ ДЛЯ УПРАВЛЕНИЯ СТАТУСОМ ДОМА НА ЭТОЙ СТРАНИЦЕ ===
  const [localHouseHealth, setLocalHouseHealth] = useState<'red' | 'yellow' | 'green'>('green')
  const [localIncidentStatus, setLocalIncidentStatus] = useState<string>('Новый')
  // ======================================================================

  // Состояния для управления disabled
  const [houseHealthDisabled, setHouseHealthDisabled] = useState(false);
  const [incidentStatusDisabled, setIncidentStatusDisabled] = useState(false);

  useEffect(() => {
    if (houseId) {
      // Используем новый endpoint для получения статуса
      axios.get(`${apiBase()}/api/houses/${houseId}/status-detail`)
        .then(r => {
          setData(r.data)
          setLocalHouseHealth(r.data.status)
          setLocalIncidentStatus(r.data.incident_status)

          // Также сохраняем в основные состояния для других частей компонента
          setStatus(r.data.status)
          setIncidentStatus(r.data.incident_status)
        })
        .catch(error => {
          console.error('Ошибка загрузки деталей дома:', error)
        })
    }
  }, [houseId])

  // Функция для синхронизации статусов и временного отключения полей
  const syncStatusesAndDisable = (
    newHealth: 'red' | 'yellow' | 'green',
    newIncident: string,
    source: 'health' | 'incident'
  ) => {
    let updatedHealth = newHealth;
    let updatedIncident = newIncident;
    let disableHealth = false;
    let disableIncident = false;

    // Если источник - "Статус проблемы"
    if (source === 'health') {
      if (newHealth === 'green') { // Если "Нет проблем"
        updatedIncident = 'Решен'; // Установить "Решен"
        disableIncident = true; // Отключить поле инцидента
      }
    }
    // Если источник - "Статус инцидента"
    else if (source === 'incident') {
      if (newIncident === 'Решен') { // Если "Решен"
        updatedHealth = 'green'; // Установить "Нет проблем"
        disableHealth = true; // Отключить поле проблемы
      }
    }

    // Устанавливаем обновлённые состояния
    setLocalHouseHealth(updatedHealth);
    setLocalIncidentStatus(updatedIncident);

    // Устанавливаем состояния disabled
    setHouseHealthDisabled(disableHealth);
    setIncidentStatusDisabled(disableIncident);

    // Если какое-то поле было отключено, включаем его обратно через 1 секунду
    if (disableHealth || disableIncident) {
      setTimeout(() => {
        setHouseHealthDisabled(false);
        setIncidentStatusDisabled(false);
      }, 1000);
    }
  };
  // Функция для получения цвета индикатора на основе статуса
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'red':
        return 'var(--red)'
      case 'yellow':
        return 'var(--yellow)'
      case 'green':
        return 'var(--green)'
      case 'in_work':
        return 'var(--primary)'
      default:
        return 'var(--muted)'
    }
  }

  const handleSave = () => {
    if (!houseId) return

    // Маппинг house_health (Статус проблемы)
    const healthMapping: { [key: string]: string } = {
      'red': 'Red',
      'yellow': 'Yellow',
      'green': 'Green'
    }

    // Маппинг incident_status (Статус инцидента)
    const statusMapping: { [key: string]: string } = {
      'Новый': 'New',
      'В работе': 'Work',
      'В ремонте': 'Repair',
      'Решен': 'Resolved'
    }

    let apiHouseHealth = healthMapping[localHouseHealth];
    let apiIncidentStatus = statusMapping[localIncidentStatus];

    // Если один из статусов "Решен" или "Нет проблем", принудительно устанавливаем оба
    if (localIncidentStatus === 'Решен' || localHouseHealth === 'green') {
      apiHouseHealth = 'Green';
      apiIncidentStatus = 'Resolved';
    }

    const requestData = {
      house_health: apiHouseHealth, // <-- Используем скорректированное значение
      incident_status: apiIncidentStatus // <-- Используем скорректированное значение
    }


    axios.post(`${apiBase()}/api/houses/${houseId}/status`, requestData)
      .then(response => {
        console.log('Ответ сервера:', response.data)
        alert('Статус обновлен успешно!')

        // Если мы отправили "Green" и "Resolved", обновим локальные состояния для отображения
        if (apiHouseHealth === 'Green' && apiIncidentStatus === 'Resolved') {
          setLocalHouseHealth('green');
          setLocalIncidentStatus('Решен');
        }

      })
      .catch(error => {
        console.error('Ошибка обновления статуса:', error)
        alert('Ошибка при обновлении статуса')
      })
  }

  if (!data) return <div>Загрузка...</div>

  return (
    <div>
      {/* Шапка с кнопками */}
      <div className="topbar" style={{ marginBottom: '20px' }}>
        <div className="title">Детали по дому: {data.simple_address || data.address}</div>
        <div
          style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(data.status),
            flexShrink: 0
          }}
        />
      </div>

      {/* Управление статусом дома */}
      <div className="panel" style={{ marginBottom: '20px' }}>
        <h3>Управление статусом дома</h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px',
          marginBottom: '20px'
        }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              Статус проблемы:
            </label>
            <select
              className="select"
              value={localHouseHealth} // Используем локальное состояние
              onChange={e => {
                const newHealth = e.target.value as 'red' | 'yellow' | 'green';

                // Синхронизируем статусы
                syncStatusesAndDisable(newHealth, localIncidentStatus, 'health');
              }}
              disabled={houseHealthDisabled} // Управляем disabled
              style={{ width: '100%' }}
            >
              <option value="red">Критический инцидент</option>
              <option value="yellow">Предупреждение</option>
              <option value="green">Нет проблем</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
              Статус инцидента:
            </label>
            <select
              className="select"
              value={localIncidentStatus} // Используем локальное состояние
              onChange={e => {
                const newIncident = e.target.value;

                // Синхронизируем статусы
                syncStatusesAndDisable(localHouseHealth, newIncident, 'incident');
              }}
              disabled={incidentStatusDisabled} // Управляем disabled
              style={{ width: '100%' }}
            >
              <option value="Новый">Новый</option>
              <option value="В работе">В работе</option>
              <option value="В ремонте">В ремонте</option>
              <option value="Решен">Решен</option>
            </select>
          </div>
        </div>
        <div style={{
          display: 'flex',
          gap: '10px',
          justifyContent: 'flex-end'
        }}>
          <button
            className="button"
            onClick={handleSave}
          >
            Сохранить изменения
          </button>
        </div>
      </div>
      <GrafanaTable
        baseUrl="http://158.255.3.5:3000/d-solo/adkwrzz?orgId=1&timezone=utc&__feature.dashboardSceneSolo=true"
        houseId={+data.house_id}
        panelId="panel-2"
        from="now-5m"
        to="now"
      />
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '20px',
        marginBottom: '20px',
        marginTop: '20px'
      }}>
        <GrafanaChart
          baseUrl="http://158.255.3.5:3000/d-solo/adkwggn/-?orgId=1&from=1759000195391&to=1759172995391&timezone=browser&refresh=5m&__feature.dashboardSceneSolo=true"
          houseId={+data.house_id}
          panelId="panel-1"
          from="now-1d"
          to="now"
        />
        <GrafanaChart
          baseUrl="http://158.255.3.5:3000/d-solo/adkwggn/-?orgId=1&from=1759000195391&to=1759172995391&timezone=Europe%2FMoscow&refresh=5m&__feature.dashboardSceneSolo=true"
          houseId={+data.house_id}
          panelId="panel-2"
          from="now-1d"
          to="now"
        />
        <GrafanaChart
          baseUrl="http://158.255.3.5:3000/d-solo/adkwggn/-?orgId=1&from=1758574166583&to=1759178966583&timezone=Europe%2FMoscow&refresh=1h&__feature.dashboardSceneSolo=true"
          houseId={+data.house_id}
          panelId="panel-5"
          from="now-7d"
          to="now"
        />

        <GrafanaChart
          baseUrl="http://158.255.3.5:3000/d-solo/adkwggn/-?orgId=1&from=1758574166583&to=1759178966583&timezone=Europe%2FMoscow&refresh=1h&__feature.dashboardSceneSolo=true"
          houseId={+data.house_id}
          panelId="panel-4"
          from="now-7d"
          to="now"
        />

      </div>
      <div style={{ marginTop: '20px' }}>
        <GrafanaChart
          baseUrl="http://158.255.3.5:3000/d-solo/adkwrzz?orgId=1&from=1759232754922&to=1759578354922&timezone=utc&var-query0=&editIndex=0&var-id_house=53&showCategory=Panel%20links&panelId=panel-1&__feature.dashboardSceneSolo=true"
          houseId={+data.house_id}
          panelId="panel-1"
          from="now-2d"
          to="now+2d"
        />
      </div>
      <div style={{ marginTop: '20px' }}>
        <GrafanaTable
          baseUrl="http://158.255.3.5:3000/d-solo/adtvscz/-?orgId=1&timezone=Europe%2FMoscow&var-query0=&__feature.dashboardSceneSolo=true"
          houseId={+data.house_id}
          panelId="panel-1"
          from="now-1y"
          to="now"
        />
      </div>
      {/* Информация о доме */}
      <div className="panel" style={{ marginTop: '20px' }}>
        <div className="row">
          <div>
            <strong>УНОМ:</strong> {data.unom || "Нет данных"}
          </div>
          <div>
            <strong>ФИАС:</strong> {data.fias || "Нет данных"}
          </div>
          <div>
            <strong>Номер регистрации:</strong> {data.nreg || "Нет данных"}
          </div>
        </div>
      </div>


      <LLMChatWidget
        houseId={houseId || ''}
        houseData={data}
      />
    </div>
  )
}