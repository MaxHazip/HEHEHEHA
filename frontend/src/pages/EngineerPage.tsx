import { useState } from 'react'
import { useTickets, useCompleteTicket, useRefuseTicket } from '@/features/tickets/hooks/useTickets'
import { useAuthStore } from '@/store/authStore'
import { CheckCircle, XCircle, FileText, Bot, Wrench, ShieldAlert } from 'lucide-react'
import ConfirmModal from '@/components/ConfirmModal'
import type { Ticket } from '@/types/ticket.types'

export default function EngineerPage() {
  const user = useAuthStore((s) => s.user)
  const { data: tickets = [], isLoading } = useTickets()
  
  const { mutate: completeTicket, isPending: isCompleting } = useCompleteTicket()
  const { mutate: refuseTicket, isPending: isRefusing } = useRefuseTicket()

  const [actionState, setActionState] = useState<{ ticket: Ticket, action: 'complete' | 'refuse' } | null>(null)

  const myTickets = tickets.filter(
    (t) => t.status === 'in_progress' && t.assignee?.name === user?.name
  )

  const handleConfirm = () => {
    if (!actionState) return
    const { ticket, action } = actionState
    
    if (action === 'complete') {
      completeTicket(ticket.id, { onSuccess: () => setActionState(null) })
    } else {
      refuseTicket(ticket.id, { onSuccess: () => setActionState(null) })
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-black" />
          Загружаем задачи...
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto pb-8">
      
      {/* Заголовок (Убрали синий цвет у ключа) */}
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Кабинет инженера
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#222] flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#242424] text-white">
              <Wrench size={20} strokeWidth={1.8} />
            </div>
            Мои задачи
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Выполняйте назначенные заявки или отказывайтесь с переназначением.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500 shadow-sm">
          <CheckCircle size={15} />
          Активных: {myTickets.length}
        </div>
      </div>
      
      {myTickets.length === 0 ? (
        <div className="glass-card flex min-h-[280px] flex-col items-center justify-center p-8 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
            <Wrench size={24} className="text-gray-400" />
          </div>
          <h3 className="text-base font-semibold text-[#222]">Задач пока нет</h3>
          <p className="mt-2 max-w-sm text-sm leading-6 text-gray-400">
            У вас нет назначенных заявок. Ожидайте, пока диспетчер отправит вам новую задачу.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {myTickets.map((ticket) => (
            <div key={ticket.id} className="glass-card overflow-hidden group hover:border-gray-300 transition duration-200">
              
              {/* Шапка карточки */}
              <div className="bg-white/50 px-6 py-4 border-b border-gray-100 flex flex-wrap justify-between items-center gap-3">
                <div className="flex items-center gap-3">
                  <span className="bg-[#242424] text-white text-[10px] uppercase tracking-wider px-3 py-1.5 rounded-md font-semibold">
                    {ticket.category}
                  </span>
                  <span className="text-gray-400 text-xs font-medium">Заявка #{ticket.id}</span>
                </div>
                {ticket.priority === 'high' && (
                  <span className="flex items-center gap-1.5 text-[#b87979] text-[10px] font-bold uppercase tracking-wider bg-rose-50 px-2.5 py-1 rounded-md border border-rose-100">
                    <ShieldAlert size={12} /> Срочно
                  </span>
                )}
              </div>
              
              <div className="p-6 space-y-5">
                {/* Проблема */}
                <div>
                  <h3 className="text-lg font-semibold text-[#222] mb-1">{ticket.title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed">{ticket.aiDescription}</p>
                </div>

                {/* Решение от ИИ */}
                {ticket.aiSolution && (
                  <div className="bg-[#f8f9fa] border border-gray-200 p-4 rounded-2xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-[#242424]"></div>
                    <div className="flex items-center gap-2 text-[#222] font-semibold mb-2 text-xs uppercase tracking-wider">
                      <Bot size={16} className="text-gray-500" /> Рекомендация ИИ
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed pl-1">
                      {ticket.aiSolution}
                    </p>
                  </div>
                )}

                {/* Документация */}
                {ticket.documents && ticket.documents.length > 0 && (
                  <div>
                    <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">Документация:</div>
                    <div className="flex flex-wrap gap-2">
                      {ticket.documents.map((doc, idx) => (
                        <a 
                          key={idx} 
                          href="#" 
                          onClick={(e) => { e.preventDefault(); alert(`Открытие файла: ${doc}`) }}
                          className="flex items-center gap-2 bg-white border border-gray-200 hover:border-gray-400 px-3 py-2 rounded-xl text-xs font-medium text-gray-700 transition shadow-sm"
                        >
                          <FileText size={14} className="text-gray-400" />
                          {doc}
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Кнопки действий (Обновили стили) */}
                <div className="pt-5 border-t border-gray-100 flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={() => setActionState({ ticket, action: 'complete' })}
                    disabled={isCompleting || isRefusing}
                    className="button-dark flex-1 !h-12 disabled:opacity-50"
                  >
                    <CheckCircle size={18} /> Подтвердить выполнение
                  </button>
                  <button
                    onClick={() => setActionState({ ticket, action: 'refuse' })}
                    disabled={isCompleting || isRefusing}
                    className="button-light flex-1 !h-12 !border-gray-200 text-gray-600 hover:!text-rose-600 hover:!border-rose-200 hover:!bg-rose-50 disabled:opacity-50"
                  >
                    <XCircle size={18} /> Отказаться
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Модалка подтверждения */}
      <ConfirmModal
        isOpen={!!actionState}
        title={actionState?.action === 'complete' ? 'Завершить задачу?' : 'Отказаться от задачи?'}
        message={
          actionState?.action === 'complete' 
            ? `Подтвердите, что проблема в заявке #${actionState.ticket.id} действительно решена.` 
            : `Заявка #${actionState?.ticket.id} вернется диспетчеру для переназначения.`
        }
        confirmText={actionState?.action === 'complete' ? 'Да, выполнено' : 'Да, отказаться'}
        confirmType={actionState?.action === 'complete' ? 'success' : 'danger'}
        onConfirm={handleConfirm}
        onCancel={() => setActionState(null)}
        isLoading={isCompleting || isRefusing}
      />
    </div>
  )
}