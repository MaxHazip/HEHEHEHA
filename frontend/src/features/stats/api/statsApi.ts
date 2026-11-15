import { api } from '@/services/api'

export interface CountItem {
  name: string
  count: number
}

export interface HourlyItem {
  time: string
  tickets: number
}

export interface DailyItem {
  date: string
  created: number
  closed: number
}

export interface EngineerLoadItem {
  id: number
  name: string
  competencies: string[]
  load: number
  available: boolean
  open_tickets: number
}

export interface Stats {
  total_tickets: number
  new_tickets: number
  draft_tickets: number
  in_progress_tickets: number
  resolved_tickets: number
  closed_tickets: number
  high_priority_tickets: number
  unassigned_tickets: number
  ai_review_tickets: number
  mass_incident_tickets: number
  sla_risks: number
  completion_rate: number
  avg_ai_confidence: number
  avg_resolution_hours: number
  manual_edits: number
  by_status: CountItem[]
  by_priority: CountItem[]
  by_category: CountItem[]
  by_subcategory: CountItem[]
  by_channel: CountItem[]
  hourly: HourlyItem[]
  daily: DailyItem[]
  engineers: {
    total: number
    available: number
    load: number
  }
  engineers_detail: EngineerLoadItem[]
  calls: {
    total: number
    today: number
    with_recording: number
    with_transcript: number
  }
  attachments: {
    total: number
    images: number
    audio: number
    documents: number
  }
  knowledge_articles: number
  generated_at: string
}

export async function getStats(): Promise<Stats> {
  const { data } = await api.get<Stats>('/stats')
  return data
}
