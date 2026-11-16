interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  filename?: string;
  readOnly?: boolean;
}

export default function CodeEditor({ value, onChange, filename, readOnly }: CodeEditorProps) {
  const lines = value.split("\n");
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => onChange(e.target.value);

  return (
    <div className="editor-wrap">
      {filename && (
        <div className="border-b border-code-border bg-[#eef0f3] px-3 py-2 flex items-center justify-between text-xs font-mono text-slate-500">
          <span>{filename}</span>
          <span>{lines.length} lines</span>
        </div>
      )}
      <div className="flex h-full min-h-[260px]">
        <div className="editor-gutter">
          {lines.map((_, i) => (
            <div key={i} className="editor-gutter-line">
              {i + 1}
            </div>
          ))}
        </div>
        <textarea
          className="editor-textarea"
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
