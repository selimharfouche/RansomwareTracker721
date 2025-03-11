"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export function StatsPanel({ title, value, icon, description, className }) {
  const [count, setCount] = useState(0)

  useEffect(() => {
    // Animate the counter
    const duration = 2000 // ms
    const steps = 20
    const stepValue = value / steps
    const stepTime = duration / steps

    let current = 0
    const timer = setInterval(() => {
      current += stepValue
      if (current >= value) {
        setCount(value)
        clearInterval(timer)
      } else {
        setCount(Math.floor(current))
      }
    }, stepTime)

    return () => clearInterval(timer)
  }, [value])

  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="h-4 w-4 text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{count.toLocaleString()}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
        <div className="mt-4 h-1 w-full bg-muted">
          <div className="h-1 bg-primary transition-all duration-1000" style={{ width: `${(count / value) * 100}%` }} />
        </div>
      </CardContent>
    </Card>
  )
}

