PRODUCT_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Máster Product Management: AI & Data-Driven — LAB Lovable — NexusFinLabs</title>
<meta name="description" content="Guía completa del LAB de Lovable. 3 sesiones para construir un prototipo funcional sin código. Setup, prompt engineering, Supabase y presentación final.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,600&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --gold:#C9A84C;--gold-light:#F5DFA0;--gold-glow:rgba(201,168,76,.15);
  --dark:#0D0D0D;--dark2:#1A1A1A;--dark3:#262626;--dark4:#333;
  --text:#f0f0f0;--muted:#8b8b8b;--muted2:#666;
  --border:rgba(255,255,255,.08);--border2:rgba(255,255,255,.12);
  --code-bg:#111;--code-border:#2a2a2a;
  --green:#22c55e;--blue:#60a5fa;--red:#f87171;--purple:#a78bfa;--amber:#fbbf24;
}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;background:var(--dark);color:var(--text);min-height:100vh}

nav{position:fixed;top:0;left:0;right:0;z-index:100;height:52px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;background:rgba(13,13,13,.92);backdrop-filter:blur(16px);border-bottom:1px solid var(--border)}
.nav-brand{display:flex;align-items:center;gap:10px;text-decoration:none}
.nav-logo{font-size:18px;font-weight:300;color:#fff;letter-spacing:.06em}
.nav-logo strong{font-weight:800}
.nav-sep{width:1px;height:20px;background:var(--border2)}
.nav-sub{font-size:10px;color:var(--muted);letter-spacing:.04em}
.nav-r{display:flex;gap:4px;align-items:center}
.nav-r a{color:var(--muted);text-decoration:none;padding:5px 10px;border-radius:6px;font-size:12px;font-weight:500;transition:.15s}
.nav-r a:hover{color:#fff;background:rgba(255,255,255,.06)}
.nav-cta{background:var(--gold)!important;color:var(--dark)!important;font-weight:700!important;border-radius:100px!important;padding:6px 16px!important}

/* HERO */
.hero{background:var(--dark);min-height:360px;position:relative;overflow:hidden;display:flex;align-items:center;padding:80px 32px 48px}
.hero::before{content:'';position:absolute;top:-200px;right:-100px;width:900px;height:900px;background:repeating-conic-gradient(from 30deg,transparent 0deg,transparent 50deg,rgba(201,168,76,.06) 50deg,rgba(201,168,76,.06) 55deg,transparent 55deg);border-radius:50%;animation:spin 60s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.hero::after{content:'';position:absolute;top:50px;right:-50px;width:600px;height:600px;border:1px solid rgba(201,168,76,.08);border-radius:50%}
.hero-content{position:relative;z-index:1;max-width:700px}
.hero-badges{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.h-badge{background:rgba(255,255,255,.06);border:1px solid var(--border2);border-radius:8px;padding:6px 14px;font-size:11px;font-weight:600;color:var(--muted);display:flex;align-items:center;gap:6px}
.hero h1{font-size:clamp(2rem,3.5vw,3rem);font-weight:300;color:#fff;letter-spacing:-.02em;line-height:1.1;margin-bottom:14px}
.hero h1 strong{font-weight:900}
.hero-em{color:var(--gold)}
.live-badge{display:inline-flex;align-items:center;gap:6px;background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.25);border-radius:8px;padding:4px 12px;font-size:11px;font-weight:700;color:var(--gold);margin-left:8px;vertical-align:middle}
.live-dot{width:6px;height:6px;background:var(--gold);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.hero-sub{color:var(--muted);font-size:14px;line-height:1.7;max-width:520px;margin-bottom:22px}
.hero-meta{display:flex;gap:24px;flex-wrap:wrap}
.hm .n{font-size:1.4rem;font-weight:900;color:var(--gold)}
.hm .l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:2px}

/* LAYOUT */
.page{display:grid;grid-template-columns:220px 1fr;max-width:1200px;margin:0 auto}
@media(max-width:900px){.page{grid-template-columns:1fr}.sidebar{display:none!important}}

/* SIDEBAR */
.sidebar{position:sticky;top:52px;height:calc(100vh - 52px);overflow-y:auto;padding:16px 12px;border-right:1px solid var(--border);background:var(--dark2);scrollbar-width:thin;scrollbar-color:var(--dark4) transparent}
.sb-section{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.14em;color:var(--muted2);margin:14px 0 6px;padding-left:8px}
.sb-section:first-child{margin-top:0}
.sidebar a{display:block;font-size:12px;padding:5px 10px;border-radius:6px;text-decoration:none;color:var(--muted);font-weight:500;transition:.12s;margin-bottom:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sidebar a:hover{background:rgba(255,255,255,.04);color:#fff}

/* MAIN */
.main{padding:28px 36px 100px;min-width:0}
.main h2{font-size:1.4rem;font-weight:900;letter-spacing:-.02em;margin:48px 0 6px;padding-top:20px;border-top:1px solid var(--border);color:#fff}
.main h2:first-child{margin-top:0;padding-top:0;border-top:none}
.main h2 .e{margin-right:6px}
.main h3{font-size:1rem;font-weight:800;margin:28px 0 8px;color:#e0e0e0}
.main p{font-size:13px;line-height:1.75;color:var(--muted);margin-bottom:10px}
.main ul,.main ol{font-size:13px;line-height:1.75;color:var(--muted);margin:0 0 14px 18px}
.main li{margin-bottom:3px}
.main strong{color:#e0e0e0}
.main a{color:var(--blue);text-decoration:none;font-weight:500}
.main a:hover{text-decoration:underline}
.main hr{border:none;border-top:1px solid var(--border);margin:36px 0}

/* CODE */
pre{background:var(--code-bg);border:1px solid var(--code-border);border-radius:8px;padding:16px 18px;margin:10px 0 16px;overflow-x:auto;font-family:'JetBrains Mono',monospace;font-size:12px;line-height:1.7;color:#c9d1d9}
code{background:rgba(255,255,255,.06);padding:2px 6px;border-radius:3px;font-size:12px;font-family:'JetBrains Mono',monospace;color:var(--purple)}
pre code{background:none;padding:0;color:inherit}
.cm{color:#6e7681}.kw{color:#ff7b72}.st{color:#a5d6ff}.vr{color:var(--gold-light)}

/* TABLES */
.tbl{width:100%;border-collapse:collapse;margin:12px 0 20px;border:1px solid var(--border);border-radius:8px;overflow:hidden;font-size:12px}
.tbl th{text-align:left;padding:8px 12px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:var(--dark2);border-bottom:1px solid var(--border)}
.tbl td{padding:8px 12px;border-bottom:1px solid var(--border);color:var(--muted)}
.tbl td strong{color:#e0e0e0}
.tbl tr:last-child td{border-bottom:none}
.tbl tr:hover td{background:rgba(255,255,255,.02)}
.tbl .gold{color:var(--gold);font-weight:700}

/* BOXES */
.box{border-radius:8px;padding:14px 16px;margin:12px 0 16px;font-size:12px;line-height:1.65;border:1px solid}
.box-info{background:rgba(96,165,250,.06);border-color:rgba(96,165,250,.15);color:var(--blue)}
.box-tip{background:rgba(34,197,94,.06);border-color:rgba(34,197,94,.15);color:var(--green)}
.box-warn{background:rgba(251,191,36,.06);border-color:rgba(251,191,36,.15);color:var(--amber)}
.box-err{background:rgba(248,113,113,.06);border-color:rgba(248,113,113,.15);color:var(--red)}
.box-title{font-weight:800;font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;display:flex;align-items:center;gap:5px}

/* SESSION CARDS */
.session-card{background:var(--dark2);border:1px solid var(--border);border-radius:12px;padding:20px;margin:16px 0}
.session-card:hover{border-color:var(--border2)}
.session-header{display:flex;align-items:center;gap:14px;margin-bottom:16px}
.session-num{min-width:44px;height:44px;background:var(--gold);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;color:var(--dark);flex-shrink:0}
.session-meta h3{font-size:15px;font-weight:900;color:#fff;margin:0 0 3px}
.session-meta .pills{display:flex;gap:6px;flex-wrap:wrap}
.pill{font-size:10px;font-weight:700;padding:2px 8px;border-radius:100px}
.pill-clase{background:rgba(96,165,250,.12);color:var(--blue);border:1px solid rgba(96,165,250,.2)}
.pill-mentoria{background:rgba(201,168,76,.12);color:var(--gold);border:1px solid rgba(201,168,76,.2)}
.pill-duracion{background:rgba(255,255,255,.05);color:var(--muted);border:1px solid var(--border)}
.pill-presencial{background:rgba(34,197,94,.08);color:var(--green);border:1px solid rgba(34,197,94,.15)}

/* BLOCK SECTION inside session */
.block{background:var(--dark3);border:1px solid var(--border);border-radius:8px;padding:14px 16px;margin:10px 0}
.block-title{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--gold);margin-bottom:10px;display:flex;align-items:center;gap:6px}
.block ul{list-style:none;margin:0;padding:0}
.block li{font-size:12px;color:var(--muted);padding:3px 0;display:flex;align-items:flex-start;gap:6px}
.block li::before{content:'→';color:var(--gold);font-weight:700;flex-shrink:0;margin-top:1px}

/* CHECKLIST */
.checklist{list-style:none;margin:8px 0;padding:0}
.checklist li{font-size:12px;color:#c0c0c0;padding:4px 0;display:flex;align-items:center;gap:8px}
.checklist li::before{content:'□';color:var(--gold);font-weight:700;font-size:13px}

/* PROMPT EXAMPLE */
.prompt-bad{background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.15);border-radius:8px;padding:12px 14px;margin:8px 0;font-size:12px;color:var(--red)}
.prompt-good{background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.15);border-radius:8px;padding:12px 14px;margin:8px 0;font-size:12px;color:var(--green)}
.prompt-label{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;margin-bottom:5px;opacity:.7}

/* FRAMEWORK */
.framework{background:var(--dark3);border:1px solid rgba(201,168,76,.2);border-radius:8px;padding:14px 16px;margin:12px 0;font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--gold-light);line-height:1.8}

/* WEEK LABEL */
.week{display:inline-flex;align-items:center;gap:5px;background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.15);border-radius:100px;padding:3px 11px;font-size:10px;font-weight:800;color:var(--gold);margin-bottom:10px}

/* CREDITS TABLE */
.credit-total td{background:rgba(201,168,76,.06)!important;color:var(--gold)!important;font-weight:800!important}

/* RESOURCES */
.res-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin:14px 0}
.res-link{background:var(--dark2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-decoration:none;transition:.15s;display:flex;align-items:center;gap:8px}
.res-link:hover{border-color:var(--border2);text-decoration:none}
.res-link .ri{font-size:18px;flex-shrink:0}
.res-link .rl{font-size:12px;font-weight:600;color:#e0e0e0}
.res-link .rd{font-size:10px;color:var(--muted)}

/* DELIVERABLE */
.deliv{background:rgba(34,197,94,.04);border:1px solid rgba(34,197,94,.12);border-radius:8px;padding:14px 16px;margin:14px 0}
.deliv h4{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--green);margin-bottom:8px}

/* FEEDBACK TABLE */
.fb-table td:first-child{font-weight:700;color:#e0e0e0;white-space:nowrap}

/* CHEAT SHEET (igual que /classes) */
.cheat{background:var(--dark2);border:1px solid var(--border);border-radius:10px;padding:18px;margin:16px 0}
.cheat h4{font-size:12px;font-weight:800;color:var(--gold);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.cheat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:640px){.cheat-grid{grid-template-columns:1fr}}
.cheat-item{background:var(--dark3);border:1px solid var(--border);border-radius:6px;padding:10px 12px}
.cheat-item .cmd{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--green);margin-bottom:3px;word-break:break-all;font-weight:700}
.cheat-item .desc{font-size:11px;color:var(--muted)}

/* ERA TIMELINE */
.era-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px;margin:14px 0}
.era-card{background:var(--dark2);border:1px solid var(--border);border-radius:8px;padding:14px;transition:.15s}
.era-card:hover{border-color:var(--border2)}
.era-card .era-label{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:var(--gold);margin-bottom:4px}
.era-card .era-title{font-size:13px;font-weight:800;color:#e0e0e0;margin-bottom:6px}
.era-card .era-desc{font-size:11px;color:var(--muted);line-height:1.55}
.era-card .era-arrow{font-size:11px;color:var(--gold);margin-top:6px;font-weight:700}

/* 5 LAYERS */
.layers{display:flex;flex-direction:column;gap:4px;margin:12px 0}
.layer{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:6px;border:1px solid var(--border)}
.layer:nth-child(1){background:rgba(201,168,76,.08);border-color:rgba(201,168,76,.2)}
.layer:nth-child(2){background:rgba(96,165,250,.06);border-color:rgba(96,165,250,.15)}
.layer:nth-child(3){background:rgba(167,139,250,.06);border-color:rgba(167,139,250,.15)}
.layer:nth-child(4){background:rgba(34,197,94,.06);border-color:rgba(34,197,94,.15)}
.layer:nth-child(5){background:rgba(248,113,113,.06);border-color:rgba(248,113,113,.15)}
.layer .lnum{font-size:10px;font-weight:900;color:var(--gold);min-width:16px}
.layer .ltitle{font-size:12px;font-weight:800;color:#e0e0e0;min-width:130px}
.layer .ldesc{font-size:11px;color:var(--muted)}

/* INSIGHT BOX */
.insight{background:linear-gradient(135deg,rgba(201,168,76,.08),rgba(201,168,76,.03));border:1px solid rgba(201,168,76,.25);border-radius:10px;padding:16px 18px;margin:16px 0;text-align:center}
.insight p{font-size:14px;color:#e0e0e0;font-weight:600;font-style:italic;margin:0;line-height:1.6}
.insight .insight-label{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:var(--gold);margin-bottom:8px}

footer{background:var(--dark);border-top:1px solid var(--border);padding:28px 24px;text-align:center}
footer p{color:var(--muted2);font-size:11px}
footer a{color:var(--muted);text-decoration:none}

@media(max-width:768px){.main{padding:20px 18px 80px}.hero{padding:70px 20px 36px}.hero h1{font-size:1.8rem}}
</style>
</head>
<body>

<nav>
  <a href="/" class="nav-brand">
    <span class="nav-logo"><strong>nuclio</strong>°</span>
    <span class="nav-sep"></span>
    <span class="nav-sub">digital school</span>
  </a>
  <div class="nav-r">
    <a href="/classes">Automation & AI</a>
    <a href="#setup">Setup</a>
    <a href="#sesion1">Sesión I</a>
    <a href="#sesion2">Sesión II</a>
    <a href="#sesion3">Sesión III</a>
    <a href="mailto:alberto@nexusfinlabs.com" class="nav-cta">Contacto</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="hero-content">
    <div class="hero-badges">
      <div class="h-badge">LAB Presencial + Online</div>
      <div class="h-badge">✳️ <strong>Lovable</strong></div>
      <div class="h-badge">🗄️ <strong>Supabase</strong></div>
    </div>
    <h1>Máster en <strong><span class="hero-em">Product Management</span></strong> <span class="live-badge"><span class="live-dot"></span>AI & Data-Driven</span></h1>
    <p class="hero-sub">LAB de Lovable — Guía del instructor. 3 sesiones para que cada grupo construya un prototipo funcional sin escribir una línea de código.</p>
    <div class="hero-meta">
      <div class="hm"><div class="n">3</div><div class="l">Sesiones</div></div>
      <div class="hm"><div class="n">~8h</div><div class="l">Total LAB</div></div>
      <div class="hm"><div class="n">3–4</div><div class="l">Alumnos/grupo</div></div>
      <div class="hm"><div class="n">20–40</div><div class="l">Créditos/grupo</div></div>
    </div>
  </div>
</div>

<div class="page">

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sb-section">Intro (10-15 min)</div>
  <a href="#intro">🧠 Qué es PM</a>
  <a href="#historia">Historia y eras</a>
  <a href="#capas">Las 5 capas</a>
  <a href="#frameworks">Frameworks</a>
  <a href="#insight">Insight clave</a>
  <div class="sb-section">LAB Setup</div>
  <a href="#setup">📦 Setup Inicial</a>
  <a href="#cuentas">Cuentas necesarias</a>
  <a href="#deps">Librerías</a>
  <a href="#env">Variables .env</a>
  <a href="#contexto">🎯 Contexto del LAB</a>
  <a href="#sesiones">📅 Dashboard sesiones</a>
  <div class="sb-section">Sesión I</div>
  <a href="#sesion1">Teoría + Arranque</a>
  <a href="#b1">B1 · ¿Qué es Lovable?</a>
  <a href="#b2">B2 · Framework PRE-LOVABLE</a>
  <a href="#b3">B3 · Prompt Engineering</a>
  <a href="#b4">B4 · Hands-on</a>
  <div class="sb-section">Sesión II</div>
  <a href="#sesion2">Mentoría por grupos</a>
  <a href="#checklist">Checklist de avance</a>
  <a href="#problemas">Problemas frecuentes</a>
  <a href="#supabase">Supabase setup</a>
  <div class="sb-section">Sesión III</div>
  <a href="#sesion3">Presentaciones</a>
  <a href="#formato">Formato presentación</a>
  <a href="#feedback">Framework feedback</a>
  <div class="sb-section">Extras</div>
  <a href="#creditos">💳 Créditos</a>
  <a href="#entregable">📋 Entregable</a>
  <a href="#recursos">📎 Recursos</a>
</aside>

<!-- MAIN -->
<main class="main">

<!-- ============ INTRO PM ============ -->
<h2 id="intro" style="margin-top:0;padding-top:0;border-top:none"><span class="e">🧠</span> Intro a Product Management <span class="week" style="margin-left:8px;vertical-align:middle">10–15 min</span></h2>
<p>Visión estructurada para contextualizar el máster antes del primer LAB.</p>

<h3 id="historia">Historia y Eras del PM</h3>
<div class="era-grid">
  <div class="era-card">
    <div class="era-label">Años 30</div>
    <div class="era-title">🏭 Industria</div>
    <div class="era-desc">Nace en P&G con el <em>Brand Manager</em>. Responsabilidades: producto + mercado + posicionamiento.</div>
    <div class="era-arrow">→ Producto = negocio + cliente</div>
  </div>
  <div class="era-card">
    <div class="era-label">S. XX</div>
    <div class="era-title">🏗️ Ingeniería Clásica</div>
    <div class="era-desc">Modelo en V, Waterfall, Systems Engineering. Alta precisión, baja adaptabilidad.</div>
    <div class="era-arrow">→ Producto = especificación → desarrollo → validación</div>
  </div>
  <div class="era-card">
    <div class="era-label">2000–2015</div>
    <div class="era-title">🌐 Era Software</div>
    <div class="era-desc">Agile (Scrum, Kanban), Lean Startup. Iteración constante y feedback de mercado.</div>
    <div class="era-arrow">→ Producto = iteración + feedback + mercado</div>
  </div>
  <div class="era-card">
    <div class="era-label">2020+</div>
    <div class="era-title">🤖 Era Actual</div>
    <div class="era-desc">AI, data, plataformas. El producto no se entrega, evoluciona. Aprende en tiempo real.</div>
    <div class="era-arrow">→ Producto = sistema vivo que aprende</div>
  </div>
</div>

<h3 id="capas">Qué define un producto digital — Las 5 capas</h3>
<p>Un producto digital no es una app. Es un sistema con 5 capas interdependientes:</p>
<div class="layers">
  <div class="layer"><span class="lnum">1</span><span class="ltitle">User Value</span><span class="ldesc">Problema que resuelve · Usuario objetivo</span></div>
  <div class="layer"><span class="lnum">2</span><span class="ltitle">Business Model</span><span class="ldesc">Monetización · CAC, LTV, pricing</span></div>
  <div class="layer"><span class="lnum">3</span><span class="ltitle">Product Experience (UX)</span><span class="ldesc">Interfaz · Flujo de usuario</span></div>
  <div class="layer"><span class="lnum">4</span><span class="ltitle">Technology Layer</span><span class="ldesc">Backend · APIs · Infraestructura</span></div>
  <div class="layer"><span class="lnum">5</span><span class="ltitle">Data Layer</span><span class="ldesc">Generación de datos · Analytics · AI</span></div>
</div>
<div class="insight">
  <div class="insight-label">Fórmula</div>
  <p>Producto digital = Value + UX + Tech + Data + Business</p>
</div>

<h3 id="frameworks">Frameworks clave — Chuleta</h3>
<div class="cheat">
  <h4>🗒️ Los Estándares que importan hoy</h4>
  <div class="cheat-grid">
    <div class="cheat-item"><div class="cmd">Product Lifecycle</div><div class="desc">Discovery → Definition → Development → Delivery → Iteration (ciclo continuo)</div></div>
    <div class="cheat-item"><div class="cmd">Dual Track Agile</div><div class="desc">Discovery (¿qué construir?) en paralelo con Delivery (construirlo). Estándar actual.</div></div>
    <div class="cheat-item"><div class="cmd">Product Operating Model</div><div class="desc">Cómo se organiza la empresa: equipos, decisiones y alineación con negocio.</div></div>
    <div class="cheat-item"><div class="cmd">North Star Metric</div><div class="desc">Métrica central del producto: engagement, revenue o usage. Una sola.</div></div>
    <div class="cheat-item"><div class="cmd">OKRs</div><div class="desc">Objective (dirección) + Key Results (medición). Equivalente moderno a requirements.</div></div>
    <div class="cheat-item"><div class="cmd">Data Product Thinking</div><div class="desc">Datos como producto: APIs internas, pipelines reutilizables.</div></div>
    <div class="cheat-item"><div class="cmd">AI Product Systems</div><div class="desc">RAG + Feedback loops + Evaluation pipelines. Estándares aún emergentes.</div></div>
    <div class="cheat-item"><div class="cmd">Analogía Ingeniería</div><div class="desc">Requisitos→Discovery · Diseño→Product Design · Validación→Metrics+Feedback</div></div>
  </div>
</div>

<table class="tbl">
  <thead><tr><th>Ingeniería Clásica</th><th>Product Digital</th></tr></thead>
  <tbody>
    <tr><td>Requisitos</td><td><strong>Discovery</strong></td></tr>
    <tr><td>Diseño de sistema</td><td><strong>Product Design</strong></td></tr>
    <tr><td>Implementación</td><td><strong>Delivery</strong></td></tr>
    <tr><td>Validación</td><td><strong>Metrics + Feedback</strong></td></tr>
    <tr><td>Integración</td><td><strong>Platform Thinking</strong></td></tr>
  </tbody>
</table>

<div class="box box-info" id="insight">
  <div class="box-title">💡 Insight clave — La diferencia real</div>
  <strong>PM básico</strong> → gestión de tareas<br>
  <strong>PM técnico</strong> → ejecución de features<br>
  <strong>PM con data + AI</strong> → <em>impacto en negocio medido en tiempo real</em><br><br>
  <span style="color:var(--gold);font-weight:700">→ El salto no es de herramientas, es de mindset: de sistema cerrado a sistema adaptativo.</span>
</div>

<hr>

<!-- SETUP -->
<h2 id="setup"><span class="e">📦</span> Setup Inicial — Día 1</h2>
<p>Cada grupo debe tener estas cuentas antes de la Sesión I.</p>

<h3 id="cuentas">Cuentas necesarias</h3>
<table class="tbl">
  <thead><tr><th>Plataforma</th><th>URL</th><th>Plan</th><th>Cuándo</th></tr></thead>
  <tbody>
    <tr><td><strong>Lovable</strong></td><td><a href="https://lovable.dev" target="_blank">lovable.dev</a></td><td>Free (5 cred/día) o Pro (20€/mes)</td><td class="gold">Antes S1</td></tr>
    <tr><td><strong>GitHub</strong></td><td><a href="https://github.com" target="_blank">github.com</a></td><td>Free</td><td class="gold">Antes S1</td></tr>
    <tr><td><strong>Supabase</strong></td><td><a href="https://supabase.com" target="_blank">supabase.com</a></td><td>Free</td><td>S2 (si quieren datos reales)</td></tr>
    <tr><td><strong>Vercel</strong></td><td><a href="https://vercel.com" target="_blank">vercel.com</a></td><td>Free Hobby</td><td>S3 (para deploy)</td></tr>
    <tr><td><strong>Figma</strong></td><td><a href="https://figma.com" target="_blank">figma.com</a></td><td>Free Starter</td><td>Opcional</td></tr>
  </tbody>
</table>

<h3 id="deps">Librerías (para los que quieran editar en local)</h3>
<pre><span class="cm"># Node.js >= 18.x requerido</span>
node --version

<span class="cm"># Vite + React (base que usa Lovable internamente)</span>
npm create vite@latest my-app -- --template react-ts
cd my-app && npm install

<span class="cm"># Tailwind CSS (Lovable lo usa por defecto)</span>
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

<span class="cm"># shadcn/ui (componentes que genera Lovable)</span>
npx shadcn@latest init

<span class="cm"># Supabase client</span>
npm install @supabase/supabase-js

<span class="cm"># Deploy a Vercel (opcional)</span>
npm install -g vercel
vercel login</pre>

<h3 id="env">Variables de entorno (.env.local)</h3>
<pre><span class="cm"># Crear en la raíz del proyecto</span>
<span class="vr">VITE_SUPABASE_URL</span>=https://xxxx.supabase.co
<span class="vr">VITE_SUPABASE_ANON_KEY</span>=eyJ...</pre>

<div class="box box-warn">
  <div class="box-title">⚠️ Importante</div>
  El <code>.env.local</code> nunca va a GitHub. Añadir al <code>.gitignore</code> antes del primer push.
</div>

<!-- CONTEXTO -->
<h2 id="contexto"><span class="e">🎯</span> Contexto del LAB</h2>
<p>Los alumnos llegan al LAB con:</p>
<ul>
  <li>Un proyecto/producto <strong>ya conceptualizado</strong> del Lab de Product Inception con Borja Núñez</li>
  <li>Conocimiento de Product Management y metodologías ágiles</li>
  <li>Ninguna o mínima experiencia en código</li>
</ul>
<p><strong>Objetivo del LAB:</strong> en 3 sesiones, cada grupo tiene un <strong>prototipo funcional y desplegable</strong>, construido con Lovable, sin escribir código a mano.</p>

<div class="box box-info">
  <div class="box-title">ℹ️ Grupos</div>
  Dividir en grupos de <strong>3–4 alumnos</strong>. Cada grupo trabaja sobre su propio proyecto de Inception. El instructor rota por los grupos en Sesión II.
</div>

<!-- DASHBOARD -->
<h2 id="sesiones"><span class="e">📅</span> Dashboard de Sesiones</h2>
<table class="tbl">
  <thead><tr><th>Sesión</th><th>Tipo</th><th>Formato</th><th>Duración</th></tr></thead>
  <tbody>
    <tr><td><strong>Sesión I</strong></td><td>Clase + Hands-on</td><td>Presencial (BCN) + Online</td><td>2–3h</td></tr>
    <tr><td><strong>Sesión II</strong></td><td>Mentoría grupos</td><td>Presencial + Online</td><td>2–3h</td></tr>
    <tr><td><strong>Sesión III</strong></td><td>Presentaciones</td><td>Presencial + Online</td><td>2–3h</td></tr>
  </tbody>
</table>

<!-- ============ SESIÓN I ============ -->
<h2 id="sesion1"><span class="e">🎬</span> Sesión I — Teoría, Planificación y Arranque</h2>

<div class="session-card">
  <div class="session-header">
    <div class="session-num">I</div>
    <div class="session-meta">
      <h3>Teoría, Planificación y Arranque del Prototipo</h3>
      <div class="pills">
        <span class="pill pill-clase">Clase directa</span>
        <span class="pill pill-presencial">Presencial + Online</span>
        <span class="pill pill-duracion">2–3 horas</span>
      </div>
    </div>
  </div>

  <!-- BLOQUE 1 -->
  <h3 id="b1">Bloque 1 · ¿Qué es Lovable y cómo funciona? (30 min)</h3>
  <div class="block">
    <div class="block-title">📖 Teoría</div>
    <ul>
      <li>Lovable como <strong>Full-Stack AI Engineer</strong>: genera React + Tailwind + Supabase desde prompts en lenguaje natural</li>
      <li>Arquitectura generada: <strong>Vite + React + TypeScript + shadcn/ui + Supabase</strong></li>
      <li>El modelo mental clave: <em>no es un generador de código, es un colaborador de producto</em></li>
      <li>Créditos: qué son y cómo no malgastarlos</li>
    </ul>
  </div>

  <table class="tbl" style="margin-top:12px">
    <thead><tr><th>Concepto</th><th>Detalle</th></tr></thead>
    <tbody>
      <tr><td><strong>1 mensaje</strong></td><td>≈ 1 crédito consumido</td></tr>
      <tr><td><strong>Prompt vago</strong></td><td>Más iteraciones → más créditos gastados</td></tr>
      <tr><td><strong>Prompt preciso</strong></td><td>Menos vueltas → ahorro real de dinero</td></tr>
      <tr><td><strong>Edición directa CSS/texto</strong></td><td>0 créditos — usar siempre para tweaks pequeños</td></tr>
    </tbody>
  </table>

  <div class="box box-tip">
    <div class="box-title">🎥 Demo en vivo</div>
    Crear proyecto nuevo en Lovable. Tour por interfaz: Chat · Preview · Code Editor · GitHub sync.
  </div>

  <hr>

  <!-- BLOQUE 2 -->
  <h3 id="b2">Bloque 2 · Cómo pensar antes de empezar — Framework PRE-LOVABLE (45 min)</h3>
  <div class="block">
    <div class="block-title">📖 El Framework PRE-LOVABLE</div>
    <ul>
      <li>Antes del primer prompt, responder estas 5 preguntas en equipo</li>
    </ul>
  </div>

  <div class="framework">1. ¿QUIÉN usa esto?      → Define el usuario principal<br>
2. ¿QUÉ hace?            → La acción core (una sola)<br>
3. ¿QUÉ datos necesita?  → Inputs y outputs del sistema<br>
4. ¿QUÉ pantallas hay?   → Máximo 3–5 vistas para el prototipo<br>
5. ¿Qué NO es esto?      → Acotar el scope para no perder créditos</div>

  <h3 style="margin-top:16px">Ejercicio grupal (15 min)</h3>
  <p>Cada grupo completa la plantilla para su proyecto:</p>
  <div class="framework">Producto: [Nombre del producto]<br>
Usuario: [Persona que lo usa]<br>
Acción core: [El verbo principal — lo que hace la app]<br>
Datos principales: [3–5 campos clave]<br>
Pantallas: [Lista de vistas — máximo 5]<br>
Fuera de scope: [Lo que NO hacemos en el prototipo]</div>

  <hr>

  <!-- BLOQUE 3 -->
  <h3 id="b3">Bloque 3 · Prompt Engineering para Lovable (30 min)</h3>
  <div class="block">
    <div class="block-title">📖 Anatomía del Prompt Perfecto</div>
    <ul>
      <li>Estructura: <strong>[CONTEXTO] + [PANTALLA/COMPONENTE] + [DATOS] + [COMPORTAMIENTO] + [ESTILO]</strong></li>
    </ul>
  </div>

  <div class="prompt-bad">
    <div class="prompt-label">❌ Prompt malo</div>
    "Crea una app para gestionar proyectos"
  </div>

  <div class="prompt-good">
    <div class="prompt-label">✅ Prompt bueno</div>
    "Crea una pantalla de dashboard para gestores de proyectos freelance. Muestra una tabla con los proyectos activos con columnas: nombre, cliente, fecha entrega, estado (badge de color: verde=en curso, amarillo=en revisión, rojo=retrasado), y presupuesto. Usa un diseño limpio con sidebar izquierdo de navegación. Colores corporativos: azul #1E40AF y gris neutro."
  </div>

  <h3>Tipos de prompts por situación</h3>
  <table class="tbl">
    <thead><tr><th>Tipo</th><th>Cuándo usarlo</th><th>Ejemplo</th></tr></thead>
    <tbody>
      <tr><td><strong>Scaffold inicial</strong></td><td>Al empezar — describir el producto completo</td><td>"Crea una app de [X] con estas pantallas: ..."</td></tr>
      <tr><td><strong>Pantalla a pantalla</strong></td><td>Añadir vistas nuevas paso a paso</td><td>"Añade una pantalla de detalle de proyecto"</td></tr>
      <tr><td><strong>Corrección quirúrgica</strong></td><td>Cambios puntuales sin tocar lo demás</td><td>"Cambia solo el botón de Submit a color rojo"</td></tr>
      <tr><td><strong>Integración de datos</strong></td><td>Conectar a Supabase</td><td>"Conecta este formulario a Supabase tabla `projects`"</td></tr>
    </tbody>
  </table>

  <hr>

  <!-- BLOQUE 4 -->
  <h3 id="b4">Bloque 4 · Hands-on — Arrancamos (45 min)</h3>
  <div class="block">
    <div class="block-title">⚡ Pasos guiados</div>
    <ul>
      <li>Cada grupo crea un nuevo proyecto en Lovable</li>
      <li>Toman el framework PRE-LOVABLE y escriben el <strong>prompt inicial de scaffold</strong></li>
      <li>Instructor revisa y da feedback en tiempo real por grupos</li>
      <li>Primera iteración: ajustar navegación y layout general</li>
    </ul>
  </div>

  <p><strong>Workflow de trabajo durante todo el LAB:</strong></p>
  <div class="framework">Prompt → Preview → ¿Está bien?<br>
  → SÍ: siguiente pantalla o feature<br>
  → NO: prompt de corrección quirúrgica (no volver a escribir todo)</div>

  <div class="block" style="margin-top:12px">
    <div class="block-title">💡 Consejos de ahorro de créditos</div>
    <ul>
      <li>Usar "Edit" en código directamente para cambios pequeños (CSS, textos) = <strong>0 créditos</strong></li>
      <li>Conectar GitHub y editar localmente en VS Code para tweaks visuales</li>
      <li>Guardar versiones con <strong>"Checkpoint"</strong> antes de cambios grandes (punto de rollback)</li>
    </ul>
  </div>
</div>

<!-- ============ SESIÓN II ============ -->
<h2 id="sesion2"><span class="e">🔧</span> Sesión II — Trabajo Guiado por Grupos</h2>

<div class="session-card">
  <div class="session-header">
    <div class="session-num">II</div>
    <div class="session-meta">
      <h3>Mentoría — El instructor rota, los grupos avanzan</h3>
      <div class="pills">
        <span class="pill pill-mentoria">Mentoría</span>
        <span class="pill pill-presencial">Presencial + Online</span>
        <span class="pill pill-duracion">2–3 horas</span>
      </div>
    </div>
  </div>

  <div class="block">
    <div class="block-title">🗂️ Estructura de la sesión</div>
    <ul>
      <li><strong>Primeros 10 min:</strong> cada grupo cuenta dónde quedó y qué quiere conseguir hoy</li>
      <li><strong>Rotación:</strong> instructor cada 20–25 min por grupo</li>
      <li><strong>Última media hora:</strong> checkpoint de avance + preparar presentación de S3</li>
    </ul>
  </div>

  <h3 id="checklist">Checklist de avance por grupo</h3>
  <ul class="checklist" style="margin:8px 0">
    <li>Pantalla principal funcional</li>
    <li>Al menos 2 pantallas navegables</li>
    <li>Datos de ejemplo (mock data o Supabase conectado)</li>
    <li>Formulario que guarda información</li>
    <li>Diseño coherente con identidad del producto</li>
    <li>URL de preview compartible</li>
  </ul>

  <h3 id="problemas" style="margin-top:20px">Problemas frecuentes y cómo resolverlos</h3>
  <table class="tbl">
    <thead><tr><th>Problema</th><th>Solución</th></tr></thead>
    <tbody>
      <tr><td>Lovable "rompe" algo al iterar</td><td>Usar <strong>"Revert to checkpoint"</strong> — volver al estado estable</td></tr>
      <tr><td>El diseño no es fiel al concepto</td><td>Describir con más detalle o pegar referencia visual en el chat</td></tr>
      <tr><td>Quieren lógica compleja</td><td>Simplificar al MVP: ¿cuál es el mínimo para demostrarlo?</td></tr>
      <tr><td>Supabase no conecta</td><td>Revisar <code>.env.local</code> y <strong>RLS policies</strong> en Supabase Dashboard</td></tr>
      <tr><td>Se quedan sin créditos</td><td>Cambiar a edición directa de código en el editor de Lovable</td></tr>
    </tbody>
  </table>

  <h3 id="supabase" style="margin-top:20px">Integración Supabase (para grupos que quieran datos reales)</h3>
  <pre><span class="cm">-- Ejemplo: tabla de proyectos (adaptar a cada producto)</span>
<span class="kw">CREATE TABLE</span> projects (
  id UUID <span class="kw">DEFAULT</span> gen_random_uuid() <span class="kw">PRIMARY KEY</span>,
  name TEXT <span class="kw">NOT NULL</span>,
  client TEXT,
  deadline DATE,
  status TEXT <span class="kw">DEFAULT</span> <span class="st">'active'</span>,
  budget DECIMAL,
  created_at TIMESTAMPTZ <span class="kw">DEFAULT</span> NOW()
);

<span class="cm">-- Habilitar RLS (necesario para que Lovable conecte)</span>
<span class="kw">ALTER TABLE</span> projects <span class="kw">ENABLE ROW LEVEL SECURITY</span>;
<span class="kw">CREATE POLICY</span> <span class="st">"Allow all"</span> <span class="kw">ON</span> projects <span class="kw">FOR ALL USING</span> (true);</pre>

  <p>Luego en Lovable:</p>
  <div class="prompt-good">
    <div class="prompt-label">✅ Prompt de integración</div>
    "Conecta el formulario de creación de proyecto a la tabla `projects` de Supabase. Al hacer submit, inserta los datos y recarga la lista automáticamente."
  </div>
</div>

<!-- ============ SESIÓN III ============ -->
<h2 id="sesion3"><span class="e">🎤</span> Sesión III — Presentaciones y Feedback</h2>

<div class="session-card">
  <div class="session-header">
    <div class="session-num">III</div>
    <div class="session-meta">
      <h3>Presentaciones + Feedback estructurado</h3>
      <div class="pills">
        <span class="pill pill-mentoria">Mentoría</span>
        <span class="pill pill-presencial">Presencial + Online</span>
        <span class="pill pill-duracion">2–3 horas</span>
      </div>
    </div>
  </div>

  <h3 id="formato">Formato de presentación por grupo (10–12 min)</h3>
  <div class="framework">1. Contexto del producto (1 min)<br>
   → ¿Quién lo usa? ¿Qué problema resuelve?<br><br>
2. Demo en vivo del prototipo (5–7 min)<br>
   → Navegar por pantallas reales en Lovable/Vercel<br>
   → Mostrar: home + formulario + listado de datos<br><br>
3. Decisiones de diseño (2 min)<br>
   → ¿Qué priorizaron? ¿Qué dejaron fuera del MVP?<br><br>
4. Próximos pasos (1 min)<br>
   → Si continuaran, ¿qué añadirían?</div>

  <h3 id="feedback" style="margin-top:20px">Framework de Feedback del Instructor</h3>
  <table class="tbl fb-table">
    <thead><tr><th>Dimensión</th><th>Pregunta clave</th></tr></thead>
    <tbody>
      <tr><td>Claridad de producto</td><td>¿Se entiende para qué sirve en 5 segundos?</td></tr>
      <tr><td>UX / Usabilidad</td><td>¿El flujo es intuitivo? ¿Hay fricción innecesaria?</td></tr>
      <tr><td>Fidelidad técnica</td><td>¿Funciona? ¿Los datos se guardan y muestran bien?</td></tr>
      <tr><td>MVP Mindset</td><td>¿Scope bien acotado o intentaron hacer demasiado?</td></tr>
    </tbody>
  </table>
</div>

<!-- CRÉDITOS -->
<h2 id="creditos"><span class="e">💳</span> Créditos — Estimación por Grupo</h2>
<table class="tbl">
  <thead><tr><th>Actividad</th><th>Créditos aprox.</th></tr></thead>
  <tbody>
    <tr><td>Scaffold inicial (1 prompt detallado)</td><td>1–2</td></tr>
    <tr><td>Añadir pantalla nueva</td><td>1–3</td></tr>
    <tr><td>Corrección de diseño</td><td>1</td></tr>
    <tr><td>Integración Supabase</td><td>2–4</td></tr>
    <tr><td>Iteraciones totales del prototipo</td><td>15–30</td></tr>
    <tr class="credit-total"><td><strong>Total estimado por grupo (3 sesiones)</strong></td><td><strong>20–40 créditos</strong></td></tr>
  </tbody>
</table>

<div class="box box-info">
  <div class="box-title">💡 Estrategia de créditos</div>
  <strong>Free:</strong> 5 créditos/día × 7 días entre sesiones ≈ 35 créditos. Suficiente si planifican bien.<br>
  <strong>Pro (20€/mes):</strong> 100 mensajes/día. Recomendado si quieren seguir desarrollando tras el máster.<br>
  <strong>Recomendación:</strong> 1 cuenta Pro por grupo (el que quiera continuar el proyecto).
</div>

<!-- ENTREGABLE -->
<div class="deliv" id="entregable">
  <h4>📋 Entregable Final del LAB</h4>
  <ul class="checklist" style="margin:0">
    <li>URL del prototipo desplegado (Vercel o Lovable preview)</li>
    <li>Repo GitHub con el código generado</li>
    <li>Documento de 1 página: decisiones de producto + próximos pasos</li>
  </ul>
</div>

<!-- RECURSOS -->
<h2 id="recursos"><span class="e">📎</span> Recursos Clave</h2>
<div class="res-grid">
  <a href="https://docs.lovable.dev" target="_blank" class="res-link"><span class="ri">✳️</span><div><div class="rl">Lovable Docs</div><div class="rd">Documentación oficial</div></div></a>
  <a href="https://supabase.com/docs" target="_blank" class="res-link"><span class="ri">🗄️</span><div><div class="rl">Supabase Docs</div><div class="rd">Base de datos + Auth + RLS</div></div></a>
  <a href="https://ui.shadcn.com" target="_blank" class="res-link"><span class="ri">🎨</span><div><div class="rl">shadcn/ui</div><div class="rd">Componentes que usa Lovable</div></div></a>
  <a href="https://tailwindcss.com/docs" target="_blank" class="res-link"><span class="ri">💨</span><div><div class="rl">Tailwind CSS</div><div class="rd">Utilidades CSS</div></div></a>
  <a href="https://vercel.com/docs" target="_blank" class="res-link"><span class="ri">🚀</span><div><div class="rl">Vercel Deploy</div><div class="rd">Deploy en segundos</div></div></a>
  <a href="https://figma.com" target="_blank" class="res-link"><span class="ri">🖼️</span><div><div class="rl">Figma</div><div class="rd">Referencias visuales para Lovable</div></div></a>
</div>

</main>
</div>

<footer>
  <p>© 2025 Nuclio Digital School × <a href="https://www.nexusfinlabs.com">NexusFinLabs</a> · Alberto Lobo · <a href="/classes">Máster Automation & AI →</a></p>
</footer>

</body>
</html>"""
