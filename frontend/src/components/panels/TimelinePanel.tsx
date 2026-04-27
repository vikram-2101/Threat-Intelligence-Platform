import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts'
import { Activity } from 'lucide-react'
import type { ConfidenceSnapshot } from '@/types'

interface Props {
  history: ConfidenceSnapshot[]
}

export function TimelinePanel({ history }: Props) {
  // Sort chronologically and prepare data for Recharts
  const chartData = useMemo(() => {
    return [...history]
      .sort((a, b) => new Date(a.calculated_at).getTime() - new Date(b.calculated_at).getTime())
      .map((snap) => ({
        ...snap,
        dateObj: new Date(snap.calculated_at),
        dateStr: new Date(snap.calculated_at).toLocaleDateString(undefined, {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }),
      }))
  }, [history])

  // Custom tooltip for the line chart
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as typeof chartData[0]
      return (
        <div className="bg-surface-850 border border-slate-700/50 p-3 rounded-lg shadow-xl">
          <p className="text-slate-300 text-xs mb-1 font-medium">{data.dateStr}</p>
          <p className="text-brand-400 font-bold text-lg mb-1">{data.score.toFixed(1)}</p>
          <div className="flex items-center gap-1.5 mt-2">
            <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">Trigger:</span>
            <span className="text-[10px] text-slate-300 bg-surface-950 px-1.5 py-0.5 rounded border border-slate-700/50">
              {data.trigger}
            </span>
          </div>
        </div>
      )
    }
    return null
  }

  // Identify snapshots triggered by analysts (to render reference dots)
  const analystActions = chartData.filter((d) => 
    d.trigger.includes('analyst') || d.trigger === 'evidence.created' // Adjust based on exact backend strings mapping
  )

  return (
    <div className="card flex flex-col h-full h-[350px]">
      <div className="px-5 py-4 border-b border-slate-700/50 flex items-center gap-2">
        <Activity className="w-4 h-4 text-brand-400" />
        <h2 className="text-sm font-semibold text-slate-200">Confidence Timeline</h2>
      </div>
      <div className="flex-1 p-4 w-full h-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} vertical={false} />
            <XAxis 
              dataKey="dateStr" 
              stroke="#64748b" 
              fontSize={11} 
              tickMargin={10}
              tickLine={false}
              minTickGap={30}
            />
            <YAxis 
              domain={[0, 100]} 
              stroke="#64748b" 
              fontSize={11}
              tickLine={false}
              axisLine={false}
              ticks={[0, 20, 40, 60, 80, 100]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#6366f1"
              strokeWidth={3}
              dot={{ r: 3, fill: '#1e293b', strokeWidth: 2 }}
              activeDot={{ r: 6, fill: '#6366f1', stroke: '#fff', strokeWidth: 2 }}
            />
            {analystActions.map((action, i) => (
              <ReferenceDot 
                key={`ref-${i}`} 
                x={action.dateStr} 
                y={action.score} 
                r={4}
                fill="#f97316" 
                stroke="#fff" 
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
