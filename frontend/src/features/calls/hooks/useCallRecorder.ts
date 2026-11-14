import { useCallback, useEffect, useRef, useState } from 'react'

export type CallStatus = 'idle' | 'connecting' | 'active' | 'error'

export interface RecordedCall {
  blob: Blob
  mimeType: string
  transcript: string
  durationSeconds: number
}

interface SpeechRecognitionResultLike {
  isFinal: boolean
  readonly 0: { transcript: string }
}

interface SpeechRecognitionEventLike {
  resultIndex: number
  results: {
    readonly length: number
    [index: number]: SpeechRecognitionResultLike
  }
}

interface SpeechRecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: ((event: { error: string }) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike

// Браузерное распознавание (Google Web Speech) выключено по умолчанию:
// расшифровка выполняется локально T-one после звонка. Включить можно
// переменной окружения VITE_BROWSER_SPEECH=true.
const BROWSER_SPEECH_ENABLED =
  import.meta.env.VITE_BROWSER_SPEECH === 'true'

interface SpeechWindow {
  SpeechRecognition?: SpeechRecognitionConstructor
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}

function getSpeechRecognitionConstructor(): SpeechRecognitionConstructor | null {
  if (!BROWSER_SPEECH_ENABLED) return null
  const speechWindow = window as unknown as SpeechWindow
  return (
    speechWindow.SpeechRecognition ??
    speechWindow.webkitSpeechRecognition ??
    null
  )
}

function pickMimeType(): string {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
  ]
  if (typeof MediaRecorder === 'undefined') return ''
  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) ?? ''
}

/**
 * Захват микрофона через WebRTC (getUserMedia) + запись MediaRecorder.
 * Расшифровка по умолчанию выполняется на backend локальной моделью
 * T-one после звонка. Браузерный Google Web Speech — опционально
 * (VITE_BROWSER_SPEECH=true). Аудио никуда не уходит до сохранения.
 */
export function useCallRecorder() {
  const [status, setStatus] = useState<CallStatus>('idle')
  const [seconds, setSeconds] = useState(0)
  const [transcript, setTranscript] = useState('')
  const [interim, setInterim] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [speechSupported, setSpeechSupported] = useState(
    () => getSpeechRecognitionConstructor() !== null,
  )

  const secureContext =
    typeof window !== 'undefined' ? window.isSecureContext : false
  const microphoneSupported =
    typeof navigator !== 'undefined' &&
    Boolean(navigator.mediaDevices?.getUserMedia)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  const finalTextRef = useRef('')
  const interimTextRef = useRef('')
  const startedAtRef = useRef(0)
  const timerRef = useRef<number | null>(null)
  const activeRef = useRef(false)
  const stopResolveRef = useRef<((value: RecordedCall | null) => void) | null>(
    null,
  )

  const start = useCallback(async (): Promise<boolean> => {
    if (activeRef.current) return true

    if (!secureContext) {
      setStatus('error')
      setError(
        'Микрофон доступен только на localhost или HTTPS. Откройте ' +
          'http://localhost:5173 либо запустите npm run dev:https.',
      )
      return false
    }

    if (!microphoneSupported || !navigator.mediaDevices?.getUserMedia) {
      setStatus('error')
      setError('Браузер не поддерживает запись с микрофона.')
      return false
    }

    setStatus('connecting')
    setError(null)
    setTranscript('')
    setInterim('')
    setSeconds(0)
    finalTextRef.current = ''
    interimTextRef.current = ''

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []

      const mimeType = pickMimeType()
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined,
      )

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        })
        const durationSeconds = Math.max(
          1,
          Math.round((Date.now() - startedAtRef.current) / 1000),
        )
        const resolve = stopResolveRef.current
        stopResolveRef.current = null
        resolve?.({
          blob,
          mimeType: recorder.mimeType || 'audio/webm',
          transcript: (
            finalTextRef.current +
            ' ' +
            interimTextRef.current
          ).trim(),
          durationSeconds,
        })
      }

      recorder.start(1000)
      recorderRef.current = recorder

      const Recognition = getSpeechRecognitionConstructor()
      if (Recognition) {
        const recognition = new Recognition()
        recognition.lang = 'ru-RU'
        recognition.continuous = true
        recognition.interimResults = true

        recognition.onresult = (event) => {
          let interimText = ''
          for (
            let index = event.resultIndex;
            index < event.results.length;
            index += 1
          ) {
            const result = event.results[index]
            const text = result[0].transcript
            if (result.isFinal) {
              finalTextRef.current += `${text.trim()} `
            } else {
              interimText += text
            }
          }
          interimTextRef.current = interimText.trim()
          setTranscript(finalTextRef.current.trim())
          setInterim(interimTextRef.current)
        }

        recognition.onerror = (event) => {
          if (event.error === 'not-allowed') {
            setError(
              'Доступ к микрофону запрещён. Разрешите микрофон в браузере.',
            )
          } else if (event.error === 'network') {
            setError(
              'Браузерное распознавание недоступно. После звонка запись ' +
                'расшифрует локальный T-one на backend.',
            )
          } else if (event.error === 'audio-capture') {
            setError('Микрофон не найден или занят другим приложением.')
          }
        }

        // Chrome останавливает распознавание после паузы — перезапускаем,
        // пока идёт звонок.
        recognition.onend = () => {
          if (!activeRef.current) return
          try {
            recognition.start()
          } catch {
            // Игнорируем повторный запуск, если сессия уже закрыта.
          }
        }

        recognition.start()
        recognitionRef.current = recognition
      } else {
        setSpeechSupported(false)
      }

      activeRef.current = true
      startedAtRef.current = Date.now()
      timerRef.current = window.setInterval(() => {
        setSeconds(
          Math.floor((Date.now() - startedAtRef.current) / 1000),
        )
      }, 1000)
      setStatus('active')
      return true
    } catch (err) {
      setStatus('error')
      setError(
        err instanceof Error
          ? `Не удалось получить доступ к микрофону: ${err.message}`
          : 'Не удалось получить доступ к микрофону',
      )
      streamRef.current?.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      return false
    }
  }, [secureContext, microphoneSupported])

  const stop = useCallback(async (): Promise<RecordedCall | null> => {
    const recorder = recorderRef.current
    if (!recorder || recorder.state === 'inactive') return null

    activeRef.current = false
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current)
      timerRef.current = null
    }

    try {
      recognitionRef.current?.stop()
    } catch {
      // Распознавание могло быть уже остановлено.
    }
    recognitionRef.current = null

    const result = new Promise<RecordedCall | null>((resolve) => {
      stopResolveRef.current = resolve
    })

    try {
      recorder.stop()
    } catch {
      // Если запись уже остановлена браузером, возвращаем null.
      const resolve = stopResolveRef.current
      stopResolveRef.current = null
      resolve?.(null)
    }
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    recorderRef.current = null
    setStatus('idle')

    return result
  }, [])

  useEffect(() => {
    return () => {
      activeRef.current = false
      if (timerRef.current !== null) {
        window.clearInterval(timerRef.current)
      }
      try {
        recognitionRef.current?.stop()
      } catch {
        // Ничего не делаем при размонтировании.
      }
      if (recorderRef.current?.state === 'recording') {
        recorderRef.current.stop()
      }
      streamRef.current?.getTracks().forEach((track) => track.stop())
    }
  }, [])

  return {
    status,
    seconds,
    transcript,
    interim,
    error,
    speechSupported,
    secureContext,
    microphoneSupported,
    start,
    stop,
  }
}
