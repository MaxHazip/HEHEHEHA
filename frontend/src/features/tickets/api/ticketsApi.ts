import { api } from '@/services/api'
import type { Engineer, Ticket } from '@/types/ticket.types'

export const ticketsApi = {
  // 1. Получение списка заявок
  getTickets: async (): Promise<Ticket[]> => {
    const { data } = await api.get('/tickets')
    return data
  },

  // 2. Получение списка инженеров
  getEngineers: async (): Promise<Engineer[]> => {
    // Если на бэкенде эндпоинт называется иначе (например, /users?role=engineer), поменяй здесь
    const { data } = await api.get('/engineers')
    return data
  },

  // 3. Назначение инженера на заявку
  assignEngineer: async (ticketId: number, engineer: Engineer): Promise<void> => {
    // Отправляем ID инженера на бэкенд
    await api.patch(`/tickets/${ticketId}/assign`, { assignee_id: engineer.id })
  },

  // 4. Утверждение заявки диспетчером (перевод в статус "В работе")
  approveTicket: async (ticketId: number): Promise<void> => {
    await api.patch(`/tickets/${ticketId}/status`, { status: 'in_progress' })
  },

  // 5. Завершение заявки инженером
  completeTicket: async (ticketId: number): Promise<void> => {
    await api.patch(`/tickets/${ticketId}/status`, { status: 'closed' })
  },

  // 6. Отказ инженера от заявки (возврат диспетчеру)
  refuseTicket: async (ticketId: number): Promise<void> => {
    await api.patch(`/tickets/${ticketId}/status`, { status: 'new', assignee_id: null })
  },

  // 7. Обновление текста ИИ диспетчером
  updateAiDescription: async (ticketId: number, newDescription: string): Promise<void> => {
    await api.patch(`/tickets/${ticketId}`, { aiDescription: newDescription })
  }
}