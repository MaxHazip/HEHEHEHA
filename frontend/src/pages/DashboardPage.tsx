export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Главная панель</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Metric label="Активных заявок" value="12" />
        <Metric label="На проверке ИИ" value="3" accent="amber" />
        <Metric label="Высокий приоритет" value="2" accent="rose" />
        <Metric label="Риск нарушения SLA" value="0" accent="rose" />
      </div>
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h2 className="font-medium mb-2">Рекомендации ИИ</h2>
        <p className="text-sm text-slate-500">Ожидание подключения бэкенда...</p>
      </div>
    </div>
  )
}

function Metric({ label, value, accent }: { label: string, value: string, accent?: 'amber' | 'rose' }) {
  const color = accent === 'amber' ? 'text-amber-600' : accent === 'rose' ? 'text-rose-600' : 'text-slate-800'
  return (
    <div className="bg-white rounded-xl p-5 shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`text-3xl font-semibold mt-2 ${color}`}>{value}</div>
    </div>
  )
}