import { useEffect, useRef, useState } from 'react'
import {
  CheckCircle2,
  Loader2,
  Mic,
  Phone,
  PhoneOff,
  Server,
} from 'lucide-react'
import { wsUrl } from '@/lib/api'
import {
  createCallSession,
  saveCall,
  type SavedCall,
} from '../api/callsApi'
import { useCallRecorder } from '../hooks/useCallRecorder'

interface CallWidgetProps {
  ticketId: number | null
  clientPhone?: string
  onSaved?: (ticketId: number) => void
}

function formatTime(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

export default function CallWidget({
  ticketId,
  clientPhone,
  onSaved,
}: CallWidgetProps) {
  const {
    status,
    seconds,
    transcript,
    interim,
    error: recorderError,
    speechSupported,
    secureContext,
    microphoneSupported,
    start,
    stop,
  } = useCallRecorder()

  const [saving, setSaving] = useState(false)
  const [preparing, setPreparing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedCall, setSavedCall] = useState<SavedCall | null>(null)

  const callIdRef = useRef<number | null>(null)
  const socketRef = useRef<WebSocket | null>(null)

  const isActive = status === 'active'
  const isConnecting = status === 'connecting'

  useEffect(() => {
    return () => {
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [])

  // Пока идёт звонок, отправляем диспетчеру live-субтитры.
  useEffect(() => {
    if (status !== 'active') return
    const socket = socketRef.current
    if (!socket || socket.readyState !== WebSocket.OPEN) return

    const text = `${transcript} ${interim}`.trim()
    if (!text) return

    socket.send(
      JSON.stringify({
        type: 'transcript',
        text,
        is_final: interim.trim().length === 0,
        provider: 'browser-google',
      }),
    )
  }, [transcript, interim, status])

  const connectSocket = (callId: number) => {
    socketRef.current?.close()
    try {
      const socket = new WebSocket(
        wsUrl(
          `/api/calls/${callId}/signal?role=client&peer_id=web-${Date.now()}`,
        ),
      )
      socketRef.current = socket
      socket.onerror = () => {
        // Live-субтитры не критичны: запись всё равно сохранится.
      }
      socket.onclose = () => {
        if (socketRef.current === socket) socketRef.current = null
      }
    } catch {
      socketRef.current = null
    }
  }

  const handleStart = async () => {
    setError(null)
    setSavedCall(null)

    const started = await start()
    if (!started) return

    setPreparing(true)
    try {
      const callId = await createCallSession(ticketId, clientPhone)
      callIdRef.current = callId
      connectSocket(callId)
    } catch {
      setError(
        'Запись идёт, но live-связь с диспетчером недоступна. ' +
          'После завершения звонок сохранится в БД.',
      )
    } finally {
      setPreparing(false)
    }
  }

  const handleStop = async () => {
    setError(null)
    setSaving(true)
    socketRef.current?.close()
    socketRef.current = null

    try {
      const recorded = await stop()
      if (!recorded) return

      const saved = await saveCall({
        callId: callIdRef.current,
        ticketId,
        clientPhone,
        blob: recorded.blob,
        mimeType: recorded.mimeType,
        transcript: recorded.transcript,
        durationSeconds: recorded.durationSeconds,
      })

      callIdRef.current = null
      setSavedCall(saved)
      if (saved.ticketId !== null) onSaved?.(saved.ticketId)
    } catch (err) {
      setError(
        err instanceof Error
          ? `Не удалось сохранить звонок: ${err.message}`
          : 'Не удалось сохранить звонок',
      )
    } finally {
      setSaving(false)
    }
  }

  const displayError = error ?? recorderError

  return (
    <div className="bg-white border-b border-slate-200 p-4">
      <div className="max-w-3xl mx-auto space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center">
              <Phone size={18} />
            </div>
            <div>
              <div className="font-medium text-slate-800">
                Звонок в поддержку
              </div>
              <div className="text-xs text-slate-500">
                WebRTC + Google Web Speech, fallback — Whisper
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {(isActive || isConnecting) && (
              <span className="text-sm font-mono text-slate-700">
                {formatTime(seconds)}
              </span>
            )}
            {isConnecting && (
              <span className="text-xs text-amber-600 flex items-center gap-1">
                <Loader2 size={14} className="animate-spin" /> Подключение
              </span>
            )}
            {isActive && (
              <span className="text-xs text-rose-600 flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                Идёт запись
              </span>
            )}
            {saving && (
              <span className="text-xs text-slate-500 flex items-center gap-1">
                <Loader2 size={14} className="animate-spin" /> Сохраняю и
                расшифровываю
              </span>
            )}
          </div>
        </div>

        <div className="min-h-[64px] rounded-lg bg-slate-50 border border-slate-200 p-3 text-sm text-slate-700">
          {transcript || interim ? (
            <p className="whitespace-pre-wrap">
              {transcript}
              {interim && (
                <span className="text-slate-400"> {interim}</span>
              )}
            </p>
          ) : (
            <p className="text-slate-400">
              {isActive
                ? 'Говорите — распознанный текст появится здесь и у диспетчера.'
                : 'Нажмите «Позвонить», чтобы записать обращение.'}
            </p>
          )}
        </div>

        {!secureContext && (
          <p className="text-xs text-rose-600">
            Браузер блокирует микрофон на http://IP. Откройте
            http://localhost:5173 или запустите{' '}
            <code className="font-mono">npm run dev:https</code> и зайдите
            по HTTPS.
          </p>
        )}

        {secureContext && !microphoneSupported && (
          <p className="text-xs text-rose-600">
            Браузер не поддерживает запись с микрофона. Используйте
            актуальный Chrome/Edge.
          </p>
        )}

        {!speechSupported && (
          <p className="text-xs text-amber-600">
            Google Web Speech API недоступен в этом браузере. Это не
            проблема: после звонка backend расшифрует запись локальным
            Whisper или Google STT.
          </p>
        )}

        {speechSupported && (
          <p className="text-xs text-slate-400 flex items-center gap-1">
            <Server size={12} /> Если браузер не распознает речь, backend
            сделает это через Whisper/Google STT.
          </p>
        )}

        {!isActive && !isConnecting && !savedCall && (
          <p className="text-xs text-slate-400 flex items-center gap-1">
            <Mic size={12} /> Аудио и текст сохраняются в БД и доступны
            диспетчеру.
          </p>
        )}

        {displayError && (
          <p className="text-xs text-rose-600">{displayError}</p>
        )}

        {savedCall && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 space-y-2">
            <p className="text-xs text-emerald-700 flex items-center gap-1">
              <CheckCircle2 size={14} /> Запись и расшифровка сохранены в БД
              {savedCall.ticketId !== null && ` · заявка #${savedCall.ticketId}`}
            </p>
            <audio
              controls
              src={savedCall.recordingUrl}
              className="w-full"
            />
            {savedCall.transcript ? (
              <p className="text-xs text-slate-600 whitespace-pre-wrap">
                {savedCall.transcript}
              </p>
            ) : (
              <p className="text-xs text-slate-500">
                Текст не получен: расшифровка на сервере не настроена.
                Запись доступна для прослушивания.
              </p>
            )}
          </div>
        )}

        <div className="flex gap-2">
          {isActive || isConnecting ? (
            <button
              type="button"
              onClick={handleStop}
              disabled={saving || preparing}
              className="flex-1 flex items-center justify-center gap-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white py-2.5 rounded-xl font-medium transition"
            >
              <PhoneOff size={18} /> Завершить и сохранить
            </button>
          ) : (
            <button
              type="button"
              onClick={handleStart}
              disabled={saving || !secureContext}
              className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white py-2.5 rounded-xl font-medium transition"
            >
              <Phone size={18} /> Позвонить
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
