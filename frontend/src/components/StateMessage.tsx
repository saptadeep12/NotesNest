type StateMessageProps = {
  title: string;
  description?: string;
  action?: { label: string; onClick: () => void };
  tone?: "default" | "error";
};

export function StateMessage({
  title,
  description,
  action,
  tone = "default",
}: StateMessageProps) {
  return (
    <div
      className={`rounded-xl border px-5 py-8 ${
        tone === "error"
          ? "border-red-200 bg-red-50 text-red-900"
          : "border-ink/10 bg-white"
      }`}
      role={tone === "error" ? "alert" : undefined}
    >
      <p className="font-medium">{title}</p>
      {description && <p className="mt-1 text-sm opacity-80">{description}</p>}
      {action && (
        <button
          type="button"
          onClick={action.onClick}
          className="mt-4 min-h-11 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-dark focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
