import { RefreshCw } from "lucide-react";

export default function ScanLoader() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="relative w-12 h-12 mb-4">
        <RefreshCw className="h-6 w-6 text-blue-400 animate-spin" />
      </div>
      <p className="text-sm text-slate-400">Analyzing code...</p>
    </div>
  );
}
