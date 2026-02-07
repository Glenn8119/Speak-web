interface ConfirmModalProps {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmModal({
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel
}: ConfirmModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 animate-fade-in"
      onClick={onCancel}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-sm mx-4 shadow-xl animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-5">
          <h2 className="text-lg font-semibold text-gray-100 mb-2">{title}</h2>
          <p className="text-sm text-gray-400">{message}</p>
        </div>

        <div className="flex gap-3 p-4 pt-0">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors cursor-pointer"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-colors cursor-pointer"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
