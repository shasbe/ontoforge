/** Force-directed relaxation for schema diagrams.
 *
 * The emitted grid layout keeps golden files stable but reads poorly at 30+
 * nodes. This runs client-side only; the result is persisted into the
 * downloaded JSON's display block, so a tidied layout is not throwaway.
 */
export type Pos = { x: number; y: number };

export function forceLayout(
  ids: string[],
  edges: [string, string][],
  seed: Record<string, Pos>,
  opts: { iterations?: number; width?: number; height?: number } = {}
): Record<string, Pos> {
  const N = ids.length;
  if (N === 0) return {};
  const iterations = opts.iterations ?? 400;
  const W = opts.width ?? Math.max(1400, N * 78);
  const H = opts.height ?? Math.max(900, N * 52);

  const idx = new Map(ids.map((id, i) => [id, i]));
  const px = new Float64Array(N);
  const py = new Float64Array(N);
  ids.forEach((id, i) => {
    const s = seed[id];
    // Seed from current positions, jittered, so repeated runs converge
    // differently rather than locking into the same poor local minimum.
    px[i] = (s?.x ?? 0) + (Math.random() - 0.5) * 40;
    py[i] = (s?.y ?? 0) + (Math.random() - 0.5) * 40;
  });

  const deg = new Float64Array(N);
  const links: [number, number][] = [];
  for (const [a, b] of edges) {
    const i = idx.get(a), j = idx.get(b);
    if (i === undefined || j === undefined || i === j) continue;  // self-loops don't pull
    links.push([i, j]);
    deg[i]++; deg[j]++;
  }

  const area = W * H;
  const k = Math.sqrt(area / N);          // ideal separation
  const REPULSION = k * k * 1.05;
  const vx = new Float64Array(N);
  const vy = new Float64Array(N);

  for (let it = 0; it < iterations; it++) {
    const cooling = 1 - it / iterations;
    vx.fill(0); vy.fill(0);

    for (let i = 0; i < N; i++) {
      for (let j = i + 1; j < N; j++) {
        let dx = px[i] - px[j], dy = py[i] - py[j];
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) { dx = Math.random() - 0.5; dy = Math.random() - 0.5; d2 = 1; }
        const f = REPULSION / d2;
        const d = Math.sqrt(d2);
        vx[i] += (dx / d) * f; vy[i] += (dy / d) * f;
        vx[j] -= (dx / d) * f; vy[j] -= (dy / d) * f;
      }
    }
    for (const [i, j] of links) {
      const dx = px[i] - px[j], dy = py[i] - py[j];
      const d = Math.max(1, Math.hypot(dx, dy));
      // High-degree nodes resist being pulled to the rim, which keeps the
      // structural hubs (Patient, Organization) near the centre.
      const f = (d * d) / k / 90;
      const wi = 1 / (1 + deg[i] * 0.14), wj = 1 / (1 + deg[j] * 0.14);
      vx[i] -= (dx / d) * f * wi; vy[i] -= (dy / d) * f * wi;
      vx[j] += (dx / d) * f * wj; vy[j] += (dy / d) * f * wj;
    }
    for (let i = 0; i < N; i++) {
      vx[i] -= px[i] * 0.008;                       // gentle gravity to origin
      vy[i] -= py[i] * 0.008;
      const step = Math.min(Math.hypot(vx[i], vy[i]), 34 * cooling + 1);
      const m = Math.max(1e-6, Math.hypot(vx[i], vy[i]));
      px[i] += (vx[i] / m) * step;
      py[i] += (vy[i] / m) * step;
    }
  }

  // normalise into a tidy positive-ish box, snapped to 10px
  let minX = Infinity, minY = Infinity;
  for (let i = 0; i < N; i++) { minX = Math.min(minX, px[i]); minY = Math.min(minY, py[i]); }
  const out: Record<string, Pos> = {};
  ids.forEach((id, i) => {
    out[id] = {
      x: Math.round((px[i] - minX - W / 2) / 10) * 10,
      y: Math.round((py[i] - minY - H / 2) / 10) * 10,
    };
  });
  return out;
}
