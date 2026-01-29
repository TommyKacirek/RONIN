import { useEffect, useRef, useState, useMemo } from 'react';
import {
    createChart,
    ColorType,
    CrosshairMode,
    CandlestickSeries,
    HistogramSeries,
    IChartApi,
    ISeriesApi,
    Time
} from 'lightweight-charts';

interface ChartProps {
    data: {
        candles: any[];
        volume: any[];
        meta: any;
    };
    symbol?: string;
    isMeasuring?: boolean;
    measurements?: Measurement[];
    selectedId?: string | null;
    onAddMeasure?: (measure: Measurement) => void;
    onSelectMeasure?: (measure: Measurement | null) => void;
    onClearAll?: () => void;
    colors?: {
        backgroundColor?: string;
        lineColor?: string;
        textColor?: string;
        areaTopColor?: string;
        areaBottomColor?: string;
    };
}

export interface Measurement {
    id: string;
    start: { time: Time; price: number };
    end: { time: Time; price: number };
    note?: string;
    color?: string;
}

const formatVolume = (val: number) => {
    if (val >= 1000000000) return (val / 1000000000).toFixed(2) + 'B';
    if (val >= 1000000) return (val / 1000000).toFixed(2) + 'M';
    if (val >= 1000) return (val / 1000).toFixed(2) + 'K';
    return val.toString();
};

const formatPrice = (val: number) => val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const DetailChart = (props: ChartProps) => {
    const {
        data,
        symbol,
        isMeasuring = false,
        measurements = [],
        selectedId = null,
        onAddMeasure,
        onSelectMeasure,
        onClearAll,
        colors: {
            backgroundColor = 'transparent',
            textColor = '#d4d4d8',
        } = {},
    } = props;

    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

    const [legendData, setLegendData] = useState<any>(null);
    const [activeMeasure, setActiveMeasure] = useState<{ start: { time: Time; price: number }, current: { time: Time; price: number } } | null>(null);
    const [coords, setCoords] = useState<Record<string, { x: number, y: number }>>({});

    // Coordinate mapping logic
    const updateCoords = () => {
        if (!chartRef.current || !candleSeriesRef.current) return;
        try {
            const chart = chartRef.current;
            const series = candleSeriesRef.current;
            const timeScale = chart.timeScale();
            const priceScale = series.priceScale();

            const newCoords: Record<string, { x: number, y: number }> = {};

            // Helper to map a point
            const mapPoint = (id: string, time: Time, price: number) => {
                const x = timeScale.timeToCoordinate(time);
                const y = series.priceToCoordinate(price);
                if (x !== null && y !== null) {
                    newCoords[id] = { x, y };
                }
            };

            measurements.forEach(m => {
                mapPoint(`${m.id}_start`, m.start.time, m.start.price);
                mapPoint(`${m.id}_end`, m.end.time, m.end.price);
            });

            if (activeMeasure) {
                mapPoint('active_start', activeMeasure.start.time, activeMeasure.start.price);
                mapPoint('active_end', activeMeasure.current.time, activeMeasure.current.price);
            }

            setCoords(newCoords);
        } catch (e) {
            // Chart improperly state or disposed
        }
    };

    // Trigger updateCoords when measurements or view changes
    useEffect(() => {
        updateCoords();
    }, [measurements, activeMeasure]);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: backgroundColor },
                textColor,
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.1)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.1)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: 400,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: 'rgba(197, 203, 206, 0.1)',
            },
            crosshair: {
                mode: CrosshairMode.Normal,
                vertLine: { labelBackgroundColor: '#4f46e5' },
                horzLine: { labelBackgroundColor: '#4f46e5' }
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.1)',
            },
        });

        chartRef.current = chart;

        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#22c55e',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#22c55e',
            wickDownColor: '#ef4444',
        });
        candleSeriesRef.current = candleSeries;

        const volumeSeries = chart.addSeries(HistogramSeries, {
            priceFormat: { type: 'volume' },
            priceScaleId: '',
        });

        volumeSeries.priceScale().applyOptions({
            scaleMargins: { top: 0.8, bottom: 0 },
        });

        candleSeries.setData(data.candles);
        volumeSeries.setData(data.volume);

        chart.timeScale().fitContent();

        // Legend Initial
        if (data.candles.length > 0) {
            const last = data.candles[data.candles.length - 1];
            setLegendData({ ...last, volume: data.volume[data.volume.length - 1]?.value || 0 });
        }

        // Subscriptions
        chart.subscribeCrosshairMove((param) => {
            if (param.time) {
                const candle = param.seriesData.get(candleSeries) as any;
                const volume = param.seriesData.get(volumeSeries) as any;
                if (candle) {
                    setLegendData({ ...candle, volume: volume?.value || 0 });
                }
            } else {
                const last = data.candles[data.candles.length - 1];
                setLegendData({ ...last, volume: data.volume[data.volume.length - 1]?.value || 0 });
            }
            // Update active measurement point if dragging
            if (isMeasuring && activeMeasure && param.time && param.point) {
                const price = candleSeries.coordinateToPrice(param.point.y);
                if (price) {
                    setActiveMeasure(prev => prev ? { ...prev, current: { time: param.time!, price } } : null);
                }
            }
            updateCoords();
        });

        chart.timeScale().subscribeVisibleTimeRangeChange(updateCoords);

        const handleResize = () => chart.applyOptions({ width: chartContainerRef.current!.clientWidth });
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
            chartRef.current = null;
            candleSeriesRef.current = null;
        };
    }, [data, backgroundColor, textColor, isMeasuring]);



    // Interaction Handlers for Measurement
    const handleMouseDown = (e: React.MouseEvent) => {
        if (!isMeasuring || !chartRef.current || !candleSeriesRef.current) return;

        // This is tricky because we need the chart's coordinate system. 
        // We'll use the crosshair location which we have from subscribeCrosshairMove.
        // But for MouseDown, we can force a crosshair param check if needed.
        // Actually, let's use the click flow.
    };

    const handleChartClick = (e: React.MouseEvent) => {
        if (!isMeasuring || !chartRef.current || !candleSeriesRef.current) return;

        // Since we can't easily get the crosshair data here, we'll use a hack of
        // tracking the crosshair in a ref or local state.
    };

    // Refined click logic using a transparent overlay
    const onCanvasClick = (e: React.MouseEvent) => {
        if (!isMeasuring || !chartRef.current || !candleSeriesRef.current) return;

        const rect = chartContainerRef.current!.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const time = chartRef.current.timeScale().coordinateToTime(x);
        const price = candleSeriesRef.current.coordinateToPrice(y);

        if (time && price) {
            if (!activeMeasure) {
                setActiveMeasure({ start: { time, price }, current: { time, price } });
            } else {
                // Finalize
                const newMeasure: Measurement = {
                    id: Math.random().toString(36).substr(2, 9),
                    start: activeMeasure.start,
                    end: { time, price }
                };
                if (onAddMeasure) onAddMeasure(newMeasure);
                setActiveMeasure(null);
            }
        }
    };

    const isUp = legendData ? legendData.close >= legendData.open : true;

    return (
        <div
            ref={chartContainerRef}
            className={`w-full relative group ${isMeasuring ? 'cursor-crosshair' : ''}`}
            onClick={onCanvasClick}
        >
            {/* Legend */}
            {legendData && (
                <div className="absolute top-2 left-2 z-20 flex flex-wrap gap-x-4 gap-y-1 bg-zinc-900/80 backdrop-blur-md p-3 rounded-xl border border-zinc-800/50 pointer-events-none select-none">
                    <div className="flex items-center gap-2 pr-2 border-r border-zinc-800">
                        <span className="text-sm font-bold text-white tracking-wider">{symbol}</span>
                        <span className="text-[10px] text-zinc-500 font-mono">
                            {typeof legendData.time === 'string' ? legendData.time : new Date((legendData.time as number) * 1000).toLocaleDateString()}
                        </span>
                    </div>

                    <div className="grid grid-cols-2 lg:flex lg:items-center gap-x-4 gap-y-1 font-mono text-xs">
                        <div className="flex gap-1.5"><span className="text-zinc-500 uppercase">O</span><span className="text-zinc-100">{formatPrice(legendData.open)}</span></div>
                        <div className="flex gap-1.5"><span className="text-zinc-500 uppercase">H</span><span className="text-zinc-100">{formatPrice(legendData.high)}</span></div>
                        <div className="flex gap-1.5"><span className="text-zinc-500 uppercase">L</span><span className="text-zinc-100">{formatPrice(legendData.low)}</span></div>
                        <div className="flex gap-1.5"><span className="text-zinc-500 uppercase">C</span><span className={`font-bold ${isUp ? 'text-green-500' : 'text-red-500'}`}>{formatPrice(legendData.close)}</span></div>
                        <div className="flex gap-1.5 lg:pl-4 lg:border-l lg:border-zinc-800"><span className="text-zinc-500 uppercase">Vol</span><span className="text-zinc-100">{formatVolume(legendData.volume)}</span></div>
                    </div>
                </div>
            )}

            {/* SVG Measurements Overlay */}
            <svg className="absolute inset-0 z-10 pointer-events-none w-full h-full">
                {/* Active Measurement */}
                {activeMeasure && coords.active_start && coords.active_end && (
                    <g>
                        <line
                            x1={coords.active_start.x} y1={coords.active_start.y}
                            x2={coords.active_end.x} y2={coords.active_end.y}
                            stroke="#6366f1" strokeWidth="2" strokeDasharray="4 2"
                        />
                        <circle cx={coords.active_start.x} cy={coords.active_start.y} r="4" fill="#6366f1" />
                        <circle cx={coords.active_end.x} cy={coords.active_end.y} r="4" fill="#6366f1" />
                        <rect
                            x={(coords.active_start.x + coords.active_end.x) / 2 - 30}
                            y={(coords.active_start.y + coords.active_end.y) / 2 - 12}
                            width="60" height="24" rx="6" fill="#4f46e5"
                        />
                        <text
                            x={(coords.active_start.x + coords.active_end.x) / 2}
                            y={(coords.active_start.y + coords.active_end.y) / 2 + 5}
                            textAnchor="middle" fill="white" fontSize="10" fontWeight="bold"
                        >
                            {(((activeMeasure.current.price - activeMeasure.start.price) / activeMeasure.start.price) * 100).toFixed(2)}%
                        </text>
                    </g>
                )}

                {/* Finalized Measurements */}
                {measurements.map(m => {
                    const s = coords[`${m.id}_start`];
                    const e = coords[`${m.id}_end`];
                    if (!s || !e) return null;
                    const isSelected = selectedId === m.id;
                    const pct = ((m.end.price - m.start.price) / m.start.price) * 100;
                    const color = isSelected ? "#6366f1" : "#FFD700";

                    return (
                        <g
                            key={m.id}
                            className="cursor-pointer pointer-events-auto"
                            onClick={(event) => {
                                event.stopPropagation();
                                if (onSelectMeasure) onSelectMeasure(isSelected ? null : m);
                            }}
                        >
                            <line x1={s.x} y1={s.y} x2={e.x} y2={e.y} stroke={color} strokeWidth={isSelected ? "3" : "2"} opacity={isSelected ? "1" : "0.8"} />
                            <circle cx={s.x} cy={s.y} r={isSelected ? "5" : "4"} fill={color} />
                            <circle cx={e.x} cy={e.y} r={isSelected ? "5" : "4"} fill={color} />
                            <rect
                                x={(s.x + e.x) / 2 - (isSelected ? 35 : 30)}
                                y={(s.y + e.y) / 2 - 12}
                                width={isSelected ? 70 : 60}
                                height="24" rx="6"
                                fill={isSelected ? "#312e81" : "#92400e"}
                                opacity="0.9"
                            />
                            <text x={(s.x + e.x) / 2} y={(s.y + e.y) / 2 + 5} textAnchor="middle" fill="white" fontSize={isSelected ? "11" : "10"} fontWeight="bold">
                                {pct.toFixed(2)}%
                            </text>
                        </g>
                    );
                })}
            </svg>

            {/* Hint for clear */}
            {(measurements.length > 0 || selectedId) && isMeasuring && (
                <div className="absolute bottom-2 left-2 right-2 flex justify-between items-center pointer-events-none">
                    <div className="bg-zinc-900/80 backdrop-blur p-2 rounded text-[10px] text-zinc-400 pointer-events-auto">
                        Click measurement to select/edit
                    </div>
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            if (onClearAll) onClearAll();
                        }}
                        className="px-2 py-1 bg-zinc-800 text-[10px] text-zinc-400 rounded hover:text-white pointer-events-auto"
                    >
                        Clear All
                    </button>
                </div>
            )}
        </div>
    );
};
