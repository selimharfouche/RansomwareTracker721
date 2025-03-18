"use client"

import { useTheme } from "next-themes"
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface RevenueChartProps {
  data: Array<{ name: string; value: number }>
  language: string
}

export function RevenueChart({ data, language }: RevenueChartProps) {
  const { theme } = useTheme()
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#8884d8", "#82ca9d"]

  // Custom label that shows both name and percentage
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }: any) => {
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text x={x} y={y} fill="white" textAnchor={x > cx ? "start" : "end"} dominantBaseline="central" fontSize="12">
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    )
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{language === "en" ? "Top Revenue Ranges" : "Principales Tranches de Revenus"}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={renderCustomizedLabel}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: theme === "dark" ? "#27272a" : "#ffffff",
                  color: theme === "dark" ? "#e4e4e7" : "#18181b",
                  border: `1px solid ${theme === "dark" ? "#3f3f46" : "#e4e4e7"}`,
                }}
                formatter={(value: number, name: string, props: any) => [
                  `${value} ${language === "en" ? "entities" : "entités"} (${(props.payload.percent * 100).toFixed(1)}%)`,
                  props.payload.name,
                ]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

