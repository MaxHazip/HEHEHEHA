import { useState } from 'react'
import type { Ticket } from '@/types/ticket.types'
import {
  UserCircle2,
  Wrench,
  AlertCircle,
  CheckCircle2,
  Pencil,
  X,
  Check,
  Clock3,
  Sparkles,
  FileText,
  ArrowUpRight,
  Loader2,
  UserRound,
} from 'lucide-react'

import {
  useApproveTicket,
  useAssignEngineer,
  useEngineers,
  useUpdateAiDescription,
} from '../hooks/useTickets'

interface Props {
  ticket: Ticket
}

const statusLabels: Record<Ticket['status'], string> = {
  new: 'Ожидает обработки',
  in_progress: 'В работе',
  closed: 'Завершена',
}

const formatDate = (date: string) => {
  const parsed = new Date(date)

  if (Number.isNaN(parsed.getTime())) {
    return 'Дата неизвестна'
  }

  return parsed.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  })
}

export default function TicketCard({ ticket }: Props) {
  const [isEditingEngineer, setIsEditingEngineer] = useState(false)
  const [isEditingDesc, setIsEditingDesc] = useState(false)
  const [descValue, setDescValue] = useState(ticket.aiDescription)

  const { data: engineers = [] } = useEngineers()

  const {
    mutate: assignEngineer,
    isPending: isAssigning,
  } = useAssignEngineer()

  const {
    mutate: approveTicket,
    isPending: isApproving,
  } = useApproveTicket()

  const {
    mutate: updateDesc,
    isPending: isUpdatingDesc,
  } = useUpdateAiDescription()

  const handleSaveDesc = () => {
    if (!descValue.trim()) return

    updateDesc(
      {
        ticketId: ticket.id,
        description: descValue.trim(),
      },
      {
        onSuccess: () => setIsEditingDesc(false),
      }
    )
  }

  const handleCancelDesc = () => {
    setDescValue(ticket.aiDescription)
    setIsEditingDesc(false)
  }

  const handleAssign = (engineerId: string) => {
    const engineer = engineers.find(
      (item) => item.id === Number(engineerId)
    )

    if (!engineer) return

    assignEngineer(
      {
        ticketId: ticket.id,
        engineer,
      },
      {
        onSuccess: () => setIsEditingEngineer(false),
      }
    )
  }

  return (
    <article className="glass-card group overflow-hidden p-5 transition duration-200 hover:-translate-y-1 hover:shadow-[0_15px_40px_rgba(0,0,0,0.055)] sm:p-6">

      {/* Верхняя панель */}

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-gray-100 px-3 py-1 text-[10px] font-semibold text-gray-500">
              #{ticket.id}
            </span>

            <span className="text-[11px] text-gray-400">
              {ticket.category}
            </span>
          </div>

          <h3 className="text-lg font-semibold leading-snug tracking-tight text-[#222]">
            {ticket.title}
          </h3>
        </div>

        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gray-100 text-[#333] transition group-hover:bg-[#242424] group-hover:text-white">
          {ticket.status === 'closed' ? (
            <CheckCircle2 size={18} />
          ) : ticket.status === 'in_progress' ? (
            <Wrench size={18} />
          ) : (
            <InboxIcon />
          )}
        </div>
      </div>

      {/* Статусы */}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[10px] font-semibold ${
            ticket.status === 'new'
              ? 'bg-gray-100 text-gray-700'
              : ticket.status === 'in_progress'
                ? 'bg-[#242424] text-white'
                : 'border border-gray-200 bg-white text-gray-500'
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${
              ticket.status === 'in_progress'
                ? 'bg-white'
                : 'bg-current'
            }`}
          />

          {statusLabels[ticket.status]}
        </span>

        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-semibold ${
            ticket.priority === 'high'
              ? 'bg-[#ededed] text-[#222]'
              : 'bg-white text-gray-400 border border-gray-100'
          }`}
        >
          {ticket.priority === 'high' && (
            <AlertCircle size={12} />
          )}

          {ticket.priority === 'high'
            ? 'Высокий приоритет'
            : ticket.priority === 'medium'
              ? 'Средний приоритет'
              : 'Низкий приоритет'}
        </span>
      </div>

      {/* Анализ ИИ */}

      <div className="mt-5 rounded-2xl bg-[#f5f5f3] p-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-white">
              <Sparkles size={14} />
            </div>

            <span className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
              Анализ ИИ
            </span>
          </div>

          {ticket.status === 'new' && !isEditingDesc && (
            <button
              type="button"
              onClick={() => setIsEditingDesc(true)}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-white text-gray-400 transition hover:bg-[#242424] hover:text-white"
              title="Редактировать анализ"
            >
              <Pencil size={13} />
            </button>
          )}
        </div>

        {isEditingDesc ? (
          <div>
            <textarea
              value={descValue}
              onChange={(event) => setDescValue(event.target.value)}
              autoFocus
              rows={4}
              className="w-full resize-y rounded-xl border border-gray-200 bg-white p-3 text-sm leading-6 text-[#333] outline-none transition focus:border-gray-500"
            />

            <div className="mt-3 flex justify-end gap-2">
              <button
                type="button"
                onClick={handleCancelDesc}
                disabled={isUpdatingDesc}
                className="button-light"
              >
                <X size={14} />
                Отмена
              </button>

              <button
                type="button"
                onClick={handleSaveDesc}
                disabled={!descValue.trim() || isUpdatingDesc}
                className="button-dark disabled:opacity-50"
              >
                {isUpdatingDesc ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <Check size={14} />
                )}

                Сохранить
              </button>
            </div>
          </div>
        ) : (
          <p className="whitespace-pre-wrap text-sm leading-6 text-gray-600">
            {ticket.aiDescription || 'Описание отсутствует.'}
          </p>
        )}
      </div>

      {/* Дополнительные документы */}

      {ticket.documents && ticket.documents.length > 0 && (
        <div className="mt-5">
          <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">
            <FileText size={14} />
            Прикреплённые документы
          </div>

          <div className="flex flex-wrap gap-2">
            {ticket.documents.map((document, index) => (
              <div
                key={`${document}-${index}`}
                className="flex max-w-full items-center gap-2 rounded-xl border border-gray-100 bg-white px-3 py-2 text-xs text-gray-500"
              >
                <FileText size={13} className="shrink-0" />

                <span className="truncate">
                  {document}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Исполнитель */}

      <div className="mt-5 border-t border-gray-100 pt-5">
        <div className="mb-3 text-[10px] font-semibold uppercase tracking-[1.5px] text-gray-400">
          Ответственный исполнитель
        </div>

        {isEditingEngineer ? (
          <div className="space-y-3">
            <select
              value={ticket.assignee?.id || ''}
              onChange={(event) => handleAssign(event.target.value)}
              disabled={isAssigning}
              className="glass-input"
            >
              <option value="" disabled>
                Выберите инженера
              </option>

              {engineers.map((engineer) => (
                <option key={engineer.id} value={engineer.id}>
                  {engineer.name} — {engineer.specialty}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={() => setIsEditingEngineer(false)}
              disabled={isAssigning}
              className="text-xs text-gray-400 hover:text-black"
            >
              Отмена
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setIsEditingEngineer(true)}
            disabled={ticket.status !== 'new' || isAssigning}
            className="flex w-full items-center gap-3 rounded-2xl border border-gray-100 bg-white p-3 text-left transition hover:border-gray-300 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gray-100">
              {ticket.assignee ? (
                <UserCircle2 size={20} />
              ) : (
                <UserRound size={20} className="text-gray-400" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-[#222]">
                {ticket.assignee?.name || 'Не назначен'}
              </div>

              <div className="mt-1 text-[11px] text-gray-400">
                {ticket.assignee?.specialty || 'Исполнитель не выбран'}
              </div>
            </div>

            {isAssigning ? (
              <Loader2 size={15} className="animate-spin text-gray-400" />
            ) : (
              <ArrowUpRight size={16} className="text-gray-300" />
            )}
          </button>
        )}
      </div>

      {/* Нижняя панель */}

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100 pt-4">
        <div className="flex items-center gap-2 text-[10px] text-gray-400">
          <Clock3 size={13} />
          {formatDate(ticket.createdAt)}
        </div>

        {ticket.status === 'new' && (
          <button
            type="button"
            onClick={() => approveTicket(ticket.id)}
            disabled={
              isApproving ||
              isEditingDesc ||
              isEditingEngineer ||
              !descValue.trim()
            }
            className="button-dark disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isApproving ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <CheckCircle2 size={14} />
            )}

            {isApproving ? 'Отправка...' : 'Утвердить заявку'}
          </button>
        )}

        {ticket.status === 'in_progress' && (
          <span className="flex items-center gap-2 text-[10px] font-medium text-gray-500">
            <Wrench size={13} />
            Передана инженеру
          </span>
        )}

        {ticket.status === 'closed' && (
          <span className="flex items-center gap-2 text-[10px] font-medium text-gray-500">
            <CheckCircle2 size={13} />
            Работа завершена
          </span>
        )}
      </div>
    </article>
  )
}

function InboxIcon() {
  return <FileText size={18} />
}