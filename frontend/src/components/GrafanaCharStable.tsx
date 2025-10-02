import React from 'react'
import { getGrafanaUrlStable } from '../utils/grafana'

type GrafanaChartProps = {
    baseUrl: string
    panelId: string
    from?: string
    to?: string
    height?: number
}

export const GrafanaChartStable: React.FC<GrafanaChartProps> = ({
    baseUrl,
    panelId,
    from = 'now-2d',
    to = 'now',
    height = 400
}) => {
    const fullUrl = getGrafanaUrlStable(baseUrl, panelId, from, to)

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