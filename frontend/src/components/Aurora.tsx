import { useEffect, useRef } from "react";

export type AuroraState = "idle" | "listening" | "thinking" | "speaking";

export default function Aurora({ state = "idle" }: { state?: AuroraState }) {
  const starsRef = useRef<HTMLSpanElement>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  // Campo estelar disperso
  useEffect(() => {
    const host = starsRef.current;
    if (!host || host.childElementCount) return;
    const placed: { x: number; y: number }[] = [];
    const MIN_DIST = 7;
    let tries = 0;
    while (placed.length < 46 && tries < 600) {
      tries++;
      const x = Math.random() * 100;
      const y = Math.random() * 100;
      if (placed.some((p) => Math.hypot(p.x - x, p.y - y) < MIN_DIST)) continue;
      placed.push({ x, y });

      const s = document.createElement("span");
      s.className = "au-star";
      const sz = (Math.random() * 1.4 + 0.5).toFixed(1);
      s.style.width = `${sz}px`;
      s.style.height = `${sz}px`;
      s.style.left = `${x.toFixed(1)}%`;
      s.style.top = `${y.toFixed(1)}%`;
      s.style.opacity = (0.12 + Math.random() * 0.45).toFixed(2);
      const d = (3 + Math.random() * 4).toFixed(1);
      s.style.animation = `au-tw ${d}s ease-in-out ${(-Math.random() * Number(d)).toFixed(1)}s infinite`;
      host.appendChild(s);
    }
  }, []);

  // Subtormenta: brillo vivo aleatorio cada 20–40s
  useEffect(() => {
    const root = rootRef.current;
    if (!root) return;
    let timer: ReturnType<typeof setTimeout>;
    const schedule = () => {
      const delay = 20000 + Math.random() * 20000;
      timer = setTimeout(() => {
        root.classList.add("au-surge");
        setTimeout(() => root.classList.remove("au-surge"), 3200);
        schedule();
      }, delay);
    };
    schedule();
    return () => clearTimeout(timer);
  }, []);

  return (
    <div ref={rootRef} data-state={state} className="au-root">
      <style>{auroraCss}</style>
      <span ref={starsRef} className="au-stars" aria-hidden />

      <div className="au-veil">
        <span className="au-curtain au-c5" />
        <span className="au-curtain au-c1" />
        <span className="au-curtain au-c2" />

        <svg className="au-filaments" viewBox="0 0 120 400" preserveAspectRatio="none" aria-hidden>
          <defs>
            <linearGradient id="auFil" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0%" stopColor="#fcd34d" stopOpacity="0" />
              <stop offset="22%" stopColor="#7fead4" stopOpacity=".95" />
              <stop offset="68%" stopColor="#b89bf5" stopOpacity=".5" />
              <stop offset="100%" stopColor="#b89bf5" stopOpacity="0" />
            </linearGradient>
          </defs>
          <g className="au-filgroup" stroke="url(#auFil)" strokeWidth="1.3" fill="none">
            <path d="M52 400 Q56 210 50 40" />
            <path d="M60 400 Q56 200 64 36" />
            <path d="M70 400 Q74 210 66 42" />
          </g>
        </svg>

        <span className="au-curtain au-c3" />
        <span className="au-curtain au-c4" />
        <span className="au-voice" />
      </div>

      <span className="au-horizon" />

      {/* Reflejo en el suelo: eco invertido y difuso del velo */}
      <div className="au-reflection" aria-hidden>
        <span className="au-rc au-rc1" />
        <span className="au-rc au-rc2" />
        <span className="au-rc au-rc3" />
      </div>
    </div>
  );
}

const auroraCss = `
.au-root{position:relative;width:460px;height:560px;display:flex;align-items:center;justify-content:center}
.au-stars{position:absolute;inset:-40px;display:block;z-index:0;transition:filter .6s ease}
.au-star{position:absolute;border-radius:50%;background:#cdeee6;will-change:opacity}

.au-veil{position:relative;width:320px;height:440px;display:flex;align-items:center;justify-content:center;transition:transform .8s cubic-bezier(.16,1,.3,1),filter .8s ease;z-index:2;margin-bottom:60px}
.au-curtain{position:absolute;top:0;height:100%;border-radius:50%;will-change:transform;transform-origin:center bottom;
  -webkit-mask-image:linear-gradient(to bottom,transparent 0%,#000 14%,#000 80%,transparent 100%);
  mask-image:linear-gradient(to bottom,transparent 0%,#000 14%,#000 80%,transparent 100%)}
.au-c5{width:150px;filter:blur(34px);opacity:.4;background:linear-gradient(to top,#2dd4bf33 0%,#34b3c4 50%,#8b5cf6 100%);animation:au-sway1 13s ease-in-out infinite}
.au-c1{width:164px;filter:blur(28px);opacity:.6;background:linear-gradient(to top,#fcd34d4d 0%,#2dd4bf 30%,#34b3c4 58%,#8b5cf6 100%);animation:au-sway1 9.5s ease-in-out infinite}
.au-c2{width:128px;filter:blur(22px);opacity:.64;background:linear-gradient(to top,#5eead4aa 0%,#34d3c4 44%,#a78bf5 100%);animation:au-sway2 7.5s ease-in-out infinite}
.au-c3{width:86px;filter:blur(16px);opacity:.62;background:linear-gradient(to top,#eafff6 0%,#7fead4 38%,#b89bf5 100%);animation:au-sway3 11s ease-in-out infinite}
.au-c4{width:56px;filter:blur(12px);opacity:.5;background:linear-gradient(to top,#fcd34d66 0%,#5eead4 42%,#a78bf5 100%);animation:au-sway2 8.4s ease-in-out infinite reverse}

.au-filaments{position:absolute;top:0;left:50%;width:120px;height:440px;transform:translateX(-50%);
  -webkit-mask-image:linear-gradient(to bottom,transparent 0%,#000 18%,#000 72%,transparent 100%);
  mask-image:linear-gradient(to bottom,transparent 0%,#000 18%,#000 72%,transparent 100%)}
.au-filgroup{opacity:.5;animation:au-filflicker 6s ease-in-out infinite}

.au-voice{position:absolute;top:0;left:50%;margin-left:-55px;width:110px;height:100%;opacity:0;border-radius:50%;filter:blur(14px);
  background:linear-gradient(to top,transparent,#eafff6cc,transparent);
  -webkit-mask-image:linear-gradient(to bottom,transparent,#000 24%,#000 76%,transparent);
  mask-image:linear-gradient(to bottom,transparent,#000 24%,#000 76%,transparent)}

.au-horizon{position:absolute;top:372px;left:50%;transform:translateX(-50%);width:300px;height:90px;border-radius:50%;filter:blur(40px);
  background:radial-gradient(ellipse at center,#fcd34d3a 0%,#2dd4bf1a 42%,transparent 70%);animation:au-horizonpulse 8s ease-in-out infinite;z-index:1}

.au-reflection{position:absolute;top:420px;left:50%;transform:translateX(-50%) scaleY(-1);width:320px;height:150px;opacity:.22;z-index:0;
  -webkit-mask-image:linear-gradient(to bottom,#000 0%,transparent 80%);
  mask-image:linear-gradient(to bottom,#000 0%,transparent 80%)}
.au-rc{position:absolute;top:0;left:50%;border-radius:50%;filter:blur(20px);transform-origin:center top}
.au-rc1{width:164px;height:150px;margin-left:-82px;background:linear-gradient(to bottom,#fcd34d4d 0%,#2dd4bf 30%,#8b5cf6 100%);animation:au-sway1 9.5s ease-in-out infinite}
.au-rc2{width:128px;height:150px;margin-left:-64px;background:linear-gradient(to bottom,#5eead4aa 0%,#34d3c4 44%,#a78bf5 100%);animation:au-sway2 7.5s ease-in-out infinite}
.au-rc3{width:86px;height:150px;margin-left:-43px;background:linear-gradient(to bottom,#eafff6 0%,#7fead4 38%,#b89bf5 100%);filter:blur(16px);animation:au-sway3 11s ease-in-out infinite}

[data-state="listening"] .au-veil{transform:scaleX(.78) scaleY(1.05)}
[data-state="listening"] .au-c1{animation-duration:3.4s;opacity:.85}
[data-state="listening"] .au-c2{animation-duration:2.8s;opacity:.85}
[data-state="listening"] .au-c3{animation-duration:3.8s;opacity:.8}
[data-state="listening"] .au-filgroup{opacity:.85;animation-duration:2.6s}
[data-state="thinking"] .au-filgroup{opacity:.7;animation-duration:1.8s}
[data-state="thinking"] .au-c2{animation-duration:4.4s}

[data-state="speaking"] .au-voice{opacity:.82;animation:au-rise 1.4s ease-in-out infinite}
[data-state="speaking"] .au-filgroup{opacity:.8}
[data-state="speaking"] .au-stars{animation:au-starshimmer 1.6s ease-in-out infinite}

.au-surge .au-veil{filter:brightness(1.45) saturate(1.15)}
.au-surge .au-stars{filter:brightness(1.5)}

@keyframes au-sway1{0%,100%{transform:translateX(-5px) skewX(4deg) scaleY(1)}50%{transform:translateX(6px) skewX(-4deg) scaleY(1.04)}}
@keyframes au-sway2{0%,100%{transform:translateX(6px) skewX(-5deg) scaleY(1.02)}50%{transform:translateX(-5px) skewX(5deg) scaleY(1)}}
@keyframes au-sway3{0%,100%{transform:translateX(-4px) skewX(3deg)}50%{transform:translateX(5px) skewX(-3deg)}}
@keyframes au-filflicker{0%,100%{opacity:.38;transform:translateX(-50%) translateY(0)}50%{opacity:.72;transform:translateX(-50%) translateY(-8px)}}
@keyframes au-horizonpulse{0%,100%{opacity:.7;transform:translateX(-50%) scale(1)}50%{opacity:1;transform:translateX(-50%) scale(1.07)}}
@keyframes au-rise{0%{transform:translateY(40%);opacity:0}30%{opacity:.82}100%{transform:translateY(-45%);opacity:0}}
@keyframes au-tw{0%,100%{opacity:.15}50%{opacity:.7}}
@keyframes au-starshimmer{0%,100%{filter:brightness(1)}50%{filter:brightness(1.55)}}
@media (prefers-reduced-motion:reduce){.au-curtain,.au-filgroup,.au-voice,.au-horizon,.au-star,.au-veil,.au-rc,.au-stars{animation:none!important}}
`;