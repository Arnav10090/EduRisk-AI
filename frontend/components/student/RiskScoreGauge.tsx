'use client';

import { useEffect, useState } from 'react';

interface RiskScoreGaugeProps {
  riskScore: number;  // 0-100
  size?: number;      // Diameter in pixels
}

export function RiskScoreGauge({ riskScore, size = 200 }: RiskScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0);

  // Animate from 0 to actual score on mount
  useEffect(() => {
    const duration = 1000; // 1 second
    const steps = 60;
    const increment = riskScore / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= riskScore) {
        setAnimatedScore(riskScore);
        clearInterval(timer);
      } else {
        setAnimatedScore(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [riskScore]);

  // Determine color based on risk score
  const getColor = (score: number) => {
    if (score <= 33) return '#22c55e'; // green (low risk)
    if (score <= 66) return '#f59e0b'; // amber (medium risk)
    return '#ef4444'; // red (high risk)
  };

  // Calculate arc parameters
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const arcLength = (animatedScore / 100) * circumference * 0.75; // 270 degrees (0.75 of circle)
  const strokeDasharray = `${arcLength} ${circumference}`;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-[135deg]">
        {/* Background arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth="12"
          strokeDasharray={`${circumference * 0.75} ${circumference}`}
        />
        
        {/* Colored arc */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor(animatedScore)}
          strokeWidth="12"
          strokeDasharray={strokeDasharray}
          strokeLinecap="round"
          className="transition-all duration-100"
        />
      </svg>

      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-4xl font-bold" style={{ color: getColor(animatedScore) }}>
          {animatedScore}
        </div>
        <div className="text-sm text-muted-foreground">Risk Score</div>
      </div>
    </div>
  );
}
