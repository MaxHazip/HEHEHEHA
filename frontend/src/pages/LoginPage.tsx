import { useState } from 'react'
import { useAuthStore, type Role } from '@/store/authStore'
import { Ticket, User, Wrench, ArrowLeft, BarChart3, LogIn, AlertCircle } from 'lucide-react'

export default function LoginPage() {
  const login = useAuthStore((s) => s.login)
  const [selectedRole, setSelectedRole] = useState<Role>(null)
  
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  
  // Состояние для ошибок валидации
  const [errors, setErrors] = useState<{ phone?: string; password?: string }>({})

  const roleNames: Record<string, string> = {
    client: 'Клиент',
    dispatcher: 'Диспетчер',
    engineer: 'Инженер',
    admin: 'Администратор'
  }

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    const newErrors: { phone?: string; password?: string } = {}

    // Валидация телефона (минимум 10 цифр)
    const phoneDigits = phone.replace(/\D/g, '')
    if (!phone) {
      newErrors.phone = 'Введите номер телефона'
    } else if (phoneDigits.length < 10) {
      newErrors.phone = 'Номер должен содержать минимум 10 цифр'
    }

    // Валидация пароля (минимум 4 символа)
    if (!password) {
      newErrors.password = 'Введите пароль'
    } else if (password.length < 4) {
      newErrors.password = 'Пароль должен быть не менее 4 символов'
    }

    setErrors(newErrors)

    // Если ошибок нет — входим
    if (Object.keys(newErrors).length === 0) {
      let defaultName = 'Пользователь'
      if (selectedRole === 'engineer') defaultName = 'Иван Сетевой'
      if (selectedRole === 'dispatcher') defaultName = 'Иван Диспетчеров'
      if (selectedRole === 'admin') defaultName = 'Администратор'
      if (selectedRole === 'client') defaultName = 'Клиент'

      login({ name: defaultName, phone, role: selectedRole })
    }
  }

  // Сброс ошибок при возврате назад
  const handleBack = () => {
    setSelectedRole(null)
    setErrors({})
    setPhone('')
    setPassword('')
  }

  if (!selectedRole) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-100">
        <div className="bg-white p-10 rounded-2xl shadow-xl max-w-md w-full text-center">
          <h1 className="text-3xl font-bold mb-2">Dispatch<span className="text-blue-600">AI</span></h1>
          <p className="text-slate-500 mb-8">Выберите роль для входа</p>

          <div className="space-y-4">
            <button onClick={() => setSelectedRole('client')} className="w-full flex items-center justify-center gap-3 bg-emerald-600 text-white py-3 rounded-xl font-medium hover:bg-emerald-700 transition">
              <User size={20} /> Войти как Клиент
            </button>
            <button onClick={() => setSelectedRole('dispatcher')} className="w-full flex items-center justify-center gap-3 bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition">
              <Ticket size={20} /> Войти как Диспетчер
            </button>
            <button onClick={() => setSelectedRole('engineer')} className="w-full flex items-center justify-center gap-3 bg-slate-800 text-white py-3 rounded-xl font-medium hover:bg-slate-900 transition">
              <Wrench size={20} /> Войти как Инженер
            </button>
            <button onClick={() => setSelectedRole('admin')} className="w-full flex items-center justify-center gap-3 bg-purple-600 text-white py-3 rounded-xl font-medium hover:bg-purple-700 transition">
              <BarChart3 size={20} /> Войти как Админ
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full">
        <button onClick={handleBack} className="text-slate-400 hover:text-slate-700 mb-6 flex items-center gap-1 text-sm">
          <ArrowLeft size={16} /> Назад к выбору роли
        </button>
        
        <h2 className="text-2xl font-bold mb-6">
          Вход: <span className="text-blue-600">{roleNames[selectedRole]}</span>
        </h2>
        
        <form onSubmit={handleLogin} className="space-y-4" noValidate>
          {/* Поле Телефона */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Номер телефона</label>
            <input 
              type="tel" 
              value={phone} 
              onChange={e => { setPhone(e.target.value); setErrors(prev => ({...prev, phone: undefined})) }} 
              className={`w-full border rounded-lg px-4 py-2 outline-none transition ${
                errors.phone ? 'border-rose-300 focus:ring-2 focus:ring-rose-200' : 'border-slate-300 focus:ring-2 focus:ring-blue-500'
              }`} 
              placeholder="+7 (999) 000-00-00" 
            />
            {errors.phone && (
              <p className="text-rose-500 text-xs mt-1 flex items-center gap-1">
                <AlertCircle size={12} /> {errors.phone}
              </p>
            )}
          </div>

          {/* Поле Пароля */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Пароль</label>
            <input 
              type="password" 
              value={password} 
              onChange={e => { setPassword(e.target.value); setErrors(prev => ({...prev, password: undefined})) }} 
              className={`w-full border rounded-lg px-4 py-2 outline-none transition ${
                errors.password ? 'border-rose-300 focus:ring-2 focus:ring-rose-200' : 'border-slate-300 focus:ring-2 focus:ring-blue-500'
              }`} 
              placeholder="••••••••" 
            />
            {errors.password && (
              <p className="text-rose-500 text-xs mt-1 flex items-center gap-1">
                <AlertCircle size={12} /> {errors.password}
              </p>
            )}
          </div>

          <button 
            type="submit" 
            disabled={!phone || !password}
            className="w-full flex justify-center items-center gap-2 bg-blue-600 text-white py-3 rounded-xl font-medium hover:bg-blue-700 transition mt-6 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <LogIn size={20} /> Войти в систему
          </button>
        </form>
      </div>
    </div>
  )
}