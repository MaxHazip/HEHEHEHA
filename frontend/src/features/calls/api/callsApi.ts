import { api, apiUrl } from '@/lib/api'

export interface CallListItem {
  id: number
  ticket_id: number | null
  external_id: string | null
  direction: string
  transport: string
  provider: string | null
  client_phone: string | null
  status: string
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
  has_recording: boolean
  recording_url: string | null
  transcript_preview: string | null
}

export interface TranscriptSegment {
  id: number
  position: number
  start_ms: number | null
  end_ms: number | null
  speaker: string | null
  text: string
  confidence: number | null
}

export interface CallDetail {
  id: number
  ticket_id: number | null
  external_id: string | null
  direction: string
  transport: string
  provider: string | null
  client_phone: string | null
  status: string
  started_at: string
  ended_at: string | null
  duration_seconds: number | null
  recording_mime: string | null
  recording_size: number | null
  has_recording: boolean
  recording_url: string | null
  transcript_text: string | null
  transcript_language: string | null
  transcript_provider: string | null
  created_at: string
  segments: TranscriptSegment[]
}

export interface AnalysisResult {
  ticket_id?: string
}

export interface SaveCallParams {
  callId?: number | null
  ticketId: number | null
  blob: Blob
  mimeType: string
  transcript: string
  durationSeconds: number
  clientPhone?: string
}

export interface SavedCall {
  id: number
  ticketId: number | null
  recordingUrl: string
  transcript: string
  transcriptProvider?: string
}

export async function listCalls(params?: {
  status?: string
  limit?: number
}): Promise<CallListItem[]> {
  const { data } = await api.get<CallListItem[]>('/api/calls', { params })
  return data
}

export async function getCall(callId: number): Promise<CallDetail> {
  const { data } = await api.get<CallDetail>(`/api/calls/${callId}`)
  return data
}

export async function createCallSession(
  ticketId: number | null,
  clientPhone?: string,
): Promise<number> {
  const { data } = await api.post<{ id: number }>('/api/calls', {
    ticket_id: ticketId,
    direction: 'inbound',
    transport: 'webrtc',
    provider: 'browser-webrtc',
    client_phone: clientPhone,
  })
  return data.id
}

async function uploadRecording(
  callId: number,
  blob: Blob,
  mimeType: string,
): Promise<void> {
  const extension = mimeType.includes('ogg')
    ? 'ogg'
    : mimeType.includes('mp4') || mimeType.includes('m4a')
      ? 'm4a'
      : 'webm'
  const form = new FormData()
  form.append('file', blob, `call.${extension}`)
  form.append('mime_type', mimeType)
  await api.post(`/api/calls/${callId}/recording`, form)
}

async function completeCall(
  callId: number,
  durationSeconds: number,
): Promise<void> {
  await api.patch(`/api/calls/${callId}`, {
    status: 'completed',
    duration_seconds: durationSeconds,
  })
}

async function saveTranscript(
  callId: number,
  text: string,
): Promise<void> {
  await api.put(`/api/calls/${callId}/transcript`, {
    text,
    language: 'ru-RU',
    provider: 'google-web-speech',
    segments: [],
  })
}

export async function transcribeCall(callId: number): Promise<CallDetail> {
  const { data } = await api.post<CallDetail>(
    `/api/calls/${callId}/transcribe`,
  )
  return data
}

async function analyzeCall(callId: number): Promise<AnalysisResult> {
  const { data } = await api.post<AnalysisResult>(
    `/api/calls/${callId}/analyze`,
  )
  return data
}

/**
 * Сохраняет звонок:
 * если браузер не дал расшифровку, backend попробует локальный Whisper
 * или Google STT, затем создаст/обновит заявку.
 */
export async function saveCall(params: SaveCallParams): Promise<SavedCall> {
  const callId =
    params.callId ??
    (await createCallSession(params.ticketId, params.clientPhone))

  await uploadRecording(callId, params.blob, params.mimeType)
  await completeCall(callId, params.durationSeconds)

  let transcript = params.transcript.trim()
  let transcriptProvider: string | undefined
  if (transcript) {
    await saveTranscript(callId, transcript)
    transcriptProvider = 'google-web-speech'
  } else {
    try {
      const detail = await transcribeCall(callId)
      transcript = detail.transcript_text ?? ''
      transcriptProvider = detail.transcript_provider ?? 'server'
    } catch {
      // Серверная расшифровка не настроена — запись всё равно сохранена.
    }
  }

  let ticketId = params.ticketId
  try {
    const analysis = await analyzeCall(callId)
    const parsed = Number(analysis.ticket_id)
    if (Number.isFinite(parsed)) ticketId = parsed
  } catch {
    // Сбой ИИ не должен терять уже сохранённые запись и расшифровку.
  }

  return {
    id: callId,
    ticketId,
    recordingUrl: apiUrl(`/api/calls/${callId}/recording`) ?? '',
    transcript,
    transcriptProvider,
  }
}
