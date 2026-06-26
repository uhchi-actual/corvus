"use client";

import { useEffect, useRef } from "react";

type Node = {
  x: number;
  y: number;
  r: number;
  phase: number;
};

type MarginNode = {
  gx: number;
  gy: number;
  r: number;
  phase: number;
};

const CORE_NODES: Node[] = [
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

const CORE_EDGES = [
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

// Same visual rhythm as the core field — positioned inside each side gutter.
const MARGIN_NODES: MarginNode[] = [
  { gx: 0.18, gy: 0.11, r: 1.2, phase: 0.35 },
  { gx: 0.52, gy: 0.17, r: 1.0, phase: 1.15 },
  { gx: 0.12, gy: 0.23, r: 1.4, phase: 2.05 },
  { gx: 0.68, gy: 0.14, r: 1.1, phase: 0.75 },
  { gx: 0.34, gy: 0.29, r: 1.3, phase: 1.55 },
  { gx: 0.22, gy: 0.43, r: 1.2, phase: 0.65 },
  { gx: 0.08, gy: 0.5, r: 1.0, phase: 1.45 },
  { gx: 0.58, gy: 0.56, r: 1.5, phase: 2.25 },
  { gx: 0.3, gy: 0.63, r: 1.1, phase: 0.95 },
  { gx: 0.16, gy: 0.73, r: 1.3, phase: 1.25 },
  { gx: 0.48, gy: 0.8, r: 1.0, phase: 2.15 },
  { gx: 0.1, gy: 0.87, r: 1.4, phase: 0.55 },
  { gx: 0.62, gy: 0.91, r: 1.2, phase: 1.85 },
  { gx: 0.4, gy: 0.96, r: 1.1, phase: 2.65 },
];

const MARGIN_EDGES = [
  [0, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 0],
  [5, 6],
  [6, 7],
  [7, 8],
  [8, 5],
  [9, 10],
  [10, 11],
  [11, 12],
  [12, 13],
  [13, 9],
  [4, 5],
  [8, 9],
] as const;

const DASHBOARD_MAX_WIDTH = 1180;
const DASHBOARD_SIDE_PADDING = 22;

function gutterWidth(viewWidth: number): number {
  const contentWidth = Math.min(DASHBOARD_MAX_WIDTH, viewWidth - DASHBOARD_SIDE_PADDING * 2);
  return Math.max(0, (viewWidth - contentWidth) / 2 - DASHBOARD_SIDE_PADDING);
}

function marginPositions(viewWidth: number, viewHeight: number, side: "left" | "right") {
  const gutter = gutterWidth(viewWidth);
  return MARGIN_NODES.map((node) => {
    const x =
      side === "left"
        ? gutter * node.gx
        : viewWidth - gutter * node.gx;
    return {
      x,
      y: node.gy * viewHeight,
      r: node.r,
      phase: node.phase,
    };
  });
}

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
      height = window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const drawEdge = (
      a: { x: number; y: number; phase: number },
      b: { x: number; y: number },
      t: number,
    ) => {
      const pulse = 0.42 + 0.28 * Math.sin(t + a.phase);
      context.strokeStyle = `rgba(31, 113, 108, ${0.09 + pulse * 0.08})`;
      context.beginPath();
      context.moveTo(a.x, a.y);
      context.lineTo(b.x, b.y);
      context.stroke();
    };

    const drawNode = (node: { x: number; y: number; r: number; phase: number }, t: number) => {
      const pulse = 0.55 + 0.45 * Math.sin(t + node.phase);
      context.fillStyle = `rgba(211, 188, 155, ${0.18 + pulse * 0.18})`;
      context.beginPath();
      context.arc(node.x, node.y, node.r + pulse * 0.8, 0, Math.PI * 2);
      context.fill();
    };

    const drawCluster = (
      nodes: Array<{ x: number; y: number; r: number; phase: number }>,
      edges: ReadonlyArray<readonly [number, number]>,
      t: number,
    ) => {
      for (const [aIndex, bIndex] of edges) {
        drawEdge(nodes[aIndex], nodes[bIndex], t);
      }
      for (const node of nodes) {
        drawNode(node, t);
      }
    };

    const draw = (time: number) => {
      const t = reducedMotion ? 0 : time / 1800;
      context.clearRect(0, 0, width, height);

      context.lineWidth = 1;

      for (const [aIndex, bIndex] of CORE_EDGES) {
        const a = CORE_NODES[aIndex];
        const b = CORE_NODES[bIndex];
        drawEdge(
          { x: a.x * width, y: a.y * height, phase: a.phase },
          { x: b.x * width, y: b.y * height },
          t,
        );
      }

      for (const node of CORE_NODES) {
        drawNode({ x: node.x * width, y: node.y * height, r: node.r, phase: node.phase }, t);
      }

      const gutter = gutterWidth(width);
      if (gutter >= 40) {
        const leftNodes = marginPositions(width, height, "left");
        const rightNodes = marginPositions(width, height, "right");
        drawCluster(leftNodes, MARGIN_EDGES, t);
        drawCluster(rightNodes, MARGIN_EDGES, t);
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
