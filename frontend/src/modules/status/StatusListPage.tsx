import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axios from 'axios'
import * as XLSX from 'xlsx'

type HouseRow = {
  house_id: string
  unom: string
  address: string
  region: string
  status: 'red' | 'yellow' | 'green' | 'in_work'
  last_failure_date?: string
  incident_status: string
}

const apiBase = () => (import.meta.env.VITE_API_URL)

export const StatusListPage: React.FC = () => {
  const { regionId, status } = useParams()
  const navigate = useNavigate()
  const [rows, setRows] = useState<HouseRow[]>([])
  const [query, setQuery] = useState('')
  const [is, setIs] = useState<string>('')
  const [sortBy, setSortBy] = useState<keyof HouseRow>('address')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    const base = apiBase()
    axios.get(`${base}/api/regions/${regionId}/houses`, {
      params: { status, incident_status: is || undefined, search: query || undefined }
    }).then(r => setRows(r.data))
  }, [regionId, status, query, is])

  const sorted = useMemo(() => {
    const arr = [...rows]
    arr.sort((a, b) => {
      if (sortBy === 'unom') {
        const numA = Number(a.unom) || 0
        const numB = Number(b.unom) || 0
        return sortDir === 'asc' ? numA - numB : numB - numA
      }

      const av = (a[sortBy] ?? '').toString()
      const bv = (b[sortBy] ?? '').toString()
      return sortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av)
    })
    return arr
  }, [rows, sortBy, sortDir])

  const exportCsv = () => {
    const data = prepareExportData()
    const ws = XLSX.utils.json_to_sheet(data)
    const csv = XLSX.utils.sheet_to_csv(ws)
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `houses_${status || 'all'}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // Экспорт в Excel (.xlsx)
  const exportXlsx = () => {
    const data = prepareExportData()
    const ws = XLSX.utils.json_to_sheet(data)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Дома')
    XLSX.writeFile(wb, `houses_${status || 'all'}.xlsx`)
  }

  const prepareExportData = () => {
    return sorted.map((row) => ({
      УНОМ: row.unom,
      Адрес: row.address,
      'Текущий статус': row.incident_status,
    }))
  }

  const exportPdf = () => {
    // Создание PDF отчета
    const printWindow = window.open('', '_blank')
    if (!printWindow) return

    const tableHtml = document.querySelector('.table')?.outerHTML || ''
    const html = `
      <html>
        <head>
          <title>Отчет по домам - ${status === 'red' ? 'Критический инцидент' : status === 'yellow' ? 'Предупреждение' : status === 'green' ? 'Нет проблем' : 'В работе'}</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .header { text-align: center; margin-bottom: 20px; }
            .date { color: #666; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Отчет по домам</h1>
            <p>Статус: ${status === 'red' ? 'Критический инцидент' : status === 'yellow' ? 'Предупреждение' : status === 'green' ? 'Нет проблем' : 'В работе'}</p>
            <p class="date">Создано: ${new Date().toLocaleString()}</p>
          </div>
          ${tableHtml}
        </body>
      </html>
    `
    printWindow.document.write(html)
    printWindow.document.close()
    printWindow.print()
  }

  const th = (k: keyof HouseRow, label: string) => (
    <th onClick={() => { setSortBy(k); setSortDir(d => d === 'asc' ? 'desc' : 'asc') }} style={{ cursor: 'pointer' }}>{label}</th>
  )

  return (
    <div>
      <div className="topbar">
        <div className="title">Список домов — {status === 'red' ? 'Критический инцидент' : status === 'yellow' ? 'Предупреждение' : status === 'green' ? 'Нет проблем' : 'В работе'}</div>
        <div className="controls">
          <input className="input" placeholder="Поиск по адресу" value={query} onChange={e => setQuery(e.target.value)} />
          <select className="select" value={is} onChange={e => setIs(e.target.value)}>
            <option value="">Статус инцидента</option>
            <option value="В работе">В работе</option>
            <option value="В ремонте">В ремонте</option>
            <option value="Новый">Новый</option>
          </select>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="button" onClick={exportCsv}>CSV</button>
            <button className="button" onClick={exportXlsx}>Excel</button>
            <button className="button" onClick={exportPdf}>PDF</button>
          </div>
        </div>
      </div>

      <div className="panel">
        {/* Обертка для прокрутки */}
        <div style={{ 
          maxHeight: '70vh',
          overflow: 'auto'
        }}>
          <table className="table" style={{ tableLayout: 'auto', width: '100%' }}>
            <thead style={{ 
              position: 'sticky', 
              top: 0,
              zIndex: 10,
              background: 'var(--panel)'
            }}>
              <tr>
                {th('unom', 'УНОМ')}
                {th('address', 'Адрес')}
                {th('incident_status', 'Текущий статус')}
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(r => (
                <tr key={r.house_id}>
                  <td>{r.unom}</td>
                  <td>{r.address}</td>
                  <td>{r.incident_status}</td>
                  <td>
                    <button className="button" onClick={() => navigate(`/house/${r.house_id}`)}>Подробнее</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}