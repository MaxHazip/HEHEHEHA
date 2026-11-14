import { api } from '@/services/api'
import type {
  Engineer,
  Ticket,
  TicketPriority,
  TicketStatus,
} from '@/types/ticket.types'

interface BackendUser {
  id: number
  name: string
  engineer_id: number | null
  specialty: string | null
}

interface BackendTicket {
  id: number
  title: string
  description: string
  status: string
  priority: string
  category_code: string
  assignee: BackendUser | null
  ai_description: string | null
  ai_solution: string | null
  knowledge?: Array<{
    id: number
    code: string
    title: string
    body: string
    keywords: string[]
    score?: number | null
  }>
  created_at: string
}

const STATUS_MAP: Record<string, TicketStatus> = {
  draft: 'new',
  new: 'new',
  in_progress: 'in_progress',
  resolved: 'closed',
  closed: 'closed',
}

const PRIORITY_MAP: Record<string, TicketPriority> = {
  low: 'low',
  medium: 'medium',
  high: 'high',
  critical: 'high',
}

function mapTicket(raw: BackendTicket): Ticket {
  const assignee =
    raw.assignee && raw.assignee.engineer_id !== null
      ? {
          id: raw.assignee.engineer_id,
          name: raw.assignee.name,
          specialty: raw.assignee.specialty ?? '',
        }
      : null

  return {
    id: raw.id,
    title: raw.title,
    aiDescription: raw.ai_description ?? raw.description,
    aiSolution: raw.ai_solution ?? undefined,
    category: raw.category_code,
    status: STATUS_MAP[raw.status] ?? 'new',
    priority: PRIORITY_MAP[raw.priority] ?? 'medium',
    assignee,
    knowledge: raw.knowledge ?? [],
    createdAt: raw.created_at,
  }
}

export const ticketsApi = {
  getTickets: async (): Promise<Ticket[]> => {
    const { data } = await api.get<BackendTicket[]>('/tickets')
    return data.map(mapTicket)
  },

  getEngineers: async (): Promise<Engineer[]> => {
    const { data } = await api.get<BackendUser[]>('/users', {
      params: { role: 'engineer' },
    })
    return data
      .filter((user) => user.engineer_id !== null)
      .map((user) => ({
        id: user.engineer_id as number,
        name: user.name,
        specialty: user.specialty ?? '',
      }))
  },

  assignEngineer: async (
    ticketId: number,
    engineer: Engineer,
  ): Promise<void> => {
    await api.post(`/tickets/${ticketId}/assign`, {
      engineer_id: engineer.id,
    })
  },

  approveTicket: async (ticketId: number): Promise<void> => {
    await api.patch(`/tickets/${ticketId}`, { status: 'in_progress' })
  },

  completeTicket: async (ticketId: number): Promise<void> => {
    await api.patch(`/tickets/${ticketId}`, { status: 'closed' })
  },

  refuseTicket: async (ticketId: number): Promise<void> => {
    await api.patch(`/tickets/${ticketId}`, {
      status: 'new',
      engineer_id: null,
    })
  },

  updateAiDescription: async (
    ticketId: number,
    newDescription: string,
  ): Promise<void> => {
    await api.patch(`/tickets/${ticketId}`, {
      ai_description: newDescription,
    })
  },
}
