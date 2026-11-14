import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts'
import { Bot, AlertTriangle, TrendingUp, CheckCircle, Activity, ShieldCheck } from 'lucide-react'

// --- Моковые данные для графиков (в стиле SIGNAL) ---
const DATA_CATEGORIES = [
  { name: 'Интернет', value: 400 },
  { name: 'Сантехника', value: 300 },
  { name: 'Электрика', value: 200 },
  { name: 'ПО', value: 100 },
]
const COLORS = ['#242424', '#a5a5a5', '#dedede', '#888888']

const DATA_PRIORITIES = [
  { name: 'Низкий', count: 120 },
  { name: 'Средний', count: 250 },
  { name: 'Высокий', count: 80 },
  { name: 'Критичный', count: 20 },
]

const DATA_LOAD = [
  { time: '08:00', tickets: 5 },
  { time: '10:00', tickets: 25 },
  { time: '12:00', tickets: 15 },
  { time: '14:00', tickets: 40 },
  { time: '16:00', tickets: 20 },
  { time: '18:00', tickets: 8 },
]
// ----------------------------------------------------

export default function AdminDashboardPage() {
  return (
    <div className="space-y-6 pb-8">
      
      {/* Заголовок */}
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
          Данные за 24 часа
        </div>
      </div>

      {/* ВЕРХНИЙ РЯД: Ключевые метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Главная карточка (темная) */}
        <div className="dark-card p-6 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full border border-white/10" />
          <div className="relative">
            <p className="text-xs text-white/50 mb-1">Всего заявок</p>
            <p className="text-4xl font-semibold tracking-tight">470</p>
          </div>
          <p className="relative text-[10px] text-emerald-400 mt-4 flex items-center gap-1">
            <TrendingUp size={12} /> +12% к прошлой смене
          </p>
        </div>

        <div className="glass-card p-6 flex flex-col justify-between">
          <div>
            <p className="text-xs text-gray-500 mb-1">SLA-риски</p>
            <p className="text-3xl font-semibold text-[#b87979]">12</p>
          </div>
          <p className="text-[10px] text-gray-400 mt-4">Заявки близки к просрочке</p>
        </div>

        <div className="glass-card p-6 flex flex-col justify-between">
          <div>
            <p className="text-xs text-gray-500 mb-1">Точность ИИ</p>
            <p className="text-3xl font-semibold text-[#222]">94%</p>
          </div>
          <div className="w-full bg-gray-200/50 h-1.5 mt-4 rounded-full overflow-hidden">
            <div className="bg-[#242424] h-full rounded-full" style={{ width: '94%' }}></div>
          </div>
        </div>

        <div className="glass-card p-6 flex flex-col justify-between">
          <div>
            <p className="text-xs text-gray-500 mb-1">Правки диспетчеров</p>
            <p className="text-3xl font-semibold text-[#222]">6%</p>
          </div>
          <p className="text-[10px] text-gray-400 mt-4">ИИ ошибся при назначении</p>
        </div>
      </div>

      {/* СРЕДНИЙ РЯД: Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        
        {/* Категории */}
        <div className="glass-card p-6">
          <h2 className="text-sm font-semibold text-[#222] mb-1">Распределение по категориям</h2>
          <p className="text-xs text-gray-400 mb-6">Типы входящих обращений</p>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={DATA_CATEGORIES} cx="50%" cy="50%" innerRadius={70} outerRadius={90} paddingAngle={2} dataKey="value" stroke="none">
                  {DATA_CATEGORIES.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center flex-wrap gap-4 mt-4">
            {DATA_CATEGORIES.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-xs text-gray-600 font-medium">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLORS[index] }}></span>
                {entry.name}
              </div>
            ))}
          </div>
        </div>

        {/* Нагрузка */}
        <div className="glass-card p-6">
          <h2 className="text-sm font-semibold text-[#222] mb-1">Пики нагрузки</h2>
          <p className="text-xs text-gray-400 mb-6">Количество заявок по часам</p>
          
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={DATA_LOAD} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#242424" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#242424" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                <RechartsTooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }} />
                <Area type="monotone" dataKey="tickets" stroke="#242424" strokeWidth={2} fillOpacity={1} fill="url(#colorTickets)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* НИЖНИЙ РЯД: Приоритеты и Тональность */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Приоритеты */}
        <div className="glass-card p-6 lg:col-span-2">
          <h2 className="text-sm font-semibold text-[#222] mb-1">Заявки по приоритетам</h2>
          <p className="text-xs text-gray-400 mb-6">Распределение уровня срочности</p>
          
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DATA_PRIORITIES} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e5e5" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#999' }} />
                <RechartsTooltip cursor={{ fill: 'rgba(0,0,0,0.03)' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="count" fill="#242424" radius={[6, 6, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Тональность */}
        <div className="dark-card p-6 relative overflow-hidden">
          <div className="absolute -right-6 -bottom-6 h-32 w-32 rounded-full border border-white/10" />
          <h2 className="text-sm font-semibold relative mb-1">Тональность</h2>
          <p className="text-xs text-white/40 mb-8 relative">Эмоциональный фон клиентов</p>
          
          <div className="space-y-5 relative">
            <div>
              <div className="flex justify-between text-xs mb-2">
                <span className="text-white/60">Позитив / Нейтрально</span>
                <span className="font-semibold text-emerald-400">78%</span>
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-emerald-400 h-full rounded-full" style={{ width: '78%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-2">
                <span className="text-white/60">Недовольство</span>
                <span className="font-semibold text-[#c6a66b]">16%</span>
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#c6a66b] h-full rounded-full" style={{ width: '16%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-xs mb-2">
                <span className="text-white/60">Авария / Агрессия</span>
                <span className="font-semibold text-[#b87979]">6%</span>
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div className="bg-[#b87979] h-full rounded-full" style={{ width: '6%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}