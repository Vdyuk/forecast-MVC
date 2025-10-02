import React from 'react'
import { getGrafanaTableUrl } from '../utils/grafana'

type GrafanaTableProps = {
    baseUrl: string
    houseId: string | number
    panelId: string
    from?: string
    to?: string
    height?: number
}

export const GrafanaTable: React.FC<GrafanaTableProps> = ({
    baseUrl,
    houseId,
    panelId,
    from = 'now-7d',
    to = 'now',
    height = 300
}) => {
    const fullUrl = getGrafanaTableUrl(baseUrl, houseId, panelId, from, to)

    return (
        <div className="table-container">
            <iframe
                src={fullUrl}
                width="100%"
                height={`${height}px`}
                frameBorder="0"
            />
        </div>
    )
}