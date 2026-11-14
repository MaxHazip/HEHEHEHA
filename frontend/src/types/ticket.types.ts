export type TicketStatus = 'draft' | 'new' | 'in_progress' | 'resolved' | 'closed'
export type TicketPriority = 'low' | 'medium' | 'high' | 'critical'

export interface Engineer {
  id: number
  name: string
  specialty: string
}

export interface Ticket {
  id: number
  title: string
  aiDescription: string
  aiSolution?: string // Решение от нейросети
  documents?: string[] // Прикрепленные файлы
  category: string
  status: TicketStatus
  priority: TicketPriority
  assignee: Engineer | null
  createdAt: string
}