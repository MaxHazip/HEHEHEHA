import { api } from '@/lib/api'
import type { Engineer, Ticket } from '@/types/ticket.types'

interface UserRead {
  id: number
  name: string
  specialty: string | null
  engineer_id: number | null
}

interface TicketRead {
  id: number
  title: string
  description: string
  ai_description: string | null
  ai_solution: string | null
  category_code: string
  status: Ticket['status']
  priority: Ticket['priority']
  assignee: UserRead | null
  created_at: string
  recommended_engineer: UserRead | null
  sla_deadline: string
  sla_status: string
  knowledge_articles: Ticket['knowledgeArticles']
}

function engineerProfile(user: UserRead): Engineer | null {
  if (user.engineer_id === null) return null
  return { id: user.engineer_id, name: user.name, specialty: user.specialty ?? '' }
}

async function update(id: number, changes: object): Promise<void> {
  await api.patch(`/api/tickets/${id}`, changes)
}

export const ticketsApi = {
  async getTickets(signal?: AbortSignal): Promise<Ticket[]> {
    const tickets = new Map<number, TicketRead>()
    const limit = 100
    for (let offset = 0; ; offset += limit) {
      const { data } = await api.get<TicketRead[]>('/api/tickets', {
        params: { limit, offset },
        signal,
      })
      for (const ticket of data) tickets.set(ticket.id, ticket)
      if (data.length < limit) break
    }
    return Array.from(tickets.values()).map((ticket) => ({
      id: ticket.id,
      title: ticket.title,
      aiDescription: ticket.ai_description ?? ticket.description,
      aiSolution: ticket.ai_solution ?? undefined,
      category: ticket.category_code,
      status: ticket.status,
      priority: ticket.priority,
      assignee: ticket.assignee ? engineerProfile(ticket.assignee) : null,
      createdAt: ticket.created_at,
      recommendedEngineer: ticket.recommended_engineer ? engineerProfile(ticket.recommended_engineer) : null,
      slaDeadline: ticket.sla_deadline,
      slaStatus: ticket.sla_status,
      knowledgeArticles: ticket.knowledge_articles,
    }))
  },
  async getEngineers(): Promise<Engineer[]> {
    const { data } = await api.get<UserRead[]>('/api/users', { params: { role: 'engineer' } })
    return data.map(engineerProfile).filter((engineer) => engineer !== null)
  },
  async assignEngineer(id: number, engineer: Engineer): Promise<void> {
    await api.post(`/api/tickets/${id}/assign`, { engineer_id: engineer.id })
  },
  approveTicket: (id: number) => update(id, { status: 'in_progress' }),
  completeTicket: (id: number) => update(id, { status: 'closed' }),
  refuseTicket: (id: number) => update(id, { status: 'new', engineer_id: null }),
  updateAiDescription: (id: number, description: string) =>
    update(id, { reviewed_description: description }),
}
