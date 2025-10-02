export const getGrafanaUrl = (
    baseUrl: string,
    houseId: string | number,
    panelId: string,
    from: string = 'now-2d',
    to: string = 'now'
): string => {
    const theme = localStorage.getItem('theme') || 'dark'

    const url = new URL(baseUrl)
    url.searchParams.set('var-id_house', String(houseId))
    url.searchParams.set('panelId', panelId)
    url.searchParams.set('theme', theme)
    url.searchParams.set('from', from)
    url.searchParams.set('to', to)

    return url.toString()
}

export const getGrafanaTableUrl = (
    baseUrl: string,
    houseId: string | number,
    panelId: string,
    from: string = 'now-2d',
    to: string = 'now'
): string => {
    const theme = localStorage.getItem('theme') || 'dark'

    const url = new URL(baseUrl)
    url.searchParams.set('var-id_house', String(houseId))
    url.searchParams.set('panelId', panelId)
    url.searchParams.set('theme', theme)
    url.searchParams.set('from', from)
    url.searchParams.set('to', to)

    return url.toString()
}

export const getGrafanaUrlStable = (
    baseUrl: string,
    panelId: string,
    from: string = 'now-2d',
    to: string = 'now'
): string => {
    const theme = localStorage.getItem('theme') || 'dark'

    const url = new URL(baseUrl)
    url.searchParams.set('panelId', panelId)
    url.searchParams.set('theme', theme)
    url.searchParams.set('from', from)
    url.searchParams.set('to', to)

    return url.toString()
}
