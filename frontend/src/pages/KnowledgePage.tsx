import { useState } from 'react'
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  AlertCircle,
  BookOpen,
  Database,
  Loader2,
  RefreshCw,
  Search,
  X,
} from 'lucide-react'
import {
  getKnowledgeStatus,
  listArticles,
  reindexKnowledge,
  searchArticles,
  type KnowledgeArticle,
  type KnowledgeStatus,
} from '@/features/knowledge/api/knowledgeApi'

export default function KnowledgePage() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const queryClient = useQueryClient()

  const initialQuery = useQuery({
    queryKey: ['knowledge'],
    queryFn: async () => {
      const [articles, status] = await Promise.all([
        listArticles(),
        getKnowledgeStatus(),
      ])
      return { articles, status }
    },
  })

  const searchQuery = useQuery({
    queryKey: ['knowledge-search', submittedQuery],
    queryFn: () => searchArticles(submittedQuery),
    enabled: submittedQuery.length > 0,
  })

  const reindexMutation = useMutation({
    mutationFn: reindexKnowledge,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['knowledge'] })
      if (submittedQuery) {
        void queryClient.invalidateQueries({
          queryKey: ['knowledge-search', submittedQuery],
        })
      }
    },
  })

  const articles: KnowledgeArticle[] = submittedQuery
    ? searchQuery.data ?? []
    : initialQuery.data?.articles ?? []
  const status: KnowledgeStatus | null =
    initialQuery.data?.status ?? null
  const isSearching = submittedQuery.length > 0 && searchQuery.isFetching
  const isReindexing = reindexMutation.isPending
  const hasError =
    initialQuery.isError ||
    searchQuery.isError ||
    reindexMutation.isError

  const handleSearch = (event: React.FormEvent) => {
    event.preventDefault()
    setSubmittedQuery(query.trim())
  }

  const handleClear = () => {
    setQuery('')
    setSubmittedQuery('')
  }

  if (initialQuery.isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex items-center gap-3 text-sm text-gray-500">
          <Loader2 className="h-5 w-5 animate-spin" />
          Загружаем базу знаний...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            База знаний
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Статьи и рекомендации
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Семантический поиск Qdrant и рекомендации для заявок.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500 shadow-sm">
            <Database size={15} />
            Qdrant: {status?.qdrant_available ? 'доступен' : 'fallback на БД'}
            {' · '}
            статей: {status?.articles ?? articles.length}
          </div>
          <button
            type="button"
            onClick={() => reindexMutation.mutate()}
            disabled={isReindexing}
            className="button-dark flex items-center gap-2 px-4 py-2.5 text-xs disabled:opacity-50"
          >
            {isReindexing ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <RefreshCw size={15} />
            )}
            Переиндексировать
          </button>
        </div>
      </div>

      <section className="glass-card p-4 sm:p-5">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search
              size={17}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Например: не работает интернет в 305 кабинете"
              className="glass-input h-11 w-full pl-11 pr-10"
              style={{ paddingLeft: '42px' }}
            />
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-black"
              >
                <X size={15} />
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={isSearching}
            className="button-dark flex items-center gap-2 px-5 disabled:opacity-50"
          >
            {isSearching ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Search size={16} />
            )}
            Найти
          </button>
        </form>

        {status && (
          <p className="mt-3 text-[11px] text-gray-400">
            Коллекция: {status.collection} · модель: {status.embedding_model} ·
            индекс: {status.indexed ? 'готов' : 'не построен'}
          </p>
        )}
      </section>

      {hasError && (
        <div className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-600">
          <AlertCircle size={15} />
          Не удалось получить данные. Проверьте backend, Qdrant и модель
          эмбеддингов.
        </div>
      )}

      {isSearching && articles.length === 0 ? (
        <div className="glass-card flex min-h-[240px] items-center justify-center p-8">
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <Loader2 className="h-5 w-5 animate-spin" />
            Ищем по базе знаний...
          </div>
        </div>
      ) : articles.length === 0 ? (
        <div className="glass-card flex min-h-[240px] flex-col items-center justify-center p-8 text-center">
          <BookOpen size={26} className="mb-3 text-gray-400" />
          <h3 className="text-base font-semibold text-[#222]">
            Статьи не найдены
          </h3>
          <p className="mt-2 max-w-sm text-sm text-gray-400">
            Попробуйте другой запрос или добавьте статьи в
            json/knowledge_articles.json.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          {articles.map((article) => (
            <article
              key={article.id}
              className="glass-card flex flex-col gap-3 p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#f2f2f2]">
                    <BookOpen size={17} />
                  </div>
                  <div>
                    <h2 className="text-sm font-semibold text-[#222]">
                      {article.title}
                    </h2>
                    <p className="text-[10px] uppercase tracking-[1px] text-gray-400">
                      {article.code}
                    </p>
                  </div>
                </div>
                {article.score !== null && article.score !== undefined && (
                  <span className="rounded-full bg-gray-100 px-2 py-1 text-[10px] font-semibold text-gray-600">
                    {Math.round(article.score * 100)}%
                  </span>
                )}
              </div>

              <p className="text-sm leading-6 text-gray-600">
                {article.body}
              </p>

              {article.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {article.keywords.map((keyword) => (
                    <span
                      key={keyword}
                      className="rounded-md bg-gray-100 px-2 py-1 text-[10px] font-medium text-gray-500"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
