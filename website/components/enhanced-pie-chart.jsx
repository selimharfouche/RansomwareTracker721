"use client"

import React, { useState } from 'react';
import { 
  PieChart as RechartsPieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer,
  Sector,
  Legend,
  Tooltip
} from 'recharts';

export function EnhancedPieChart({ data, index, category, colors, valueFormatter }) {
  const [activeIndex, setActiveIndex] = useState(null);
  
  // Calculate percentages
  const total = data.reduce((sum, entry) => sum + entry[category], 0);
  const dataWithPercentage = data.map(entry => ({
    ...entry,
    percentage: Math.round((entry[category] / total) * 100)
  }));
  
  // Custom active shape for the pie chart
  const renderActiveShape = (props) => {
    const { 
      cx, cy, innerRadius, outerRadius, startAngle, endAngle,
      fill, payload, percent, value
    } = props;
    
    return (
      <g>
        <Sector
          cx={cx}
          cy={cy}
          innerRadius={innerRadius}
          outerRadius={outerRadius + 8}
          startAngle={startAngle}
          endAngle={endAngle}
          fill={fill}
        />
        <Sector
          cx={cx}
          cy={cy}
          startAngle={startAngle}
          endAngle={endAngle}
          innerRadius={outerRadius + 10}
          outerRadius={outerRadius + 12}
          fill={fill}
        />
        <text x={cx} y={cy - 8} textAnchor="middle" fill="currentColor" className="font-medium">
          {payload[index]}
        </text>
        <text x={cx} y={cy + 8} textAnchor="middle" fill="currentColor" className="text-sm font-medium">
          {valueFormatter ? valueFormatter(value) : value}
        </text>
        <text x={cx} y={cy + 25} textAnchor="middle" fill="currentColor" className="text-xs">
          {`(${(percent * 100).toFixed(1)}%)`}
        </text>
      </g>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-background border rounded-md p-2 shadow-md text-sm">
          <p className="font-medium">{data[index]}</p>
          <p className="text-primary">{valueFormatter ? valueFormatter(data[category]) : data[category]}</p>
          <p className="text-xs text-muted-foreground">{data.percentage}% of total</p>
        </div>
      );
    }
    return null;
  };

  // Custom legend that includes percentages
  const CustomLegend = ({ payload }) => {
    return (
      <ul className="flex flex-wrap justify-center gap-4 mt-4 text-xs md:text-sm">
        {payload.map((entry, idx) => (
          <li 
            key={`item-${idx}`} 
            className="flex items-center gap-2 cursor-pointer transition-colors hover:text-primary" 
            onClick={() => setActiveIndex(idx === activeIndex ? null : idx)}
          >
            <div 
              className="w-3 h-3 rounded-sm" 
              style={{ backgroundColor: entry.color }} 
            />
            <span className={`${idx === activeIndex ? 'font-bold' : 'font-medium'}`}>
              {entry.value}: {dataWithPercentage[idx].percentage}%
            </span>
          </li>
        ))}
      </ul>
    );
  };

  const onPieEnter = (_, index) => {
    setActiveIndex(index);
  };
  
  const onPieLeave = () => {
    setActiveIndex(null);
  };

  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsPieChart>
          <Pie
            data={dataWithPercentage}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            dataKey={category}
            nameKey={index}
            activeIndex={activeIndex}
            activeShape={renderActiveShape}
            onMouseEnter={onPieEnter}
            onMouseLeave={onPieLeave}
          >
            {dataWithPercentage.map((entry, idx) => (
              <Cell 
                key={`cell-${idx}`} 
                fill={colors[idx % colors.length]} 
                stroke="transparent"
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}