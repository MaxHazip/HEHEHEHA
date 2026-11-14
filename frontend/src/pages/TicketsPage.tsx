import TicketCard from '@/features/tickets/components/TicketCard'
import { useTickets } from '@/features/tickets/hooks/useTickets'

export default function TicketsPage() {
  const { data: tickets = [], isLoading, isError } = useTickets()

  if (isLoading) return <div className="p-6 text-slate-500">Загрузка заявок...</div>
  if (isError) return <p role="alert">Не удалось загрузить заявки</p>

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-slate-800">Входящие заявки</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {tickets.map((ticket) => (
          <TicketCard key={ticket.id} ticket={ticket} />
        ))}
      </div>
    </div>
  )
}