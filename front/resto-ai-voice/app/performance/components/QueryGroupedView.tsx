"use client";

import { useState } from 'react'

interface QueryGroupedViewProps {
  logs: Array<{
    timestamp: string;
    operation: string;
    duration_seconds: number;
    context?: Record<string, any>;
  }>
}

interface QueryGroup {
  query_id: string;
  logs: Array<{
    timestamp: string;
    operation: string;
    duration_seconds: number;
    context?: Record<string, any>;
  }>;
  totalDuration: number;
  operations: string[];
  agents: string[];
  firstTimestamp: string;
  queryPreview?: string;
}

export default function QueryGroupedView({ logs }: QueryGroupedViewProps) {
  const [expandedQueries, setExpandedQueries] = useState<Set<string>>(new Set())
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set())

  const toggleQuery = (queryId: string) => {
    const newExpanded = new Set(expandedQueries)
    if (newExpanded.has(queryId)) {
      newExpanded.delete(queryId)
    } else {
      newExpanded.add(queryId)
    }
    setExpandedQueries(newExpanded)
  }

  const toggleLog = (logId: string) => {
    const newExpanded = new Set(expandedLogs)
    if (newExpanded.has(logId)) {
      newExpanded.delete(logId)
    } else {
      newExpanded.add(logId)
    }
    setExpandedLogs(newExpanded)
  }

  // Group logs by query_id
  const queryGroups: QueryGroup[] = []
  const queryMap = new Map<string, QueryGroup>()

  logs.forEach(log => {
    const queryId = log.context?.query_id || 'no-query-id'
    
    if (!queryMap.has(queryId)) {
      queryMap.set(queryId, {
        query_id: queryId,
        logs: [],
        totalDuration: 0,
        operations: [],
        agents: [],
        firstTimestamp: log.timestamp,
        queryPreview: log.context?.query_preview || log.context?.query_full
      })
    }

    const group = queryMap.get(queryId)!
    group.logs.push(log)
    group.totalDuration += log.duration_seconds
    
    if (!group.operations.includes(log.operation)) {
      group.operations.push(log.operation)
    }
    
    const agent = log.context?.agent_name
    if (agent && !group.agents.includes(agent)) {
      group.agents.push(agent)
    }

    // Keep the earliest timestamp
    if (new Date(log.timestamp) < new Date(group.firstTimestamp)) {
      group.firstTimestamp = log.timestamp
    }

    // Prefer query_preview from earlier logs
    if (!group.queryPreview && (log.context?.query_preview || log.context?.query_full)) {
      group.queryPreview = log.context.query_preview || log.context.query_full
    }
  })

  // Convert to array and sort by timestamp (most recent first)
  queryGroups.push(...Array.from(queryMap.values()).sort((a, b) => 
    new Date(b.firstTimestamp).getTime() - new Date(a.firstTimestamp).getTime()
  ))

  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-orange-400">
        <p>No logs to display</p>
      </div>
    )
  }

  const agentColors: Record<string, string> = {
    'orchestrator': 'bg-purple-100 text-purple-700',
    'menu': 'bg-blue-100 text-blue-700',
    'faq': 'bg-green-100 text-green-700',
    'reservation': 'bg-pink-100 text-pink-700',
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-orange-600 mb-4">
        <p className="italic">
          📊 Showing {queryGroups.length} unique {queryGroups.length === 1 ? 'query' : 'queries'} with {logs.length} total {logs.length === 1 ? 'operation' : 'operations'}
        </p>
      </div>

      {queryGroups.map((group) => {
        const isExpanded = expandedQueries.has(group.query_id)
        const sortedLogs = [...group.logs].sort((a, b) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        )

        return (
          <div key={group.query_id} className="bg-white rounded-lg shadow-md overflow-hidden border-2 border-orange-200">
            {/* Query Header - Clickable */}
            <div 
              className="p-4 bg-gradient-to-r from-orange-50 to-amber-50 cursor-pointer hover:bg-orange-100 transition-colors"
              onClick={() => toggleQuery(group.query_id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-lg font-bold text-orange-800">
                      {isExpanded ? '▼' : '▶'}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-gray-800 font-mono">Query ID:</span>
                        <span className="text-xs font-mono bg-white px-2 py-1 rounded border border-orange-300 text-gray-900">
                          {group.query_id === 'no-query-id' ? 'No Query ID' : group.query_id}
                        </span>
                      </div>
                      {group.queryPreview && (
                        <div className="text-sm text-gray-900 italic mt-1">
                          "{group.queryPreview}"
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4 text-xs ml-8">
                    <span className="text-gray-600">
                      🕐 {new Date(group.firstTimestamp).toLocaleString()}
                    </span>
                    <span className="font-semibold text-orange-700">
                      ⏱️ Total: {group.totalDuration.toFixed(3)}s
                    </span>
                    <span className="text-gray-600">
                      📝 {group.logs.length} {group.logs.length === 1 ? 'operation' : 'operations'}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {group.agents.map(agent => (
                    <span 
                      key={agent}
                      className={`px-2 py-1 rounded-full text-xs font-semibold ${agentColors[agent] || 'bg-gray-100 text-gray-700'}`}
                    >
                      {agent}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Expanded Operations List */}
            {isExpanded && (
              <div className="p-4 bg-white border-t-2 border-orange-100">
                <div className="space-y-2">
                  {sortedLogs.map((log, idx) => {
                    const agent = log.context?.agent_name || 'N/A'
                    const logId = `${group.query_id}-${idx}`
                    const isLogExpanded = expandedLogs.has(logId)
                    
                    return (
                      <div key={idx} className="border border-orange-200 rounded-lg overflow-hidden">
                        {/* Log Header - Clickable */}
                        <div 
                          className="flex items-center justify-between p-3 bg-orange-50 hover:bg-orange-100 cursor-pointer transition-colors"
                          onClick={() => toggleLog(logId)}
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <span className="text-orange-700 font-bold">
                              {isLogExpanded ? '▼' : '▶'}
                            </span>
                            <span className="text-xs text-gray-800">
                              {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                            <span className="px-2 py-1 bg-white rounded-full text-xs font-medium text-orange-800 border border-orange-300">
                              {log.operation}
                            </span>
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${agentColors[agent] || 'bg-gray-100 text-gray-700'}`}>
                              {agent}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            {log.context?.response_preview && (
                              <div className="max-w-xs text-xs text-gray-800 truncate hidden md:block">
                                {log.context.response_preview}
                              </div>
                            )}
                            <span className="text-sm font-bold text-orange-900 whitespace-nowrap">
                              {log.duration_seconds.toFixed(3)}s
                            </span>
                          </div>
                        </div>

                        {/* Log Details - Expanded */}
                        {isLogExpanded && (
                          <div className="p-4 bg-white space-y-3 text-xs">
                            {/* Query/Response */}
                            {(log.context?.query_preview || log.context?.response_preview || log.context?.query_full || log.context?.response_full) && (
                              <div className="bg-orange-50 p-3 rounded">
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
                            {(log.context?.tokens_total || log.context?.tokens_prompt) && (
                              <div className="bg-blue-50 p-3 rounded">
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

                            {/* Additional Context */}
                            <div className="bg-gray-50 p-3 rounded">
                              <span className="font-semibold text-gray-800">Context:</span>
                              <div className="mt-1 space-y-1">
                                {log.context?.invoked_by && (
                                  <div><span className="text-gray-800">Invoked by:</span> <span className="font-medium text-gray-900">{log.context.invoked_by}</span></div>
                                )}
                                {log.context?.tool_name && (
                                  <div><span className="text-gray-800">Tool:</span> <span className="font-medium text-gray-900">{log.context.tool_name}</span></div>
                                )}
                                {log.context?.endpoint && (
                                  <div><span className="text-gray-800">Endpoint:</span> <span className="font-medium font-mono text-gray-900">{log.context.endpoint}</span></div>
                                )}
                                {log.context?.user_id && (
                                  <div><span className="text-gray-800">User ID:</span> <span className="font-medium font-mono text-gray-900">{log.context.user_id}</span></div>
                                )}
                                {log.context?.query_length !== undefined && (
                                  <div><span className="text-gray-800">Query Length:</span> <span className="font-medium text-gray-900">{log.context.query_length} chars</span></div>
                                )}
                                {log.context?.response_length !== undefined && (
                                  <div><span className="text-gray-800">Response Length:</span> <span className="font-medium text-gray-900">{log.context.response_length} chars</span></div>
                                )}
                              </div>
                            </div>

                            {/* Timing Details */}
                            {(log.context?.agent_retrieval_time || log.context?.agent_processing_time || log.context?.overhead_time) && (
                              <div className="bg-purple-50 p-3 rounded">
                                <span className="font-semibold text-purple-800">Timing Breakdown:</span>
                                <div className="mt-1 space-y-1">
                                  {log.context.agent_retrieval_time && (
                                    <div><span className="text-gray-800">Agent Retrieval:</span> <span className="font-medium text-gray-900">{log.context.agent_retrieval_time}s</span></div>
                                  )}
                                  {log.context.agent_processing_time && (
                                    <div><span className="text-gray-800">Agent Processing:</span> <span className="font-medium text-gray-900">{log.context.agent_processing_time}s</span></div>
                                  )}
                                  {log.context.overhead_time && (
                                    <div><span className="text-gray-800">Overhead:</span> <span className="font-medium text-gray-900">{log.context.overhead_time}s</span></div>
                                  )}
                                  {log.context.orchestrator_time && (
                                    <div><span className="text-gray-800">Orchestrator:</span> <span className="font-medium text-gray-900">{log.context.orchestrator_time}s</span></div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Full Context (Raw) */}
                            {log.context && Object.keys(log.context).length > 0 && (
                              <details className="bg-gray-100 p-3 rounded">
                                <summary className="font-semibold text-gray-800 cursor-pointer hover:text-orange-700">
                                  Full Context (JSON)
                                </summary>
                                <pre className="mt-2 text-xs overflow-x-auto bg-white p-2 rounded border border-gray-300 text-gray-900">
                                  {JSON.stringify(log.context, null, 2)}
                                </pre>
                              </details>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>

                {/* Summary Stats */}
                <div className="mt-4 p-3 bg-orange-50 rounded-lg">
                  <div className="text-xs font-semibold text-orange-800 mb-2">Query Summary:</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div>
                      <span className="text-gray-600">Total Duration:</span>
                      <div className="font-bold text-orange-700">{group.totalDuration.toFixed(3)}s</div>
                    </div>
                    <div>
                      <span className="text-gray-600">Avg Per Operation:</span>
                      <div className="font-bold text-orange-700">
                        {(group.totalDuration / group.logs.length).toFixed(3)}s
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Fastest:</span>
                      <div className="font-bold text-green-700">
                        {Math.min(...group.logs.map(l => l.duration_seconds)).toFixed(3)}s
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Slowest:</span>
                      <div className="font-bold text-red-700">
                        {Math.max(...group.logs.map(l => l.duration_seconds)).toFixed(3)}s
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
