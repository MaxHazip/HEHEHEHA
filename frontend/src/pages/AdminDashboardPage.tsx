import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area
} from 'recharts'
import { Bot, AlertTriangle, TrendingUp, CheckCircle, Activity } from 'lucide-react'

// --- Моковые данные для графиков ---
const DATA_CATEGORIES = [
  { name: 'Интернет', value: 400 },
  { name: 'Сантехника', value: 300 },
  { name: 'Электрика', value: 200 },
  { name: 'ПО', value: 100 },
]
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']

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
  { time: '14:00', tickets: 40 }, // Пик нагрузки
  { time: '16:00', tickets: 20 },
  { time: '18:00', tickets: 8 },
]
// ----------------------------------

export default function AdminDashboardPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Аналитика и контроль</h1>
          <p className="text-slate-500 text-sm mt-1">Обзор работы системы, нагрузки и качества ИИ</p>
        </div>
        <div className="text-sm text-slate-500 bg-white px-4 py-2 rounded-lg border border-slate-200">
          Данные за последние 24 часа
        </div>
      </div>

      {/* ВЕРХНИЙ РЯД: Ключевые метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-slate-500 mb-1">Всего заявок</p>
              <p className="text-3xl font-semibold text-slate-800">470</p>
            </div>
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg"><Activity size={20} /></div>
          </div>
          <p className="text-xs text-emerald-600 mt-2 flex items-center gap-1">
            <TrendingUp size={12} /> +12% к прошлой смене
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-slate-500 mb-1">SLA-риски</p>
              <p className="text-3xl font-semibold text-rose-600">12</p>
            </div>
            <div className="p-2 bg-rose-50 text-rose-600 rounded-lg"><AlertTriangle size={20} /></div>
          </div>
          <p className="text-xs text-slate-500 mt-2">Заявки близки к просрочке</p>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-slate-500 mb-1">Качество ИИ (точность)</p>
              <p className="text-3xl font-semibold text-slate-800">94%</p>
            </div>
            <div className="p-2 bg-purple-50 text-purple-600 rounded-lg"><Bot size={20} /></div>
          </div>
          <div className="w-full bg-slate-100 h-1.5 mt-3 rounded-full overflow-hidden">
            <div className="bg-purple-500 h-full rounded-full" style={{ width: '94%' }}></div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-sm text-slate-500 mb-1">Правки от диспетчеров</p>
              <p className="text-3xl font-semibold text-slate-800">6%</p>
            </div>
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><CheckCircle size={20} /></div>
          </div>
          <p className="text-xs text-slate-500 mt-2">ИИ ошибся при назначении</p>
        </div>
      </div>

      {/* СРЕДНИЙ РЯД: Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Распределение по категориям */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Распределение по категориям</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={DATA_CATEGORIES} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {DATA_CATEGORIES.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 mt-2">
            {DATA_CATEGORIES.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-1.5 text-xs text-slate-600">
                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index] }}></span>
                {entry.name}
              </div>
            ))}
          </div>
        </div>

        {/* Пики нагрузки */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Нагрузка по часам</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={DATA_LOAD} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTickets" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <RechartsTooltip />
                <Area type="monotone" dataKey="tickets" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorTickets)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* НИЖНИЙ РЯД: Приоритеты и Тональность */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Приоритеты */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 lg:col-span-2">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Заявки по приоритетам</h2>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={DATA_PRIORITIES} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#64748b' }} />
                <RechartsTooltip cursor={{ fill: '#f8fafc' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Тональность */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">Тональность обращений</h2>
          <div className="space-y-4 mt-6">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Позитивная / Нейтральная</span>
                <span className="font-medium text-emerald-600">78%</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full" style={{ width: '78%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Негативная (недовольство)</span>
                <span className="font-medium text-amber-500">16%</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full" style={{ width: '16%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-600">Агрессия / Авария</span>
                <span className="font-medium text-rose-600">6%</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-rose-500 h-full" style={{ width: '6%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}