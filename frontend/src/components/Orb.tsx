export type OrbState = "idle" | "listening" | "thinking" | "speaking";

export default function Orb({ state = "idle" }: { state?: OrbState }) {
  return (
    <div data-state={state} className="orb-root">
      <style>{orbCss}</style>

      <span className="orb-glow" />

      <span className="orb-orbit orb-o1"><span className="sat sat-cyan" /></span>
      <span className="orb-orbit orb-o2"><span className="sat sat-coral" /></span>
      <span className="orb-orbit orb-o3"><span className="sat sat-purple" /></span>

      <span className="orb-arc" />
      <span className="orb-sphere orb-base" />
      <span className="orb-sphere orb-purpledrift" />
      <span className="orb-cyan" />
      <span className="orb-spec" />
    </div>
  );
}

const orbCss = `
.orb-root{position:relative;width:300px;height:300px;display:flex;align-items:center;justify-content:center}
.orb-root>span{position:absolute}
.orb-root>span:not(.orb-orbit){border-radius:50%;will-change:transform,opacity}

.orb-glow{width:240px;height:240px;filter:blur(42px);opacity:.8;
  background:radial-gradient(circle,#ff8ab855 0%,#b15cd633 42%,transparent 70%);
  animation:orb-glowdrift 16s ease-in-out infinite}

.orb-sphere{width:150px;height:150px}
.orb-base{background:radial-gradient(circle at 34% 30%,#ffe9f2 0%,#ff9ec4 26%,#e07ab0 50%,#a85fd6 76%,#7c3aed 100%);
  animation:orb-breathe 6.5s ease-in-out infinite}
.orb-purpledrift{opacity:0;background:radial-gradient(circle at 34% 30%,#f3ddff 0%,#cf9bf5 30%,#9b5cd6 62%,#6d3ab8 100%);
  animation:orb-breathe 6.5s ease-in-out infinite,orb-pd 16s ease-in-out infinite}

.orb-cyan{width:170px;height:170px;filter:blur(14px);mix-blend-mode:screen;opacity:.35;
  background:radial-gradient(circle at 62% 66%,#7fe3f0 0%,#22d3ee 32%,transparent 60%);
  animation:orb-cyandrift 11s ease-in-out infinite}

.orb-spec{width:150px;height:150px;background:radial-gradient(circle at 35% 28%,#ffffffcc 0%,transparent 24%)}

.orb-arc{width:196px;height:196px;border:2px solid transparent;border-top-color:#c9a0ff;filter:blur(.4px);opacity:0;border-radius:50%}

.orb-orbit{border-radius:50%;will-change:transform}
.orb-o1{width:230px;height:230px;animation:orb-spin 17s linear infinite}
.orb-o2{width:276px;height:276px;animation:orb-spin 23s linear infinite reverse}
.orb-o3{width:200px;height:200px;animation:orb-spin 29s linear infinite}
.sat{position:absolute;top:0;left:50%;border-radius:50%;filter:blur(1px)}
.sat-cyan{width:13px;height:13px;margin-left:-6.5px;background:radial-gradient(circle at 35% 30%,#bff5fb 0%,#22d3ee 60%,#0e9ec4 100%);box-shadow:0 0 12px #22d3ee99}
.sat-coral{width:10px;height:10px;margin-left:-5px;background:radial-gradient(circle at 35% 30%,#ffd9c4 0%,#ff8a5b 60%,#d85a30 100%);box-shadow:0 0 11px #ff8a5b99}
.sat-purple{width:15px;height:15px;margin-left:-7.5px;background:radial-gradient(circle at 35% 30%,#e6d4ff 0%,#a85fd6 60%,#7c3aed 100%);box-shadow:0 0 13px #9b5cd699}

[data-state="listening"] .orb-cyan{opacity:.8;animation:orb-cyandrift 4s ease-in-out infinite}
[data-state="listening"] .orb-base{animation:orb-breathe 2.4s ease-in-out infinite}
[data-state="listening"] .orb-glow{background:radial-gradient(circle,#22d3ee55 0%,#7fa8f033 45%,transparent 70%)}
[data-state="listening"] .orb-o1{animation-duration:7s}
[data-state="listening"] .orb-o2{animation-duration:9s}
[data-state="listening"] .orb-o3{animation-duration:11s}

[data-state="thinking"] .orb-arc{opacity:.7;animation:orb-spin 2.4s linear infinite}

[data-state="speaking"] .orb-base{animation:orb-pulse 1s ease-in-out infinite}
[data-state="speaking"] .orb-glow{opacity:1;animation:orb-glowdrift 16s ease-in-out infinite,orb-pulse 1s ease-in-out infinite}
[data-state="speaking"] .orb-o1{animation-duration:4.5s}
[data-state="speaking"] .orb-o2{animation-duration:5.5s}
[data-state="speaking"] .orb-o3{animation-duration:6.5s}

@keyframes orb-breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.045)}}
@keyframes orb-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
@keyframes orb-spin{to{transform:rotate(360deg)}}
@keyframes orb-pd{0%,100%{opacity:0}30%{opacity:0}50%{opacity:.85}70%{opacity:0}}
@keyframes orb-cyandrift{0%,100%{opacity:.3;transform:translate(0,0)}50%{opacity:.6;transform:translate(6px,-5px)}}
@keyframes orb-glowdrift{
  0%,100%{background:radial-gradient(circle,#ff8ab855 0%,#b15cd633 42%,transparent 70%)}
  50%{background:radial-gradient(circle,#b15cd655 0%,#7c3aed33 42%,transparent 70%)}}
@media (prefers-reduced-motion:reduce){.orb-root>span{animation:none!important}}
`;