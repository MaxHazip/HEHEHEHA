import type { ReactNode } from 'react'
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
  LineChart,
  Line,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
} from 'recharts'
import {
  Activity,
  AlertCircle,
  Bot,
  CheckCircle2,
  Clock3,
  Inbox,
  Loader2,
  Paperclip,
  Phone,
  TrendingUp,
  Users,
  Wrench,
} from 'lucide-react'
import { useStats } from '@/features/stats/hooks/useStats'

const COLORS = ['#242424', '#a5a5a5', '#dedede', '#888888', '#c6a66b', '#8da995']

const STATUS_ORDER = ['draft', 'new', 'in_progress', 'resolved', 'closed']
const STATUS_LABELS: Record<string, string> = {
  draft: 'Черновик',
  new: 'Новая',
  in_progress: 'В работе',
  resolved: 'Решена',
  closed: 'Закрыта',
}

const PRIORITY_ORDER = ['low', 'medium', 'high', 'critical', 'none']
const PRIORITY_LABELS: Record<string, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
  critical: 'Критичный',
  none: 'Без приоритета',
}

const CHANNEL_LABELS: Record<string, string> = {
  chat: 'Чат',
  voice: 'Голос',
  image: 'Изображение',
}

const percent = (value: number, total: number) =>
  total > 0 ? Math.min(100, Math.round((value / total) * 100)) : 0

interface StatCardProps {
  label: string
  value: string | number
  hint?: string
  dark?: boolean
  icon?: ReactNode
}

function StatCard({ label, value, hint, dark, icon }: StatCardProps) {
  return (
    <div
      className={`${dark ? 'dark-card' : 'glass-card'} flex flex-col justify-between p-5`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className={`mb-1 text-xs ${dark ? 'text-white/50' : 'text-gray-500'}`}>
            {label}
          </p>
          <p
            className={`text-3xl font-semibold tracking-tight ${
              dark ? 'text-white' : 'text-[#222]'
            }`}
          >
            {value}
          </p>
        </div>
        {icon && (
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-xl ${
              dark ? 'bg-white/10 text-white' : 'bg-gray-100 text-[#333]'
            }`}
          >
            {icon}
          </div>
        )}
      </div>
      {hint && (
        <p className={`mt-3 text-[10px] ${dark ? 'text-white/45' : 'text-gray-400'}`}>
          {hint}
        </p>
      )}
    </div>
  )
}

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
  const statusData = STATUS_ORDER.map((code) => ({
    name: STATUS_LABELS[code],
    value:
      stats.by_status.find((item) => item.name === code)?.count ?? 0,
  })).filter((item) => item.value > 0)

  const categoryData = stats.by_category.map((item) => ({
    name: item.name,
    value: item.count,
  }))

  const priorityData = PRIORITY_ORDER.map((code) => ({
    name: PRIORITY_LABELS[code],
    count:
      stats.by_priority.find((item) => item.name === code)?.count ?? 0,
  })).filter((item) => item.count > 0)

  const channelData = stats.by_channel.map((item) => ({
    name: CHANNEL_LABELS[item.name] ?? item.name,
    count: item.count,
  }))

  const engineerData = stats.engineers_detail.map((engineer) => ({
    name: engineer.name,
    open: engineer.open_tickets,
    available: engineer.available,
  }))

  const subcategoryData = stats.by_subcategory.slice(0, 8).map((item) => ({
    name: item.name,
    count: item.count,
  }))

  const completionData = [
    { name: 'completion', value: stats.completion_rate },
  ]

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
            Заявки, категории, нагрузка инженеров, SLA и качество ИИ.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
          <span className="flex items-center gap-1.5 rounded-full border border-white bg-white/70 px-4 py-2.5 shadow-sm">
            <Activity size={15} /> Заявок: {stats.total_tickets}
          </span>
          <span className="flex items-center gap-1.5 rounded-full border border-white bg-white/70 px-4 py-2.5 shadow-sm">
            <Phone size={15} /> Звонков 24ч: {stats.calls.today}
          </span>
          <span className="flex items-center gap-1.5 rounded-full border border-white bg-white/70 px-4 py-2.5 shadow-sm">
            <Paperclip size={15} /> Вложений: {stats.attachments.total}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          dark
          label="Всего заявок"
          value={stats.total_tickets}
          hint={`Закрыто: ${stats.completion_rate}%`}
          icon={<TrendingUp size={17} />}
        />
        <StatCard
          label="Новые"
          value={stats.new_tickets}
          hint={`Черновиков: ${stats.draft_tickets}`}
          icon={<Inbox size={17} />}
        />
        <StatCard
          label="В работе"
          value={stats.in_progress_tickets}
          hint="Активные обращения"
          icon={<Wrench size={17} />}
        />
        <StatCard
          label="Закрытые"
          value={stats.closed_tickets}
          hint={`Решено: ${stats.resolved_tickets}`}
          icon={<CheckCircle2 size={17} />}
        />
        <StatCard
          label="SLA-риски"
          value={stats.sla_risks}
          hint="Открыты дольше 24 часов"
          icon={<Clock3 size={17} />}
        />
        <StatCard
          label="Высокий приоритет"
          value={stats.high_priority_tickets}
          hint="High + critical, не закрыты"
          icon={<AlertCircle size={17} />}
        />
        <StatCard
          label="Без исполнителя"
          value={stats.unassigned_tickets}
          hint="Ожидают назначения"
          icon={<Users size={17} />}
        />
        <StatCard
          label="Проверка ИИ"
          value={stats.ai_review_tickets}
          hint={`Средняя уверенность: ${stats.avg_ai_confidence}%`}
          icon={<Bot size={17} />}
        />
        <StatCard
          label="Среднее решение"
          value={`${stats.avg_resolution_hours} ч`}
          hint="По закрытым заявкам"
          icon={<Clock3 size={17} />}
        />
        <StatCard
          label="Звонки"
          value={stats.calls.total}
          hint={`Сегодня: ${stats.calls.today} · с записью: ${stats.calls.with_recording}`}
          icon={<Phone size={17} />}
        />
        <StatCard
          label="Вложения"
          value={stats.attachments.total}
          hint={`Фото: ${stats.attachments.images} · видео: ${stats.attachments.video} · аудио: ${stats.attachments.audio}`}
          icon={<Paperclip size={17} />}
        />
        <StatCard
          label="Массовые инциденты"
          value={stats.mass_incident_tickets}
          hint={`Правок ИИ: ${stats.manual_edits}`}
          icon={<AlertCircle size={17} />}
        />
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Заявки по статусам
          </h2>
          <p className="mb-4 text-xs text-gray-400">Текущее распределение</p>
          <div className="h-56">
            {statusData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Нет данных
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={78}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {statusData.map((_entry, index) => (
                      <Cell
                        key={`status-${index}`}
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
          <div className="mt-2 grid grid-cols-2 gap-2">
            {statusData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-[11px] text-gray-500">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
                {entry.name}: {entry.value}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Каналы обращений
          </h2>
          <p className="mb-4 text-xs text-gray-400">Чат, голос, изображения</p>
          <div className="h-56">
            {channelData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Нет данных
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={channelData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                  <RechartsTooltip cursor={{ fill: 'rgba(0,0,0,0.03)' }} contentStyle={{ borderRadius: '12px', border: 'none' }} />
                  <Bar dataKey="count" fill="#242424" radius={[6, 6, 0, 0]} barSize={36} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Процент закрытия
          </h2>
          <p className="mb-4 text-xs text-gray-400">Доля завершённых заявок</p>
          <div className="relative h-56">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                innerRadius="72%"
                outerRadius="100%"
                data={completionData}
                startAngle={90}
                endAngle={-270}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar dataKey="value" cornerRadius={10} fill="#242424" background />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-semibold text-[#222]">
                {stats.completion_rate}%
              </span>
              <span className="mt-1 text-[10px] uppercase tracking-wider text-gray-400">
                closed
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Распределение по категориям
          </h2>
          <p className="mb-4 text-xs text-gray-400">Типы входящих обращений</p>
          <div className="h-64">
            {categoryData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Нет данных
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" innerRadius={58} outerRadius={82} paddingAngle={4} dataKey="value">
                    {categoryData.map((_entry, index) => (
                      <Cell key={`cat-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip contentStyle={{ borderRadius: '12px', border: 'none' }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            {categoryData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-[11px] text-gray-500">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
                {entry.name} · {entry.value}
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Заявки по приоритетам
          </h2>
          <p className="mb-4 text-xs text-gray-400">Уровень срочности</p>
          <div className="h-64">
            {priorityData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Нет данных
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={priorityData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                  <RechartsTooltip cursor={{ fill: 'rgba(0,0,0,0.03)' }} contentStyle={{ borderRadius: '12px', border: 'none' }} />
                  <Bar dataKey="count" fill="#242424" radius={[6, 6, 0, 0]} barSize={38} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Динамика за 14 дней
          </h2>
          <p className="mb-4 text-xs text-gray-400">Создано и закрыто</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.daily} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                <RechartsTooltip contentStyle={{ borderRadius: '12px', border: 'none' }} />
                <Line type="monotone" dataKey="created" stroke="#242424" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="closed" stroke="#a5a5a5" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex gap-4 text-[10px] text-gray-500">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#242424]" /> Создано</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-[#a5a5a5]" /> Закрыто</span>
          </div>
        </div>

        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Нагрузка по часам
          </h2>
          <p className="mb-4 text-xs text-gray-400">Заявки за последние 24 часа</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.hourly} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#242424" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#242424" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                <RechartsTooltip contentStyle={{ borderRadius: '12px', border: 'none' }} />
                <Area type="monotone" dataKey="tickets" stroke="#242424" strokeWidth={2} fillOpacity={1} fill="url(#colorTickets)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Нагрузка инженеров
          </h2>
          <p className="mb-4 text-xs text-gray-400">Открытые заявки на сотрудника</p>
          <div className="h-64">
            {engineerData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Нет инженеров
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={engineerData} margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e5e5" />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                  <YAxis type="category" dataKey="name" width={110} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                  <RechartsTooltip cursor={{ fill: 'rgba(0,0,0,0.03)' }} contentStyle={{ borderRadius: '12px', border: 'none' }} />
                  <Bar dataKey="open" fill="#242424" radius={[0, 6, 6, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="glass-card p-5">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">
            Подкатегории
          </h2>
          <p className="mb-4 text-xs text-gray-400">Топ-8 по количеству</p>
          <div className="h-64">
            {subcategoryData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-xs text-gray-400">
                Нет данных
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={subcategoryData} margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e5e5" />
                  <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                  <YAxis type="category" dataKey="name" width={130} axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#999' }} />
                  <RechartsTooltip cursor={{ fill: 'rgba(0,0,0,0.03)' }} contentStyle={{ borderRadius: '12px', border: 'none' }} />
                  <Bar dataKey="count" fill="#a5a5a5" radius={[0, 6, 6, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="glass-card overflow-x-auto p-6">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">Категории</h2>
          <p className="mb-4 text-xs text-gray-400">Количество и доля</p>
          {categoryData.length === 0 ? (
            <p className="text-xs text-gray-400">Нет данных</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-gray-400">
                  <th className="pb-2">Категория</th>
                  <th className="pb-2">Заявок</th>
                  <th className="pb-2">Доля</th>
                </tr>
              </thead>
              <tbody>
                {categoryData.map((item) => (
                  <tr key={item.name} className="border-t border-gray-100">
                    <td className="py-2 text-gray-700">{item.name}</td>
                    <td className="py-2 text-gray-700">{item.value}</td>
                    <td className="py-2 text-gray-500">{percent(item.value, total)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="glass-card overflow-x-auto p-6">
          <h2 className="mb-1 text-sm font-semibold text-[#222]">Инженеры</h2>
          <p className="mb-4 text-xs text-gray-400">Компетенции и нагрузка</p>
          {stats.engineers_detail.length === 0 ? (
            <p className="text-xs text-gray-400">Нет инженеров</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-[10px] uppercase tracking-wider text-gray-400">
                  <th className="pb-2">Инженер</th>
                  <th className="pb-2">Компетенции</th>
                  <th className="pb-2">В работе</th>
                  <th className="pb-2">Статус</th>
                </tr>
              </thead>
              <tbody>
                {stats.engineers_detail.map((engineer) => (
                  <tr key={engineer.id} className="border-t border-gray-100">
                    <td className="py-2 text-gray-700">{engineer.name}</td>
                    <td className="py-2">
                      <div className="flex flex-wrap gap-1">
                        {engineer.competencies.map((code) => (
                          <span key={code} className="rounded-md bg-gray-100 px-1.5 py-0.5 text-[9px] text-gray-500">
                            {code}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2 text-gray-700">{engineer.open_tickets}</td>
                    <td className="py-2">
                      <span className={`rounded-full px-2 py-1 text-[9px] font-semibold ${engineer.available ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-500'}`}>
                        {engineer.available ? 'доступен' : 'занят'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
