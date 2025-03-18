"use client"

import { useTheme } from "next-themes"
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface EmployeeChartProps {
  data: Array<{ name: string; count: number }>
  language: string
}

export function EmployeeChart({ data, language }: EmployeeChartProps) {
  const { theme } = useTheme()

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{language === "en" ? "Entities by Employee Range" : "Entités par Nombre d'Employés"}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }} layout="vertical">
              <XAxis type="number" tick={{ fill: theme === "dark" ? "#e4e4e7" : "#18181b" }} />
              <YAxis
                dataKey="name"
                type="category"
                width={100}
                tick={{ fill: theme === "dark" ? "#e4e4e7" : "#18181b" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: theme === "dark" ? "#27272a" : "#ffffff",
                  color: theme === "dark" ? "#e4e4e7" : "#18181b",
                  border: `1px solid ${theme === "dark" ? "#3f3f46" : "#e4e4e7"}`,
                }}
                formatter={(value: number) => [
                  `${value} ${language === "en" ? "entities" : "entités"}`,
                  language === "en" ? "Count" : "Nombre",
                ]}
              />
              <Bar
                dataKey="count"
                fill="#10b981"
                name={language === "en" ? "Entities" : "Entités"}
                radius={[0, 4, 4, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}

