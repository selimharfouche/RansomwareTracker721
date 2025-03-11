// components/ui/chart.tsx
import type React from "react"

interface BarChartProps {
  data: { name: string; value: number }[]
  index: string
  categories: string[]
  colors: string[]
  valueFormatter?: (value: number) => string
  yAxisWidth?: number
}

export const BarChart: React.FC<BarChartProps> = ({
  data,
  index,
  categories,
  colors,
  valueFormatter,
  yAxisWidth = 80,
}) => {
  return (
    <div>
      {/* Placeholder for BarChart */}
      <p>BarChart Component</p>
      <pre>{JSON.stringify({ data, index, categories, colors, valueFormatter, yAxisWidth }, null, 2)}</pre>
    </div>
  )
}

interface PieChartProps {
  data: { name: string; value: number }[]
  index: string
  category: string
  colors: string[]
  valueFormatter?: (value: number) => string
}

export const PieChart: React.FC<PieChartProps> = ({ data, index, category, colors, valueFormatter }) => {
  return (
    <div>
      {/* Placeholder for PieChart */}
      <p>PieChart Component</p>
      <pre>{JSON.stringify({ data, index, category, colors, valueFormatter }, null, 2)}</pre>
    </div>
  )
}

