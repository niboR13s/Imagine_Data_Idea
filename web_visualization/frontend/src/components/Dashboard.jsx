import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { FitnessChart, ErrorsChart, TimeChart, CorrelationChart, RMSEChart } from './Charts';
import AlignmentViewer from './AlignmentViewer';
import clsx from 'clsx';
import * as THREE from 'three';

const Dashboard = ({ data, detailedData, fetchDetailed, detailedLoading, fetchScanPoints, fetchGTRow }) => {
    const sensors = useMemo(() => [...new Set(data.map(d => d.Sensor))], [data]);
    const [selectedSensor, setSelectedSensor] = useState(sensors[0] || '');

    // 3D View States
    const [selectedSample, setSelectedSample] = useState(0);
    const [isAligned, setIsAligned] = useState(false);
    const [scanPoints, setScanPoints] = useState([]);
    const [refPoints, setRefPoints] = useState([]);
    const [gtData, setGtData] = useState(null);
    const [viewType, setViewType] = useState('charts'); // 'charts' or 'alignment'
    const [pointsLoading, setPointsLoading] = useState(false);

    // Manual Alignment States
    const [manualTransform, setManualTransform] = useState({
        tx: 0, ty: 0, tz: 0,
        rx: 0, ry: 0, rz: 0
    });

    const resetManual = () => setManualTransform({ tx: 0, ty: 0, tz: 0, rx: 0, ry: 0, rz: 0 });

    // Update selected sensor when data changes
    useEffect(() => {
        if (sensors.length > 0 && !sensors.includes(selectedSensor)) {
            setSelectedSensor(sensors[0]);
        }
    }, [sensors, selectedSensor]);

    useEffect(() => {
        if (selectedSensor) {
            fetchDetailed(selectedSensor);
        }
    }, [selectedSensor, fetchDetailed]);

    // Positions for the current sensor
    const positions = useMemo(() => {
        return [...new Set(data.filter(d => d.Sensor === selectedSensor).map(d => d.Position))];
    }, [data, selectedSensor]);

    const [selectedPosition, setSelectedPosition] = useState(positions[0] || '');

    useEffect(() => {
        if (positions.length > 0 && !positions.includes(selectedPosition)) {
            setSelectedPosition(positions[0]);
        }
    }, [positions, selectedPosition]);

    const filteredData = useMemo(() => {
        if (!selectedSensor) return data;
        return data.filter(d => d.Sensor === selectedSensor);
    }, [data, selectedSensor]);

    // Load Scan and Reference points when sample selection changes
    const load3DData = useCallback(async () => {
        if (!selectedSensor || !selectedPosition) return;

        setPointsLoading(true);
        try {
            const filename = `scan_${selectedSample.toString().padStart(4, '0')}.csv`;
            const refFilename = `scan_0000.csv`;

            const [scan, ref, gt] = await Promise.all([
                fetchScanPoints(selectedSensor, selectedPosition, filename),
                fetchScanPoints(selectedSensor, selectedPosition, refFilename),
                fetchGTRow(selectedSensor, selectedPosition, selectedSample)
            ]);

            setScanPoints(scan);
            setRefPoints(ref);
            setGtData(gt);
        } catch (err) {
            console.error("Failed to load 3D data:", err);
        } finally {
            setPointsLoading(false);
        }
    }, [selectedSensor, selectedPosition, selectedSample, fetchScanPoints, fetchGTRow]);

    useEffect(() => {
        if (viewType === 'alignment') {
            load3DData();
        }
    }, [viewType, load3DData]);

    // Computed Ground Truth Matrix
    const gtMatrix = useMemo(() => {
        if (!gtData) return null;
        const m = new THREE.Matrix4();
        m.set(
            gtData.m00, gtData.m01, gtData.m02, gtData.m03,
            gtData.m10, gtData.m11, gtData.m12, gtData.m13,
            gtData.m20, gtData.m21, gtData.m22, gtData.m23,
            gtData.m30, gtData.m31, gtData.m32, gtData.m33
        );
        return m;
    }, [gtData]);

    const gtEuler = useMemo(() => {
        if (!gtMatrix) return null;
        const e = new THREE.Euler();
        e.setFromRotationMatrix(gtMatrix);
        return {
            rx: (e.x * 180) / Math.PI,
            ry: (e.y * 180) / Math.PI,
            rz: (e.z * 180) / Math.PI
        };
    }, [gtMatrix]);

    // Current Active Matrix
    const activeMatrix = useMemo(() => {
        if (isAligned && gtMatrix) return gtMatrix;

        const m = new THREE.Matrix4();
        const euler = new THREE.Euler(
            (manualTransform.rx * Math.PI) / 180,
            (manualTransform.ry * Math.PI) / 180,
            (manualTransform.rz * Math.PI) / 180
        );
        m.makeRotationFromEuler(euler);
        m.setPosition(manualTransform.tx, manualTransform.ty, manualTransform.tz);
        return m;
    }, [isAligned, gtMatrix, manualTransform]);

    // Live Metrics
    const liveMetrics = useMemo(() => {
        if (!gtData || !gtEuler) return null;

        // Determine current effective transform
        const current_tx = isAligned ? gtData.tx_m : manualTransform.tx;
        const current_ty = isAligned ? gtData.ty_m : manualTransform.ty;
        const current_tz = isAligned ? gtData.tz_m : manualTransform.tz;

        const current_rx = isAligned ? gtEuler.rx : manualTransform.rx;
        const current_ry = isAligned ? gtEuler.ry : manualTransform.ry;
        const current_rz = isAligned ? gtEuler.rz : manualTransform.rz;

        const d_tx = Math.abs(current_tx - gtData.tx_m);
        const d_ty = Math.abs(current_ty - gtData.ty_m);
        const d_tz = Math.abs(current_tz - gtData.tz_m);
        const trans_err = Math.sqrt(d_tx ** 2 + d_ty ** 2 + d_tz ** 2);

        const d_rx = Math.abs(current_rx - gtEuler.rx);
        const d_ry = Math.abs(current_ry - gtEuler.ry);
        const d_rz = Math.abs(current_rz - gtEuler.rz);
        const rot_err = Math.sqrt(d_rx ** 2 + d_ry ** 2 + d_rz ** 2);

        // Heuristic RMSE and Score
        const est_rmse = isAligned ? (gtData.RMSE || 0) : (gtData.RMSE || 0) + trans_err * 0.1 + rot_err * 0.001;

        // More sensitive accuracy score: 100% at perfection, drops off organically
        // Perfection means trans_err=0 and rot_err=0
        const accuracy = isAligned ? 100 : Math.max(0, 100 * Math.exp(-(trans_err * 20 + rot_err * 0.5)));

        return { trans_err, rot_err, est_rmse, accuracy };
    }, [manualTransform, gtData, gtEuler, isAligned]);

    if (!data || data.length === 0) {
        return <div className="text-gray-400 text-center py-10">No data available.</div>;
    }

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Navigation Tabs */}
            <div className="flex border-b border-gray-700">
                <button
                    onClick={() => setViewType('charts')}
                    className={clsx(
                        "px-6 py-3 font-semibold transition-colors",
                        viewType === 'charts' ? "text-blue-400 border-b-2 border-blue-400" : "text-gray-400 hover:text-white"
                    )}
                >
                    Analytics Dashboard
                </button>
                <button
                    onClick={() => setViewType('alignment')}
                    className={clsx(
                        "px-6 py-3 font-semibold transition-colors",
                        viewType === 'alignment' ? "text-blue-400 border-b-2 border-blue-400" : "text-gray-400 hover:text-white"
                    )}
                >
                    3D Alignment View
                </button>
            </div>

            {/* Global Filters */}
            <div className="flex flex-wrap items-center gap-6 bg-gray-800 p-4 rounded-xl shadow border border-gray-700">
                <div className="flex flex-col gap-1.5">
                    <label className="text-gray-400 text-xs uppercase font-bold tracking-wider">Sensor</label>
                    <select
                        value={selectedSensor}
                        onChange={(e) => setSelectedSensor(e.target.value)}
                        className="bg-gray-900 text-white border border-gray-700 rounded-lg px-3 py-2.5 min-w-[180px] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    >
                        {sensors.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>

                {viewType === 'alignment' && (
                    <>
                        <div className="flex flex-col gap-1.5">
                            <label className="text-gray-400 text-xs uppercase font-bold tracking-wider">Position</label>
                            <select
                                value={selectedPosition}
                                onChange={(e) => setSelectedPosition(e.target.value)}
                                className="bg-gray-900 text-white border border-gray-700 rounded-lg px-3 py-2.5 min-w-[180px] focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                            >
                                {positions.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                        </div>

                        <div className="flex flex-col gap-1.5">
                            <label className="text-gray-400 text-xs uppercase font-bold tracking-wider">Sample ID (0-999)</label>
                            <div className="flex items-center gap-3">
                                <input
                                    type="number"
                                    min="0"
                                    max="999"
                                    value={selectedSample}
                                    onChange={(e) => setSelectedSample(parseInt(e.target.value) || 0)}
                                    className="bg-gray-900 text-white border border-gray-700 rounded-lg px-3 py-2.5 w-24 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                                />
                                <button
                                    onClick={() => setSelectedSample(Math.floor(Math.random() * 1000))}
                                    className="p-2.5 rounded-lg bg-gray-700 hover:bg-gray-600 border border-gray-600 transition-colors"
                                    title="Random Sample"
                                >
                                    🎲
                                </button>
                            </div>
                        </div>
                    </>
                )}

                {detailedLoading && <span className="text-blue-400 text-sm animate-pulse flex items-center gap-2 ml-auto">
                    <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
                    Syncing data...
                </span>}
            </div>

            {viewType === 'charts' ? (
                <>
                    {/* KPI Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                        <KPICard
                            title="Avg Fitness"
                            value={filteredData.reduce((acc, curr) => acc + (curr.Fitness || 0), 0) / (filteredData.length || 1)}
                            format={(v) => v.toFixed(4)}
                        />
                        <KPICard
                            title="Avg Rot Error"
                            value={filteredData.reduce((acc, curr) => acc + (curr.Error_Rot_Deg || 0), 0) / (filteredData.length || 1)}
                            format={(v) => v.toFixed(3) + '°'}
                            color="text-red-400"
                        />
                        <KPICard
                            title="Avg Trans Error"
                            value={filteredData.reduce((acc, curr) => acc + (curr.Error_Trans_M || 0), 0) / (filteredData.length || 1)}
                            format={(v) => (v * 1000).toFixed(1) + 'mm'}
                            color="text-green-400"
                        />
                        <KPICard
                            title="Avg Time"
                            value={filteredData.reduce((acc, curr) => acc + (curr.Time_Total || 0), 0) / (filteredData.length || 1)}
                            format={(v) => v.toFixed(2) + 's'}
                            color="text-purple-400"
                        />
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <div className="bg-gray-800/50 p-6 rounded-2xl border border-gray-700">
                            <h3 className="text-lg font-semibold mb-6 text-gray-100 flex items-center gap-2">
                                <div className="w-1 h-6 bg-blue-500 rounded-full" />
                                Error vs. Rotation Magnitude
                            </h3>
                            <div className="grid gap-8">
                                <CorrelationChart
                                    data={detailedData}
                                    yKey="Error_Rot_Deg"
                                    yLabel="Rot Error (Deg)"
                                    color="#EF4444"
                                />
                                <CorrelationChart
                                    data={detailedData}
                                    yKey="Error_Trans_M"
                                    yLabel="Trans Error (M)"
                                    color="#10B981"
                                />
                            </div>
                        </div>

                        <div className="bg-gray-800/50 p-6 rounded-2xl border border-gray-700">
                            <h3 className="text-lg font-semibold mb-6 text-gray-100 flex items-center gap-2">
                                <div className="w-1 h-6 bg-purple-500 rounded-full" />
                                Metric Overview
                            </h3>
                            <div className="space-y-8">
                                <FitnessChart data={filteredData} />
                                <ErrorsChart data={filteredData} />
                            </div>
                        </div>
                    </div>
                </>
            ) : (
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">
                    <div className="xl:col-span-2 space-y-6">
                        <div className="relative group">
                            <AlignmentViewer
                                scanPoints={scanPoints}
                                referencePoints={refPoints}
                                matrix={activeMatrix}
                            />
                            {pointsLoading && (
                                <div className="absolute inset-0 bg-gray-950/60 backdrop-blur-sm flex items-center justify-center rounded-xl z-20">
                                    <div className="flex flex-col items-center gap-4 text-white font-medium tracking-tight">
                                        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
                                        <span>Loading point clouds...</span>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 shadow-xl overflow-hidden relative">
                            <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
                            <h3 className="text-xl font-bold mb-6 text-gray-100 pb-4 border-b border-gray-700">Alignment Controls</h3>

                            <div className="space-y-6">
                                <div className="flex items-center justify-between p-4 bg-gray-900/50 rounded-xl border border-gray-700">
                                    <div className="flex flex-col">
                                        <span className="text-gray-300 font-bold text-sm">Auto-Align (GT)</span>
                                        <span className="text-[10px] text-gray-500">Use ground truth registry</span>
                                    </div>
                                    <button
                                        onClick={() => setIsAligned(!isAligned)}
                                        className={clsx(
                                            "relative inline-flex h-7 w-14 items-center rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900",
                                            isAligned ? "bg-blue-500" : "bg-gray-600"
                                        )}
                                    >
                                        <span className={clsx(
                                            "inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-300",
                                            isAligned ? "translate-x-8" : "translate-x-1"
                                        )} />
                                    </button>
                                </div>

                                {liveMetrics && (
                                    <div className="grid grid-cols-2 gap-4 animate-fadeIn">
                                        <div className="p-4 bg-gray-900/50 rounded-xl border border-gray-700 col-span-2">
                                            <div className="flex justify-between items-end mb-2">
                                                <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest">Registration Score</div>
                                                <div className="text-xl font-black text-blue-400 tabular-nums">
                                                    {liveMetrics.accuracy.toFixed(1)}%
                                                </div>
                                            </div>
                                            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden border border-gray-700">
                                                <div
                                                    className={clsx(
                                                        "h-full transition-all duration-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]",
                                                        liveMetrics.accuracy > 90 ? "bg-emerald-500" : liveMetrics.accuracy > 70 ? "bg-blue-500" : "bg-red-500"
                                                    )}
                                                    style={{ width: `${liveMetrics.accuracy}%` }}
                                                />
                                            </div>
                                        </div>
                                        <div className="p-4 bg-gray-900/50 rounded-xl border border-gray-700">
                                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1 text-emerald-500">Residual Dist</div>
                                            <div className="text-lg font-black text-gray-100 tabular-nums">
                                                {(liveMetrics.trans_err * 1000).toFixed(2)}<span className="text-xs text-gray-500 ml-1">mm</span>
                                            </div>
                                        </div>
                                        <div className="p-4 bg-gray-900/50 rounded-xl border border-gray-700">
                                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-widest mb-1 text-red-400">Residual Rot</div>
                                            <div className="text-lg font-black text-gray-100 tabular-nums">
                                                {liveMetrics.rot_err.toFixed(2)}<span className="text-xs text-gray-500 ml-1">°</span>
                                            </div>
                                        </div>
                                        <div className="p-4 bg-gray-900/50 rounded-xl border border-gray-700 col-span-2">
                                            <div className="text-[10px] text-gray-400 uppercase font-bold tracking-widest mb-1 border-b border-gray-800 pb-1 flex justify-between">
                                                <span>Estimated RMSE</span>
                                                <span className="text-gray-600 font-mono">GT: {(gtData?.RMSE || 0).toFixed(6)}</span>
                                            </div>
                                            <div className="text-xl font-black text-blue-300 tabular-nums mt-2">
                                                {liveMetrics.est_rmse.toFixed(6)}
                                            </div>
                                        </div>
                                    </div>
                                )}

                                <div className={clsx(
                                    "space-y-4 bg-gray-900/50 p-5 rounded-xl border transition-all duration-300",
                                    isAligned ? "opacity-30 pointer-events-none border-gray-800" : "border-gray-700"
                                )}>
                                    <div className="flex justify-between items-center mb-2">
                                        <h4 className="text-xs font-black text-blue-300 uppercase tracking-widest">Manual Alignment Tools</h4>
                                        <button
                                            onClick={resetManual}
                                            className="text-[10px] text-gray-500 hover:text-white uppercase tracking-widest font-bold"
                                        >
                                            Reset
                                        </button>
                                    </div>
                                    <div className="space-y-4">
                                        <Slider label="TX (m)" value={manualTransform.tx} min={-0.2} max={0.2} step={0.001} onChange={(v) => setManualTransform(prev => ({ ...prev, tx: v }))} />
                                        <Slider label="TY (m)" value={manualTransform.ty} min={-0.2} max={0.2} step={0.001} onChange={(v) => setManualTransform(prev => ({ ...prev, ty: v }))} />
                                        <Slider label="TZ (m)" value={manualTransform.tz} min={-0.2} max={0.2} step={0.001} onChange={(v) => setManualTransform(prev => ({ ...prev, tz: v }))} />
                                        <div className="h-px bg-gray-800 my-4" />
                                        <Slider label="RX (°)" value={manualTransform.rx} min={-30} max={30} step={0.1} onChange={(v) => setManualTransform(prev => ({ ...prev, rx: v }))} />
                                        <Slider label="RY (°)" value={manualTransform.ry} min={-30} max={30} step={0.1} onChange={(v) => setManualTransform(prev => ({ ...prev, ry: v }))} />
                                        <Slider label="RZ (°)" value={manualTransform.rz} min={-30} max={30} step={0.1} onChange={(v) => setManualTransform(prev => ({ ...prev, rz: v }))} />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="bg-amber-900/10 p-5 rounded-2xl border border-amber-500/20 shadow-inner">
                            <h4 className="text-amber-400 text-xs font-black flex items-center gap-2 mb-3 uppercase tracking-tighter">
                                <span className="p-1 rounded bg-amber-500/20">💡</span> Manual Alignment Guide
                            </h4>
                            <p className="text-[11px] text-amber-200/60 leading-relaxed font-medium">
                                Use the sliders to transform the <b>Scan (Pink)</b>. Your goal is to reach 100% accuracy and minimize <b>Residual Distance</b>.
                                The "Auto-Align" toggle uses the high-precision ground truth directly.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Data Table */}
            <div className="bg-gray-800 rounded-2xl shadow-lg border border-gray-700 overflow-hidden mt-8">
                <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center">
                    <h3 className="text-xl font-bold text-gray-100">Sensor Performance Log</h3>
                    <span className="text-xs text-gray-500 font-mono tracking-tighter uppercase px-2 py-1 bg-gray-900 rounded border border-gray-700">
                        {filteredData.length} Entry Results
                    </span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-gray-300 border-collapse">
                        <thead className="bg-gray-900/50 text-gray-500 uppercase text-[10px] font-black tracking-widest">
                            <tr>
                                <th className="px-6 py-4">Position</th>
                                <th className="px-6 py-4">Fitness Score</th>
                                <th className="px-6 py-4">Rot Error</th>
                                <th className="px-6 py-4">Trans Error</th>
                                <th className="px-6 py-4">Sync Time</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700/50">
                            {filteredData.map((row, idx) => (
                                <tr key={idx} className="hover:bg-blue-500/5 transition-all group cursor-default">
                                    <td className="px-6 py-4 font-mono text-xs">{row.Position}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${Math.min(100, (row.Fitness || 0) * 100)}%` }} />
                                            </div>
                                            <span className="font-semibold tabular-nums text-sm text-gray-200">{(row.Fitness || 0).toFixed(4)}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-red-400 font-bold tabular-nums text-sm">{(row.Error_Rot_Deg || 0).toFixed(3)}°</td>
                                    <td className="px-6 py-4 text-green-400 font-bold tabular-nums text-sm">{(row.Error_Trans_M * 1000 || 0).toFixed(2)}mm</td>
                                    <td className="px-6 py-4">
                                        <span className="px-2.5 py-1 rounded bg-purple-500/10 text-purple-300 text-xs font-bold tabular-nums border border-purple-500/20">
                                            {(row.Time_Total || 0).toFixed(2)}s
                                        </span>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

// --- Sub components ---

const Slider = ({ label, value, min, max, step, onChange }) => (
    <div className="space-y-1.5 group">
        <div className="flex justify-between text-[10px] font-black uppercase tracking-wider">
            <span className="text-gray-500 group-hover:text-blue-300 transition-colors">{label}</span>
            <span className="text-gray-100 font-mono tabular-nums">{value.toFixed(3)}</span>
        </div>
        <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            className="w-full h-1.5 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-all"
        />
    </div>
);

const AxisValue = ({ label, value, color }) => (
    <div className="flex flex-col items-center transition-transform hover:scale-110">
        <span className={clsx("text-[10px] font-black uppercase mb-1 opacity-50", color)}>{label}</span>
        <span className="text-xs font-mono font-bold text-gray-100 tabular-nums">
            {value !== undefined ? value.toFixed(3) : '0.000'}
        </span>
    </div>
)

const KPICard = ({ title, value, format, color = "text-blue-400" }) => (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700 flex flex-col items-center justify-center">
        <span className="text-gray-400 text-sm uppercase tracking-wider mb-2">{title}</span>
        <span className={clsx("text-3xl font-bold", color)}>
            {isNaN(value) ? '-' : format(value)}
        </span>
    </div>
);

export default Dashboard;
