import { useState } from 'react'
import { useEngineers } from '@/features/tickets/hooks/useTickets'
import { Search, UserCircle2, Wrench, Phone, SlidersHorizontal, X, Users } from 'lucide-react'

export default function EngineersPage() {
  const { data: engineers = [], isLoading } = useEngineers()
  
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSpecialty, setSelectedSpecialty] = useState('Все')

  const specialties = ['Все', ...Array.from(new Set(engineers.map(e => e.specialty)))]

  const filteredEngineers = engineers.filter(eng => {
    const matchesSearch = eng.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesSpecialty = selectedSpecialty === 'Все' || eng.specialty === selectedSpecialty
    return matchesSearch && matchesSpecialty
  })

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center">
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-gray-200 border-t-black" />
          Загружаем список исполнителей...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 pb-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[2px] text-gray-400">
            Управление командой
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[#222]">
            Все исполнители
          </h1>
          <p className="mt-2 text-sm text-gray-400">
            Список инженеров, их специализации и возможность связи.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-full border border-white bg-white/70 px-4 py-2.5 text-xs text-gray-500 shadow-sm">
          <Users size={15} />
          Всего в системе: {engineers.length}
        </div>
      </div>

      <section className="glass-card p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="relative w-full lg:max-w-sm">
            <Search size={17} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Поиск по ФИО инженера..."
              className="glass-input h-11 pl-11 pr-10"
              style={{ paddingLeft: '42px' }}
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-black"
              >
                <X size={15} />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <SlidersHorizontal size={15} className="mr-1 text-gray-400" />
            <select
              value={selectedSpecialty}
              onChange={(e) => setSelectedSpecialty(e.target.value)}
              className="glass-input h-11 w-full sm:w-[220px] cursor-pointer"
            >
              {specialties.map(spec => (
                <option key={spec} value={spec}>{spec}</option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {filteredEngineers.length === 0 ? (
        <div className="glass-card flex min-h-[280px] flex-col items-center justify-center p-8 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gray-100">
            <UserCircle2 size={24} className="text-gray-400" />
          </div>
          <h3 className="text-base font-semibold text-[#222]">Никого не нашли</h3>
          <p className="mt-2 max-w-sm text-sm leading-6 text-gray-400">
            Попробуйте изменить поисковый запрос или выбрать другую специализацию.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {filteredEngineers.map(eng => (
            <div key={eng.id} className="glass-card p-5 flex flex-col gap-4 group hover:-translate-y-1 hover:border-gray-300 transition duration-200">
              <div className="flex items-start gap-4">
                <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-[#f2f2f2] text-[#333] transition group-hover:bg-[#242424] group-hover:text-white">
                  <UserCircle2 size={28} strokeWidth={1.5} />
                </div>
                <div>
                  <h3 className="font-semibold text-[#222] text-lg leading-tight">{eng.name}</h3>
                  <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-1.5">
                    <Wrench size={14} />
                    {eng.specialty}
                  </div>
                </div>
              </div>
              
              <div className="pt-4 border-t border-gray-100 flex items-center justify-between mt-auto">
                <span className="flex items-center gap-1.5 text-[10px] font-semibold text-gray-600 bg-gray-100 px-2.5 py-1.5 rounded-md">
                  <span className="h-1.5 w-1.5 rounded-full bg-[#8da995]" />
                  В сети
                </span>
                <button className="text-gray-400 hover:text-black transition flex items-center gap-1.5 text-xs font-medium">
                  <Phone size={14} /> Позвонить
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}