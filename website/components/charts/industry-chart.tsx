"use client"

import { useTheme } from "next-themes"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface IndustryChartProps {
  data: Array<{ name: string; count: number }>
  language: string
}

export function IndustryChart({ data, language }: IndustryChartProps) {
  const { theme } = useTheme()

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{language === "en" ? "Top 5 Industries" : "Top 5 des Industries"}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <XAxis
                dataKey="name"
                angle={-45}
                textAnchor="end"
                height={70}
                tick={{ fill: theme === "dark" ? "#e4e4e7" : "#18181b" }}
              />
              <YAxis tick={{ fill: theme === "dark" ? "#e4e4e7" : "#18181b" }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: theme === "dark" ? "#27272a" : "#ffffff",
                  color: theme === "dark" ? "#e4e4e7" : "#18181b",
                  border: `1px solid ${theme === "dark" ? "#3f3f46" : "#e4e4e7"}`,
                }}
                labelStyle={{
                  color: theme === "dark" ? "#e4e4e7" : "#18181b",
                }}
              />
              <Bar
                dataKey="count"
                fill="#3b82f6"
                name={language === "en" ? "Entities" : "Entités"}
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

