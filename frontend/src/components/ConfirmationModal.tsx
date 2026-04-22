import { X } from 'lucide-react'

interface Props {
  isOpen: boolean
  title: string
  description: string
  confirmText?: string
  cancelText?: string
  isDestructive?: boolean
  onConfirm: () => void
  onCancel: () => void
  children?: React.ReactNode
}

export function ConfirmationModal({
  isOpen,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDestructive = false,
  onConfirm,
  onCancel,
  children
}: Props) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-surface-950/80 backdrop-blur-sm">
      <div 
        className="w-full max-w-md bg-surface-900 border border-slate-700 shadow-2xl rounded-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        <div className="flex items-center justify-between p-4 border-b border-slate-700/50">
          <h2 className="text-lg font-semibold text-slate-100">{title}</h2>
          <button 
            onClick={onCancel}
            className="p-1 text-slate-400 hover:text-slate-200 hover:bg-surface-800 rounded-md transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-4 md:p-5">
          <p className="text-sm text-slate-300 mb-4">{description}</p>
          {children}
        </div>
        
        <div className="p-4 border-t border-slate-700/50 bg-surface-850 flex items-center justify-end gap-3">
          <button 
            onClick={onCancel} 
            className="btn-ghost"
          >
            {cancelText}
          </button>
          <button 
            onClick={onConfirm} 
            className={isDestructive ? 'btn-danger' : 'btn-primary'}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
