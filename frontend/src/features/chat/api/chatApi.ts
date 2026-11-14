import { api } from '@/lib/api'

export interface CreateTicketPayload {
  description: string
  source: 'chat' | 'web' | 'phone'
  client_name?: string
  client_phone?: string
}

export interface TicketResponse {
  id: number
  title: string
  priority: string
  category_code: string
  subcategory_code: string
  ai_description?: string | null
}

export interface AttachmentResponse {
  id: number
  kind: string
  filename: string
  mime_type: string
  size_bytes: number
  url: string
}

export interface ClarificationQuestion {
  field: string
  question: string
}

export interface AnalysisResponse {
  ticket_id: string
  schema_version: string
  classification: {
    category_code: string
    subcategory_code: string
    status: string
  }
  intake: {
    state: string
    ready_for_dispatcher: boolean
    missing_fields: string[]
    questions_to_client: ClarificationQuestion[]
  }
  priority: { suggested: string }
  issue: { description?: string | null }
  extracted_fields: {
    location: {
      building?: string | null
      floor?: string | null
      room?: string | null
    }
  }
}

export async function createTicket(
  payload: CreateTicketPayload,
): Promise<TicketResponse> {
  const { data } = await api.post<TicketResponse>('/api/tickets', payload)
  return data
}

export async function uploadAttachment(
  ticketId: number,
  file: File,
): Promise<AttachmentResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<AttachmentResponse>(
    `/api/tickets/${ticketId}/attachments`,
    form,
  )
  return data
}

export async function addMessage(
  ticketId: number,
  text: string,
  attachmentIds: number[] = [],
): Promise<void> {
  await api.post(`/api/tickets/${ticketId}/messages`, {
    role: 'client',
    text,
    attachment_ids: attachmentIds,
  })
}

export async function analyzeTicket(
  ticketId: number,
): Promise<AnalysisResponse> {
  const { data } = await api.post<AnalysisResponse>(
    `/api/tickets/${ticketId}/analyze`,
    { force: true },
  )
  return data
}
