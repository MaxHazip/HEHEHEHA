export type TicketStatus = 'new' | 'in_progress' | 'closed'
export type TicketPriority = 'low' | 'medium' | 'high'

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