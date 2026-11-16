interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  filename?: string;
  readOnly?: boolean;
  highlightedLines?: number[];
}

export default function CodeEditor({ value, onChange, filename, readOnly, highlightedLines = [] }: CodeEditorProps) {
  const lines = value.split("\n");
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value);

  return (
    <div className="panel overflow-hidden flex flex-col">
      {filename && (
        <div className="px-4 py-2 border-b border-white/80 flex items-center justify-between text-xs text-slate-400 bg-slate-50/60">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-400" />
            <div className="w-2 h-2 rounded-full bg-amber-400" />
            <div className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="font-mono">{filename}</span>
          </div>
          <span>{lines.length} lines</span>
        </div>
      )}
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-none border-r border-white/60 bg-slate-50 text-slate-400 select-none font-mono text-xs">
          {lines.map((_, i) => (
            <div key={i} className={`h-5 w-12 flex items-center justify-end px-2 ${highlightedLines.includes(i + 1) ? "text-blue-600 font-bold" : ""}`}>
              {i + 1}
            </div>
          ))}
        </div>
        <textarea
          className="flex-1 bg-transparent w-full min-h-[400px] font-mono text-sm leading-6 px-4 py-4 outline-none resize-none text-slate-700"
          value={value}
          onChange={handleChange}
          readOnly={readOnly}
          spellCheck={false}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
        />
      </div>
    </div>
  );
}
