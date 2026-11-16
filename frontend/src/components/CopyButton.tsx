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
      className="p-2 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
      title="Copy to clipboard"
    >
      {copied ? <Check className="h-4 w-4 text-emerald-400" /> : <Clipboard className="h-4 w-4" />}
    </button>
  );
}
