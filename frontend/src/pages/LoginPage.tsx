import { useState } from 'react'
import { useAuthStore, type Role } from '@/store/authStore'
import {
  Ticket,
  User,
  Wrench,
  ArrowRight,
  ArrowLeft,
  BarChart3,
  LogIn,
  AlertCircle,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

const roles = [
  {
    id: 'client',
    label: 'Клиент',
    description: 'Создание обращений и связь с поддержкой',
    icon: User,
  },
  {
    id: 'dispatcher',
    label: 'Диспетчер',
    description: 'Обработка заявок и управление звонками',
    icon: Ticket,
  },
  {
    id: 'engineer',
    label: 'Инженер',
    description: 'Выполнение назначенных задач',
    icon: Wrench,
  },
  {
    id: 'admin',
    label: 'Администратор',
    description: 'Контроль и аналитика системы',
    icon: BarChart3,
  },
] as const

const roleNames: Record<string, string> = {
  client: 'Клиент',
  dispatcher: 'Диспетчер',
  engineer: 'Инженер',
  admin: 'Администратор',
}

const defaultNames: Record<string, string> = {
  engineer: 'Иван Сетевой',
  dispatcher: 'Иван Диспетчеров',
  admin: 'Администратор',
  client: 'Клиент',
}

export default function LoginPage() {
  const login = useAuthStore((state) => state.login)

  const [selectedRole, setSelectedRole] = useState<Role>(null)
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{
    phone?: string
    password?: string
  }>({})

  const handleLogin = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const nextErrors: typeof errors = {}
    const phoneDigits = phone.replace(/\D/g, '')

    if (!phone.trim()) {
      nextErrors.phone = 'Введите номер телефона'
    } else if (phoneDigits.length < 10) {
      nextErrors.phone = 'Введите корректный номер телефона'
    }

    if (!password) {
      nextErrors.password = 'Введите пароль'
    } else if (password.length < 4) {
      nextErrors.password = 'Минимальная длина пароля — 4 символа'
    }

    setErrors(nextErrors)

    if (Object.keys(nextErrors).length > 0 || !selectedRole) {
      return
    }

    login({
      name: defaultNames[selectedRole],
      phone,
      role: selectedRole,
    })
  }

  const handleBack = () => {
    setSelectedRole(null)
    setPhone('')
    setPassword('')
    setErrors({})
    setShowPassword(false)
  }

  return (
    <div className="app-background flex min-h-screen items-center justify-center p-4 sm:p-8">
      <div className="relative z-10 grid w-full max-w-6xl overflow-hidden rounded-[32px] border border-white/80 bg-white/30 shadow-[0_25px_90px_rgba(0,0,0,0.08)] backdrop-blur-2xl lg:min-h-[650px] lg:grid-cols-[1.05fr_0.95fr]">

        {/* Левая информационная панель */}

        <div className="relative hidden flex-col justify-between overflow-hidden bg-[#242424] p-10 text-white lg:flex">
          <div className="absolute -right-36 -top-32 h-[420px] w-[420px] rounded-full border border-white/10" />
          <div className="absolute -right-20 -top-16 h-[300px] w-[300px] rounded-full border border-white/10" />
          <div className="absolute -bottom-36 -left-32 h-[400px] w-[400px] rounded-full border border-white/10" />

          <div className="relative flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-white text-[#222]">
              <span className="text-xl font-bold">D</span>
            </div>

            <div>
              <div className="text-xl font-semibold tracking-tight">
                DispatchAI
              </div>
              <div className="text-[10px] tracking-[2px] text-white/40">
                OPERATIONS PLATFORM
              </div>
            </div>
          </div>

          <div className="relative max-w-md">
            <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10">
              <Sparkles size={23} />
            </div>

            <h1 className="text-5xl font-semibold leading-[1.12] tracking-[-2px]">
              Контроль.
              <br />
              Скорость.
              <br />
              <span className="text-white/40">Результат.</span>
            </h1>

            <p className="mt-6 max-w-sm text-sm leading-7 text-white/50">
              Единое пространство для обработки обращений, взаимодействия
              специалистов и интеллектуальной автоматизации.
            </p>

            <div className="mt-10 flex items-center gap-3 border-t border-white/10 pt-6">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10">
                <ShieldCheck size={17} />
              </div>

              <div>
                <div className="text-xs font-medium">
                  Рабочее пространство DispatchAI
                </div>
                <div className="mt-1 text-[10px] text-white/40">
                  Единая система управления обращениями
                </div>
              </div>
            </div>
          </div>

          <div className="relative flex items-center justify-between text-[10px] text-white/35">
            <span>DISPATCHAI</span>
            <span>WORKSPACE · 2026</span>
          </div>
        </div>

        {/* Правая панель авторизации */}

        <div className="flex flex-col justify-center bg-white/75 p-6 sm:p-10 lg:p-12">
          <div className="mb-10 flex items-center gap-3 lg:hidden">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-[#242424] text-white">
              <span className="font-bold">D</span>
            </div>

            <span className="text-xl font-semibold">
              DispatchAI
            </span>
          </div>

          {!selectedRole ? (
            <>
              <div className="mb-8">
                <div className="mb-3 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
                  Добро пожаловать
                </div>

                <h2 className="text-3xl font-semibold tracking-tight text-[#222]">
                  Выберите роль
                </h2>

                <p className="mt-3 text-sm leading-6 text-gray-400">
                  Укажите, в каком качестве вы хотите войти в систему.
                </p>
              </div>

              <div className="space-y-3">
                {roles.map(({ id, label, description, icon: Icon }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setSelectedRole(id as Role)}
                    className="group flex w-full items-center gap-4 rounded-2xl border border-gray-100 bg-white p-4 text-left transition duration-200 hover:-translate-y-0.5 hover:border-gray-300 hover:shadow-lg hover:shadow-black/[0.035]"
                  >
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-[#f2f2f2] text-[#333] transition group-hover:bg-[#242424] group-hover:text-white">
                      <Icon size={20} strokeWidth={1.7} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-semibold text-[#222]">
                        {label}
                      </div>

                      <div className="mt-1 text-xs leading-5 text-gray-400">
                        {description}
                      </div>
                    </div>

                    <ArrowRight
                      size={17}
                      className="shrink-0 text-gray-300 transition group-hover:translate-x-1 group-hover:text-black"
                    />
                  </button>
                ))}
              </div>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleBack}
                className="mb-9 flex w-fit items-center gap-2 text-xs font-medium text-gray-400 transition hover:text-black"
              >
                <ArrowLeft size={15} />
                Вернуться к выбору роли
              </button>

              <div className="mb-8">
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#242424] text-white">
                  {selectedRole === 'client' && <User size={23} />}
                  {selectedRole === 'dispatcher' && <Ticket size={23} />}
                  {selectedRole === 'engineer' && <Wrench size={23} />}
                  {selectedRole === 'admin' && <BarChart3 size={23} />}
                </div>

                <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
                  Авторизация
                </div>

                <h2 className="text-3xl font-semibold tracking-tight text-[#222]">
                  {roleNames[selectedRole]}
                </h2>

                <p className="mt-2 text-sm text-gray-400">
                  Введите данные для входа в систему.
                </p>
              </div>

              <form
                onSubmit={handleLogin}
                className="space-y-5"
                noValidate
              >
                <div>
                  <label
                    htmlFor="login-phone"
                    className="mb-2 block text-xs font-semibold text-gray-500"
                  >
                    Номер телефона
                  </label>

                  <input
                    id="login-phone"
                    type="tel"
                    autoComplete="tel"
                    value={phone}
                    onChange={(event) => {
                      setPhone(event.target.value)
                      setErrors((previous) => ({
                        ...previous,
                        phone: undefined,
                      }))
                    }}
                    placeholder="+7 (999) 000-00-00"
                    className={`glass-input h-12 ${
                      errors.phone ? 'border-red-400' : ''
                    }`}
                  />

                  {errors.phone && (
                    <p className="mt-2 flex items-center gap-2 text-xs text-red-500">
                      <AlertCircle size={13} />
                      {errors.phone}
                    </p>
                  )}
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label
                      htmlFor="login-password"
                      className="text-xs font-semibold text-gray-500"
                    >
                      Пароль
                    </label>
                  </div>

                  <div className="relative">
                    <input
                      id="login-password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      value={password}
                      onChange={(event) => {
                        setPassword(event.target.value)
                        setErrors((previous) => ({
                          ...previous,
                          password: undefined,
                        }))
                      }}
                      placeholder="Введите пароль"
                      className={`glass-input h-12 pr-20 ${
                        errors.password ? 'border-red-400' : ''
                      }`}
                    />

                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-gray-400 hover:text-black"
                    >
                      {showPassword ? 'Скрыть' : 'Показать'}
                    </button>
                  </div>

                  {errors.password && (
                    <p className="mt-2 flex items-center gap-2 text-xs text-red-500">
                      <AlertCircle size={13} />
                      {errors.password}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={!phone || !password}
                  className="button-dark mt-3 h-12 w-full disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <LogIn size={16} />
                  Войти в систему
                  <ArrowRight size={16} />
                </button>
              </form>
            </>
          )}

          <div className="mt-10 border-t border-gray-100 pt-5 text-center text-[10px] text-gray-400">
            DispatchAI · Система управления обращениями
          </div>
        </div>
      </div>
    </div>
  )
}