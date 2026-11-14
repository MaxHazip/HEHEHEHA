import { useEffect, useState } from 'react'
import { PhoneOff, Mic, Loader2, Volume2 } from 'lucide-react'

interface Props {
  isOpen: boolean
  onClose: (transcribedText?: string, aiReply?: string) => void
}

// Этапы звонка
type CallStatus = 'connecting' | 'talking' | 'processing' | 'ai_reply'

export default function VoiceCallModal({ isOpen, onClose }: Props) {
  const [seconds, setSeconds] = useState(0)
  const [status, setStatus] = useState<CallStatus>('connecting')

  // Таймер и управление этапами
  useEffect(() => {
    if (!isOpen) {
      setSeconds(0)
      setStatus('connecting')
      return
    }

    // 1. Имитация установки соединения (1.5 сек)
    const connectTimeout = setTimeout(() => {
      setStatus('talking')
    }, 1500)

    const timer = setInterval(() => {
      setSeconds(s => s + 1)
    }, 1000)

    return () => {
      clearTimeout(connectTimeout)
      clearInterval(timer)
    }
  }, [isOpen])

  const handleEndCall = () => {
    setStatus('processing')
    
    // Имитация обработки речи
    setTimeout(() => {
      setStatus('ai_reply')
      
      // Имитация голосового ответа ИИ (2.5 сек)
      setTimeout(() => {
        const mockTranscribedText = 'Здравствуйте, у меня не работает интернет в кабинете 305, компьютер пишет "Нет подключения".'
        const mockAiReply = 'Ваша заявка принята в работу. Ожидайте инженера.'
        
        // Закрываем модалку и передаем данные в чат
        onClose(mockTranscribedText, mockAiReply)
      }, 2500)
    }, 2000)
  }

  if (!isOpen) return null

  const formatTime = (totalSeconds: number) => {
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0')
    const s = (totalSeconds % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-sm w-full p-8 flex flex-col items-center text-center animate-in fade-in zoom-in-95 duration-200">
        
        {/* Аватарка / Анимация */}
        <div className="relative mb-6">
          <div className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-500 ${
            status === 'talking' ? 'bg-blue-100 text-blue-600' : 
            status === 'ai_reply' ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-100 text-slate-400'
          }`}>
            {status === 'connecting' && <Loader2 size={40} className="animate-spin" />}
            
            {status === 'talking' && (
              <>
                <div className="absolute inset-0 bg-blue-400 rounded-full animate-ping opacity-20"></div>
                <Mic size={40} className="relative z-10" />
              </>
            )}
            
            {status === 'processing' && <Loader2 size={40} className="animate-spin text-purple-600" />}
            
            {status === 'ai_reply' && (
              <>
                <div className="absolute inset-0 bg-emerald-400 rounded-full animate-pulse opacity-20"></div>
                <Volume2 size={40} className="relative z-10" />
              </>
            )}
          </div>
        </div>

        {/* Статус и текст */}
        <h3 className="text-xl font-semibold text-slate-800 mb-2">
          {status === 'connecting' && 'Соединение с ИИ...'}
          {status === 'talking' && 'Идет звонок...'}
          {status === 'processing' && 'ИИ обрабатывает...'}
          {status === 'ai_reply' && 'Ответ ИИ:'}
        </h3>
        
        <p className={`text-sm mb-6 h-12 font-medium ${status === 'ai_reply' ? 'text-emerald-600' : 'text-slate-500'}`}>
          {status === 'talking' && 'Говорите, ИИ вас внимательно слушает.'}
          {status === 'processing' && 'Нейросеть формирует заявку...'}
          {status === 'ai_reply' && '«Ваша заявка принята в работу. Ожидайте инженера.»'}
        </p>

        {/* Таймер */}
        <div className={`text-2xl font-mono mb-8 ${status === 'talking' ? 'text-blue-600' : 'text-slate-300'}`}>
          {formatTime(seconds)}
        </div>

        {/* Кнопка сброса */}
        <button
          onClick={handleEndCall}
          disabled={status === 'processing' || status === 'ai_reply'}
          className="w-16 h-16 bg-rose-500 hover:bg-rose-600 disabled:bg-rose-300 text-white rounded-full flex items-center justify-center transition shadow-lg shadow-rose-200"
          title="Завершить звонок"
        >
          {(status === 'processing' || status === 'ai_reply') 
            ? <Loader2 size={24} className="animate-spin" /> 
            : <PhoneOff size={24} />
          }
        </button>
        <p className="text-xs text-slate-400 mt-4">
          {status === 'talking' ? 'Нажмите, чтобы завершить' : 'Подождите...'}
        </p>
      </div>
    </div>
  )
}