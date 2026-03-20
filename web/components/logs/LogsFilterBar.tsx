"use client";

type AgentOption = {
  id: string;
  name: string;
};

type Filters = {
  agent: string;
  status: string;
  service: string;
  range: string;
};

type LogsFilterBarProps = {
  agents: AgentOption[];
  filters: Filters;
  onFilterChange: (key: keyof Filters, value: string) => void;
  onClear: () => void;
  showClear: boolean;
};

const rangeOptions = [
  { label: "Last 1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
  { label: "7d", value: "7d" }
];

const selectClassName =
  "h-8 rounded-[6px] border border-brand-border bg-brand-card px-3 text-[13px] text-[#a1a1aa] outline-none transition-colors focus:border-[#3f3f46] focus:ring-1 focus:ring-[#3f3f46]";

export function LogsFilterBar({
  agents,
  filters,
  onFilterChange,
  onClear,
  showClear
}: LogsFilterBarProps) {
  return (
    <div className="mb-5 flex flex-wrap items-center gap-2">
      <select
        value={filters.agent}
        onChange={(event) => onFilterChange("agent", event.target.value)}
        className={`${selectClassName} min-w-[170px]`}
      >
        <option value="">All agents</option>
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name}
          </option>
        ))}
      </select>
      <select
        value={filters.status}
        onChange={(event) => onFilterChange("status", event.target.value)}
        className={`${selectClassName} min-w-[140px]`}
      >
        <option value="">All statuses</option>
        <option value="allowed">Allowed</option>
        <option value="blocked">Blocked</option>
      </select>
      <select
        value={filters.service}
        onChange={(event) => onFilterChange("service", event.target.value)}
        className={`${selectClassName} min-w-[140px]`}
      >
        <option value="">All services</option>
        <option value="openai">OpenAI</option>
        <option value="anthropic">Anthropic</option>
        <option value="github">GitHub</option>
      </select>
      <div className="flex h-8 overflow-hidden rounded-[6px] border border-brand-border bg-brand-card">
        {rangeOptions.map((option) => {
          const active = filters.range === option.value;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => onFilterChange("range", option.value)}
              className={`border-r border-brand-border px-3 text-[13px] last:border-r-0 ${
                active ? "bg-brand-subtle text-white" : "text-[#a1a1aa] hover:bg-brand-elevated"
              }`}
            >
              {option.label}
            </button>
          );
        })}
      </div>
      {showClear ? (
        <button
          type="button"
          onClick={onClear}
          className="text-[13px] text-[#a1a1aa] transition-colors hover:text-white"
        >
          Clear filters
        </button>
      ) : null}
    </div>
  );
}
