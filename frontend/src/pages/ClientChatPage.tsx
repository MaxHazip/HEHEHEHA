import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Bot,
  LogOut,
  Paperclip,
  Phone,
  Send,
  User,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import CallWidget from '@/features/calls/components/CallWidget'
import {
  addMessage,
  analyzeTicket,
  createTicket,
  uploadAttachment,
  type AnalysisResponse,
} from '@/features/chat/api/chatApi'

type ChatMessage = {
  id: number
  text: string
  sender: 'user' | 'bot'
  image?: string
}

function botReply(analysis: AnalysisResponse, ticketId: number): string {
  const question = analysis.intake.questions_to_client[0]?.question
  if (question) return question

  if (analysis.intake.state === 'urgent_escalation') {
    return (
      'Похоже на серьёзную проблему. Я передал заявку диспетчеру ' +
      'как срочную — с вами свяжутся.'
    )
  }

  return (
    `Спасибо! Заявка #${ticketId} создана и передана диспетчеру. ` +
    'При необходимости он задаст уточняющие вопросы.'
  )
}

export default function ClientChatPage() {
  const logout = useAuthStore((s) => s.logout)
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

    // Сбрасываем input, чтобы можно было выбрать тот же файл снова.
    event.target.value = ''
  }

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault()
    if ((!input.trim() && !selectedFile) || sending) return

    const text = input.trim()
    const file = selectedFile
    const preview = selectedImage

    const userMessage: ChatMessage = {
      id: Date.now(),
      text,
      sender: 'user',
      image: preview ?? undefined,
    }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setSelectedFile(null)
    setSelectedImage(null)
    setSending(true)

    try {
      const activeTicketId = await ensureTicket(
        text || 'Клиент отправил изображение',
      )

      const attachmentIds: number[] = []
      if (file) {
        const attachment = await uploadAttachment(activeTicketId, file)
        attachmentIds.push(attachment.id)
      }

      if (text || attachmentIds.length > 0) {
        await addMessage(activeTicketId, text, attachmentIds)
      }

      const analysis = await analyzeTicket(activeTicketId)

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          text: botReply(analysis, activeTicketId),
          sender: 'bot',
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 2,
          text:
            'Не удалось отправить обращение. Проверьте, что backend ' +
            'запущен и доступен.',
          sender: 'bot',
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      <header className="bg-white border-b border-slate-200 p-4 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
            <Bot size={24} />
          </div>
          <div>
            <h1 className="font-semibold text-slate-800">Чат с поддержкой</h1>
            <p className="text-xs text-emerald-500">
              {ticketId ? `Заявка #${ticketId}` : 'Бот онлайн'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowCall((value) => !value)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition ${
              showCall
                ? 'bg-emerald-600 text-white'
                : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
            }`}
            title="Позвонить в поддержку"
          >
            <Phone size={16} />
            <span className="hidden sm:inline">Позвонить</span>
          </button>
          <button
            onClick={logout}
            className="text-slate-400 hover:text-rose-500 transition"
            title="Выйти"
          >
            <LogOut size={20} />
          </button>
        </div>
      </header>

      {showCall && (
        <CallWidget
          ticketId={ticketId}
          clientPhone={user?.phone}
          onSaved={(id) => setTicketId((current) => current ?? id)}
        />
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-3xl w-full mx-auto">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`flex gap-2 max-w-[85%] ${
                message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center ${
                  message.sender === 'user'
                    ? 'bg-slate-800 text-white'
                    : 'bg-blue-600 text-white'
                }`}
              >
                {message.sender === 'user' ? (
                  <User size={16} />
                ) : (
                  <Bot size={16} />
                )}
              </div>

              <div
                className={`p-3 rounded-2xl text-sm flex flex-col gap-2 ${
                  message.sender === 'user'
                    ? 'bg-slate-800 text-white rounded-tr-sm'
                    : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'
                }`}
              >
                {message.image && (
                  <img
                    src={message.image}
                    alt="Вложение"
                    className="max-w-[200px] sm:max-w-[300px] rounded-lg border border-slate-600/20"
                  />
                )}
                {message.text && (
                  <p className="whitespace-pre-wrap">{message.text}</p>
                )}
              </div>
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 text-slate-500 rounded-2xl rounded-tl-sm px-4 py-3 text-sm shadow-sm">
              Обрабатываю обращение…
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="p-4 bg-white border-t border-slate-200 shrink-0">
        <div className="max-w-3xl mx-auto">
          {selectedImage && (
            <div className="mb-3 relative inline-block">
              <img
                src={selectedImage}
                alt="Превью"
                className="h-16 w-16 object-cover rounded-lg border border-slate-200 shadow-sm"
              />
              <button
                onClick={() => {
                  setSelectedImage(null)
                  setSelectedFile(null)
                }}
                className="absolute -top-2 -right-2 bg-rose-500 text-white rounded-full p-1 hover:bg-rose-600 transition"
                title="Удалить фото"
              >
                <X size={12} />
              </button>
            </div>
          )}

          <form onSubmit={handleSend} className="flex gap-2">
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
              className="p-3 text-slate-400 hover:text-blue-600 hover:bg-slate-100 rounded-xl transition flex items-center justify-center shrink-0"
              title="Прикрепить фото"
            >
              <Paperclip size={20} />
            </button>

            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Напишите сообщение..."
              className="flex-1 border border-slate-300 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />

            <button
              type="submit"
              disabled={(!input.trim() && !selectedFile) || sending}
              className="bg-blue-600 text-white px-5 rounded-xl hover:bg-blue-700 transition flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
