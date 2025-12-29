"use client";

import { useEffect, useRef } from 'react'
import { Chart, registerables } from 'chart.js'
import 'chartjs-adapter-date-fns'

// Register all Chart.js components
Chart.register(...registerables)

interface PerformanceChartsProps {
  logs: Array<{
    timestamp: string;
    operation: string;
    duration_seconds: number;
    context?: Record<string, any>;
  }>
}

export default function PerformanceCharts({ logs }: PerformanceChartsProps) {
  const chartRef1 = useRef<HTMLCanvasElement>(null)
  const chartRef2 = useRef<HTMLCanvasElement>(null)
  const chartRef3 = useRef<HTMLCanvasElement>(null)
  const chartRef4 = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (logs.length === 0) return

    // Filter logs for agent_invocation operations only
    const agentLogs = logs.filter(log => 
      log.operation === 'agent_invocation' && log.context?.agent_name
    )
    console.log('Agent Logs for Charts:', agentLogs)
    console.log('all operations:', logs)
    // Clean up previous charts
    const cleanupCharts = () => {
      if (chartRef1.current) {
        const chart1 = Chart.getChart(chartRef1.current)
        if (chart1) chart1.destroy()
      }
      if (chartRef2.current) {
        const chart2 = Chart.getChart(chartRef2.current)
        if (chart2) chart2.destroy()
      }
      if (chartRef3.current) {
        const chart3 = Chart.getChart(chartRef3.current)
        if (chart3) chart3.destroy()
      }
      if (chartRef4.current) {
        const chart4 = Chart.getChart(chartRef4.current)
        if (chart4) chart4.destroy()
      }
    }

    cleanupCharts()

    if (agentLogs.length === 0) {
      return
    }

    // Define color palette for different agents
    const agentColors: Record<string, { bg: string; border: string }> = {
      'orchestrator': { bg: 'rgba(249, 115, 22, 0.7)', border: 'rgba(249, 115, 22, 1)' },
      'menu': { bg: 'rgba(251, 146, 60, 0.7)', border: 'rgba(251, 146, 60, 1)' },
      'reservation': { bg: 'rgba(253, 186, 116, 0.7)', border: 'rgba(253, 186, 116, 1)' },
      'faq': { bg: 'rgba(254, 215, 170, 0.7)', border: 'rgba(254, 215, 170, 1)' },
    }

    // Chart 1: Average Response Time by Agent (Bar Chart)
    if (chartRef1.current) {
      const ctx1 = chartRef1.current.getContext('2d')
      if (ctx1) {
        const agentStats = agentLogs.reduce((acc, log) => {
          const agent = log.context!.agent_name
          if (!acc[agent]) {
            acc[agent] = []
          }
          acc[agent].push(log.duration_seconds)
          return acc
        }, {} as Record<string, number[]>)

        const labels = Object.keys(agentStats)
        const averages = Object.values(agentStats).map(durations =>
          durations.reduce((sum, val) => sum + val, 0) / durations.length
        )
        const backgroundColors = labels.map(agent => 
          agentColors[agent]?.bg || 'rgba(249, 115, 22, 0.7)'
        )
        const borderColors = labels.map(agent => 
          agentColors[agent]?.border || 'rgba(249, 115, 22, 1)'
        )

        new Chart(ctx1, {
          type: 'bar',
          data: {
            labels,
            datasets: [{
              label: 'Average Duration (seconds)',
              data: averages,
              backgroundColor: backgroundColors,
              borderColor: borderColors,
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
              title: {
                display: true,
                text: 'Average Response Time by Agent',
                font: { size: 16 }
              },
              legend: {
                display: false
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Seconds'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Agent'
                }
              }
            }
          }
        })
      }
    }

    // Chart 2: Response Time Timeline by Agent (Multi-line Chart)
    if (chartRef2.current) {
      const ctx2 = chartRef2.current.getContext('2d')
      if (ctx2) {
        const agentTimelines = agentLogs.reduce((acc, log) => {
          const agent = log.context!.agent_name
          if (!acc[agent]) {
            acc[agent] = []
          }
          acc[agent].push({
            x: new Date(log.timestamp).getTime(),
            y: log.duration_seconds
          })
          return acc
        }, {} as Record<string, Array<{ x: number; y: number }>>)

        // Sort each agent's timeline
        Object.values(agentTimelines).forEach(timeline => {
          timeline.sort((a, b) => a.x - b.x)
        })

        const datasets = Object.entries(agentTimelines).map(([agent, data]) => ({
          label: agent,
          data,
          backgroundColor: agentColors[agent]?.bg || 'rgba(249, 115, 22, 0.2)',
          borderColor: agentColors[agent]?.border || 'rgba(249, 115, 22, 1)',
          borderWidth: 2,
          pointRadius: 4,
          tension: 0.1,
          fill: false
        }))

        new Chart(ctx2, {
          type: 'line',
          data: { datasets },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
              title: {
                display: true,
                text: 'Agent Response Time Over Time',
                font: { size: 16 }
              },
              legend: {
                display: true,
                position: 'top'
              }
            },
            scales: {
              x: {
                type: 'time',
                time: {
                  unit: 'minute',
                  displayFormats: {
                    minute: 'HH:mm',
                    hour: 'MMM d, HH:mm'
                  }
                },
                title: {
                  display: true,
                  text: 'Time'
                }
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Seconds'
                }
              }
            }
          }
        })
      }
    }

    // Chart 3: Agent Performance Statistics (Min/Avg/Max)
    if (chartRef3.current) {
      const ctx3 = chartRef3.current.getContext('2d')
      if (ctx3) {
        const agentStats = agentLogs.reduce((acc, log) => {
          const agent = log.context!.agent_name
          if (!acc[agent]) {
            acc[agent] = []
          }
          acc[agent].push(log.duration_seconds)
          return acc
        }, {} as Record<string, number[]>)

        const labels = Object.keys(agentStats)
        const minValues = Object.values(agentStats).map(durations => Math.min(...durations))
        const avgValues = Object.values(agentStats).map(durations =>
          durations.reduce((sum, val) => sum + val, 0) / durations.length
        )
        const maxValues = Object.values(agentStats).map(durations => Math.max(...durations))

        new Chart(ctx3, {
          type: 'bar',
          data: {
            labels,
            datasets: [
              {
                label: 'Min',
                data: minValues,
                backgroundColor: 'rgba(34, 197, 94, 0.7)',
                borderColor: 'rgba(34, 197, 94, 1)',
                borderWidth: 1
              },
              {
                label: 'Average',
                data: avgValues,
                backgroundColor: 'rgba(249, 115, 22, 0.7)',
                borderColor: 'rgba(249, 115, 22, 1)',
                borderWidth: 1
              },
              {
                label: 'Max',
                data: maxValues,
                backgroundColor: 'rgba(239, 68, 68, 0.7)',
                borderColor: 'rgba(239, 68, 68, 1)',
                borderWidth: 1
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
              title: {
                display: true,
                text: 'Agent Performance Statistics (Min/Avg/Max)',
                font: { size: 16 }
              },
              legend: {
                display: true,
                position: 'top'
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Seconds'
                }
              },
              x: {
                title: {
                  display: true,
                  text: 'Agent'
                }
              }
            }
          }
        })
      }
    }

    // Chart 4: Agent Invocation Count (Doughnut Chart)
    if (chartRef4.current) {
      const ctx4 = chartRef4.current.getContext('2d')
      if (ctx4) {
        const agentCounts = agentLogs.reduce((acc, log) => {
          const agent = log.context!.agent_name
          acc[agent] = (acc[agent] || 0) + 1
          return acc
        }, {} as Record<string, number>)

        const labels = Object.keys(agentCounts)
        const data = Object.values(agentCounts)
        const backgroundColors = labels.map(agent => 
          agentColors[agent]?.bg || 'rgba(249, 115, 22, 0.7)'
        )
        const borderColors = labels.map(agent => 
          agentColors[agent]?.border || 'rgba(249, 115, 22, 1)'
        )

        new Chart(ctx4, {
          type: 'doughnut',
          data: {
            labels,
            datasets: [{
              data,
              backgroundColor: backgroundColors,
              borderColor: borderColors,
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
              title: {
                display: true,
                text: 'Agent Invocation Count',
                font: { size: 16 }
              },
              legend: {
                position: 'bottom'
              }
            }
          }
        })
      }
    }

    return () => {
      cleanupCharts()
    }
  }, [logs])

  const agentInvocationLogs = logs.filter(log => 
    log.operation === 'agent_invocation' && log.context?.agent_name
  )

  if (logs.length === 0) {
    return (
      <div className="text-center py-8 text-orange-400">
        <p>No performance data available to display charts</p>
      </div>
    )
  }

  if (agentInvocationLogs.length === 0) {
    return (
      <div className="text-center py-8 text-orange-400">
        <p>No agent invocation data available. Charts require logs with operation=&quot;agent_invocation&quot; and context.agent_name field.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-orange-50 p-4 rounded-lg">
        <canvas ref={chartRef1} />
      </div>
      <div className="bg-orange-50 p-4 rounded-lg">
        <canvas ref={chartRef2} />
      </div>
      <div className="bg-orange-50 p-4 rounded-lg">
        <canvas ref={chartRef3} />
      </div>
      <div className="bg-orange-50 p-4 rounded-lg">
        <canvas ref={chartRef4} />
      </div>
    </div>
  )
}