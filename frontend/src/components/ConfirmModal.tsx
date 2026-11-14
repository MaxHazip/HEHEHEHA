import { AlertTriangle, CheckCircle, X } from 'lucide-react'

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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="glass-card max-w-sm w-full p-6 sm:p-8 relative animate-in zoom-in-95 duration-200">
        
        <button 
          onClick={onCancel}
          className="absolute top-4 right-4 text-gray-400 hover:text-black transition"
        >
          <X size={18} />
        </button>

        <div className="flex flex-col items-center text-center">
          <div className={`flex h-14 w-14 items-center justify-center rounded-2xl mb-4 ${
            confirmType === 'danger' ? 'bg-rose-50 text-rose-500' : 'bg-emerald-50 text-emerald-500'
          }`}>
            {confirmType === 'danger' ? <AlertTriangle size={28} /> : <CheckCircle size={28} />}
          </div>

          <h3 className="text-lg font-semibold text-[#222] mb-2">{title}</h3>
          <p className="text-gray-500 text-sm mb-6 leading-relaxed">
            {message}
          </p>
          
          <div className="flex w-full gap-3">
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="button-light flex-1 !h-11 !border-gray-200"
            >
              Отмена
            </button>
            <button
              onClick={onConfirm}
              disabled={isLoading}
              className={`flex-1 !h-11 flex items-center justify-center gap-2 rounded-full text-xs font-semibold text-white transition ${
                confirmType === 'danger' 
                  ? 'bg-rose-500 hover:bg-rose-600 shadow-md shadow-rose-200' 
                  : 'bg-[#242424] hover:bg-[#454545] shadow-md shadow-black/10'
              }`}
            >
              {isLoading ? 'Обработка...' : confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}