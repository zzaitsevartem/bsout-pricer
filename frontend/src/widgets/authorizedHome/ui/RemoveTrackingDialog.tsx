'use client';
import { useEffect, useId, useRef } from 'react';

export function RemoveTrackingDialog({
  name,
  pending,
  error,
  onCancel,
  onConfirm,
}: {
  name: string;
  pending: boolean;
  error: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = dialog.current;
    modal?.showModal();
    cancel.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      modal?.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, []);
  return (
    <dialog
      ref={dialog}
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      aria-modal="true"
      onCancel={(event) => {
        event.preventDefault();
        if (!pending) onCancel();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-[480px] rounded-[24px] border border-border-light-subtle bg-ivory p-6 text-body shadow-lg backdrop:bg-black/30 backdrop:backdrop-blur-sm"
    >
      <h3 id={titleId} className="mb-3 text-2xl font-semibold text-slate">
        Перестать отслеживать?
      </h3>
      <p id={descriptionId} className="break-words text-[15px] text-body-subtle">
        «{name}» будет удалён из отслеживания.
      </p>
      {error && (
        <p role="alert" className="mt-4 text-[14px] text-clay">
          Не удалось удалить. Попробуйте ещё раз.
        </p>
      )}
      <div className="mt-6 flex flex-wrap justify-end gap-3">
        <button
          ref={cancel}
          type="button"
          className="btn-secondary btn-sm disabled:opacity-50"
          disabled={pending}
          onClick={onCancel}
        >
          Отмена
        </button>
        <button
          type="button"
          className="btn-danger btn-sm disabled:opacity-50"
          disabled={pending}
          onClick={onConfirm}
        >
          {pending ? 'Удаляем…' : 'Удалить'}
        </button>
      </div>
    </dialog>
  );
}
