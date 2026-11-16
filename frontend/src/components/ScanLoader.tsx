import { RefreshCw } from "lucide-react";

export default function ScanLoader() {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <div className="relative w-14 h-14 mb-5">
        <RefreshCw className="h-6 w-6 text-blue-500 animate-spin" />
      </div>
      <p className="text-sm font-medium text-slate-600">Analyzing code...</p>
    </div>
  );
}
