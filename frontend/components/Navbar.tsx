"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LucideLayoutDashboard, LucideLineChart } from "lucide-react";

export function Navbar() {
    const pathname = usePathname();

    const getLinkClass = (path: string) => {
        const isActive = pathname === path;
        return `flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${isActive
            ? "bg-indigo-500/10 text-indigo-400"
            : "text-zinc-400 hover:text-white hover:bg-zinc-900"
            }`;
    };

    return (
        <nav className="border-b border-zinc-800 bg-black/50 backdrop-blur-md sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-8 h-16 flex items-center justify-between">
                <div className="flex items-center space-x-8">
                    <Link href="/" className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                            <span className="font-mono text-sm">P1</span>
                        </div>
                        RONIN
                    </Link>

                    <div className="flex items-center space-x-2">
                        <Link href="/" className={getLinkClass("/")}>
                            <LucideLayoutDashboard size={18} />
                            <span>Dashboard</span>
                        </Link>
                        <Link href="/watchlist" className={getLinkClass("/watchlist")}>
                            <LucideLineChart size={18} />
                            <span>Watchlist</span>
                        </Link>
                        <Link href="/options" className={getLinkClass("/options")}>
                            <LucideLayoutDashboard size={18} />
                            <span>Options</span>
                        </Link>
                    </div>
                </div>
            </div>
        </nav>
    );
}
