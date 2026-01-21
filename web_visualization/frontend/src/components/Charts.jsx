import React from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    LineChart,
    Line,
    ScatterChart,
    Scatter,
    ZAxis,
    XAxis as RechartsXAxis,
    YAxis as RechartsYAxis,
} from 'recharts';

const ChartContainer = ({ title, children }) => (
    <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700 hover:border-blue-500 transition-colors duration-300">
        <h3 className="text-xl font-semibold mb-4 text-gray-100">{title}</h3>
        <div className="h-64 w-full">
            {children}
        </div>
    </div>
);

export const FitnessChart = ({ data }) => {
    return (
        <ChartContainer title="Fitness Score by Position">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="Position" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '0.5rem', color: '#F3F4F6' }}
                        itemStyle={{ color: '#F3F4F6' }}
                    />
                    <Legend wrapperStyle={{ color: '#9CA3AF' }} />
                    <Bar dataKey="Fitness" fill="#3B82F6" name="Fitness" radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </ChartContainer>
    );
};

export const ErrorsChart = ({ data }) => {
    return (
        <ChartContainer title="Errors (Rotation & Translation)">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="Position" stroke="#9CA3AF" />
                    <YAxis yAxisId="left" stroke="#EF4444" label={{ value: 'Rot (Deg)', angle: -90, position: 'insideLeft', fill: '#EF4444' }} />
                    <YAxis yAxisId="right" orientation="right" stroke="#10B981" label={{ value: 'Trans (M)', angle: 90, position: 'insideRight', fill: '#10B981' }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '0.5rem', color: '#F3F4F6' }}
                    />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="Error_Rot_Deg" stroke="#EF4444" activeDot={{ r: 8 }} name="Rot Error (Deg)" />
                    <Line yAxisId="right" type="monotone" dataKey="Error_Trans_M" stroke="#10B981" name="Trans Error (M)" />
                </LineChart>
            </ResponsiveContainer>
        </ChartContainer>
    );
};

export const TimeChart = ({ data }) => {
    return (
        <ChartContainer title="Total Time Execution">
            <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis type="number" stroke="#9CA3AF" />
                    <YAxis dataKey="Position" type="category" stroke="#9CA3AF" width={100} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '0.5rem', color: '#F3F4F6' }}
                    />
                    <Legend />
                    <Bar dataKey="Time_Total" fill="#8B5CF6" name="Time (s)" radius={[0, 4, 4, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </ChartContainer>
    );
};

export const CorrelationChart = ({ data, yKey, yLabel, color }) => {
    return (
        <ChartContainer title={`Object Rotation vs ${yLabel}`}>
            <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <RechartsXAxis
                        type="number"
                        dataKey="Obj_Rot_Mag"
                        name="Object Rotation"
                        unit="°"
                        stroke="#9CA3AF"
                        label={{ value: 'Object Rotation (Deg)', position: 'insideBottom', offset: -10, fill: '#9CA3AF' }}
                    />
                    <RechartsYAxis
                        type="number"
                        dataKey={yKey}
                        name={yLabel}
                        stroke={color}
                        label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: color }}
                    />
                    <ZAxis type="number" range={[50, 50]} />
                    <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '0.5rem', color: '#F3F4F6' }}
                    />
                    <Legend />
                    <Scatter name={yLabel} data={data} fill={color} />
                </ScatterChart>
            </ResponsiveContainer>
        </ChartContainer>
    );
};

export const RMSEChart = ({ data }) => {
    return (
        <ChartContainer title="RMSE by Position">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="Position" stroke="#9CA3AF" />
                    <YAxis stroke="#F59E0B" label={{ value: 'RMSE', angle: -90, position: 'insideLeft', fill: '#F59E0B' }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1F2937', border: 'none', borderRadius: '0.5rem', color: '#F3F4F6' }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="RMSE" stroke="#F59E0B" name="RMSE" activeDot={{ r: 8 }} />
                </LineChart>
            </ResponsiveContainer>
        </ChartContainer>
    );
};
