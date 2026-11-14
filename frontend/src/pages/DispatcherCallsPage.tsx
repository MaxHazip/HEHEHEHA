import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Clock, Headphones, Phone, Radio, RefreshCw } from 'lucide-react'
import { apiUrl, wsUrl } from '@/lib/api'
import {
  getCall,
  listCalls,
  type CallDetail,
} from '@/features/calls/api/callsApi'

function formatDateTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '—'
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

function formatMs(value: number | null): string {
  if (value === null) return '--:--'
  const total = Math.floor(value / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

function statusLabel(status: string): string {
  switch (status) {
    case 'active':
      return 'В эфире'
    case 'ringing':
      return 'Звонит'
    case 'completed':
      return 'Завершён'
    case 'missed':
      return 'Пропущен'
    case 'failed':
      return 'Ошибка'
    default:
      return status
  }
}

function statusClass(status: string): string {
  if (status === 'active' || status === 'ringing') {
    return 'bg-rose-100 text-rose-700'
  }
  if (status === 'completed') {
    return 'bg-emerald-100 text-emerald-700'
  }
  return 'bg-slate-100 text-slate-600'
}

export default function DispatcherCallsPage() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [liveText, setLiveText] = useState('')
  const [liveStatus, setLiveStatus] = useState<string | null>(null)
  const socketRef = useRef<WebSocket | null>(null)

  const {
    data: calls = [],
    isLoading,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ['calls'],
    queryFn: () => listCalls({ limit: 100 }),
    refetchInterval: 5000,
  })

  const activeId = selectedId ?? calls[0]?.id ?? null

  const {
    data: selectedCall,
    isLoading: isDetailLoading,
  } = useQuery<CallDetail>({
    queryKey: ['call', activeId],
    queryFn: () => getCall(activeId as number),
    enabled: activeId !== null,
    refetchInterval: (query) =>
      query.state.data?.status === 'active' ? 3000 : false,
  })

  const selectedCallId = selectedCall?.id
  const selectedCallStatus = selectedCall?.status
  const selectedCallTransport = selectedCall?.transport

  useEffect(() => {
    socketRef.current?.close()
    socketRef.current = null

    if (
      !selectedCallId ||
      selectedCallStatus !== 'active' ||
      selectedCallTransport !== 'webrtc'
    ) {
      return
    }

    try {
      const socket = new WebSocket(
        wsUrl(`/api/calls/${selectedCallId}/signal?role=dispatcher`),
      )
      socketRef.current = socket

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as {
            type?: string
            text?: string
            status?: string
          }
          if (
            (payload.type === 'snapshot' ||
              payload.type === 'transcript') &&
            typeof payload.text === 'string'
          ) {
            setLiveText(payload.text)
          }
          if (payload.type === 'status' && payload.status) {
            setLiveStatus(payload.status)
          }
        } catch {
          // Игнорируем не-JSON сообщения сигналинга.
        }
      }

      socket.onclose = () => {
        if (socketRef.current === socket) socketRef.current = null
      }

      return () => {
        socket.close()
        if (socketRef.current === socket) socketRef.current = null
      }
    } catch {
      return
    }
  }, [selectedCallId, selectedCallStatus, selectedCallTransport])

  const isLive =
    liveStatus === 'active' || selectedCallStatus === 'active'
  const supportsLiveCaptions = selectedCallTransport === 'webrtc'
  const liveTranscript = isLive
    ? liveText || selectedCall?.transcript_text || ''
    : selectedCall?.transcript_text || ''
  const recordingSrc = selectedCall?.has_recording
    ? apiUrl(selectedCall.recording_url)
    : undefined

  const handleSelect = (callId: number) => {
    setSelectedId(callId)
    setLiveText('')
    setLiveStatus(null)
  }

  const handleRefresh = () => {
    void refetch()
    if (activeId !== null) {
      void queryClient.invalidateQueries({ queryKey: ['call', activeId] })
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <div className="flex items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800 flex items-center gap-2">
            <Headphones className="text-blue-600" /> Звонки
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Записи, расшифровки и live-субтитры активных звонков
          </p>
        </div>
        <button
          type="button"
          onClick={handleRefresh}
          className="flex items-center gap-2 bg-white border border-slate-200 px-4 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-50 transition"
        >
          <RefreshCw size={16} className={isFetching ? 'animate-spin' : ''} />
          Обновить
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-4">
        <aside className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 text-sm font-medium text-slate-700">
            Всего звонков: {calls.length}
          </div>
          <div className="max-h-[calc(100vh-240px)] overflow-y-auto divide-y divide-slate-100">
            {isLoading && (
              <div className="p-4 text-sm text-slate-400">Загрузка…</div>
            )}
            {!isLoading && calls.length === 0 && (
              <div className="p-6 text-sm text-slate-400">
                Звонков пока нет. Они появятся из браузерного виджета или
                SIP-АТС.
              </div>
            )}
            {calls.map((call) => (
              <button
                key={call.id}
                type="button"
                onClick={() => handleSelect(call.id)}
                className={`w-full text-left px-4 py-3 transition ${
                  activeId === call.id
                    ? 'bg-blue-50'
                    : 'hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-medium text-slate-800 flex items-center gap-2">
                    <Phone size={14} className="text-slate-400" />
                    {call.client_phone ||
                      call.external_id ||
                      `Звонок #${call.id}`}
                  </span>
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded ${statusClass(
                      call.status,
                    )}`}
                  >
                    {statusLabel(call.status)}
                  </span>
                </div>
                <div className="mt-1 flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock size={12} />
                    {formatDuration(call.duration_seconds)}
                  </span>
                  <span className="uppercase">{call.transport}</span>
                  <span>{formatDateTime(call.started_at)}</span>
                </div>
                {call.transcript_preview && (
                  <p className="mt-1 text-xs text-slate-400 truncate">
                    {call.transcript_preview}
                  </p>
                )}
              </button>
            ))}
          </div>
        </aside>

        <section className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 min-h-[320px]">
          {activeId === null && (
            <div className="h-full flex items-center justify-center text-sm text-slate-400 py-16">
              Выберите звонок слева
            </div>
          )}

          {activeId !== null && isDetailLoading && (
            <div className="text-sm text-slate-400">Загрузка звонка…</div>
          )}

          {selectedCall && (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-800">
                    {selectedCall.client_phone ||
                      selectedCall.external_id ||
                      `Звонок #${selectedCall.id}`}
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    {selectedCall.direction === 'inbound'
                      ? 'Входящий'
                      : 'Исходящий'}{' '}
                    · {selectedCall.transport.toUpperCase()}
                    {selectedCall.provider
                      ? ` · ${selectedCall.provider}`
                      : ''}
                    {selectedCall.ticket_id !== null
                      ? ` · заявка #${selectedCall.ticket_id}`
                      : ''}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {isLive && (
                    <span className="text-xs bg-rose-100 text-rose-700 px-2 py-1 rounded flex items-center gap-1">
                      <Radio size={12} className="animate-pulse" /> Live
                    </span>
                  )}
                  <span
                    className={`text-xs px-2 py-1 rounded ${statusClass(
                      selectedCall.status,
                    )}`}
                  >
                    {statusLabel(selectedCall.status)}
                  </span>
                  <span className="text-xs text-slate-500">
                    {formatDuration(selectedCall.duration_seconds)}
                  </span>
                </div>
              </div>

              {recordingSrc ? (
                <audio controls src={recordingSrc} className="w-full" />
              ) : (
                <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-sm text-slate-500">
                  Запись ещё не загружена. Для активного звонка она появится
                  после завершения.
                </div>
              )}

              {isLive && supportsLiveCaptions && (
                <div className="rounded-lg border border-rose-200 bg-rose-50 p-3">
                  <div className="text-xs text-rose-600 flex items-center gap-1 mb-1">
                    <Radio size={14} /> Live-субтитры
                  </div>
                  <p className="text-sm text-slate-700 whitespace-pre-wrap min-h-[48px]">
                    {liveText || 'Ожидание речи…'}
                  </p>
                </div>
              )}

              {isLive && !supportsLiveCaptions && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
                  Идёт SIP-звонок — он записывается. Расшифровка и запись
                  появятся после завершения звонка.
                </div>
              )}

              <div>
                <h3 className="text-sm font-medium text-slate-700 mb-2">
                  Расшифровка
                </h3>
                <div className="rounded-lg bg-slate-50 border border-slate-200 p-3 text-sm text-slate-700 whitespace-pre-wrap">
                  {liveTranscript || 'Расшифровки пока нет'}
                </div>
                {selectedCall.transcript_provider && (
                  <p className="mt-1 text-xs text-slate-400">
                    Источник: {selectedCall.transcript_provider}
                    {selectedCall.transcript_language
                      ? ` · ${selectedCall.transcript_language}`
                      : ''}
                  </p>
                )}
              </div>

              {selectedCall.segments.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-slate-700 mb-2">
                    Фрагменты
                  </h3>
                  <div className="max-h-64 overflow-y-auto space-y-1 pr-1">
                    {selectedCall.segments.map((segment) => (
                      <div
                        key={segment.id}
                        className="text-sm text-slate-600 flex gap-3"
                      >
                        <span className="font-mono text-xs text-slate-400 shrink-0 pt-0.5">
                          {formatMs(segment.start_ms)}
                        </span>
                        <span>{segment.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
