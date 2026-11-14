import { api } from '@/services/api'

export interface CountItem {
  name: string
  count: number
}

export interface HourlyItem {
  time: string
  tickets: number
}

export interface Stats {
  total_tickets: number
  new_tickets: number
  in_progress_tickets: number
  closed_tickets: number
  high_priority_tickets: number
  unassigned_tickets: number
  sla_risks: number
  completion_rate: number
  avg_ai_confidence: number
  manual_edits: number
  by_status: CountItem[]
  by_priority: CountItem[]
  by_category: CountItem[]
  hourly: HourlyItem[]
  engineers: {
    total: number
    available: number
    load: number
  }
  calls: {
    total: number
    today: number
    with_recording: number
  }
  knowledge_articles: number
  generated_at: string
}

export async function getStats(): Promise<Stats> {
  const { data } = await api.get<Stats>('/stats')
  return data
}
