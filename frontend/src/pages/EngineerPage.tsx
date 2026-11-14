import { useState } from 'react'
import { useTickets, useCompleteTicket, useRefuseTicket } from '@/features/tickets/hooks/useTickets'
import { useAuthStore } from '@/store/authStore'
import { CheckCircle, XCircle, FileText, Bot, Wrench } from 'lucide-react'
import ConfirmModal from '@/components/ConfirmModal'
import type { Ticket } from '@/types/ticket.types'

export default function EngineerPage() {
  const user = useAuthStore((s) => s.user)
  const { data: tickets = [], isLoading } = useTickets()
  
  const { mutate: completeTicket, isPending: isCompleting } = useCompleteTicket()
  const { mutate: refuseTicket, isPending: isRefusing } = useRefuseTicket()

  // Состояние для модального окна
  const [actionState, setActionState] = useState<{ ticket: Ticket, action: 'complete' | 'refuse' } | null>(null)

  const myTickets = tickets.filter(
    (t) => t.status === 'in_progress' && t.assignee !== null && t.assignee.id === user?.engineerId
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

  if (isLoading) return <div className="p-6 text-center text-slate-500 mt-10">Загрузка задач...</div>

  return (
    <div className="max-w-3xl mx-auto mt-4">
      <h1 className="text-2xl font-semibold text-slate-800 mb-6 flex items-center gap-2">
        <Wrench className="text-blue-600" /> Мои задачи
      </h1>
      
      {myTickets.length === 0 ? (
        <div className="bg-white p-10 rounded-xl text-center text-slate-500 border border-slate-200 shadow-sm">
          У вас пока нет назначенных задач. Ожидайте заявок от диспетчера.
        </div>
      ) : (
        <div className="space-y-6">
          {myTickets.map((ticket) => (
            <div key={ticket.id} className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              
              {/* Шапка карточки */}
              <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <span className="bg-blue-100 text-blue-700 text-sm px-3 py-1 rounded-lg font-medium">
                    {ticket.category}
                  </span>
                  <span className="text-slate-400 text-sm">Заявка #{ticket.id}</span>
                </div>
                {ticket.priority === 'high' && (
                  <span className="text-rose-600 text-xs font-bold uppercase tracking-wider bg-rose-50 px-2 py-1 rounded">
                    Срочно
                  </span>
                )}
              </div>
              
              <div className="p-6 space-y-5">
                {/* Проблема */}
                <div>
                  <h3 className="text-lg font-semibold text-slate-800 mb-1">{ticket.title}</h3>
                  <p className="text-slate-600 text-sm">{ticket.aiDescription}</p>
                  {ticket.knowledgeArticles?.map((article) => (
                    <details key={article.code} className="mt-2 text-sm">
                      <summary className="cursor-pointer text-blue-700">{article.title}</summary>
                      <p className="mt-1 text-slate-600">{article.body}</p>
                    </details>
                  ))}

                </div>

                {/* Решение от ИИ */}
                {ticket.aiSolution && (
                  <div className="bg-purple-50 border border-purple-100 p-4 rounded-lg">
                    <div className="flex items-center gap-2 text-purple-700 font-medium mb-2 text-sm">
                      <Bot size={18} /> Рекомендация нейросети
                    </div>
                    <p className="text-sm text-purple-900 leading-relaxed">
                      {ticket.aiSolution}
                    </p>
                  </div>
                )}

                {/* Документация */}
                {ticket.documents && ticket.documents.length > 0 && (
                  <div>
                    <div className="text-sm font-medium text-slate-700 mb-2">Прикрепленная документация:</div>
                    <div className="flex flex-wrap gap-2">
                      {ticket.documents.map((doc, idx) => (
                        <a 
                          key={idx} 
                          href="#" 
                          onClick={(e) => { e.preventDefault(); alert(`Открытие файла: ${doc}`) }}
                          className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 px-3 py-2 rounded-lg text-sm text-slate-700 transition"
                        >
                          <FileText size={16} className="text-blue-500" />
                          {doc}
                        </a>
                      ))}
                    </div>
                  </div>
                )}

                {/* Кнопки действий */}
                <div className="pt-4 border-t border-slate-100 flex gap-3">
                  <button
                    onClick={() => setActionState({ ticket, action: 'complete' })}
                    disabled={isCompleting || isRefusing}
                    className="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white py-3 rounded-lg font-medium transition"
                  >
                    <CheckCircle size={18} /> Подтвердить выполнение
                  </button>
                  <button
                    onClick={() => setActionState({ ticket, action: 'refuse' })}
                    disabled={isCompleting || isRefusing}
                    className="flex-1 flex items-center justify-center gap-2 bg-white border border-rose-200 text-rose-600 hover:bg-rose-50 disabled:opacity-50 py-3 rounded-lg font-medium transition"
                  >
                    <XCircle size={18} /> Отказаться от заявки
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