type SearchInputProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

export function SearchInput({ label, value, onChange, placeholder }: SearchInputProps) {
  return (
    <div className="max-w-md">
      <label htmlFor="search-input" className="block text-sm font-medium">
        {label}
      </label>
      <div className="relative mt-2">
        <input
          id="search-input"
          type="search"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          className="min-h-12 w-full rounded-lg border border-ink/20 bg-white px-3 py-3 pr-11 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
        />
        {value && (
          <button
            type="button"
            aria-label={`Clear ${label.toLowerCase()}`}
            onClick={() => onChange("")}
            className="absolute right-2 top-1/2 min-h-9 min-w-9 -translate-y-1/2 rounded-md text-xl leading-none text-ink/60 hover:text-ink focus:outline-none focus:ring-2 focus:ring-brand"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
