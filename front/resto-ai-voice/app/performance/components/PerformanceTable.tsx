"use client";

import { useState } from 'react'

interface PerformanceTableProps {
  logs: Array<{
    timestamp: string;
    operation: string;
    duration_seconds: number;
    context?: Record<string, any>;
  }>
}

export default function PerformanceTable({ logs }: PerformanceTableProps) {
  const [sortConfig, setSortConfig] = useState<{
    key: string;
    direction: 'ascending' | 'descending';
  } | null>({ key: 'timestamp', direction: 'descending' })
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedRows(newExpanded)
  }

  const requestSort = (key: string) => {
    let direction: 'ascending' | 'descending' = 'ascending'
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending'
    }
    setSortConfig({ key, direction })
  }

  const sortedLogs = [...logs].sort((a, b) => {
    if (!sortConfig) return 0

    const aValue = a[sortConfig.key as keyof typeof a]
    const bValue = b[sortConfig.key as keyof typeof b]

    if (aValue < bValue) {
      return sortConfig.direction === 'ascending' ? -1 : 1
    }
    if (aValue > bValue) {
      return sortConfig.direction === 'ascending' ? 1 : -1
    }
    return 0
  })

  return (
    <div className="overflow-x-auto">
      <div className="mb-3 text-sm text-orange-600 flex items-center gap-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="italic">Click on any row to expand and see full details</span>
      </div>
      <table className="min-w-full divide-y divide-orange-200">
        <thead className="bg-orange-50">
          <tr>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-orange-700 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('timestamp')}
            >
              <div className="flex items-center">
                Timestamp
                {sortConfig?.key === 'timestamp' && (
                  <span className="ml-1">
                    {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                  </span>
                )}
              </div>
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-orange-700 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('operation')}
            >
              <div className="flex items-center">
                Operation
                {sortConfig?.key === 'operation' && (
                  <span className="ml-1">
                    {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                  </span>
                )}
              </div>
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-orange-700 uppercase tracking-wider"
            >
              Agent
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-orange-700 uppercase tracking-wider cursor-pointer"
              onClick={() => requestSort('duration_seconds')}
            >
              <div className="flex items-center">
                Duration (s)
                {sortConfig?.key === 'duration_seconds' && (
                  <span className="ml-1">
                    {sortConfig.direction === 'ascending' ? '↑' : '↓'}
                  </span>
                )}
              </div>
            </th>
            <th
              scope="col"
              className="px-6 py-3 text-left text-xs font-medium text-orange-700 uppercase tracking-wider"
            >
              Details (Click row to expand)
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-orange-100">
          {sortedLogs.map((log, index) => {
            const agentName = log.context?.agent_name || 'N/A'
            const isExpanded = expandedRows.has(index)
            const agentColors: Record<string, string> = {
              'orchestrator': 'bg-purple-100 text-purple-700',
              'menu': 'bg-blue-100 text-blue-700',
              'faq': 'bg-green-100 text-green-700',
              'reservation': 'bg-pink-100 text-pink-700',
            }
            
            return (
              <tr 
                key={index} 
                onClick={() => toggleRow(index)}
                className="hover:bg-orange-50 transition-colors cursor-pointer"
              >
                <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-800">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-orange-800">
                  <span className="px-2 py-1 bg-orange-100 rounded-full text-xs font-medium">
                    {log.operation}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${agentColors[agentName] || 'bg-gray-100 text-gray-700'}`}>
                    {agentName}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-orange-900">
                  {log.duration_seconds.toFixed(3)}
                </td>
                <td className="px-6 py-4 text-sm text-orange-600" onClick={(e) => e.stopPropagation()}>
                  {log.context ? (
                    <div className="space-y-2 max-w-xl">
                      {/* Collapsed Preview */}
                      {!isExpanded && (
                        <div className="flex items-center gap-2">
                          <div className="text-xs text-gray-600 truncate max-w-md">
                            {log.context.query_preview && (
                              <span className="italic">"{log.context.query_preview}"</span>
                            )}
                            {!log.context.query_preview && log.context.response_preview && (
                              <span className="italic">"{log.context.response_preview}"</span>
                            )}
                            {!log.context.query_preview && !log.context.response_preview && (
                              <span>Click to see details</span>
                            )}
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              toggleRow(index)
                            }}
                            className="text-xs bg-orange-100 hover:bg-orange-200 text-orange-700 px-2 py-1 rounded whitespace-nowrap"
                          >
                            Show More
                          </button>
                        </div>
                      )}

                      {/* Expanded Full Details */}
                      {isExpanded && (
                        <>
                          <div className="flex justify-end">
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleRow(index)
                              }}
                              className="text-xs bg-orange-100 hover:bg-orange-200 text-orange-700 px-2 py-1 rounded"
                            >
                              Show Less
                            </button>
                          </div>
                          
                          {/* Query/Response Preview */}
                          {(log.context.query_preview || log.context.response_preview || log.context.query_full || log.context.response_full) && (
                            <div className="bg-orange-50 p-3 rounded text-xs">
                              {(log.context.query_full || log.context.query_preview) && (
                                <div className="mb-2">
                                  <span className="font-semibold text-orange-800">Query:</span>
                                  <div className="ml-1 text-gray-700 bg-white p-2 rounded mt-1 whitespace-pre-wrap break-words">
                                    {log.context.query_full || log.context.query_preview}
                                  </div>
                                </div>
                              )}
                              {(log.context.response_full || log.context.response_preview) && (
                                <div>
                                  <span className="font-semibold text-orange-800">Response:</span>
                                  <div className="ml-1 text-gray-700 bg-white p-2 rounded mt-1 whitespace-pre-wrap break-words">
                                    {log.context.response_full || log.context.response_preview}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Token Usage */}
                          {(log.context.tokens_total || log.context.tokens_prompt) && (
                            <div className="bg-blue-50 p-3 rounded text-xs">
                              <span className="font-semibold text-blue-800">Token Usage:</span>
                              <div className="mt-1 space-y-1">
                                {log.context.tokens_prompt && (
                                  <div>Prompt Tokens: <span className="font-medium">{log.context.tokens_prompt}</span></div>
                                )}
                                {log.context.tokens_completion && (
                                  <div>Completion Tokens: <span className="font-medium">{log.context.tokens_completion}</span></div>
                                )}
                                {log.context.tokens_total && (
                                  <div>Total Tokens: <span className="font-semibold">{log.context.tokens_total}</span></div>
                                )}
                              </div>
                            </div>
                          )}
                          
                          {/* Model and Technical Details */}
                          <div className="bg-gray-50 p-3 rounded text-xs">
                            <span className="font-semibold text-gray-800 block mb-2">Technical Details:</span>
                            <div className="grid grid-cols-2 gap-2">
                              {Object.entries(log.context)
                                .filter(([key]) => !['agent_name', 'query_preview', 'response_preview', 
                                                     'query_full', 'response_full',
                                                     'tokens_total', 'tokens_prompt', 'tokens_completion'].includes(key))
                                .map(([key, value]) => (
                                  <div key={key} className="flex flex-col">
                                    <span className="font-medium text-gray-700">{key}:</span>
                                    <span className="text-gray-600 break-words">
                                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                                    </span>
                                  </div>
                                ))}
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  ) : (
                    <span className="text-orange-400 text-xs">No details</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}