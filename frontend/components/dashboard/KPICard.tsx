import { LucideIcon } from "lucide-react";

interface KPICardProps {
    title: string;
    value: string;
    subValue: string;
    icon: LucideIcon;
    details?: React.ReactNode[];
}

export function KPICard({ title, value, subValue, icon: Icon, details }: KPICardProps) {
    return (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex flex-col justify-between hover:border-zinc-700 transition-colors relative group">
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-zinc-400 text-sm font-medium">{title}</p>
                    <h3 className="text-3xl font-bold text-white mt-2">{value}</h3>
                    <p className="text-zinc-500 text-xs mt-1">{subValue}</p>
                </div>
                <div className="p-2 bg-zinc-800 rounded-lg text-zinc-400">
                    <Icon size={20} />
                </div>
            </div>

            {/* Extended Details (Tooltip/Expandable) */}
            {details && details.length > 0 && (
                <div className="mt-4 pt-4 border-t border-zinc-800/50 space-y-1">
                    {details.map((line, i) => (
                        <div key={i} className="text-xs font-mono">{line}</div>
                    ))}
                </div>
            )}
        </div>
    );
}
