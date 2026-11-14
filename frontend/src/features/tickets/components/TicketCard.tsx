import { useState } from 'react'
import type { Ticket } from '@/types/ticket.types'
import { UserCircle2, Wrench, AlertCircle, CheckCircle2, Pencil, X, Check } from 'lucide-react'
import { useApproveTicket, useAssignEngineer, useEngineers, useUpdateAiDescription } from '../hooks/useTickets'

export default function TicketCard({ ticket }: { ticket: Ticket }) {
  const [isEditingEngineer, setIsEditingEngineer] = useState(false)
  const [isEditingDesc, setIsEditingDesc] = useState(false)
  
  // Состояние для текста ИИ
  const [descValue, setDescValue] = useState(ticket.aiDescription)

  const { data: engineers = [] } = useEngineers()
  const { mutate: assignEngineer } = useAssignEngineer()
  const { mutate: approveTicket, isPending: isApproving } = useApproveTicket()
  const { mutate: updateDesc, isPending: isUpdatingDesc } = useUpdateAiDescription()

  const handleSaveDesc = () => {
    if (!descValue.trim()) return // Валидация: не сохраняем пустоту
    updateDesc({ ticketId: ticket.id, description: descValue.trim() }, {
      onSuccess: () => setIsEditingDesc(false)
    })
  }

  const handleCancelDesc = () => {
    setDescValue(ticket.aiDescription)
    setIsEditingDesc(false)
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 flex flex-col gap-4">
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-md font-medium">
              {ticket.category}
            </span>
            <span className="text-slate-400 text-sm">#{ticket.id}</span>
            {ticket.priority === 'high' && (
              <span className="flex items-center gap-1 text-rose-600 text-xs font-medium">
                <AlertCircle size={14} /> Высокий
              </span>
            )}
          </div>
          <h3 className="text-lg font-semibold text-slate-800">{ticket.title}</h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded ${ticket.status === 'new' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
          {ticket.status === 'new' ? 'Ожидает проверки' : 'В работе'}
        </span>
      </div>

      {/* Блок Анализа ИИ (теперь редактируемый) */}
      <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
        <div className="flex justify-between items-center mb-1">
          <div className="text-xs text-slate-400 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-purple-500"></span> Анализ ИИ
          </div>
          {ticket.status === 'new' && !isEditingDesc && (
            <button 
              onClick={() => setIsEditingDesc(true)} 
              className="text-slate-400 hover:text-blue-600 transition"
              title="Редактировать текст"
            >
              <Pencil size={14} />
            </button>
          )}
        </div>

        {isEditingDesc ? (
          <div className="mt-2">
            <textarea
              className="w-full border border-slate-300 rounded-md p-2 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 min-h-[80px]"
              value={descValue}
              onChange={(e) => setDescValue(e.target.value)}
              placeholder="Опишите суть проблемы..."
              autoFocus
            />
            <div className="flex justify-end gap-2 mt-2">
              <button 
                onClick={handleCancelDesc}
                className="px-3 py-1 text-xs font-medium text-slate-600 hover:bg-slate-200 rounded transition flex items-center gap-1"
              >
                <X size={14} /> Отмена
              </button>
              <button 
                onClick={handleSaveDesc}
                disabled={!descValue.trim() || isUpdatingDesc}
                className="px-3 py-1 text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 rounded transition disabled:opacity-50 flex items-center gap-1"
              >
                <Check size={14} /> {isUpdatingDesc ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-600 mt-1">{ticket.aiDescription}</p>
        )}
      </div>

      <div className="flex items-center justify-between mt-2 pt-4 border-t border-slate-100">
        <div className="text-sm text-slate-500 flex items-center gap-2">
          <Wrench size={16} /> Исполнитель:
        </div>

        {isEditingEngineer ? (
          <select
            className="border border-slate-300 rounded-md p-2 text-sm outline-none focus:border-blue-500"
            value={ticket.assignee?.id || ''}
            onChange={(e) => {
              const eng = engineers.find((x) => x.id === Number(e.target.value))
              if (eng) assignEngineer({ ticketId: ticket.id, engineer: eng })
              setIsEditingEngineer(false)
            }}
            onBlur={() => setIsEditingEngineer(false)}
            autoFocus
          >
            {engineers.map((eng) => (
              <option key={eng.id} value={eng.id}>
                {eng.name} ({eng.specialty})
              </option>
            ))}
          </select>
        ) : (
          <button
            onClick={() => setIsEditingEngineer(true)}
            disabled={ticket.status !== 'new'}
            className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <UserCircle2 size={18} className="text-blue-600" />
            <div className="text-left">
              <div className="text-sm font-medium text-slate-800">{ticket.assignee?.name || 'Не назначен'}</div>
              <div className="text-xs text-slate-500">{ticket.assignee?.specialty}</div>
            </div>
          </button>
        )}
      </div>

      {ticket.status === 'new' && (
        <button
          onClick={() => approveTicket(ticket.id)}
          disabled={isApproving || isEditingDesc || !descValue.trim()}
          className="w-full mt-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg text-sm font-medium transition flex items-center justify-center gap-2"
        >
          <CheckCircle2 size={16} /> {isApproving ? 'Отправка...' : 'Утвердить и отправить'}
        </button>
      )}
    </div>
  )
}