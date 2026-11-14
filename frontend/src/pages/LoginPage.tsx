import { useState } from 'react'
import { useAuthStore, type Role } from '@/store/authStore'
import { Ticket, User, Wrench, ArrowLeft } from 'lucide-react'

export default function LoginPage() {
  const login = useAuthStore((s) => s.login)
  const [selectedRole, setSelectedRole] = useState<Role>(null)
  
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')

  const handleRegister = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name || !phone || !password) return alert('Заполните все поля')
    
    // Имитация отправки на бэкенд
    console.log('Данные для отправки:', { name, phone, password, role: selectedRole })
    
    login({ name, phone, role: selectedRole })
  }

  // ЭКРАН 1: Выбор роли (здесь три кнопки)
  if (!selectedRole) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="bg-white p-10 rounded-2xl shadow-xl max-w-md w-full text-center">
          <h1 className="text-3xl font-bold mb-2">Dispatch<span className="text-blue-600">AI</span></h1>
          <p className="text-slate-500 mb-8">Выберите роль для входа</p>

          <div className="space-y-4">
            <button onClick={() => setSelectedRole('client')} className="w-full flex items-center justify-center gap-3 bg-emerald-600 text-white py-4 rounded-xl font-medium hover:bg-emerald-700 transition">
              <User size={20} /> Войти как Клиент
            </button>
            <button onClick={() => setSelectedRole('dispatcher')} className="w-full flex items-center justify-center gap-3 bg-blue-600 text-white py-4 rounded-xl font-medium hover:bg-blue-700 transition">
              <Ticket size={20} /> Войти как Диспетчер
            </button>
            <button onClick={() => setSelectedRole('engineer')} className="w-full flex items-center justify-center gap-3 bg-slate-800 text-white py-4 rounded-xl font-medium hover:bg-slate-900 transition">
              <Wrench size={20} /> Войти как Инженер
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ЭКРАН 2: Форма регистрации
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full">
        <button onClick={() => setSelectedRole(null)} className="text-slate-400 hover:text-slate-700 mb-6 flex items-center gap-1 text-sm">
          <ArrowLeft size={16} /> Назад к выбору роли
        </button>
        
        <h2 className="text-2xl font-bold mb-6">Регистрация ({selectedRole})</h2>
        
        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">ФИО</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="Иванов Иван" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Номер телефона</label>
            <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="+7 (999) 000-00-00" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Пароль</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full border border-slate-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" placeholder="••••••••" />
          </div>
          <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition mt-4">
            Зарегистрироваться и войти
          </button>
        </form>
      </div>
    </div>
  )
}