import { useState } from 'react'
import {
  Bot,
  CheckCircle,
  FileText,
  Paperclip,
  PhoneCall,
  ShieldAlert,
  Wrench,
  XCircle,
} from 'lucide-react'
import {
  useCompleteTicket,
  useEngineers,
  useRefuseTicket,
  useTickets,
} from '@/features/tickets/hooks/useTickets'
import { useAuthStore } from '@/store/authStore'
import ConfirmModal from '@/components/ConfirmModal'
import { apiUrl } from '@/lib/api'
import type { Ticket } from '@/types/ticket.types'

const formatDuration = (seconds: number | null) => {
  if (seconds === null || seconds === undefined) return '—'
  const minutes = Math.floor(seconds / 60)
  const rest = seconds % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

export default function EngineerPage() {
  const user = useAuthStore((s) => s.user)
  const { data: tickets = [], isLoading } = useTickets()
  const { data: engineers = [] } = useEngineers()

  const { mutate: completeTicket, isPending: isCompleting } =
    useCompleteTicket()
  const { mutate: refuseTicket, isPending: isRefusing } = useRefuseTicket()

  const [selectedEngineerId, setSelectedEngineerId] = useState<
    number | null
  >(null)
  const [statusFilter, setStatusFilter] = useState<
    'active' | 'closed' | 'all'
  >('active')
  const [actionState, setActionState] = useState<{
    ticket: Ticket
    action: 'complete' | 'refuse'
  } | null>(null)

  const matchingEngineer = engineers.find(
    (engineer) => engineer.name === user?.name,
  )
  const activeEngineerId =
    selectedEngineerId ?? matchingEngineer?.id ?? engineers[0]?.id ?? null

  const myTickets = tickets.filter((ticket) => {
    const assigned =
      activeEngineerId !== null
        ? ticket.assignee?.id === activeEngineerId
        : ticket.assignee?.name === user?.name

    if (!assigned) return false
    if (statusFilter === 'active') return ticket.status !== 'closed'
    if (statusFilter === 'closed') return ticket.status === 'closed'
    return true
  })

  const handleConfirm = () => {
    if (!actionState) return
    const { ticket, action } = actionState

    if (action === 'complete') {
      completeTicket(ticket.id, {
        onSuccess: () => setActionState(null),
      })
    } else {
      refuseTicket(ticket.id, {
        onSuccess: () => setActionState(null),
      })
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
    <div className="mx-auto max-w-5xl pb-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Кабинет инженера
          </div>
          <h1 className="flex items-center gap-3 text-3xl font-semibold tracking-tight text-[#222]">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#242424] text-white">
              <Wrench size={20} strokeWidth={1.8} />
            </div>
            Мои задачи
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Назначенные заявки, вложения, записи звонков и действия.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={(event) =>
              setStatusFilter(
                event.target.value as 'active' | 'closed' | 'all',
              )
            }
            className="glass-input h-10 w-full sm:w-[170px]"
          >
            <option value="active">Активные</option>
            <option value="closed">Завершённые</option>
            <option value="all">Все</option>
          </select>

          {engineers.length > 0 && (
            <select
              value={activeEngineerId ?? ''}
              onChange={(event) =>
                setSelectedEngineerId(Number(event.target.value))
              }
              className="glass-input h-10 w-full sm:w-[250px]"
            >
              {engineers.map((engineer) => (
                <option key={engineer.id} value={engineer.id}>
                  {engineer.name} — {engineer.specialty}
                </option>
              ))}
            </select>
          )}

          <div className="flex items-center gap-2 rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500 shadow-sm">
            <CheckCircle size={15} />
            Активных: {myTickets.length}
          </div>
        </div>
      </div>

      {myTickets.length === 0 ? (
        <div className="glass-card flex min-h-[280px] flex-col items-center justify-center p-8 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
            <Wrench size={24} className="text-gray-400" />
          </div>
          <h3 className="text-base font-semibold text-[#222]">
            Задач пока нет
          </h3>
          <p className="mt-2 max-w-sm text-sm leading-6 text-gray-400">
            Нет заявок по выбранным фильтрам.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {myTickets.map((ticket) => (
            <div
              key={ticket.id}
              className="glass-card group overflow-hidden transition duration-200 hover:border-gray-300"
            >
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gray-100 bg-white/50 px-6 py-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-md bg-[#242424] px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-white">
                    {ticket.category}
                  </span>
                  <span className="text-xs font-medium text-gray-400">
                    Заявка #{ticket.id}
                  </span>
                  <span
                    className={`rounded-full px-3 py-1.5 text-[10px] font-semibold ${
                      ticket.status === 'closed'
                        ? 'border border-gray-200 bg-white text-gray-500'
                        : ticket.status === 'new'
                          ? 'bg-gray-100 text-gray-700'
                          : 'bg-[#242424] text-white'
                    }`}
                  >
                    {ticket.status === 'closed'
                      ? 'Завершена'
                      : ticket.status === 'new'
                        ? 'Назначена'
                        : 'В работе'}
                  </span>
                </div>

                {ticket.priority === 'high' && (
                  <span className="flex items-center gap-1.5 rounded-md border border-rose-100 bg-rose-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[#b87979]">
                    <ShieldAlert size={12} /> Срочно
                  </span>
                )}
              </div>

              <div className="space-y-5 p-6">
                <div>
                  <h3 className="mb-1 text-lg font-semibold text-[#222]">
                    {ticket.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-gray-500">
                    {ticket.aiDescription}
                  </p>
                </div>

                {ticket.aiSolution && (
                  <div className="relative overflow-hidden rounded-2xl border border-gray-200 bg-[#f8f9fa] p-4">
                    <div className="absolute left-0 top-0 h-full w-1 bg-[#242424]" />
                    <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#222]">
                      <Bot size={16} className="text-gray-500" />
                      Рекомендация ИИ
                    </div>
                    <p className="pl-1 text-sm leading-relaxed text-gray-600">
                      {ticket.aiSolution}
                    </p>
                  </div>
                )}

                {ticket.attachments && ticket.attachments.length > 0 && (
                  <div>
                    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      <Paperclip size={13} />
                      Фото, видео и документы
                    </div>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {ticket.attachments.map((attachment) => {
                        const url = apiUrl(attachment.url) ?? ''
                        const isVideo =
                          attachment.kind === 'video' ||
                          attachment.mime_type.startsWith('video/')

                        if (isVideo) {
                          return (
                            <video
                              key={attachment.id}
                              controls
                              src={url}
                              className="col-span-2 w-full rounded-xl border border-gray-100 bg-black"
                            />
                          )
                        }

                        if (attachment.kind === 'image') {
                          return (
                            <a
                              key={attachment.id}
                              href={url}
                              target="_blank"
                              rel="noreferrer"
                              className="overflow-hidden rounded-xl border border-gray-100"
                            >
                              <img
                                src={url}
                                alt={attachment.filename}
                                className="h-24 w-full object-cover"
                              />
                            </a>
                          )
                        }

                        if (attachment.kind === 'audio') {
                          return (
                            <audio
                              key={attachment.id}
                              controls
                              src={url}
                              className="col-span-2 w-full"
                            />
                          )
                        }

                        return (
                          <a
                            key={attachment.id}
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-center gap-2 rounded-xl border border-gray-100 bg-white px-3 py-2 text-xs text-gray-500"
                          >
                            <FileText size={14} className="shrink-0" />
                            <span className="truncate">
                              {attachment.filename}
                            </span>
                          </a>
                        )
                      })}
                    </div>
                  </div>
                )}

                {ticket.calls && ticket.calls.length > 0 && (
                  <div>
                    <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
                      <PhoneCall size={13} />
                      Записи звонков
                    </div>
                    <div className="space-y-2">
                      {ticket.calls.map((call) => {
                        const url = call.recording_url
                          ? apiUrl(call.recording_url) ?? ''
                          : ''

                        return (
                          <div
                            key={call.id}
                            className="rounded-xl bg-[#f5f5f3] p-3"
                          >
                            <div className="flex items-center justify-between gap-2 text-[10px] font-medium text-gray-500">
                              <span className="flex items-center gap-1">
                                <PhoneCall size={12} />
                                {call.status}
                              </span>
                              <span>
                                {formatDuration(call.duration_seconds)}
                              </span>
                            </div>

                            {url && (
                              <audio
                                controls
                                src={url}
                                className="mt-2 w-full"
                              />
                            )}

                            {call.transcript_preview && (
                              <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-gray-500">
                                {call.transcript_preview}
                              </p>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                <div className="flex flex-col gap-3 border-t border-gray-100 pt-5 sm:flex-row">
                  {ticket.status === 'closed' ? (
                    <span className="flex items-center gap-2 text-xs font-medium text-gray-500">
                      <CheckCircle size={15} /> Работа завершена
                    </span>
                  ) : (
                    <>
                      <button
                        onClick={() =>
                          setActionState({ ticket, action: 'complete' })
                        }
                        disabled={isCompleting || isRefusing}
                        className="button-dark flex-1 !h-12 disabled:opacity-50"
                      >
                        <CheckCircle size={18} /> Подтвердить выполнение
                      </button>
                      <button
                        onClick={() =>
                          setActionState({ ticket, action: 'refuse' })
                        }
                        disabled={isCompleting || isRefusing}
                        className="button-light flex-1 !h-12 !border-gray-200 text-gray-600 hover:!border-rose-200 hover:!bg-rose-50 hover:!text-rose-600 disabled:opacity-50"
                      >
                        <XCircle size={18} /> Отказаться
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmModal
        isOpen={!!actionState}
        title={
          actionState?.action === 'complete'
            ? 'Завершить задачу?'
            : 'Отказаться от задачи?'
        }
        message={
          actionState?.action === 'complete'
            ? `Подтвердите, что проблема в заявке #${actionState.ticket.id} действительно решена.`
            : `Заявка #${actionState?.ticket.id} вернется диспетчеру для переназначения.`
        }
        confirmText={
          actionState?.action === 'complete'
            ? 'Да, выполнено'
            : 'Да, отказаться'
        }
        confirmType={
          actionState?.action === 'complete' ? 'success' : 'danger'
        }
        onConfirm={handleConfirm}
        onCancel={() => setActionState(null)}
        isLoading={isCompleting || isRefusing}
      />
    </div>
  )
}
