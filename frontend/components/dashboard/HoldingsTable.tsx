"use client";

import { useMemo, useState } from "react";
import {
    ColumnDef,
    flexRender,
    getCoreRowModel,
    useReactTable,
    getSortedRowModel,
    SortingState,
} from "@tanstack/react-table";
import { Position } from "@/app/types";
import {
    LucideStickyNote,
    LucideEyeOff,
    LucideArrowDown,
    LucideArrowUp,
    LucideTarget,
    ArrowUpDown
} from "lucide-react";
import clsx from "clsx";
import axios from "axios";
import { toast } from "sonner";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

// --- Helpers ---

const formatCurrency = (val: number, curr: string) => {
    // Basic mapping
    const map: Record<string, string> = {
        'USD': '$',
        'CZK': 'Kč ',
        'EUR': '€',
        'SEK': 'kr '
    };
    const prefix = map[curr] || curr + ' ';
    return `${prefix}${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

// --- Components ---

function ZoneViz({ current, buy, sell, target }: { current: number, buy?: number, sell?: number, target?: number }) {
    if (!target || !buy || !sell) return <div className="text-zinc-600 text-xs">-</div>;

    // Visualize position: [Buy ----- Target ----- Sell]
    // Normalize to percentage 0..100 where 0=Buy, 50=Target, 100=Sell? 
    // Or linear scale. width = sell - buy.

    const range = sell - buy;
    if (range <= 0) return null;

    // Clamped percentage
    const percent = Math.min(100, Math.max(0, ((current - buy) / range) * 100));
    const targetPercent = Math.min(100, Math.max(0, ((target - buy) / range) * 100));

    // Color
    let color = "bg-zinc-500";
    if (percent < targetPercent) color = "bg-emerald-500"; // In buy zone / below target
    if (percent > targetPercent) color = "bg-rose-500"; // In sell zone

    return (
        <div className="w-24 h-6 relative flex items-center" title={`Buy: ${buy.toFixed(1)} | Curr: ${current.toFixed(1)} | Sell: ${sell.toFixed(1)}`}>
            {/* Track */}
            <div className="w-full h-1.5 bg-zinc-800 rounded-full overflow-hidden relative">
                {/* Target Marker */}
                <div className="absolute top-0 bottom-0 w-0.5 bg-white/50 z-10" style={{ left: `${targetPercent}%` }} />
                {/* Buy Zone Highlight (optional) */}
                <div className="absolute top-0 bottom-0 left-0 bg-emerald-900/30" style={{ width: `${targetPercent}%` }} />
            </div>

            {/* Current Price Dot */}
            <div
                className={clsx("absolute w-2.5 h-2.5 rounded-full border border-black shadow z-20 transition-all", color)}
                style={{ left: `calc(${percent}% - 5px)` }}
            />
        </div>
    );
}

function EditableTargetPrice({ symbol, initialValue, onSave }: { symbol: string, initialValue?: number, onSave: (val: number) => void }) {
    const [value, setValue] = useState<string>(initialValue?.toString() || "");

    const handleBlur = () => {
        const num = parseFloat(value);
        if (!isNaN(num) && num !== initialValue) {
            onSave(num);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            (e.target as HTMLInputElement).blur();
        }
    };

    return (
        <input
            type="number"
            className="bg-transparent border border-transparent hover:border-zinc-700 focus:border-blue-500 rounded px-2 py-1 w-20 text-right text-sm outline-none transition-colors placeholder:text-zinc-700"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            placeholder="Target"
        />
    );
}

function EditableNote({ symbol, initialNote, onSave }: { symbol: string, initialNote?: string, onSave: (val: string) => void }) {
    const [note, setNote] = useState(initialNote || "");
    const [open, setOpen] = useState(false);

    const handleSave = () => {
        if (note !== initialNote) {
            onSave(note);
        }
        setOpen(false);
    };

    return (
        <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
                <button className={clsx("p-1.5 rounded hover:bg-zinc-800 transition-colors", note ? "text-yellow-500" : "text-zinc-600")}>
                    <LucideStickyNote size={16} />
                </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-3 bg-zinc-900 border border-zinc-700">
                <textarea
                    className="w-full h-24 bg-zinc-950 border border-zinc-800 rounded p-2 text-sm text-zinc-300 resize-none focus:outline-none focus:border-blue-900"
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    placeholder="Add a note..."
                />
                <div className="flex justify-end mt-2">
                    <button
                        onClick={handleSave}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded font-medium"
                    >
                        Save
                    </button>
                </div>
            </PopoverContent>
        </Popover>
    );
}


function EditableNumber({ value, onSave, placeholder, className }: { value?: number, onSave: (val: number) => void, placeholder?: string, className?: string }) {
    const [localValue, setLocalValue] = useState<string>(value?.toString() || "");

    // Sync if prop updates externally
    // useEffect(() => { if (value) setLocalValue(value.toString()) }, [value]);

    const handleBlur = () => {
        const num = parseFloat(localValue);
        if (!isNaN(num) && num !== value) {
            onSave(num);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            (e.target as HTMLInputElement).blur();
        }
    };

    return (
        <input
            type="number"
            className={clsx("bg-transparent border border-transparent hover:border-zinc-700 focus:border-blue-500 rounded px-1 py-0.5 w-[4.5rem] text-right text-xs outline-none transition-colors placeholder:text-zinc-800", className)}
            value={localValue}
            onChange={(e) => setLocalValue(e.target.value)}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "-"}
        />
    );
}

// --- Table Component ---

export function HoldingsTable({ data, currency }: { data: Position[], currency: 'USD' | 'CZK' }) {
    const [sorting, setSorting] = useState<SortingState>([]);
    const prefix = currency === 'USD' ? '$' : 'Kč ';

    const saveMetaData = async (symbol: string, field: string, value: any) => {
        try {
            await axios.post("http://localhost:8000/api/metadata", {
                symbol,
                [field]: value
            });
            toast.success(`Saved ${field}`);
        } catch (e) {
            toast.error("Failed to save metadata");
        }
    };

    const columns = useMemo<ColumnDef<Position>[]>(() => [
        {
            accessorKey: "symbol",
            header: "Ticker",
            cell: ({ row }) => (
                <div className="flex flex-col">
                    <div className="flex items-center space-x-2">
                        <span className="font-bold text-white">{row.original.symbol}</span>
                        {row.original.is_excluded && <LucideEyeOff size={12} className="text-zinc-500" />}
                    </div>
                </div>
            ),
        },
        {
            accessorKey: "name",
            header: "Name",
            cell: ({ row }) => <div className="text-zinc-500 text-xs truncate max-w-[100px]" title={row.original.name}>{row.original.name}</div>
        },
        {
            accessorKey: "current_price",
            header: () => <div className="text-right">Price</div>,
            cell: ({ row }) => {
                const src = row.original.price_source;
                return (
                    <div className="text-right flex flex-col items-end">
                        <span className={clsx("font-mono", src === 'Live' ? "text-white" : "text-amber-500")} title={`Source: ${src}`}>
                            {row.original.current_price?.toFixed(2)}
                        </span>
                        <span className="text-[10px] text-zinc-600">{row.original.currency}</span>
                    </div>
                );
            }
        },
        {
            accessorKey: "average_buy_price",
            header: () => <div className="text-right">Avg Price</div>,
            cell: ({ row }) => {
                const val = row.original.average_buy_price;
                return (
                    <div className="text-right text-zinc-400 font-mono">
                        {val ? val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) : '-'}
                    </div>
                );
            }
        },
        {
            id: "high_low",
            header: () => <div className="text-center text-xs">52W Range</div>,
            cell: ({ row }) => {
                const h = row.original.year_high;
                const l = row.original.year_low;
                const c = row.original.current_price || 0;
                if (!h || !l) return <div className="text-center text-zinc-700">-</div>;

                // Position in range
                const pct = ((c - l) / (h - l)) * 100;

                return (
                    <div className="w-20 mx-auto flex flex-col items-center">
                        <div className="w-full h-1 bg-zinc-800 rounded-full relative overflow-hidden">
                            <div className="absolute w-1.5 h-1.5 bg-blue-500 rounded-full -top-0.5" style={{ left: `${Math.min(100, Math.max(0, pct))}%` }} />
                        </div>
                        <div className="flex justify-between w-full text-[9px] text-zinc-600 mt-0.5">
                            <span>{l.toFixed(0)}</span>
                            <span>{h.toFixed(0)}</span>
                        </div>
                    </div>
                );
            }
        },
        {
            accessorKey: "quantity",
            header: () => <div className="text-right">Qty</div>,
            cell: ({ row }) => <div className="text-right text-zinc-400 font-mono text-xs">{row.original.quantity.toFixed(0)}</div>,
        },
        {
            accessorKey: "market_value_czk",
            id: "value",
            header: ({ column }) => (
                <button
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                    className="text-right w-full hover:text-white transition-colors flex items-center justify-end gap-1"
                >
                    Market Value (Kč)
                    <ArrowUpDown className="h-3 w-3" />
                </button>
            ),
            cell: ({ row }) => {
                const value = row.original.market_value_czk;
                const formatted = Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 0 });
                return (
                    <div className={`text-right font-medium ${value >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {value >= 0 ? '' : '-'}{formatted}
                    </div>
                );
            }
        },
        {
            accessorKey: "pct_portfolio",
            header: () => <div className="text-right">% Port</div>,
            cell: ({ row }) => {
                const val = row.original.pct_portfolio;
                return <div className="text-right text-xs text-zinc-400">{val ? val.toFixed(2) + '%' : '-'}</div>;
            }
        },
        {
            accessorKey: "unrealized_pnl_czk",
            header: () => (
                <div className="text-right group relative cursor-help">
                    <span className="border-b border-dotted border-zinc-500">PIYC</span>
                    <div className="absolute top-full right-0 mt-2 w-32 p-2 bg-zinc-900 border border-zinc-700 rounded text-xs text-zinc-300 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none">
                        Profit In Your Currency (includes FX impact)
                    </div>
                </div>
            ),
            cell: ({ row }) => {
                const val = row.original.unrealized_pnl_czk;
                const cost = row.original.cost_basis_czk;
                const pct = (cost && cost !== 0) ? (val / cost) * 100 : 0;

                return (
                    <div className="flex flex-col items-end">
                        <div className={clsx("font-medium", val >= 0 ? "text-emerald-500" : "text-rose-500")}>
                            {val > 0 ? "+" : ""}{val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                        </div>
                        <span className={clsx("text-[10px]", pct >= 0 ? "text-emerald-500/70" : "text-rose-500/70")}>
                            {pct > 0 ? "+" : ""}{pct.toFixed(1)}%
                        </span>
                    </div>
                );
            },
        },
        {
            accessorKey: "unrealized_pnl_native",
            header: () => <div className="text-right">Asset Profit</div>,
            cell: ({ row }) => {
                const val = row.original.unrealized_pnl_native;
                const pct = row.original.pnl_percent;
                const curr = row.original.currency;

                if (val === undefined) return <div className="text-right text-zinc-600">-</div>;

                return (
                    <div className="flex flex-col items-end">
                        <div className={clsx("font-medium", val >= 0 ? "text-emerald-400" : "text-rose-400")}>
                            {val > 0 ? "+" : ""}{val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} <span className="text-[10px] opacity-70">{curr}</span>
                        </div>
                        {pct !== undefined && (
                            <span className={clsx("text-[10px]", pct >= 0 ? "text-emerald-400/70" : "text-rose-400/70")}>
                                {pct > 0 ? "+" : ""}{pct.toFixed(1)}%
                            </span>
                        )}
                    </div>
                );
            },
        },

        // --- PLANNING SECTION --- 

        {
            accessorKey: "buy_zone",
            header: "Buy Zone",
            cell: ({ row }) => (
                <EditableNumber
                    value={row.original.buy_zone}
                    placeholder="Buy"
                    onSave={(val) => saveMetaData(row.original.symbol, "buy_zone", val)}
                    className="text-emerald-300"
                />
            )
        },
        {
            accessorKey: "sell_zone",
            header: "Sell Zone",
            cell: ({ row }) => (
                <EditableNumber
                    value={row.original.sell_zone}
                    placeholder="Sell"
                    onSave={(val) => saveMetaData(row.original.symbol, "sell_zone", val)}
                    className="text-rose-300"
                />
            )
        },
        {
            accessorKey: "target_price",
            header: "Target",
            cell: ({ row }) => (
                <EditableNumber
                    value={row.original.target_price}
                    placeholder="Target"
                    onSave={(val) => saveMetaData(row.original.symbol, "target_price", val)}
                />
            )
        },
        {
            accessorKey: "risk_score",
            header: "Risk",
            cell: ({ row }) => (
                <EditableNumber
                    value={row.original.risk_score}
                    placeholder="1-10"
                    onSave={(val) => saveMetaData(row.original.symbol, "risk_score", val)}
                    className="text-yellow-200"
                />
            )
        },
        {
            accessorKey: "instruction",
            header: "Instruct",
            size: 80, // Explicit size
            cell: ({ row }) => {
                const inst = row.original.instruction || "Hold";
                let color = "text-yellow-400 bg-yellow-400/10";
                if (inst === "Buy") color = "text-emerald-400 bg-emerald-400/10";
                else if (inst !== "Hold") color = "text-rose-400 bg-rose-400/10";

                return <div className="flex justify-center"><span className={clsx("px-2 py-0.5 rounded text-xs font-bold", color)}>{inst}</span></div>
            }
        },
        {
            id: "actions",
            header: "",
            cell: ({ row }) => (
                <div className="flex justify-end">
                    <EditableNote
                        symbol={row.original.symbol}
                        initialNote={row.original.notes}
                        onSave={(val) => saveMetaData(row.original.symbol, "notes", val)}
                    />
                </div>
            )
        }
    ], [currency]);

    const table = useReactTable({
        data,
        columns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        onSortingChange: setSorting,
        state: {
            sorting,
        },
    });

    return (
        <div className="w-full overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900/50">
            <table className="w-full text-sm">
                <thead className="bg-zinc-900 text-zinc-400">
                    {table.getHeaderGroups().map((headerGroup) => (
                        <tr key={headerGroup.id}>
                            {headerGroup.headers.map((header) => (
                                <th key={header.id} className="px-4 py-3 font-medium text-left cursor-pointer hover:text-white" onClick={header.column.getToggleSortingHandler()}>
                                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody className="divide-y divide-zinc-800">
                    {table.getRowModel().rows.map((row) => (
                        <tr key={row.id} className={clsx(
                            "transition-colors",
                            row.original.is_simulated ? "bg-blue-900/20 border-blue-500/30 border-dashed" : "hover:bg-zinc-800/30",
                            row.original.is_excluded && "opacity-50 grayscale"
                        )}>
                            {row.getVisibleCells().map((cell) => (
                                <td key={cell.id} className="px-4 py-2">
                                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
