"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
  AreaChart,
} from "recharts";

interface Log {
  timestamp: string;
  level: string;
  function_name: string;
  message: string;
  execution_time_seconds?: number;
}

interface Stats {
  total_logs: number;
  by_level: Record<string, number>;
  by_function: Record<string, number>;
  by_object_name: Record<string, number>;
  by_hour: Record<string, number>;
  avg_execution_time_by_function: Record<string, number>;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, logsRes] = await Promise.all([
        fetch(`${API_BASE_URL}/logs/stats`),
        fetch(`${API_BASE_URL}/logs`),
      ]);

      if (!statsRes.ok || !logsRes.ok) {
        throw new Error("Failed to fetch data");
      }

      const statsData = await statsRes.json();
      const logsData = await logsRes.json();

      setStats(statsData);
      setLogs(logsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading logs data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Error: {error}</p>
            <button
              onClick={fetchData}
              className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const levelData = Object.entries(stats.by_level).map(([level, count]) => ({
    name: level,
    value: count,
  }));

  const functionData = Object.entries(stats.by_function)
    .map(([func, count]) => ({
      name: func,
      count,
    }))
    .sort((a, b) => b.count - a.count);

  const objectNameData = Object.entries(stats.by_object_name).map(([objName, count]) => ({
    name: objName,
    value: count,
  }));

  const objectNameBarData = Object.entries(stats.by_object_name)
    .map(([objName, count]) => ({
      name: objName,
      count,
    }))
    .sort((a, b) => b.count - a.count);

  const hourData = Object.entries(stats.by_hour)
    .map(([hour, count]) => ({
      name: hour,
      count,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  const executionTimeData = Object.entries(stats.avg_execution_time_by_function)
    .map(([func, time]) => ({
      name: func,
      time: typeof time === 'number' ? time : 0,
    }))
    .sort((a, b) => b.time - a.time);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Logs Dashboard</h1>
            <button
              onClick={fetchData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Total Logs</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {stats.total_logs}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Total Functions</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {Object.keys(stats.by_function).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">Log Levels</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {Object.keys(stats.by_level).length}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm font-medium">
              Avg Exec Time
            </p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {(
                Object.values(stats.avg_execution_time_by_function)
                  .filter(v => typeof v === 'number')
                  .reduce((a, b) => a + b, 0) / Object.keys(stats.avg_execution_time_by_function).length
              ).toFixed(2)}
              s
            </p>
          </div>
        </div>

        {/* Charts grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Logs by level - Pie Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Logs by Level</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={levelData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {levelData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Logs by object name - Pie Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Logs by Object</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={objectNameData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {objectNameData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={COLORS[index % COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Logs over time - Line Chart */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Logs Over Time
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={hourData}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  fontSize={12}
                />
                <YAxis />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  fillOpacity={1}
                  fill="url(#colorCount)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Messages per object - Bar Chart */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Messages per Object
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={objectNameBarData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Execution time by function - Bar Chart */}
          <div className="bg-white rounded-lg shadow p-6 lg:col-span-2">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              Average Execution Time by Function
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={executionTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis label={{ value: "Time (seconds)", angle: -90, position: "insideLeft" }} />
                <Tooltip
                  formatter={(value) =>
                    typeof value === 'number' ? `${value.toFixed(4)}s` : value
                  }
                />
                <Bar dataKey="time" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent logs table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">Recent Logs</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Level
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Function
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Message
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                    Exec Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {logs.slice(0, 50).map((log, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          log.level === "ERROR"
                            ? "bg-red-100 text-red-800"
                            : log.level === "WARNING"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-green-100 text-green-800"
                        }`}
                      >
                        {log.level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {log.function_name}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                      {log.message}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {log.execution_time_seconds
                        ? `${log.execution_time_seconds.toFixed(2)}s`
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
