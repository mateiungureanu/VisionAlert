import { useEffect, useRef, useState } from 'react';
import { normalizeText } from '../text';

export default function FilterDropdown({
  label,
  allLabel,
  options,
  selectedIds,
  onChange,
  searchable = false,
  searchPlaceholder = 'Caută...',
  emptyText = 'Nicio opțiune găsită.',
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const rootRef = useRef(null);
  const searchRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    searchRef.current?.focus();

    function handlePointerDown(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) setOpen(false);
    }
    function handleKeyDown(event) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const normalizedQuery = normalizeText(query.trim());
  const visibleOptions = normalizedQuery
    ? options.filter((option) => normalizeText(option.name).includes(normalizedQuery))
    : options;
  const selectedOptions = options.filter((option) => selectedIds.includes(option.id));

  let summary = allLabel;
  if (selectedOptions.length === 1) summary = selectedOptions[0].name;
  else if (selectedOptions.length > 1) {
    summary = `${selectedOptions[0].name} +${selectedOptions.length - 1}`;
  }

  function toggle(optionId) {
    onChange(
      selectedIds.includes(optionId)
        ? selectedIds.filter((id) => id !== optionId)
        : [...selectedIds, optionId],
    );
  }

  return (
    <div className="store-filter" ref={rootRef}>
      <button
        className={`store-filter-chip${selectedOptions.length ? ' selected' : ''}`}
        type="button"
        aria-haspopup="true"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="store-filter-label">{label}:</span> {summary}
        <span className="store-filter-caret" aria-hidden="true">▾</span>
      </button>

      {open && (
        <div className="store-filter-menu" role="group" aria-label={`Filtrează după ${label.toLowerCase()}`}>
          {searchable && (
            <input
              ref={searchRef}
              className="store-filter-search"
              type="search"
              placeholder={searchPlaceholder}
              aria-label={searchPlaceholder.replace(/\.+$/, '')}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          )}
          <label className="store-filter-option">
            <input
              type="checkbox"
              checked={selectedIds.length === 0}
              onChange={() => onChange([])}
            />
            <span>{allLabel}</span>
          </label>
          <div className="store-filter-list">
            {visibleOptions.map((option) => (
              <label className="store-filter-option" key={option.id}>
                <input
                  type="checkbox"
                  checked={selectedIds.includes(option.id)}
                  onChange={() => toggle(option.id)}
                />
                <span>{option.name}</span>
                <span className="store-filter-count">{option.count}</span>
              </label>
            ))}
            {visibleOptions.length === 0 && (
              <p className="store-filter-empty">{emptyText}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
