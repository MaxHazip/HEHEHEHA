import { useMemo, useState } from 'react'
import {
  Search,
  Inbox,
  Clock3,
  CheckCircle2,
  AlertCircle,
  SlidersHorizontal,
  X,
} from 'lucide-react'
import { useTickets } from '@/features/tickets/hooks/useTickets'
import TicketCard from '@/features/tickets/components/TicketCard'

type FilterStatus = 'all' | 'new' | 'in_progress' | 'closed'

const filters: { id: FilterStatus; label: string }[] = [
  { id: 'all', label: 'Все обращения' },
  { id: 'new', label: 'Новые' },
  { id: 'in_progress', label: 'В работе' },
  { id: 'closed', label: 'Завершённые' },
]

export default function TicketsPage() {
  const { data: tickets = [], isLoading, isError } = useTickets()

  const [activeFilter, setActiveFilter] = useState<FilterStatus>('all')
  const [search, setSearch] = useState('')

  const newCount = tickets.filter((ticket) => ticket.status === 'new').length
  const activeCount = tickets.filter(
    (ticket) => ticket.status === 'in_progress'
  ).length
  const closedCount = tickets.filter(
    (ticket) => ticket.status === 'closed'
  ).length

  const filteredTickets = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase()

    return tickets.filter((ticket) => {
      const matchesStatus =
        activeFilter === 'all' || ticket.status === activeFilter

      const matchesSearch =
        !normalizedSearch ||
        [
          ticket.title,
          ticket.category,
          ticket.aiDescription,
          String(ticket.id),
          ticket.assignee?.name || '',
        ]
          .join(' ')
          .toLowerCase()
          .includes(normalizedSearch)

      return matchesStatus && matchesSearch
    })
  }, [tickets, activeFilter, search])

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-black" />
          Загружаем обращения...
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="glass-card p-10 text-center">
        <AlertCircle size={30} className="mx-auto mb-3 text-gray-400" />
        <h2 className="font-semibold">Не удалось загрузить обращения</h2>
        <p className="mt-2 text-sm text-gray-400">
          Проверь соединение с системой и попробуй снова.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">

      {/* Заголовок */}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Управление обращениями
          </div>

          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Все заявки
          </h1>

          <p className="mt-2 text-sm text-gray-400">
            Просматривайте, распределяйте и обрабатывайте обращения.
          </p>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500">
          <Inbox size={15} />
          Всего: {tickets.length}
        </div>
      </div>

      {/* Статистика */}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">

        <div className="dark-card flex items-center justify-between p-5">
          <div>
            <div className="text-xs text-white/50">
              Новые обращения
            </div>

            <div className="mt-3 text-4xl font-semibold tracking-tight">
              {newCount}
            </div>

            <div className="mt-2 text-[10px] text-white/40">
              Ожидают обработки
            </div>
          </div>

          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10">
            <Inbox size={21} />
          </div>
        </div>

        <div className="glass-card flex items-center justify-between p-5">
          <div>
            <div className="text-xs text-gray-400">
              В работе
            </div>

            <div className="mt-3 text-4xl font-semibold tracking-tight text-[#222]">
              {activeCount}
            </div>

            <div className="mt-2 text-[10px] text-gray-400">
              Назначены исполнителям
            </div>
          </div>

          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100">
            <Clock3 size={21} />
          </div>
        </div>

        <div className="glass-card flex items-center justify-between p-5">
          <div>
            <div className="text-xs text-gray-400">
              Завершено
            </div>

            <div className="mt-3 text-4xl font-semibold tracking-tight text-[#222]">
              {closedCount}
            </div>

            <div className="mt-2 text-[10px] text-gray-400">
              Решённые обращения
            </div>
          </div>

          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gray-100">
            <CheckCircle2 size={21} />
          </div>
        </div>

      </div>

      {/* Панель управления */}

      <section className="glass-card p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

          <div className="relative w-full lg:max-w-sm">
            <Search
              size={17}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />

            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Поиск по заявкам..."
              className="glass-input h-11 pl-11 pr-10"
              style={{ paddingLeft: '42px' }}
            />

            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-black"
                aria-label="Очистить поиск"
              >
                <X size={15} />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <SlidersHorizontal size={15} className="mr-1 text-gray-400" />

            {filters.map((filter) => (
              <button
                key={filter.id}
                type="button"
                onClick={() => setActiveFilter(filter.id)}
                className={`rounded-full px-4 py-2.5 text-xs font-medium transition ${
                  activeFilter === filter.id
                    ? 'bg-[#242424] text-white'
                    : 'border border-gray-100 bg-white text-gray-500 hover:border-gray-300 hover:text-black'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Заголовок результатов */}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-[#222]">
            Список обращений
          </h2>

          <p className="mt-1 text-xs text-gray-400">
            Найдено: {filteredTickets.length}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="h-2 w-2 rounded-full bg-[#242424]" />
          Актуальные данные
        </div>
      </div>

      {/* Карточки */}

      {filteredTickets.length === 0 ? (
        <div className="glass-card flex min-h-[280px] flex-col items-center justify-center p-8 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
            <Inbox size={24} className="text-gray-400" />
          </div>

          <h3 className="text-base font-semibold text-[#222]">
            Обращения не найдены
          </h3>

          <p className="mt-2 max-w-sm text-sm leading-6 text-gray-400">
            Попробуйте изменить поисковый запрос или выбрать другую категорию.
          </p>

          {(search || activeFilter !== 'all') && (
            <button
              type="button"
              onClick={() => {
                setSearch('')
                setActiveFilter('all')
              }}
              className="button-dark mt-5"
            >
              Сбросить фильтры
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {filteredTickets.map((ticket) => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}

      {/* Нижняя подпись */}

      <div className="flex items-center justify-between border-t border-gray-200/70 pt-5 text-[10px] text-gray-400">
        <span>DISPATCHAI · TICKET MANAGEMENT</span>
        <span>Всего записей: {tickets.length}</span>
      </div>
    </div>
  )
}