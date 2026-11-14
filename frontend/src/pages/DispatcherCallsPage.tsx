import { useState } from 'react'
import { PhoneCall, Play, Pause, FileText, ShieldAlert } from 'lucide-react'

// Моковые данные для журнала звонков
const MOCK_CALLS = [
  {
    id: 1,
    caller: '+7 (999) 123-45-67',
    time: 'Сегодня, 14:32',
    duration: '01:24',
    status: 'ИИ обработал',
    statusType: 'success',
    transcript: 'Клиент сообщил: "Здравствуйте, у меня не работает интернет в кабинете 305, компьютер пишет Нет подключения". ИИ создал заявку #101.',
  },
  {
    id: 2,
    caller: '+7 (888) 777-66-55',
    time: 'Сегодня, 13:10',
    duration: '00:45',
    status: 'Требуется диспетчер',
    statusType: 'danger',
    transcript: 'Клиент сильно ругался, прорвало трубу. Требуется срочная эскалация сантехнику.',
  }
]

export default function DispatcherCallsPage() {
  const [playingId, setPlayingId] = useState<number | null>(null)

  const togglePlay = (id: number) => {
    setPlayingId(playingId === id ? null : id)
  }

  return (
    <div className="space-y-6 pb-8">
      {/* Заголовок */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Телефония
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Журнал звонков
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Аудиозаписи и интеллектуальные расшифровки от нейросети.
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {MOCK_CALLS.map(call => (
          <div key={call.id} className="glass-card overflow-hidden">
            {/* Шапка карточки звонка */}
            <div className="border-b border-gray-100 bg-white/50 px-5 py-4 flex flex-wrap justify-between items-center gap-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#242424] text-white">
                  <PhoneCall size={18} />
                </div>
                <div>
                  <div className="font-semibold text-[#222]">{call.caller}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{call.time}</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {call.duration}
                </span>
                <span className={`flex items-center gap-1.5 text-[10px] font-semibold px-2.5 py-1.5 rounded-md ${
                  call.statusType === 'success' 
                    ? 'bg-emerald-50 text-emerald-700' 
                    : 'bg-rose-50 text-rose-700'
                }`}>
                  {call.statusType === 'danger' && <ShieldAlert size={12} />}
                  {call.status}
                </span>
              </div>
            </div>

            {/* Плеер и расшифровка */}
            <div className="p-5 flex flex-col md:flex-row gap-5">
              {/* Кнопка Play */}
              <div className="shrink-0 flex items-center">
                <button 
                  onClick={() => togglePlay(call.id)}
                  className="flex h-12 w-12 items-center justify-center rounded-full bg-[#242424] text-white hover:bg-[#454545] transition shadow-lg shadow-black/10"
                >
                  {playingId === call.id ? <Pause size={20} /> : <Play size={20} className="ml-1" />}
                </button>
              </div>

              {/* Транскрипция */}
              <div className="flex-1 rounded-2xl border border-gray-100 bg-white/60 p-4">
                <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[1px] text-gray-400">
                  <FileText size={14} /> Расшифровка (Speech-to-Text)
                </div>
                <p className="text-sm leading-relaxed text-gray-600">
                  {call.transcript}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}