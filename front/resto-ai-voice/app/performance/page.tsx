"use client";

import { useState, useEffect } from 'react'
import api from '../services/api'
import PerformanceCharts from './components/PerformanceCharts'
import QueryGroupedView from './components/QueryGroupedView'

interface PerformanceLog {
  timestamp: string;
  operation: string;
  duration_seconds: number;
  context?: Record<string, any>;
}

export default function PerformancePage() {
  const [logs, setLogs] = useState<PerformanceLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState('all')
  const [selectedOperations, setSelectedOperations] = useState<string[]>([])
  const [selectedAgents, setSelectedAgents] = useState<string[]>([])
  const [queryIdFilter, setQueryIdFilter] = useState('')

  // Fetch logs on mount
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true)
        setError(null)
        const result = await api.getPerformanceLogs()
        
        if (result.success && result.logs) {
          setLogs(result.logs)
        } else {
          setError(result.error || 'Failed to load performance logs')
        }
      } catch (error) {
        console.error('Failed to fetch performance logs:', error)
        setError('Failed to fetch performance logs')
      } finally {
        setLoading(false)
      }
    }

    fetchLogs()
  }, [])

  // Filter and process logs
  const filteredLogs = logs.filter(log => {
    // Filter by time range
    const logDate = new Date(log.timestamp)
    const now = new Date()

    if (timeRange === 'today') {
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      if (logDate < today) return false
    } else if (timeRange === 'week') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      if (logDate < weekAgo) return false
    } else if (timeRange === 'month') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      if (logDate < monthAgo) return false
    }

    // Filter by operation type
    if (selectedOperations.length > 0 && !selectedOperations.includes(log.operation)) {
      return false
    }

    // Filter by agent
    if (selectedAgents.length > 0) {
      const agentName = log.context?.agent_name
      if (!agentName || !selectedAgents.includes(agentName)) {
        return false
      }
    }

    // Filter by query_id
    if (queryIdFilter.trim()) {
      const logQueryId = log.context?.query_id || ''
      if (!logQueryId.toLowerCase().includes(queryIdFilter.toLowerCase().trim())) {
        return false
      }
    }

    return true
  })

  // Calculate statistics
  const totalRequests = filteredLogs.length
  const avgResponseTime = filteredLogs.length > 0 
    ? filteredLogs.reduce((sum, log) => sum + log.duration_seconds, 0) / filteredLogs.length
    : 0
  const slowestRequest = filteredLogs.length > 0 
    ? Math.max(...filteredLogs.map(log => log.duration_seconds))
    : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-100 font-sans">
      <div className="max-w-6xl mx-auto p-4">
        {/* Header */}
        <header className="text-center py-8">
          <h1 className="text-3xl font-bold text-orange-800 mb-2">Performance Monitoring</h1>
          <p className="text-lg text-orange-600">LLM Response Time Analysis</p>
        </header>

        {/* Loading state */}
        {loading && (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-orange-600">Loading performance data...</p>
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-center">
            <p className="text-red-600 mb-2">⚠️ {error}</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-orange-100 hover:bg-orange-200 text-orange-700 py-2 px-4 rounded-lg transition-colors text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* Controls */}
        {!loading && !error && logs.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <div className="flex flex-wrap gap-4 items-center mb-4">
              <div className="flex items-center gap-2">
                <span className="text-orange-700 font-medium">Time Range:</span>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(e.target.value)}
                  className="p-2 border border-orange-300 rounded-lg bg-white text-gray-800 hover:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent cursor-pointer"
                >
                  <option value="all">All Time</option>
                  <option value="today">Today</option>
                  <option value="week">Last 7 Days</option>
                  <option value="month">Last 30 Days</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-orange-700 font-medium">Query ID:</span>
                <input
                  type="text"
                  placeholder="Filter by Query ID..."
                  value={queryIdFilter}
                  onChange={(e) => setQueryIdFilter(e.target.value)}
                  className="p-2 border border-orange-300 rounded-lg bg-white text-gray-800 hover:border-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent font-mono text-sm"
                  style={{ width: '250px' }}
                />
                {queryIdFilter && (
                  <button
                    onClick={() => setQueryIdFilter('')}
                    className="bg-orange-100 hover:bg-orange-200 text-orange-700 py-2 px-3 rounded-lg transition-colors text-sm"
                  >
                    Clear
                  </button>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-orange-700 font-medium">Operations:</span>
                <div className="flex flex-wrap gap-2">
                  {Array.from(new Set(logs.map((log: any) => log.operation))).map(operation => (
                    <label
                      key={operation}
                      className="inline-flex items-center gap-2 px-3 py-2 border border-orange-300 rounded-lg cursor-pointer hover:bg-orange-50 transition-colors"
                      style={{
                        backgroundColor: selectedOperations.includes(operation) ? '#fed7aa' : 'white',
                        borderColor: selectedOperations.includes(operation) ? '#f97316' : '#fed7aa'
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedOperations.includes(operation)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedOperations([...selectedOperations, operation])
                          } else {
                            setSelectedOperations(selectedOperations.filter(op => op !== operation))
                          }
                        }}
                        className="w-4 h-4 text-orange-600 border-orange-300 rounded focus:ring-orange-500 cursor-pointer"
                      />
                      <span className="text-sm text-gray-800 font-medium">{operation}</span>
                    </label>
                  ))}
                </div>
                {selectedOperations.length > 0 && (
                  <button
                    onClick={() => setSelectedOperations([])}
                    className="bg-orange-100 hover:bg-orange-200 text-orange-700 py-2 px-3 rounded-lg transition-colors text-sm font-medium"
                  >
                    Clear All
                  </button>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-orange-700 font-medium">Agents:</span>
                <div className="flex flex-wrap gap-2">
                  {Array.from(new Set(
                    logs
                      .map((log: any) => log.context?.agent_name)
                      .filter(Boolean)
                  )).map(agent => {
                    const agentColors: Record<string, string> = {
                      'orchestrator': '#c084fc',
                      'menu': '#60a5fa',
                      'faq': '#34d399',
                      'reservation': '#f472b6',
                    }
                    const bgColor = agentColors[agent] || '#d1d5db'
                    
                    return (
                      <label
                        key={agent}
                        className="inline-flex items-center gap-2 px-3 py-2 border-2 rounded-lg cursor-pointer hover:opacity-80 transition-all"
                        style={{
                          backgroundColor: selectedAgents.includes(agent) ? bgColor : 'white',
                          borderColor: bgColor,
                          color: selectedAgents.includes(agent) ? 'white' : '#1f2937'
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={selectedAgents.includes(agent)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedAgents([...selectedAgents, agent])
                            } else {
                              setSelectedAgents(selectedAgents.filter(a => a !== agent))
                            }
                          }}
                          className="w-4 h-4 rounded focus:ring-2 cursor-pointer"
                          style={{
                            accentColor: bgColor
                          }}
                        />
                        <span className="text-sm font-semibold">{agent}</span>
                      </label>
                    )
                  })}
                </div>
                {selectedAgents.length > 0 && (
                  <button
                    onClick={() => setSelectedAgents([])}
                    className="bg-orange-100 hover:bg-orange-200 text-orange-700 py-2 px-3 rounded-lg transition-colors text-sm font-medium"
                  >
                    Clear All
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Statistics Summary */}
        {!loading && !error && logs.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-orange-600 font-medium mb-2">Total Requests</h3>
              <p className="text-3xl font-bold text-orange-800">{totalRequests}</p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-orange-600 font-medium mb-2">Avg Response Time</h3>
              <p className="text-3xl font-bold text-orange-800">
                {avgResponseTime.toFixed(3)}s
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-orange-600 font-medium mb-2">Slowest Request</h3>
              <p className="text-3xl font-bold text-orange-800">
                {slowestRequest.toFixed(3)}s
              </p>
            </div>

            <div className="bg-white p-4 rounded-lg shadow">
              <h3 className="text-orange-600 font-medium mb-2">Fastest Request</h3>
              <p className="text-3xl font-bold text-orange-800">
                {filteredLogs.length > 0 
                  ? Math.min(...filteredLogs.map(log => log.duration_seconds)).toFixed(3)
                  : '0.000'}s
              </p>
            </div>
          </div>
        )}

        {/* Charts */}
        {!loading && !error && filteredLogs.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-orange-700 mb-4">Performance Charts</h2>
            <PerformanceCharts logs={filteredLogs} />
          </div>
        )}

        {/* Query Grouped View */}
        {!loading && !error && filteredLogs.length > 0 && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold text-orange-700 mb-4">Queries Overview</h2>
            <QueryGroupedView logs={filteredLogs} />
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && logs.length === 0 && (
          <div className="text-center py-8 text-orange-400">
            <p>No performance data available</p>
            <p className="mt-2 text-sm">Performance logs will appear after processing queries through the system.</p>
          </div>
        )}
      </div>
    </div>
  )
}