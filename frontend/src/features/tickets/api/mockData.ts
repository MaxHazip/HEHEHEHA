import type { Engineer, Ticket } from '@/types/ticket.types'

export const ENGINEERS: Engineer[] = [
  { id: 1, name: 'Иван Сетевой', specialty: 'Сети и интернет' },
  { id: 2, name: 'Петр Трубопроводов', specialty: 'Сантехника' },
  { id: 3, name: 'Анна Электрикова', specialty: 'Электрика' },
  { id: 4, name: 'Олег Софтов', specialty: 'Программное обеспечение' },
]

export const MOCK_TICKETS: Ticket[] = [
  {
    id: 101,
    title: 'Нет интернета в 305 кабинете',
    aiDescription: 'Клиент сообщает об отсутствии подключения к сети. Оборудование не получает IP-адрес. Требуется проверка коммутатора.',
    category: 'Интернет / Сеть',
    status: 'new',
    priority: 'high',
    assignee: ENGINEERS[0], // ИИ назначил сетевого инженера
    createdAt: new Date().toISOString(),
  },
  {
    id: 102,
    title: 'Прорвало трубу в столовой',
    aiDescription: 'Обнаружена течь воды под раковиной. Требуется срочный вызов сантехника.',
    category: 'Сантехника',
    status: 'new',
    priority: 'high',
    // ИИ ошибся и назначил сетевого инженера (чтобы диспетчер мог поменять)
    assignee: ENGINEERS[0], 
    createdAt: new Date().toISOString(),
  }
]