import { api } from '@/services/api'

export interface KnowledgeArticle {
  id: number
  code: string
  title: string
  body: string
  keywords: string[]
  score?: number | null
}

export interface KnowledgeStatus {
  enabled: boolean
  qdrant_available: boolean
  indexed: boolean
  collection: string
  embedding_model: string
  articles: number
}

export async function listArticles(): Promise<KnowledgeArticle[]> {
  const { data } = await api.get<KnowledgeArticle[]>('/knowledge/articles')
  return data
}

export async function searchArticles(
  query: string,
  limit = 8,
): Promise<KnowledgeArticle[]> {
  const { data } = await api.get<KnowledgeArticle[]>('/knowledge/search', {
    params: { q: query, limit },
  })
  return data
}

export async function getKnowledgeStatus(): Promise<KnowledgeStatus> {
  const { data } = await api.get<KnowledgeStatus>('/knowledge/status')
  return data
}

export async function reindexKnowledge(): Promise<KnowledgeStatus> {
  const { data } = await api.post<KnowledgeStatus>(
    '/knowledge/reindex',
    undefined,
    { timeout: 600_000 },
  )
  return data
}
