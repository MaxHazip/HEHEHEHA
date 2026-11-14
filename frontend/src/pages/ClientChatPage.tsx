import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, LogOut, Paperclip, X, Phone, Volume2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import VoiceCallModal from '@/components/VoiceCallModal'

type Message = { 
  id: number
  text: string
  sender: 'user' | 'bot'
  image?: string 
  isVoice?: boolean
}

export default function ClientChatPage() {
  const { logout, user } = useAuthStore()
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: 'Здравствуйте! Опишите вашу проблему, прикрепите фото или позвоните нам.', sender: 'bot' },
  ])
  const [input, setInput] = useState('')
  const [selectedImage, setSelectedImage] = useState<string | null>(null)
  const [isCalling, setIsCalling] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, selectedImage])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onloadend = () => setSelectedImage(reader.result as string)
    reader.readAsDataURL(file)
    e.target.value = ''
  }

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() && !selectedImage) return

    const userMsg: Message = { id: Date.now(), text: input, sender: 'user', image: selectedImage || undefined }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setSelectedImage(null)
    
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, text: 'Я принял информацию. Уточните, пожалуйста, номер кабинета.', sender: 'bot' },
      ])
    }, 1000)
  }

  const handleCallEnd = (transcribedText?: string, aiReply?: string) => {
    setIsCalling(false)
    if (transcribedText) {
      const clientVoiceMsg: Message = { id: Date.now(), text: transcribedText, sender: 'user', isVoice: true }
      setMessages((prev) => [...prev, clientVoiceMsg])
      
      if (aiReply) {
        setTimeout(() => {
          const aiVoiceMsg: Message = { id: Date.now() + 1, text: aiReply, sender: 'bot', isVoice: true }
          setMessages((prev) => [...prev, aiVoiceMsg])
        }, 500)
      }
    }
  }

  return (
    <div className="app-background h-screen flex items-center justify-center p-0 sm:p-4">
      <div className="app-shell !min-h-full !p-0 sm:!min-h-[90vh] sm:!h-[90vh] flex-col max-w-4xl w-full !rounded-none sm:!rounded-[34px] overflow-hidden relative">
        
        {/* Шапка чата */}
        <header className="bg-white/60 backdrop-blur-md border-b border-white/80 p-4 sm:px-6 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 bg-[#242424] text-white rounded-xl flex items-center justify-center shadow-md">
              <Bot size={22} />
            </div>
            <div>
              <h1 className="font-semibold text-[#222]">Поддержка DispatchAI</h1>
              <p className="text-[10px] uppercase tracking-wider text-emerald-600 font-semibold flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" /> Бот онлайн
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-gray-500 hidden sm:block">{user?.name}</span>
            <button onClick={logout} className="app-topbar-button !w-9 !h-9" title="Выйти">
              <LogOut size={16} />
            </button>
          </div>
        </header>

        {/* Область сообщений */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-transparent">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-3 max-w-[85%] ${msg.sender === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                
                <div className={`w-8 h-8 shrink-0 rounded-full flex items-center justify-center shadow-sm ${msg.sender === 'user' ? 'bg-[#242424] text-white' : 'bg-white border border-gray-200 text-[#242424]'}`}>
                  {msg.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                
                <div className={`p-3.5 rounded-2xl text-sm flex flex-col gap-2 shadow-sm ${
                  msg.sender === 'user' 
                    ? 'bg-[#242424] text-white rounded-tr-sm' 
                    : 'bg-white/90 border border-white text-[#222] rounded-tl-sm backdrop-blur-sm'
                }`}>
                  {msg.image && <img src={msg.image} alt="Вложение" className="max-w-[200px] rounded-xl border border-black/10" />}
                  
                  {msg.isVoice ? (
                    <div className="flex items-center gap-2.5">
                      <Volume2 size={18} className={msg.sender === 'user' ? 'text-blue-300' : 'text-[#242424]'} />
                      <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                    </div>
                  ) : (
                    msg.text && <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Поле ввода */}
        <div className="p-4 sm:p-5 bg-white/40 border-t border-white/60 backdrop-blur-lg shrink-0">
          <div className="max-w-3xl mx-auto">
            {selectedImage && (
              <div className="mb-3 relative inline-block">
                <img src={selectedImage} alt="Превью" className="h-16 w-16 object-cover rounded-xl border-2 border-white shadow-sm" />
                <button onClick={() => setSelectedImage(null)} className="absolute -top-2 -right-2 bg-[#b87979] text-white rounded-full p-1 hover:bg-rose-600 transition shadow-sm">
                  <X size={12} />
                </button>
              </div>
            )}

            <form onSubmit={handleSend} className="flex gap-2">
              <input type="file" accept="image/*" className="hidden" ref={fileInputRef} onChange={handleFileChange} />
              
              <button
                type="button"
                onClick={() => setIsCalling(true)}
                className="w-12 h-12 bg-white text-[#242424] rounded-xl border border-gray-200 hover:bg-gray-50 hover:text-emerald-600 transition flex items-center justify-center shrink-0 shadow-sm"
                title="Позвонить боту"
              >
                <Phone size={18} />
              </button>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-12 h-12 bg-white text-[#242424] rounded-xl border border-gray-200 hover:bg-gray-50 hover:text-blue-600 transition flex items-center justify-center shrink-0 shadow-sm"
                title="Прикрепить фото"
              >
                <Paperclip size={18} />
              </button>

              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Напишите сообщение..."
                className="flex-1 glass-input h-12 bg-white/80"
              />
              
              <button
                type="submit"
                disabled={!input.trim() && !selectedImage}
                className="button-dark !px-6 !h-12 !rounded-xl shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send size={18} />
              </button>
            </form>
          </div>
        </div>

        {/* Модалка звонка */}
        <VoiceCallModal isOpen={isCalling} onClose={handleCallEnd} />
      </div>
    </div>
  )
}