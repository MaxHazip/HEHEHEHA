import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, LogOut, Paperclip, X } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

// Добавили поле image в тип сообщения
type Message = { 
  id: number
  text: string
  sender: 'user' | 'bot'
  image?: string 
}

export default function ClientChatPage() {
  const logout = useAuthStore((s) => s.logout)
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: 'Здравствуйте! Опишите вашу проблему, и я создам заявку. Вы также можете прикрепить фото.', sender: 'bot' },
  ])
  const [input, setInput] = useState('')
  
  // Состояние для прикрепленного фото (в формате Base64)
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null) // Ссылка на скрытый инпут файла

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, selectedImage])

  // Обработка выбора файла
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadend = () => {
      setSelectedImage(reader.result as string)
    }
    reader.readAsDataURL(file)
    
    // Очищаем инпут, чтобы можно было выбрать тот же файл снова
    e.target.value = ''
  }

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() && !selectedImage) return // Не отправляем пустые сообщения

    // Добавляем сообщение пользователя (с фото или без)
    const userMsg: Message = { 
      id: Date.now(), 
      text: input, 
      sender: 'user',
      image: selectedImage || undefined 
    }
    setMessages((prev) => [...prev, userMsg])
    
    // Очищаем поля
    setInput('')
    setSelectedImage(null)

    // Имитация ответа бота
    setTimeout(() => {
      let botText = 'Уточните, пожалуйста, номер кабинета.'
      
      if (userMsg.image) {
        botText = 'Фото получено! Я прикрепил его к заявке. Уточните номер кабинета.'
      } else if (messages.length > 3) {
        botText = 'Спасибо! Я передал данные диспетчеру. Заявка принята в работу! ✅'
      }

      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, text: botText, sender: 'bot' },
      ])
    }, 1000)
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Шапка чата */}
      <header className="bg-white border-b border-slate-200 p-4 flex justify-between items-center shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
            <Bot size={24} />
          </div>
          <div>
            <h1 className="font-semibold text-slate-800">Чат с поддержкой</h1>
            <p className="text-xs text-emerald-500">Бот онлайн</p>
          </div>
        </div>
        <button onClick={logout} className="text-slate-400 hover:text-rose-500 transition" title="Выйти">
          <LogOut size={20} />
        </button>
      </header>

      {/* Область сообщений */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-3xl w-full mx-auto">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-2 max-w-[85%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center ${msg.sender === 'user' ? 'bg-slate-800 text-white' : 'bg-blue-600 text-white'}`}>
                {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              
              <div className={`p-3 rounded-2xl text-sm flex flex-col gap-2 ${msg.sender === 'user' ? 'bg-slate-800 text-white rounded-tr-sm' : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'}`}>
                {/* Если есть картинка - показываем её */}
                {msg.image && (
                  <img src={msg.image} alt="Вложение" className="max-w-[200px] sm:max-w-[300px] rounded-lg border border-slate-600/20" />
                )}
                {/* Текст сообщения */}
                {msg.text && <p className="whitespace-pre-wrap">{msg.text}</p>}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Поле ввода */}
      <div className="p-4 bg-white border-t border-slate-200 shrink-0">
        <div className="max-w-3xl mx-auto">
          
          {/* Превью прикрепленного фото (до отправки) */}
          {selectedImage && (
            <div className="mb-3 relative inline-block">
              <img src={selectedImage} alt="Превью" className="h-16 w-16 object-cover rounded-lg border border-slate-200 shadow-sm" />
              <button
                onClick={() => setSelectedImage(null)}
                className="absolute -top-2 -right-2 bg-rose-500 text-white rounded-full p-1 hover:bg-rose-600 transition"
                title="Удалить фото"
              >
                <X size={12} />
              </button>
            </div>
          )}

          <form onSubmit={handleSend} className="flex gap-2">
            {/* Скрытый инпут для файла */}
            <input 
              type="file" 
              accept="image/*" 
              className="hidden" 
              ref={fileInputRef}
              onChange={handleFileChange}
            />
            
            {/* Кнопка-скрепка */}
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
              onChange={(e) => setInput(e.target.value)}
              placeholder="Напишите сообщение..."
              className="flex-1 border border-slate-300 rounded-xl px-4 py-3 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            />
            
            <button
              type="submit"
              disabled={!input.trim() && !selectedImage}
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