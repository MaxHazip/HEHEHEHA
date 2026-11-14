import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ticketsApi } from '../api/ticketsApi'
import type { Engineer } from '@/types/ticket.types'

export function useTickets() {
  return useQuery({ queryKey: ['tickets'], queryFn: ticketsApi.getTickets })
}

export function useEngineers() {
  return useQuery({ queryKey: ['engineers'], queryFn: ticketsApi.getEngineers, staleTime: Infinity })
}

export function useAssignEngineer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ ticketId, engineer }: { ticketId: number; engineer: Engineer }) => 
      ticketsApi.assignEngineer(ticketId, engineer),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tickets'] }),
  })
}

export function useApproveTicket() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ticketId: number) => ticketsApi.approveTicket(ticketId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tickets'] }),
  })
}

export function useCompleteTicket() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ticketId: number) => ticketsApi.completeTicket(ticketId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tickets'] }),
  })
}

// НОВЫЙ ХУК: Отказ от задачи
export function useRefuseTicket() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (ticketId: number) => ticketsApi.refuseTicket(ticketId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tickets'] }),
  })
}