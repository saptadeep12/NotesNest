import { useRef } from "react";

type Tab = { id: string; label: string; count: number };

type TabsProps = {
  tabs: Tab[];
  selected: string;
  onChange: (id: string) => void;
};

export function Tabs({ tabs, selected, onChange }: TabsProps) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  return (
    <div role="tablist" aria-label="Resource type" className="flex gap-6 border-b border-ink/20">
      {tabs.map((tab, index) => (
        <button
          key={tab.id}
          id={`${tab.id}-tab`}
          type="button"
          role="tab"
          aria-selected={selected === tab.id}
          aria-controls={`${tab.id}-panel`}
          tabIndex={selected === tab.id ? 0 : -1}
          onClick={() => onChange(tab.id)}
          onKeyDown={(event) => {
            if (event.key === "ArrowRight") {
              event.preventDefault();
              const next = (index + 1 + tabs.length) % tabs.length;
              onChange(tabs[next].id);
              tabRefs.current[next]?.focus();
            }
            if (event.key === "ArrowLeft") {
              event.preventDefault();
              const next = (index - 1 + tabs.length) % tabs.length;
              onChange(tabs[next].id);
              tabRefs.current[next]?.focus();
            }
            if (event.key === "Home" || event.key === "End") {
              event.preventDefault();
              const next = event.key === "Home" ? 0 : tabs.length - 1;
              onChange(tabs[next].id);
              tabRefs.current[next]?.focus();
            }
          }}
          ref={(element) => {
            tabRefs.current[index] = element;
          }}
          className={`min-h-11 border-b-2 px-1 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 ${
            selected === tab.id
              ? "border-brand text-brand"
              : "border-transparent text-ink/75 hover:text-ink"
          }`}
        >
          {tab.label} <span className="ml-1 text-xs">({tab.count})</span>
        </button>
      ))}
    </div>
  );
}
