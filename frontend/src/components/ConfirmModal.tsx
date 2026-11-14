import { AlertTriangle, CheckCircle } from 'lucide-react'

interface Props {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  confirmType?: 'danger' | 'success'
  onConfirm: () => void
  onCancel: () => void
  isLoading?: boolean
}

export default function ConfirmModal({ 
  isOpen, title, message, confirmText = 'Да, подтвердить', confirmType = 'danger',
  onConfirm, onCancel, isLoading 
}: Props) {
  if (!isOpen) return null

  const btnColor = confirmType === 'danger' 
    ? 'bg-rose-600 hover:bg-rose-700' 
    : 'bg-emerald-600 hover:bg-emerald-700'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6">
        <div className={`flex items-center gap-3 mb-4 ${confirmType === 'danger' ? 'text-rose-500' : 'text-emerald-500'}`}>
          {confirmType === 'danger' ? <AlertTriangle size={24} /> : <CheckCircle size={24} />}
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
        </div>
        <p className="text-slate-600 text-sm mb-6">{message}</p>
        
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100 transition"
          >
            Отмена
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition ${btnColor}`}
          >
            {isLoading ? 'Обработка...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}