interface DiffPreviewProps {
  source_code: string;
  fixed_snippet: string | null;
}

export default function DiffPreview({ source_code, fixed_snippet }: DiffPreviewProps) {
  return (
    <div className="diff-wrap">
      <div className="diff-pane diff-pane-del">
        <div className="diff-header original">
          <span>Original code</span>
        </div>
        <pre className="diff-content">{source_code}</pre>
      </div>
      {fixed_snippet ? (
        <div className="diff-pane diff-pane-add">
          <div className="diff-header fixed">
            <span>Suggested fix</span>
          </div>
          <pre className="diff-content">{fixed_snippet}</pre>
        </div>
      ) : null}
    </div>
  );
}
