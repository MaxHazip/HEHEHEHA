import { Link } from 'react-router-dom'
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Bell,
  CheckCircle2,
  Clock3,
  Inbox,
  Plus,
  Radio,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Wrench,
} from 'lucide-react'
import { useTickets } from '@/features/tickets/hooks/useTickets'

const formatDate = (date: string) => {
  const parsed = new Date(date)

  if (Number.isNaN(parsed.getTime())) return 'Дата неизвестна'

  return parsed.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: 'long',
  })
}

export default function DashboardPage() {
  const {
    data: tickets = [],
    isLoading,
    isError,
  } = useTickets()

  const activeTickets = tickets.filter(
    (ticket) => ticket.status === 'in_progress'
  )

  const newTickets = tickets.filter(
    (ticket) => ticket.status === 'new'
  )

  const closedTickets = tickets.filter(
    (ticket) => ticket.status === 'closed'
  )

  const highPriorityTickets = tickets.filter(
    (ticket) =>
      ticket.priority === 'high' &&
      ticket.status !== 'closed'
  )

  const unassignedTickets = tickets.filter(
    (ticket) =>
      !ticket.assignee &&
      ticket.status !== 'closed'
  )

  const categories = tickets.reduce<Record<string, number>>(
    (result, ticket) => {
      result[ticket.category] = (result[ticket.category] || 0) + 1
      return result
    },
    {}
  )

  const categoryEntries = Object.entries(categories)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)

  const total = tickets.length || 1

  const completion = Math.round(
    (closedTickets.length / total) * 100
  )

  const currentDate = new Date().toLocaleDateString('ru-RU', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-black" />
          Загружаем диспетчерскую...
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="glass-card p-8 text-center">
        <ShieldAlert size={30} className="mx-auto mb-3 text-gray-400" />
        <h2 className="text-lg font-semibold">Не удалось загрузить данные</h2>
        <p className="mt-2 text-sm text-gray-500">
          Проверь подключение и попробуй обновить страницу.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">

      {/* Приветствие */}

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-[2px] text-gray-400">
            Операционный центр
          </div>

          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Добро пожаловать!
          </h1>

          <p className="mt-2 text-sm capitalize text-gray-400">
            {currentDate}
          </p>
        </div>

        <Link
          to="/tickets"
          className="button-dark"
        >
          <Plus size={16} />
          Все обращения
        </Link>
      </div>

      {/* Главная сетка */}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">

        {/* Общая информация */}

        <section className="dark-card relative overflow-hidden p-6 xl:col-span-4">
          <div className="absolute -right-16 -top-16 h-52 w-52 rounded-full border border-white/10" />
          <div className="absolute -right-8 -top-8 h-36 w-36 rounded-full border border-white/10" />

          <div className="relative flex items-center justify-between">
            <h2 className="text-sm font-semibold">
              Общая информация
            </h2>

            <Activity size={17} className="text-white/60" />
          </div>

          <div className="relative mt-8 flex items-end gap-3">
            <div className="text-6xl font-semibold tracking-tighter">
              {tickets.length}
            </div>

            <div className="mb-2 text-xs leading-relaxed text-white/50">
              Всего
              <br />
              обращений
            </div>
          </div>

          <div className="relative mt-5 h-px bg-white/15" />

          <div className="relative mt-5 grid grid-cols-2 gap-3">

            <div className="rounded-2xl bg-white/10 p-4">
              <div className="mb-3 flex items-center gap-2 text-white/55">
                <Clock3 size={14} />
                <span className="text-xs">В работе</span>
              </div>

              <div className="text-3xl font-semibold">
                {activeTickets.length}
              </div>
            </div>

            <div className="rounded-2xl bg-white/10 p-4">
              <div className="mb-3 flex items-center gap-2 text-white/55">
                <Inbox size={14} />
                <span className="text-xs">Новые</span>
              </div>

              <div className="text-3xl font-semibold">
                {newTickets.length}
              </div>
            </div>

            <div className="rounded-2xl bg-white/10 p-4">
              <div className="mb-3 flex items-center gap-2 text-white/55">
                <CheckCircle2 size={14} />
                <span className="text-xs">Завершено</span>
              </div>

              <div className="text-3xl font-semibold">
                {closedTickets.length}
              </div>
            </div>

            <div className="rounded-2xl bg-white/10 p-4">
              <div className="mb-3 flex items-center gap-2 text-white/55">
                <ShieldAlert size={14} />
                <span className="text-xs">Высокий приоритет</span>
              </div>

              <div className="text-3xl font-semibold">
                {highPriorityTickets.length}
              </div>
            </div>

          </div>

          <Link
            to="/tickets"
            className="relative mt-6 flex items-center justify-between border-t border-white/15 pt-4 text-xs text-white/65 transition hover:text-white"
          >
            Перейти к обращениям
            <ArrowUpRight size={16} />
          </Link>
        </section>

        {/* Распределение заявок */}

        <section className="glass-card p-6 xl:col-span-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">
                Структура обращений
              </h2>

              <p className="mt-1 text-xs text-gray-400">
                По текущим статусам
              </p>
            </div>

            <Activity size={18} className="text-gray-400" />
          </div>

          <div className="mt-8 flex items-center justify-center">
            <div
              className="relative flex h-44 w-44 items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(
                  #242424 0% ${activeTickets.length / total * 100}%,
                  #a5a5a5 ${activeTickets.length / total * 100}% ${(activeTickets.length + newTickets.length) / total * 100}%,
                  #dedede ${(activeTickets.length + newTickets.length) / total * 100}% 100%
                )`,
              }}
            >
              <div className="absolute inset-3 flex flex-col items-center justify-center rounded-full bg-white">
                <span className="text-3xl font-semibold tracking-tight">
                  {tickets.length}
                </span>

                <span className="mt-1 text-xs text-gray-400">
                  обращений
                </span>
              </div>
            </div>
          </div>

          <div className="mt-7 space-y-3">

            <StatusLegend
              color="#242424"
              label="В работе"
              value={activeTickets.length}
            />

            <StatusLegend
              color="#a5a5a5"
              label="Новые"
              value={newTickets.length}
            />

            <StatusLegend
              color="#dedede"
              label="Завершённые"
              value={closedTickets.length}
            />

          </div>
        </section>

        {/* Выполнение */}

        <section className="glass-card flex flex-col p-6 xl:col-span-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">
                Выполнение задач
              </h2>

              <p className="mt-1 text-xs text-gray-400">
                Доля завершённых обращений
              </p>
            </div>

            <TrendingUp size={18} className="text-gray-400" />
          </div>

          <div className="my-auto py-8">
            <div
              className="relative mx-auto flex h-48 w-48 items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(#242424 ${completion}%, #e7e7e7 ${completion}% 100%)`,
              }}
            >
              <div className="absolute inset-3 flex flex-col items-center justify-center rounded-full bg-white">
                <span className="text-4xl font-semibold tracking-tighter">
                  {completion}%
                </span>

                <span className="mt-1 text-xs text-gray-400">
                  завершено
                </span>
              </div>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">
                Выполнено обращений
              </span>

              <span className="text-sm font-semibold">
                {closedTickets.length} / {tickets.length}
              </span>
            </div>

            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-[#242424] transition-all"
                style={{ width: `${completion}%` }}
              />
            </div>
          </div>
        </section>

      </div>

      {/* Нижняя сетка */}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-12">

        {/* Срочные обращения */}

        <section className="glass-card p-6 xl:col-span-5">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold">
                Требуют внимания
              </h2>

              <p className="mt-1 text-xs text-gray-400">
                Обращения с высоким приоритетом
              </p>
            </div>

            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gray-100">
              <Bell size={16} />
            </div>
          </div>

          {highPriorityTickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <CheckCircle2 size={30} className="mb-3 text-gray-300" />

              <p className="text-sm font-medium">
                Срочных обращений нет
              </p>

              <p className="mt-1 text-xs text-gray-400">
                Сейчас всё спокойно
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {highPriorityTickets.slice(0, 4).map((ticket) => (
                <div
                  key={ticket.id}
                  className="flex items-center gap-3 rounded-2xl border border-gray-100 p-3 transition hover:bg-gray-50"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#242424] text-white">
                    <ShieldAlert size={17} />
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium">
                      {ticket.title}
                    </div>

                    <div className="mt-1 text-xs text-gray-400">
                      #{ticket.id} · {ticket.category}
                    </div>
                  </div>

                  <span className="rounded-full bg-gray-100 px-3 py-1.5 text-[10px] font-semibold">
                    Высокий
                  </span>
                </div>
              ))}
            </div>
          )}

          <Link
            to="/tickets"
            className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4 text-xs font-medium text-gray-500 transition hover:text-black"
          >
            Открыть все обращения
            <ArrowRight size={15} />
          </Link>
        </section>

        {/* Последние обращения */}

        <section className="glass-card p-6 xl:col-span-7">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold">
                Последние обращения
              </h2>

              <p className="mt-1 text-xs text-gray-400">
                Недавно созданные заявки
              </p>
            </div>

            <Link
              to="/tickets"
              className="flex items-center gap-2 text-xs text-gray-500 transition hover:text-black"
            >
              Все заявки
              <ArrowUpRight size={15} />
            </Link>
          </div>

          {tickets.length === 0 ? (
            <div className="py-12 text-center">
              <Inbox size={30} className="mx-auto mb-3 text-gray-300" />

              <p className="text-sm font-medium">
                Обращений пока нет
              </p>

              <p className="mt-1 text-xs text-gray-400">
                Здесь появятся новые заявки
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {[...tickets]
                .sort(
                  (a, b) =>
                    new Date(b.createdAt).getTime() -
                    new Date(a.createdAt).getTime()
                )
                .slice(0, 5)
                .map((ticket) => (
                  <div
                    key={ticket.id}
                    className="flex items-center gap-3 rounded-xl px-2 py-3 transition hover:bg-gray-50"
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gray-100">
                      {ticket.status === 'closed' ? (
                        <CheckCircle2 size={17} className="text-gray-500" />
                      ) : ticket.status === 'in_progress' ? (
                        <Wrench size={17} className="text-gray-600" />
                      ) : (
                        <Inbox size={17} className="text-gray-600" />
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium">
                        {ticket.title}
                      </div>

                      <div className="mt-1 text-xs text-gray-400">
                        #{ticket.id} · {formatDate(ticket.createdAt)}
                      </div>
                    </div>

                    <div className="hidden text-right sm:block">
                      <div className="text-xs font-medium">
                        {ticket.status === 'new'
                          ? 'Новая'
                          : ticket.status === 'in_progress'
                            ? 'В работе'
                            : 'Завершена'}
                      </div>

                      <div className="mt-1 text-[10px] text-gray-400">
                        {ticket.assignee?.name || 'Без исполнителя'}
                      </div>
                    </div>

                    <ArrowUpRight
                      size={15}
                      className="shrink-0 text-gray-300"
                    />
                  </div>
                ))}
            </div>
          )}
        </section>

      </div>

      {/* Нижние информационные блоки */}

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">

        {/* Категории */}

        <section className="glass-card p-6">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">
                Категории обращений
              </h2>

              <p className="mt-1 text-xs text-gray-400">
                Распределение по направлениям
              </p>
            </div>

            <Inbox size={17} className="text-gray-400" />
          </div>

          {categoryEntries.length === 0 ? (
            <p className="py-6 text-center text-xs text-gray-400">
              Пока нет данных
            </p>
          ) : (
            <div className="space-y-5">
              {categoryEntries.map(([category, count], index) => (
                <div key={category}>
                  <div className="mb-2 flex justify-between text-xs">
                    <span className="font-medium">{category}</span>

                    <span className="text-gray-400">
                      {count}
                    </span>
                  </div>

                  <div className="h-1.5 overflow-hidden rounded-full bg-gray-100">
                    <div
                      className="h-full rounded-full bg-[#242424]"
                      style={{
                        width: `${(count / tickets.length) * 100}%`,
                        opacity: 1 - index * 0.15,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Состояние системы */}

        <section className="dark-card relative overflow-hidden p-6">
          <div className="absolute -bottom-16 -right-10 h-48 w-48 rounded-full border border-white/10" />

          <div className="relative flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">
                Рабочее состояние
              </h2>

              <p className="mt-1 text-xs text-white/45">
                Текущая загрузка диспетчерской
              </p>
            </div>

            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10">
              <Radio size={18} />
            </div>
          </div>

          <div className="relative mt-7 space-y-4">

            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-white" />
                <span className="text-xs text-white/65">
                  Ожидают обработки
                </span>
              </div>

              <span className="text-sm font-semibold">
                {newTickets.length}
              </span>
            </div>

            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-white/60" />
                <span className="text-xs text-white/65">
                  Без исполнителя
                </span>
              </div>

              <span className="text-sm font-semibold">
                {unassignedTickets.length}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-2 w-2 rounded-full bg-white/35" />
                <span className="text-xs text-white/65">
                  Завершённые
                </span>
              </div>

              <span className="text-sm font-semibold">
                {closedTickets.length}
              </span>
            </div>

          </div>

          <div className="relative mt-7 flex items-center gap-2 border-t border-white/10 pt-4 text-xs text-white/45">
            <Sparkles size={14} />
            Данные обновляются через систему заявок
          </div>
        </section>

      </div>

    </div>
  )
}

function StatusLegend({
  color,
  label,
  value,
}: {
  color: string
  label: string
  value: number
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div
          className="h-2.5 w-2.5 rounded-full"
          style={{ background: color }}
        />

        <span className="text-xs text-gray-500">
          {label}
        </span>
      </div>

      <span className="text-xs font-semibold">
        {value}
      </span>
    </div>
  )
}