import { useTickets } from '@/features/tickets/hooks/useTickets'

export default function AdminDashboardPage() {
  const { data: tickets = [], isLoading, isError } = useTickets()

  if (isLoading) return <p>Загрузка статистики…</p>
  if (isError) return <p role="alert">Не удалось загрузить заявки</p>

  const counts = new Map<string, number>()
  for (const ticket of tickets) {
    counts.set(ticket.category, (counts.get(ticket.category) ?? 0) + 1)
  }
  const metrics = [
    ['Загружено заявок', tickets.length],
    ['Ожидают проверки', tickets.filter((t) => t.status === 'draft' || t.status === 'new').length],
    ['Риск SLA или просрочка', tickets.filter((t) => t.slaStatus === 'at_risk' || t.slaStatus === 'overdue').length],
    ['В работе', tickets.filter((t) => t.status === 'in_progress').length],
    ['Решены или закрыты', tickets.filter((t) => t.status === 'resolved' || t.status === 'closed').length],
  ] as const

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <h1 className="text-2xl font-semibold text-slate-800">Аналитика заявок</h1>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map(([label, count]) => (
          <section className="rounded-xl border bg-white p-5" key={label}>
            <h2 className="text-sm text-slate-500">{label}</h2>
            <p className="text-3xl font-semibold">{count}</p>
          </section>
        ))}
      </div>
      <section className="rounded-xl border bg-white p-5">
        <h2 className="font-semibold">Заявки по категориям</h2>
        {counts.size === 0 ? <p>Заявок пока нет</p> : (
          <ul className="mt-3 space-y-2">
            {[...counts].map(([category, count]) => (
              <li key={category} className="flex justify-between">
                <span>{category === 'none' ? 'Без категории' : category}</span>
                <span>{count}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
