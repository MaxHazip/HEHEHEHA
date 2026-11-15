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

export interface TicketAttachment {
  id: number
  kind: string
  filename: string
  mime_type: string
  size_bytes: number
  url: string
  description?: string | null
  created_at: string
}

export interface TicketCall {
  id: number
  status: string
  recording_url: string | null
  transcript_preview: string | null
  duration_seconds: number | null
  started_at: string
  ended_at: string | null
  client_phone: string | null
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
  attachments?: TicketAttachment[]
  calls?: TicketCall[]
  createdAt: string
}