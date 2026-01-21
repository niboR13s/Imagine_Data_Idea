import React, { useState, useMemo, useEffect } from 'react';
import { FitnessChart, ErrorsChart, TimeChart, CorrelationChart, RMSEChart } from './Charts';
import clsx from 'clsx';

const Dashboard = ({ data, detailedData, fetchDetailed, detailedLoading }) => {
    const sensors = useMemo(() => [...new Set(data.map(d => d.Sensor))], [data]);
    const [selectedSensor, setSelectedSensor] = useState(sensors[0] || '');

    // Update selected sensor when data changes if current selection is invalid
    useEffect(() => {
        if (sensors.length > 0 && !sensors.includes(selectedSensor)) {
            setSelectedSensor(sensors[0]);
        }
    }, [sensors, selectedSensor]);

    // Fetch detailed data for the specific sensor whenever selection changes
    useEffect(() => {
        if (selectedSensor) {
            fetchDetailed(selectedSensor);
        }
    }, [selectedSensor, fetchDetailed]);

    const filteredData = useMemo(() => {
        if (!selectedSensor) return data;
        return data.filter(d => d.Sensor === selectedSensor);
    }, [data, selectedSensor]);

    if (!data || data.length === 0) {
        return <div className="text-gray-400 text-center py-10">No data available.</div>;
    }

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Filters */}
            <div className="flex items-center space-x-4 bg-gray-800 p-4 rounded-lg shadow border border-gray-700">
                <label className="text-gray-300 font-medium">Select Sensor:</label>
                <select
                    value={selectedSensor}
                    onChange={(e) => setSelectedSensor(e.target.value)}
                    className="bg-gray-700 text-white border border-gray-600 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                    {sensors.map(s => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
                {detailedLoading && <span className="text-blue-400 text-sm animate-pulse">Updating correlation data...</span>}
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <KPICard
                    title="Avg Fitness"
                    value={filteredData.reduce((acc, curr) => acc + curr.Fitness, 0) / filteredData.length}
                    format={(v) => v.toFixed(2)}
                />
                <KPICard
                    title="Avg Rot Error"
                    value={filteredData.reduce((acc, curr) => acc + curr.Error_Rot_Deg, 0) / filteredData.length}
                    format={(v) => v.toFixed(2) + '°'}
                    color="text-red-400"
                />
                <KPICard
                    title="Avg Trans Error"
                    value={filteredData.reduce((acc, curr) => acc + curr.Error_Trans_M, 0) / filteredData.length}
                    format={(v) => v.toFixed(3) + 'm'}
                    color="text-green-400"
                />
                <KPICard
                    title="Avg Time"
                    value={filteredData.reduce((acc, curr) => acc + curr.Time_Total, 0) / filteredData.length}
                    format={(v) => v.toFixed(2) + 's'}
                    color="text-purple-400"
                />
            </div>

            <div className="border-t border-gray-700 pt-8 mt-8">
                <h2 className="text-2xl font-bold mb-6 text-blue-400">Error Correlations</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
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

            <div className="border-t border-gray-700 pt-8 mt-8">
                <h2 className="text-2xl font-bold mb-6 text-purple-400">Performance Overview</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <FitnessChart data={filteredData} />
                    <ErrorsChart data={filteredData} />
                    <TimeChart data={filteredData} />
                    {detailedData && detailedData.some(d => d.RMSE !== undefined) && (
                        <RMSEChart data={detailedData.filter((d, i) => i % 50 === 0)} />
                    )}
                </div>
            </div>

            {/* Data Table */}
            <div className="bg-gray-800 rounded-xl shadow-lg border border-gray-700 overflow-hidden mt-8">
                <div className="px-6 py-4 border-b border-gray-700">
                    <h3 className="text-xl font-semibold text-gray-100">Raw Data (Aggregated per Position)</h3>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-gray-300">
                        <thead className="bg-gray-900 text-gray-400 uppercase text-xs font-semibold">
                            <tr>
                                <th className="px-6 py-3">Position</th>
                                <th className="px-6 py-3">Fitness</th>
                                <th className="px-6 py-3">Rot Error (Deg)</th>
                                <th className="px-6 py-3">Trans Error (M)</th>
                                <th className="px-6 py-3">Time (s)</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-700">
                            {filteredData.map((row, idx) => (
                                <tr key={idx} className="hover:bg-gray-750 transition-colors">
                                    <td className="px-6 py-4">{row.Position}</td>
                                    <td className="px-6 py-4">{row.Fitness.toFixed(4)}</td>
                                    <td className="px-6 py-4 text-red-400">{row.Error_Rot_Deg.toFixed(4)}</td>
                                    <td className="px-6 py-4 text-green-400">{row.Error_Trans_M.toFixed(4)}</td>
                                    <td className="px-6 py-4 text-purple-400">{row.Time_Total.toFixed(4)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

const KPICard = ({ title, value, format, color = "text-blue-400" }) => (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700 flex flex-col items-center justify-center">
        <span className="text-gray-400 text-sm uppercase tracking-wider mb-2">{title}</span>
        <span className={clsx("text-3xl font-bold", color)}>
            {isNaN(value) ? '-' : format(value)}
        </span>
    </div>
);

export default Dashboard;
