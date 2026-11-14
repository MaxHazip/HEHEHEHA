export type TicketStatus = 'new' | 'in_progress' | 'closed'
export type TicketPriority = 'low' | 'medium' | 'high'

export interface Engineer {
  id: number
  name: string
  specialty: string
}

export interface TicketKnowledge {
  id: number
  code: string
  title: string
  body: string
  keywords: string[]
  score?: number | null
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
  knowledge?: TicketKnowledge[]
  createdAt: string
}