import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from 'recharts'
import { Activity, AlertCircle, Loader2, TrendingUp } from 'lucide-react'
import { useStats } from '@/features/stats/hooks/useStats'

const COLORS = ['#242424', '#a5a5a5', '#dedede', '#888888', '#c6a66b']

const PRIORITY_ORDER = ['low', 'medium', 'high', 'critical', 'none']
const PRIORITY_LABELS: Record<string, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
  critical: 'Критичный',
  none: 'Без приоритета',
}

const percent = (value: number, total: number) =>
  total > 0 ? Math.min(100, Math.round((value / total) * 100)) : 0

export default function AdminDashboardPage() {
  const { data: stats, isLoading, isError } = useStats()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          Загружаем аналитику...
        </div>
      </div>
    )
  }

  if (isError || !stats) {
    return (
      <div className="glass-card flex min-h-[240px] flex-col items-center justify-center p-8 text-center">
        <AlertCircle size={26} className="mb-3 text-[#b87979]" />
        <h3 className="text-base font-semibold text-[#222]">
          Не удалось загрузить статистику
        </h3>
        <p className="mt-2 max-w-sm text-sm text-gray-400">
          Проверьте, что backend запущен и доступен эндпоинт /api/stats.
        </p>
      </div>
    )
  }

  const total = stats.total_tickets
  const categories = stats.by_category.map((item) => ({
    name: item.name,
    value: item.count,
  }))
  const priorities = PRIORITY_ORDER.map((code) => ({
    name: PRIORITY_LABELS[code],
    count:
      stats.by_priority.find((item) => item.name === code)?.count ?? 0,
  })).filter((item) => item.count > 0)
  const hourly = stats.hourly
  const manualEditsPercent = percent(stats.manual_edits, total)
  const engineerPercent = percent(
    stats.engineers.available,
    stats.engineers.total,
  )
  const unassignedPercent = percent(stats.unassigned_tickets, total)
  const highPriorityPercent = percent(stats.high_priority_tickets, total)

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Панель руководителя
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Аналитика системы
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Контроль качества, SLA и нагрузки на диспетчерскую.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500 shadow-sm">
          <Activity size={15} />
          Звонков за 24ч: {stats.calls.today} · Статей: {stats.knowledge_articles}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="dark-card relative flex flex-col justify-between overflow-hidden p-6">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full border border-white/10" />
          <div className="relative">
            <p className="mb-1 text-xs text-white/50">Всего заявок</p>
            <p className="text-4xl font-semibold tracking-tight">{total}</p>
          </div>
          <p className="relative mt-4 flex items-center gap-1 text-[10px] text-emerald-400">
            <TrendingUp size={12} /> Закрыто: {stats.completion_rate}%
          </p>
        </div>

        <div className="glass-card flex flex-col justify-between p-6">
          <div>
            <p className="mb-1 text-xs text-gray-500">SLA-риски</p>
            <p className="text-3xl font-semibold text-[#b87979]">
              {stats.sla_risks}
            </p>
          </div>
          <p className="mt-4 text-[10px] text-gray-400">
            Открыты дольше 24 часов
          </p>
        </div>

        <div className="glass-card flex flex-col justify-between p-6">
          <div>
            <p className="mb-1 text-xs text-gray-500">Средняя уверенность ИИ</p>
            <p className="text-3xl font-semibold text-[#222]">
              {stats.avg_ai_confidence}%
            </p>
          </div>
          <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-gray-200/50">
            <div
              className="h-full rounded-full bg-[#242424]"
              style={{ width: `${stats.avg_ai_confidence}%` }}
            />
          </div>
        </div>

        <div className="glass-card flex flex-col justify-between p-6">
          <div>
            <p className="mb-1 text-xs text-gray-500">Правки диспетчеров</p>
            <p className="text-3xl font-semibold text-[#222]">
              {stats.manual_edits}
            </p>
          </div>
          <p className="mt-4 text-[10px] text-gray-400">
            {manualEditsPercent}% заявок с ручной правкой
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="glass-card p-6">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Распределение по категориям
          </h2>
          <p className="mb-6 text-xs text-gray-400">Типы входящих обращений</p>

          <div className="h-64">
            {categories.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Пока нет заявок с категориями
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categories}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {categories.map((_entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{
                      borderRadius: '12px',
                      border: 'none',
                      boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="mt-4 flex flex-wrap justify-center gap-4">
            {categories.map((entry, index) => (
              <div
                key={entry.name}
                className="flex items-center gap-1.5 text-xs font-medium text-gray-600"
              >
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                {entry.name} · {entry.value}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Пики нагрузки
          </h2>
          <p className="mb-6 text-xs text-gray-400">
            Количество заявок по часам
          </p>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={hourly}
                margin={{ top: 10, right: 0, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#242424" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#242424" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid
                  strokeDasharray="3 3"
                  vertical={false}
                  stroke="#e5e5e5"
                />
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: '#999' }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 11, fill: '#999' }}
                />
                <RechartsTooltip
                  contentStyle={{
                    borderRadius: '12px',
                    border: 'none',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="tickets"
                  stroke="#242424"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorTickets)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="glass-card p-6 lg:col-span-2">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Заявки по приоритетам
          </h2>
          <p className="mb-6 text-xs text-gray-400">
            Распределение уровня срочности
          </p>

          <div className="h-56">
            {priorities.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Пока нет данных о приоритетах
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={priorities}
                  margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="#e5e5e5"
                  />
                  <XAxis
                    dataKey="name"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 11, fill: '#999' }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fontSize: 11, fill: '#999' }}
                  />
                  <RechartsTooltip
                    cursor={{ fill: 'rgba(0,0,0,0.03)' }}
                    contentStyle={{
                      borderRadius: '12px',
                      border: 'none',
                      boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                    }}
                  />
                  <Bar
                    dataKey="count"
                    fill="#242424"
                    radius={[6, 6, 0, 0]}
                    barSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="dark-card relative overflow-hidden p-6">
          <div className="absolute -bottom-6 -right-6 h-32 w-32 rounded-full border border-white/10" />
          <h2 className="relative mb-1 text-sm font-semibold">
            Нагрузка и риски
          </h2>
          <p className="relative mb-8 text-xs text-white/40">
            Реальное состояние системы
          </p>

          <div className="relative space-y-5">
            <div>
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-white/60">Инженеры доступны</span>
                <span className="font-semibold text-emerald-400">
                  {stats.engineers.available}/{stats.engineers.total}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-emerald-400"
                  style={{ width: `${engineerPercent}%` }}
                />
              </div>
            </div>

            <div>
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-white/60">Без исполнителя</span>
                <span className="font-semibold text-[#c6a66b]">
                  {stats.unassigned_tickets}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-[#c6a66b]"
                  style={{ width: `${unassignedPercent}%` }}
                />
              </div>
            </div>

            <div>
              <div className="mb-2 flex justify-between text-xs">
                <span className="text-white/60">
                  Высокий приоритет / критичные
                </span>
                <span className="font-semibold text-[#b87979]">
                  {stats.high_priority_tickets}
                </span>
              </div>
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-[#b87979]"
                  style={{ width: `${highPriorityPercent}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
