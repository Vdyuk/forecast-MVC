import React from 'react'
import { getGrafanaUrl } from '../utils/grafana'

type GrafanaChartProps = {
    baseUrl: string
    houseId: string | number
    panelId: string
    from?: string
    to?: string
    height?: number
}

export const GrafanaChart: React.FC<GrafanaChartProps> = ({
    baseUrl,
    houseId,
    panelId,
    from = 'now-2d',
    to = 'now',
    height = 400
}) => {
    const fullUrl = getGrafanaUrl(baseUrl, houseId, panelId, from, to)

    return (
        <div className="chart-container">
            <iframe
                src={fullUrl}
                width="100%"
                height={`${height}px`}
                frameBorder="0"
            />
        </div>
    )
}