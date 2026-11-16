import React from "react";
import { Clipboard, Check } from "lucide-react";

interface CopyButtonProps { text: string; }

export default function CopyButton({ text }: CopyButtonProps) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      onClick={handleCopy}
      className="copy-btn"
      title="Copy code"
    >
      {copied ? <Check className="h-3 w-3" /> : <Clipboard className="h-3 w-3" />}
      <span>{copied ? "Copied" : "Copy code"}</span>
    </button>
  );
}
