import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

const ToastContext = createContext(null);

let toastSequence = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((toastId) => {
    setToasts((currentToasts) =>
      currentToasts.filter((toast) => toast.id !== toastId),
    );
  }, []);

  const showToast = useCallback(
    (message, type = "success", duration = 3500) => {
      toastSequence += 1;
      const toastId = toastSequence;

      setToasts((currentToasts) => [
        ...currentToasts,
        {
          id: toastId,
          message,
          type,
        },
      ]);

      window.setTimeout(() => {
        removeToast(toastId);
      }, duration);

      return toastId;
    },
    [removeToast],
  );

  const value = useMemo(
    () => ({
      showToast,
      removeToast,
    }),
    [showToast, removeToast],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}

      <div
        className="fixed right-4 top-4 z-[100] flex w-[min(92vw,380px)] flex-col gap-3"
        aria-live="polite"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`rounded-2xl border px-4 py-3 shadow-lg ${
              toast.type === "error"
                ? "border-red-200 bg-red-50 text-red-800"
                : toast.type === "info"
                  ? "border-blue-200 bg-blue-50 text-blue-800"
                  : "border-teal-200 bg-white text-slate-800"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium">{toast.message}</p>

              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                className="rounded-md px-1 text-lg leading-none opacity-60 hover:opacity-100"
                aria-label="Close notification"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast must be used inside ToastProvider.");
  }

  return context;
}