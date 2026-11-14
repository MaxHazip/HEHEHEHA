import type { Engineer, Ticket } from '@/types/ticket.types'

const ENGINEERS: Engineer[] = [
  { id: 1, name: 'Иван Сетевой', specialty: 'Сети и интернет' },
  { id: 2, name: 'Петр Трубопроводов', specialty: 'Сантехника' },
  { id: 3, name: 'Анна Электрикова', specialty: 'Электрика' },
]

const INITIAL_TICKETS: Ticket[] = [
  {
    id: 101,
    title: 'Нет интернета в 305 кабинете',
    aiDescription: 'Клиент сообщает об отсутствии подключения к сети. Оборудование не получает IP-адрес.',
    aiSolution: 'Необходимо проверить коммутатор на 3 этаже. Сбросить порт 12. Проверить настройки DHCP на роутере.',
    documents: ['Инструкция_по_настройке_DHCP.pdf', 'Схема_сети_3_этаж.png'],
    category: 'Интернет / Сеть',
    status: 'new',
    priority: 'high',
    assignee: ENGINEERS[0],
    createdAt: new Date().toISOString(),
  },
  {
    id: 102,
    title: 'Прорвало трубу в столовой',
    aiDescription: 'Обнаружена течь воды под раковиной. Требуется срочный вызов сантехника.',
    aiSolution: 'Перекрыть стояк в подвале. Заменить гибкую подводку и сифон под мойкой.',
    documents: ['План_трубопровода.pdf'],
    category: 'Сантехника',
    status: 'new',
    priority: 'high',
    assignee: ENGINEERS[0],
    createdAt: new Date().toISOString(),
  }
]

const getDB = (): Ticket[] => {
  const data = localStorage.getItem('mock_tickets_v2')
  if (data) return JSON.parse(data)
  localStorage.setItem('mock_tickets_v2', JSON.stringify(INITIAL_TICKETS))
  return INITIAL_TICKETS
}

const saveDB = (tickets: Ticket[]) => {
  localStorage.setItem('mock_tickets_v2', JSON.stringify(tickets))
}

const delay = (ms: number) => new Promise(res => setTimeout(res, ms))

export const ticketsApi = {
  getTickets: async (): Promise<Ticket[]> => { await delay(300); return getDB() },
  getEngineers: async (): Promise<Engineer[]> => ENGINEERS,
  
  assignEngineer: async (ticketId: number, engineer: Engineer): Promise<void> => {
    await delay(300)
    const tickets = getDB()
    saveDB(tickets.map(t => t.id === ticketId ? { ...t, assignee: engineer } : t))
  },
  
  approveTicket: async (ticketId: number): Promise<void> => {
    await delay(300)
    const tickets = getDB()
    saveDB(tickets.map(t => t.id === ticketId ? { ...t, status: 'in_progress' } : t))
  },
  
  completeTicket: async (ticketId: number): Promise<void> => {
    await delay(300)
    const tickets = getDB()
    saveDB(tickets.map(t => t.id === ticketId ? { ...t, status: 'closed' } : t))
  },

  refuseTicket: async (ticketId: number): Promise<void> => {
    await delay(300)
    const tickets = getDB()
    saveDB(tickets.map(t => t.id === ticketId ? { ...t, status: 'new', assignee: null } : t))
  },

  // НОВОЕ: Обновление текста ИИ
  updateAiDescription: async (ticketId: number, newDescription: string): Promise<void> => {
    await delay(300)
    const tickets = getDB()
    saveDB(tickets.map(t => t.id === ticketId ? { ...t, aiDescription: newDescription } : t))
  }
}