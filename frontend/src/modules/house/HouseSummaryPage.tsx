import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
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
const apiBase = () => (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')

export const HouseSummaryPage: React.FC = () => {
    const { houseId } = useParams()
    const [data, setData] = useState<HouseDetail | null>(null)
    const navigate = useNavigate()

    useEffect(() => {
        if (houseId) {
            axios.get(`${apiBase()}/api/houses/${houseId}/status-detail`)
                .then(r => {
                    setData(r.data)
                })
                .catch(error => {
                    console.error('Ошибка загрузки деталей дома:', error)
                })
        }
    }, [houseId])

    if (!data) return <div>Загрузка...</div>

    return (
        <div>
            {/* Шапка с кнопками */}
            <div className="topbar" style={{ marginBottom: '20px' }}>
                <div className="title center">
                    <div style={{ marginRight: '15px' }}>
                        Сводная информация по дому: {data.simple_address || data.address}</div>

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

                <button className="button" onClick={() => navigate(`/house/${data.house_id}`)}>Перейти на детальную информацию</button>

            </div>


            {/* Информация о доме */}
            <div className="panel" style={{ marginBottom: '20px', }}>
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
            <LLMChatWidget
                houseId={houseId || ''}
                houseData={data}
            />
        </div>
    )
}