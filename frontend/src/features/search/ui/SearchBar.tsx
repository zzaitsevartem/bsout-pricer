'use client';

type SearchBarProps = {
  query: string;
  onQueryChange: (q: string) => void;
  onSubmit: () => void;
};

export function SearchBar({ query, onQueryChange, onSubmit }: SearchBarProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') onSubmit();
  };

  return (
    <div className="flex gap-3 mb-6">
      <div className="relative flex-1">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-body-subtle pointer-events-none"
          width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
        >
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full pl-9 pr-3 py-[10px] text-[15px] text-slate bg-ivory border border-border-default transition-colors focus:outline-none focus:border-slate"
          placeholder="Поиск запчастей..."
        />
      </div>
      <button onClick={onSubmit} className="btn-primary whitespace-nowrap">
        Найти
      </button>
    </div>
  );
}
