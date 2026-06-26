"use client";

import { useEffect, useRef } from "react";

type Node = {
  x: number;
  y: number;
  r: number;
  phase: number;
};

const NODES: Node[] = [
  { x: 0.12, y: 0.14, r: 1.4, phase: 0.1 },
  { x: 0.22, y: 0.2, r: 1.1, phase: 0.8 },
  { x: 0.34, y: 0.16, r: 1.3, phase: 1.7 },
  { x: 0.48, y: 0.22, r: 1.0, phase: 2.1 },
  { x: 0.66, y: 0.13, r: 1.2, phase: 0.4 },
  { x: 0.78, y: 0.24, r: 1.5, phase: 1.1 },
  { x: 0.9, y: 0.18, r: 1.0, phase: 2.4 },
  { x: 0.15, y: 0.48, r: 1.2, phase: 0.6 },
  { x: 0.3, y: 0.54, r: 1.5, phase: 1.5 },
  { x: 0.44, y: 0.46, r: 1.1, phase: 2.2 },
  { x: 0.58, y: 0.56, r: 1.3, phase: 0.2 },
  { x: 0.74, y: 0.48, r: 1.1, phase: 1.8 },
  { x: 0.88, y: 0.58, r: 1.4, phase: 2.8 },
  { x: 0.2, y: 0.78, r: 1.0, phase: 1.0 },
  { x: 0.38, y: 0.84, r: 1.3, phase: 2.6 },
  { x: 0.54, y: 0.76, r: 1.0, phase: 0.9 },
  { x: 0.72, y: 0.82, r: 1.5, phase: 2.0 },
  { x: 0.86, y: 0.74, r: 1.1, phase: 0.5 },
];

const EDGES = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 5],
  [4, 5],
  [5, 6],
  [1, 8],
  [7, 8],
  [8, 9],
  [9, 10],
  [10, 11],
  [11, 12],
  [7, 13],
  [13, 14],
  [14, 15],
  [15, 16],
  [16, 17],
  [10, 15],
  [5, 11],
] as const;

export function ConstellationField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    let raf = 0;
    let width = 0;
    let height = 0;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const resize = () => {
      width = window.innerWidth;
      height = Math.max(window.innerHeight, document.documentElement.scrollHeight);
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (time: number) => {
      const t = reducedMotion ? 0 : time / 1800;
      context.clearRect(0, 0, width, height);

      context.lineWidth = 1;
      for (const [aIndex, bIndex] of EDGES) {
        const a = NODES[aIndex];
        const b = NODES[bIndex];
        const pulse = 0.42 + 0.28 * Math.sin(t + a.phase);
        context.strokeStyle = `rgba(31, 113, 108, ${0.09 + pulse * 0.08})`;
        context.beginPath();
        context.moveTo(a.x * width, a.y * height);
        context.lineTo(b.x * width, b.y * height);
        context.stroke();
      }

      for (const node of NODES) {
        const pulse = 0.55 + 0.45 * Math.sin(t + node.phase);
        const x = node.x * width;
        const y = node.y * height;
        context.fillStyle = `rgba(211, 188, 155, ${0.18 + pulse * 0.18})`;
        context.beginPath();
        context.arc(x, y, node.r + pulse * 0.8, 0, Math.PI * 2);
        context.fill();
      }

      if (!reducedMotion) {
        raf = requestAnimationFrame(draw);
      }
    };

    resize();
    window.addEventListener("resize", resize);
    raf = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className="constellationField" aria-hidden />;
}
