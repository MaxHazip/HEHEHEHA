import { api } from '@/lib/api'

// ИИ на CPU может отвечать несколько минут — не обрываем запрос через 30 с.
const AI_TIMEOUT_MS = 600_000

export interface CreateTicketPayload {
  description: string
  source: 'chat' | 'web' | 'phone'
  client_name?: string
  client_phone?: string
  // false — не запускать ИИ-анализ при создании: клиент вызовет
  // /api/tickets/{id}/analyze сам, уже с сообщением и вложениями.
  auto_analyze?: boolean
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

export interface ChatReply {
  reply: string
  ticket_id: number
}

export async function sendChatMessage(
  ticketId: number,
  text: string,
  attachmentIds: number[] = [],
): Promise<ChatReply> {
  const { data } = await api.post<ChatReply>(
    `/api/tickets/${ticketId}/chat`,
    { text, attachment_ids: attachmentIds },
    { timeout: AI_TIMEOUT_MS },
  )
  return data
}

export async function streamChatMessage(
  ticketId: number,
  text: string,
  attachmentIds: number[] = [],
  onDelta: (fullText: string) => void = () => undefined,
): Promise<string> {
  const base = String(api.defaults.baseURL ?? '').replace(/\/$/, '')
  const response = await fetch(
    `${base}/api/tickets/${ticketId}/chat/stream`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        text,
        attachment_ids: attachmentIds,
      }),
    },
  )

  if (!response.ok || !response.body) {
    const detail = await response.text()
    throw new Error(detail || `HTTP ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let full = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    let boundary = buffer.indexOf('\n\n')

    while (boundary >= 0) {
      const eventBlock = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)

      for (const line of eventBlock.split('\n')) {
        if (!line.startsWith('data:')) continue
        const raw = line.slice(5).trim()
        if (!raw) continue

        let event: {
          delta?: string
          done?: boolean
          reply?: string
        }
        try {
          event = JSON.parse(raw)
        } catch {
          continue
        }

        if (typeof event.delta === 'string') {
          full += event.delta
          onDelta(full)
        }

        if (event.done) {
          if (typeof event.reply === 'string' && event.reply) {
            full = event.reply
          }
          return full
        }
      }

      boundary = buffer.indexOf('\n\n')
    }
  }

  return full
}

export async function createTicket(
  payload: CreateTicketPayload,
): Promise<TicketResponse> {
  const { data } = await api.post<TicketResponse>(
    '/api/tickets',
    payload,
    { timeout: AI_TIMEOUT_MS },
  )
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
    { timeout: AI_TIMEOUT_MS },
  )
  return data
}
