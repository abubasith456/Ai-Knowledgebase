import React from 'react'

type Props = {
  onFile: (file: File) => void
  disabled?: boolean
}

export function UploadArea({ onFile, disabled }: Props) {
  const onDrop = (ev: React.DragEvent) => {
    ev.preventDefault()
    if (disabled) return
    const f = ev.dataTransfer.files?.[0]
    if (f) onFile(f)
  }
  const onChange = (ev: React.ChangeEvent<HTMLInputElement>) => {
    const f = ev.target.files?.[0]
    if (f) onFile(f)
  }
  return (
    <div
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
      className="border-2 border-dashed rounded-xl p-6 text-center bg-white/50 dark:bg-gray-900/40 hover:bg-white/70 dark:hover:bg-gray-900/60 transition"
    >
      <div className="text-sm text-gray-600 dark:text-gray-300">Drag & drop a PDF here, or click to choose</div>
      <input type="file" accept="application/pdf" className="hidden" id="file-input" onChange={onChange} />
      <label htmlFor="file-input" className="cursor-pointer inline-block mt-3 text-indigo-600">Browse</label>
    </div>
  )
}

