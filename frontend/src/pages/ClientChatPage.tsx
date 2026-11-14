import { useCallback, useEffect, useRef, useState } from 'react'
import { Bot, Paperclip, Phone, Send, Sparkles, User, X } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import CallWidget from '@/features/calls/components/CallWidget'
import {
  createTicket,
  streamChatMessage,
  uploadAttachment,
} from '@/features/chat/api/chatApi'

type ChatMessage = {
  id: number
  text: string
  sender: 'user' | 'bot'
  image?: string
}

export default function ClientChatPage() {
  const user = useAuthStore((s) => s.user)

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      text:
        'Здравствуйте! Опишите вашу проблему, и я создам заявку. ' +
        'Вы можете прикрепить фото или позвонить прямо из браузера.',
      sender: 'bot',
    },
  ])
  const [input, setInput] = useState('')
  const [ticketId, setTicketId] = useState<number | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [sending, setSending] = useState(false)
  const [showCall, setShowCall] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, selectedImage, sending])

  const ensureTicket = useCallback(
    async (
      description: string,
      source: 'chat' | 'phone' = 'chat',
    ): Promise<number> => {
      if (ticketId) return ticketId
      const ticket = await createTicket({
        description: description || 'Обращение в поддержку',
        source,
        client_name: user?.name,
        client_phone: user?.phone,
        auto_analyze: false,
      })
      setTicketId(ticket.id)
      return ticket.id
    },
    [ticketId, user],
  )

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadend = () => {
      setSelectedImage(reader.result as string)
      setSelectedFile(file)
    }
    reader.readAsDataURL(file)
    event.target.value = ''
  }

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault()
    if ((!input.trim() && !selectedFile) || sending) return

    const text = input.trim()
    const file = selectedFile
    const preview = selectedImage

    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        text,
        sender: 'user',
        image: preview ?? undefined,
      },
    ])
    setInput('')
    setSelectedFile(null)
    setSelectedImage(null)
    setSending(true)

    const botId = Date.now() + 1
    setMessages((prev) => [
      ...prev,
      { id: botId, text: '', sender: 'bot' },
    ])

    try {
      const activeTicketId = await ensureTicket(
        text || 'Клиент отправил изображение',
      )

      const attachmentIds: number[] = []
      if (file) {
        const attachment = await uploadAttachment(activeTicketId, file)
        attachmentIds.push(attachment.id)
      }

      const reply = await streamChatMessage(
        activeTicketId,
        text,
        attachmentIds,
        (partial) => {
          setMessages((prev) =>
            prev.map((item) =>
              item.id === botId ? { ...item, text: partial } : item,
            ),
          )
        },
      )

      setMessages((prev) =>
        prev.map((item) =>
          item.id === botId ? { ...item, text: reply } : item,
        ),
      )
    } catch {
      setMessages((prev) =>
        prev.map((item) =>
          item.id === botId
            ? {
                ...item,
                text:
                  'Не удалось получить ответ. Проверьте, что backend ' +
                  'запущен и доступен.',
              }
            : item,
        ),
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Поддержка
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Чат с ассистентом
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Опишите проблему — ИИ создаст заявку и передаст её диспетчеру.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500 shadow-sm">
            {ticketId ? `Заявка #${ticketId}` : 'Новое обращение'}
          </div>
          <button
            type="button"
            onClick={() => setShowCall((value) => !value)}
            className="button-dark flex items-center gap-2 px-4 py-2.5 text-xs"
          >
            <Phone size={15} />
            {showCall ? 'Скрыть звонок' : 'Позвонить'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="glass-card flex h-[68vh] min-h-[520px] flex-col overflow-hidden">
          <div className="flex items-center gap-3 border-b border-gray-100 p-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#242424] text-white">
              <Bot size={20} />
            </div>
            <div>
              <div className="text-sm font-semibold text-[#222]">
                AI-ассистент
              </div>
              <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-emerald-600">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Онлайн · Qwen3
              </div>
            </div>
          </div>

          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.map((message) => {
            if (!message.text && !message.image) return null

            return (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === 'user'
                    ? 'justify-end'
                    : 'justify-start'
                }`}
              >
                <div
                  className={`flex max-w-[85%] gap-2 ${
                    message.sender === 'user'
                      ? 'flex-row-reverse'
                      : 'flex-row'
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      message.sender === 'user'
                        ? 'bg-[#242424] text-white'
                        : 'border border-gray-200 bg-white text-[#333]'
                    }`}
                  >
                    {message.sender === 'user' ? (
                      <User size={15} />
                    ) : (
                      <Bot size={15} />
                    )}
                  </div>

                  <div
                    className={`flex flex-col gap-2 rounded-2xl p-3 text-sm ${
                      message.sender === 'user'
                        ? 'rounded-tr-sm bg-[#242424] text-white'
                        : 'rounded-tl-sm border border-gray-100 bg-white text-[#333]'
                    }`}
                  >
                    {message.image && (
                      <img
                        src={message.image}
                        alt="Вложение"
                        className="max-w-[200px] rounded-lg border border-white/20 object-cover sm:max-w-[280px]"
                      />
                    )}
                    {message.text && (
                      <p className="whitespace-pre-wrap leading-6">
                        {message.text}
                      </p>
                    )}
                  </div>
                </div>
              </div>
              )
            })}

            {sending && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-gray-100 bg-white px-4 py-3 text-xs text-gray-500">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-gray-400" />
                  Ассистент печатает…
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          <form onSubmit={handleSend} className="border-t border-gray-100 p-4">
            {selectedImage && (
              <div className="relative mb-3 inline-block">
                <img
                  src={selectedImage}
                  alt="Превью"
                  className="h-16 w-16 rounded-lg border border-gray-200 object-cover"
                />
                <button
                  type="button"
                  onClick={() => {
                    setSelectedImage(null)
                    setSelectedFile(null)
                  }}
                  className="absolute -right-2 -top-2 rounded-full bg-[#242424] p-1 text-white"
                  title="Удалить фото"
                >
                  <X size={11} />
                </button>
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="file"
                accept="image/*"
                className="hidden"
                ref={fileInputRef}
                onChange={handleFileChange}
              />

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-400 transition hover:border-gray-300 hover:text-[#222]"
                title="Прикрепить фото"
              >
                <Paperclip size={18} />
              </button>

              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Опишите проблему..."
                className="glass-input h-12 flex-1 px-4"
              />

              <button
                type="submit"
                disabled={(!input.trim() && !selectedFile) || sending}
                className="button-dark h-12 shrink-0 px-5 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send size={17} />
              </button>
            </div>
          </form>
        </section>

        <aside className="space-y-5">
          <div className="glass-card p-5">
            <div className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[1.5px] text-gray-400">
              <Sparkles size={14} />
              Как это работает
            </div>
            <ol className="space-y-3 text-sm leading-6 text-gray-600">
              <li>1. Опишите проблему обычным языком.</li>
              <li>2. Ассистент уточнит детали и создаст заявку.</li>
              <li>3. Диспетчер увидит её в общей очереди.</li>
            </ol>

            {ticketId && (
              <div className="mt-4 rounded-xl bg-[#f5f5f3] p-3 text-xs leading-5 text-gray-500">
                Заявка #{ticketId} уже создана. Диалог и рекомендации
                сохранены в ней.
              </div>
            )}
          </div>

          {showCall && (
            <div className="glass-card overflow-hidden">
              <CallWidget
                ticketId={ticketId}
                clientPhone={user?.phone}
                onSaved={(id) =>
                  setTicketId((current) => current ?? id)
                }
              />
            </div>
          )}

          <div className="dark-card p-5">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles size={16} />
              Локальный ИИ
            </div>
            <p className="mt-2 text-xs leading-5 text-white/50">
              Qwen3 отвечает в чате, T-one распознаёт речь, Silero озвучивает
              ответы. Данные не уходят в облако.
            </p>
          </div>
        </aside>
      </div>
    </div>
  )
}
