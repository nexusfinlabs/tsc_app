CLASSES_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Máster en Automation & AI — Guía del Curso — Nuclio × NexusFinLabs</title>
<meta name="description" content="Guía completa del Máster en Automation & AI. 17 semanas, 7 módulos, 27+ workflows reales. Setup, comandos, ejercicios y apuntes.">
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
  --green:#22c55e;--blue:#60a5fa;--red:#f87171;--purple:#a78bfa;
  --amber:#fbbf24;
}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;background:var(--dark);color:var(--text);min-height:100vh}

/* NAV */
nav{position:fixed;top:0;left:0;right:0;z-index:100;height:52px;display:flex;align-items:center;justify-content:space-between;padding:0 24px;background:rgba(13,13,13,.92);backdrop-filter:blur(16px);border-bottom:1px solid var(--border)}
.nav-brand{display:flex;align-items:center;gap:10px;text-decoration:none}
.nav-brand .logo{font-size:18px;font-weight:300;color:#fff;letter-spacing:.06em}
.nav-brand .logo strong{font-weight:800}
.nav-brand .sep{width:1px;height:20px;background:var(--border2)}
.nav-brand .sub{font-size:10px;color:var(--muted);letter-spacing:.04em}
.nav-r{display:flex;gap:4px;align-items:center}
.nav-r a{color:var(--muted);text-decoration:none;padding:5px 10px;border-radius:6px;font-size:12px;font-weight:500;transition:.15s}
.nav-r a:hover{color:#fff;background:rgba(255,255,255,.06)}
.nav-cta{background:var(--gold)!important;color:var(--dark)!important;font-weight:700!important;border-radius:100px!important;padding:6px 16px!important}

/* HERO — Nuclio style with golden arcs */
.hero{background:var(--dark);min-height:380px;position:relative;overflow:hidden;display:flex;align-items:center;padding:80px 32px 48px}
.hero::before{content:'';position:absolute;top:-200px;right:-100px;width:900px;height:900px;background:repeating-conic-gradient(from 30deg,transparent 0deg,transparent 50deg,rgba(201,168,76,.06) 50deg,rgba(201,168,76,.06) 55deg,transparent 55deg);border-radius:50%;animation:spin 60s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.hero::after{content:'';position:absolute;top:50px;right:-50px;width:600px;height:600px;border:1px solid rgba(201,168,76,.08);border-radius:50%}
.hero-content{position:relative;z-index:1;max-width:700px}
.hero-badges{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.h-badge{background:rgba(255,255,255,.06);border:1px solid var(--border2);border-radius:8px;padding:6px 14px;font-size:11px;font-weight:600;color:var(--muted);display:flex;align-items:center;gap:6px}
.h-badge img,.h-badge .b-icon{height:14px}
.h-badge strong{color:#fff;font-weight:700}
.hero h1{font-size:clamp(2.2rem,4vw,3.4rem);font-weight:300;color:#fff;letter-spacing:-.02em;line-height:1.1;margin-bottom:14px}
.hero h1 strong{font-weight:900}
.hero-live{display:inline-flex;align-items:center;gap:6px;background:rgba(201,168,76,.1);border:1px solid rgba(201,168,76,.25);border-radius:8px;padding:4px 12px;font-size:11px;font-weight:700;color:var(--gold);margin-left:8px;vertical-align:middle}
.hero-live .dot{width:6px;height:6px;background:var(--gold);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
.hero-sub{color:var(--muted);font-size:14px;line-height:1.7;max-width:520px;margin-bottom:24px}
.hero-meta{display:flex;gap:24px;flex-wrap:wrap}
.hm{text-align:left}
.hm .n{font-size:1.5rem;font-weight:900;color:var(--gold)}
.hm .l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-top:2px}

/* PAGE LAYOUT */
.page{display:grid;grid-template-columns:220px 1fr;max-width:1200px;margin:0 auto}
@media(max-width:900px){.page{grid-template-columns:1fr}.sidebar{display:none!important}}

/* SIDEBAR */
.sidebar{position:sticky;top:52px;height:calc(100vh - 52px);overflow-y:auto;padding:16px 12px;border-right:1px solid var(--border);background:var(--dark2);scrollbar-width:thin;scrollbar-color:var(--dark4) transparent}
.sidebar::-webkit-scrollbar{width:4px}
.sidebar::-webkit-scrollbar-thumb{background:var(--dark4);border-radius:4px}
.sb-section{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.14em;color:var(--muted2);margin:14px 0 6px;padding-left:8px}
.sb-section:first-child{margin-top:0}
.sidebar a{display:block;font-size:12px;padding:5px 10px;border-radius:6px;text-decoration:none;color:var(--muted);font-weight:500;transition:.12s;margin-bottom:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sidebar a:hover{background:rgba(255,255,255,.04);color:#fff}

/* MAIN */
.main{padding:28px 36px 100px;min-width:0}
.main h2{font-size:1.4rem;font-weight:900;letter-spacing:-.02em;margin:48px 0 6px;padding-top:20px;border-top:1px solid var(--border);color:#fff}
.main h2:first-child{margin-top:0;padding-top:0;border-top:none}
.main h2 .emoji{margin-right:6px}
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
.cm{color:#6e7681}
.kw{color:#ff7b72}
.st{color:#a5d6ff}
.vr{color:var(--gold-light)}

/* TABLES */
.tbl{width:100%;border-collapse:collapse;margin:12px 0 20px;border:1px solid var(--border);border-radius:8px;overflow:hidden;font-size:12px}
.tbl th{text-align:left;padding:8px 12px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:var(--dark2);border-bottom:1px solid var(--border)}
.tbl td{padding:8px 12px;border-bottom:1px solid var(--border);color:var(--muted)}
.tbl td strong{color:#e0e0e0}
.tbl tr:last-child td{border-bottom:none}
.tbl tr:hover td{background:rgba(255,255,255,.02)}
.tbl .gold{color:var(--gold);font-weight:700}
.tbl .total{background:var(--dark3);font-weight:700}
.tbl .total td{color:#fff}

/* BOXES */
.box{border-radius:8px;padding:14px 16px;margin:12px 0 16px;font-size:12px;line-height:1.65;border:1px solid}
.box-info{background:rgba(96,165,250,.06);border-color:rgba(96,165,250,.15);color:var(--blue)}
.box-tip{background:rgba(34,197,94,.06);border-color:rgba(34,197,94,.15);color:var(--green)}
.box-warn{background:rgba(251,191,36,.06);border-color:rgba(251,191,36,.15);color:var(--amber)}
.box-title{font-weight:800;font-size:11px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;display:flex;align-items:center;gap:5px}

/* WORKFLOW CARD */
.wf{background:var(--dark2);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin:10px 0;transition:.2s}
.wf:hover{border-color:var(--border2)}
.wf h4{font-size:13px;font-weight:800;margin-bottom:5px;display:flex;align-items:center;gap:8px;color:#fff}
.wf h4 .num{min-width:22px;height:22px;background:var(--gold);border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:900;color:var(--dark)}
.wf p{font-size:12px;color:var(--muted);line-height:1.55;margin:0}
.wf .flow{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--gold);background:rgba(201,168,76,.08);padding:5px 10px;border-radius:5px;margin-top:8px;display:inline-block;border:1px solid rgba(201,168,76,.12)}

/* CHEAT SHEET */
.cheat{background:var(--dark2);border:1px solid var(--border);border-radius:10px;padding:18px;margin:16px 0}
.cheat h4{font-size:12px;font-weight:800;color:var(--gold);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.cheat-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:640px){.cheat-grid{grid-template-columns:1fr}}
.cheat-item{background:var(--dark3);border:1px solid var(--border);border-radius:6px;padding:10px 12px}
.cheat-item .cmd{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--green);margin-bottom:3px;word-break:break-all}
.cheat-item .desc{font-size:11px;color:var(--muted)}

/* WEEK LABEL */
.week{display:inline-flex;align-items:center;gap:5px;background:rgba(201,168,76,.08);border:1px solid rgba(201,168,76,.15);border-radius:100px;padding:3px 11px;font-size:10px;font-weight:800;color:var(--gold);margin-bottom:10px}

/* DELIVERABLE */
.deliv{background:rgba(34,197,94,.04);border:1px solid rgba(34,197,94,.12);border-radius:8px;padding:14px 16px;margin:14px 0}
.deliv h4{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:var(--green);margin-bottom:8px}
.deliv ul{list-style:none;margin:0;padding:0}
.deliv li{font-size:12px;padding:3px 0;display:flex;align-items:center;gap:7px;color:#c0c0c0}
.deliv li::before{content:'□';color:var(--gold);font-weight:700;font-size:12px}

/* RESOURCES */
.res-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin:14px 0}
.res-link{background:var(--dark2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;text-decoration:none;transition:.15s;display:flex;align-items:center;gap:8px}
.res-link:hover{border-color:var(--border2);text-decoration:none}
.res-link .ri{font-size:18px;flex-shrink:0}
.res-link .rl{font-size:12px;font-weight:600;color:#e0e0e0}
.res-link .rd{font-size:10px;color:var(--muted)}

/* MODULE HEADER */
.mod-header{background:var(--dark2);border:1px solid var(--border);border-radius:10px;padding:18px 20px;margin:16px 0 20px;display:flex;align-items:center;gap:16px}
.mod-icon{width:44px;height:44px;background:var(--gold);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0}
.mod-header h3{font-size:16px;font-weight:900;color:#fff;margin:0 0 4px;letter-spacing:-.02em}
.mod-header p{font-size:12px;color:var(--muted);margin:0;line-height:1.5}

footer{background:var(--dark);border-top:1px solid var(--border);padding:28px 24px;text-align:center}
footer p{color:var(--muted2);font-size:11px}
footer a{color:var(--muted);text-decoration:none}

@media(max-width:768px){.main{padding:20px 18px 80px}.hero{padding:70px 20px 36px}.hero h1{font-size:1.8rem}.cheat-grid{grid-template-columns:1fr}}
</style>
</head>
<body>

<nav>
  <a href="/" class="nav-brand">
    <span class="logo"><strong>nuclio</strong>°</span>
    <span class="sep"></span>
    <span class="sub">digital school</span>
  </a>
  <div class="nav-r">
    <a href="/product">Product</a>
    <a href="#setup">Setup</a>
    <a href="#m1">M1</a><a href="#m2">M2</a><a href="#m3">M3</a><a href="#m4">M4</a><a href="#m5">M5</a><a href="#m6">M6</a><a href="#m7">M7</a>
    <a href="mailto:alberto@nexusfinlabs.com" class="nav-cta">Contacto</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="hero-content">
    <div class="hero-badges">
      <div class="h-badge">Partner educativo · <strong>make</strong></div>
      <div class="h-badge">Programa aprobado · <strong>n8n</strong></div>
    </div>
    <h1>Máster en <strong>Automation & AI</strong> <span class="hero-live"><span class="dot"></span>CLASES 100% ACTUALIZADAS</span></h1>
    <p class="hero-sub">Guía completa del curso: setup, apuntes, comandos, chuletas, workflows y entregables semana a semana.</p>
    <div class="hero-meta">
      <div class="hm"><div class="n">17</div><div class="l">Semanas</div></div>
      <div class="hm"><div class="n">~58h</div><div class="l">Docencia</div></div>
      <div class="hm"><div class="n">7</div><div class="l">Módulos</div></div>
      <div class="hm"><div class="n">27+</div><div class="l">Workflows</div></div>
    </div>
  </div>
</div>

<div class="page">

<!-- SIDEBAR -->
<aside class="sidebar">
  <div class="sb-section">Inicio</div>
  <a href="#setup">📦 Setup inicial</a>
  <a href="#cuentas">Cuentas necesarias</a>
  <a href="#n8n-install">Instalar n8n</a>
  <a href="#env">Variables .env</a>
  <a href="#cheat-cli">🗒️ Chuleta CLI</a>
  <a href="#dashboard">📅 Dashboard sesiones</a>
  <div class="sb-section">Kick-off</div>
  <a href="#kickoff">Welcome Day</a>
  <div class="sb-section">M1 · Fundamentos</div>
  <a href="#m1">🏁 Visión general</a>
  <a href="#m1-s2">Semana 2 — Fundamentos</a>
  <a href="#m1-s3">Semana 3 — Deep n8n</a>
  <div class="sb-section">M2 · Productividad IA</div>
  <a href="#m2">⚡ Visión general</a>
  <a href="#m2-s4">Semana 4 — IA + Make</a>
  <a href="#m2-s5">Semana 5 — Integraciones</a>
  <div class="sb-section">M3 · Marketing</div>
  <a href="#m3">📣 Visión general</a>
  <a href="#m3-s6">Semana 6 — Nurturing</a>
  <a href="#m3-s7">Semana 7 — Content & Funnels</a>
  <div class="sb-section">M4 · Ventas</div>
  <a href="#m4">💼 Semanas 9–12</a>
  <div class="sb-section">M5 · Atención al Cliente</div>
  <a href="#m5">🤖 Semanas 12–14</a>
  <div class="sb-section">M6 · Financiera</div>
  <a href="#m6">🧾 Semanas 15–16</a>
  <div class="sb-section">M7 · Producción</div>
  <a href="#m7">🚀 Semana 17</a>
  <div class="sb-section">Extras</div>
  <a href="#cheat-n8n">🗒️ Chuleta n8n</a>
  <a href="#cheat-make">🗒️ Chuleta Make</a>
  <a href="#cheat-api">🗒️ Chuleta APIs</a>
  <a href="#recursos">📎 Recursos</a>
</aside>

<!-- MAIN -->
<main class="main">

<!-- ============ SETUP ============ -->
<h2 id="setup"><span class="emoji">📦</span> Setup Inicial — Día 1</h2>
<p>Antes de la Semana 2. Todo es gratuito para empezar.</p>

<h3 id="cuentas">Cuentas necesarias</h3>
<table class="tbl">
  <thead><tr><th>Plataforma</th><th>URL</th><th>Plan</th><th>Estado</th></tr></thead>
  <tbody>
    <tr><td><strong>n8n Cloud</strong></td><td><a href="https://n8n.io" target="_blank">n8n.io</a></td><td>Free ó Self-hosted</td><td class="gold">Obligatorio</td></tr>
    <tr><td><strong>Zapier</strong></td><td><a href="https://zapier.com" target="_blank">zapier.com</a></td><td>Free Starter</td><td class="gold">Obligatorio</td></tr>
    <tr><td><strong>Make</strong></td><td><a href="https://make.com" target="_blank">make.com</a></td><td>Free</td><td>Semana 4</td></tr>
    <tr><td><strong>OpenAI</strong></td><td><a href="https://platform.openai.com" target="_blank">platform.openai.com</a></td><td>Pay-as-you-go</td><td class="gold">Obligatorio</td></tr>
    <tr><td><strong>Notion</strong></td><td><a href="https://notion.so" target="_blank">notion.so</a></td><td>Free</td><td class="gold">Obligatorio</td></tr>
    <tr><td><strong>Airtable</strong></td><td><a href="https://airtable.com" target="_blank">airtable.com</a></td><td>Free</td><td class="gold">Obligatorio</td></tr>
    <tr><td><strong>Slack</strong></td><td><a href="https://slack.com" target="_blank">slack.com</a></td><td>Free</td><td class="gold">Obligatorio</td></tr>
    <tr><td><strong>Brevo</strong></td><td><a href="https://brevo.com" target="_blank">brevo.com</a></td><td>Free (300 emails/día)</td><td>Semana 6</td></tr>
  </tbody>
</table>

<h3 id="n8n-install">Instalación de n8n</h3>
<pre><span class="cm"># ────────────────────────────────────────────</span>
<span class="cm"># OPCIÓN 1: npx (más rápido — empezar aquí)</span>
<span class="cm"># ────────────────────────────────────────────</span>
npx n8n

<span class="cm"># ────────────────────────────────────────────</span>
<span class="cm"># OPCIÓN 2: Docker (para producción, M7)</span>
<span class="cm"># ────────────────────────────────────────────</span>
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

<span class="cm"># ────────────────────────────────────────────</span>
<span class="cm"># OPCIÓN 3: npm global</span>
<span class="cm"># ────────────────────────────────────────────</span>
npm install n8n -g
n8n start</pre>

<div class="box box-info">
  <div class="box-title">ℹ️ Requisito</div>
  <strong>Node.js >= 18.x</strong> necesario. Comprueba: <code>node --version</code>. Si no tienes Node: <code>brew install node</code> (Mac) o <a href="https://nodejs.org" target="_blank">nodejs.org</a>
</div>

<h3>Librerías complementarias</h3>
<pre><span class="cm"># Python (scripts custom en n8n y M6)</span>
pip install openai requests pandas python-dotenv

<span class="cm"># Anthropic CLI (opcional)</span>
npm install -g @anthropic-ai/sdk
pip install langchain

<span class="cm"># M6 — OCR y facturas (instalar antes de semana 15)</span>
pip install pytesseract pillow pdf2image supabase</pre>

<h3 id="env">Variables de entorno (.env)</h3>
<pre><span class="cm"># Crear archivo .env en la raíz del proyecto</span>
<span class="vr">OPENAI_API_KEY</span>=sk-...
<span class="vr">N8N_BASIC_AUTH_ACTIVE</span>=true
<span class="vr">N8N_BASIC_AUTH_USER</span>=admin
<span class="vr">N8N_BASIC_AUTH_PASSWORD</span>=tu_password_seguro

<span class="cm"># Opcional — para Make</span>
<span class="vr">MAKE_API_KEY</span>=...
<span class="cm"># Opcional — para Supabase (M6)</span>
<span class="vr">SUPABASE_URL</span>=https://xxx.supabase.co
<span class="vr">SUPABASE_KEY</span>=eyJ...</pre>

<div class="box box-warn">
  <div class="box-title">⚠️ Seguridad</div>
  Nunca subas <code>.env</code> a GitHub. Paso 0: <code>echo ".env" >> .gitignore</code>
</div>

<!-- CLI CHEAT SHEET -->
<div class="cheat" id="cheat-cli">
  <h4>🗒️ Chuleta — Comandos esenciales</h4>
  <div class="cheat-grid">
    <div class="cheat-item"><div class="cmd">npx n8n</div><div class="desc">Arranca n8n localmente (puerto 5678)</div></div>
    <div class="cheat-item"><div class="cmd">docker ps</div><div class="desc">Ver contenedores Docker activos</div></div>
    <div class="cheat-item"><div class="cmd">node --version</div><div class="desc">Comprobar versión de Node.js</div></div>
    <div class="cheat-item"><div class="cmd">pip install openai</div><div class="desc">Instalar SDK de OpenAI</div></div>
    <div class="cheat-item"><div class="cmd">curl -X POST url -d '{}'</div><div class="desc">Testear un webhook manualmente</div></div>
    <div class="cheat-item"><div class="cmd">python -c "import openai; print('OK')"</div><div class="desc">Verificar instalación de OpenAI</div></div>
    <div class="cheat-item"><div class="cmd">docker logs n8n --tail 20</div><div class="desc">Ver últimos 20 logs de n8n</div></div>
    <div class="cheat-item"><div class="cmd">ngrok http 5678</div><div class="desc">Exponer n8n local a internet</div></div>
  </div>
</div>

<!-- DASHBOARD -->
<h2 id="dashboard"><span class="emoji">📅</span> Dashboard de Sesiones</h2>
<table class="tbl">
  <thead><tr><th>Semana</th><th>Sesión</th><th>Tipo</th><th>Horas</th></tr></thead>
  <tbody>
    <tr><td><strong>1</strong></td><td>Welcome Day</td><td>Welcome</td><td>1h</td></tr>
    <tr><td rowspan="5"><strong>2</strong></td><td>Fundamentos de automatización y buenas prácticas</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Detección y análisis de procesos ineficientes</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Instalación de n8n</td><td>Recorded</td><td>0.5h</td></tr>
    <tr><td>Instalación de básicos</td><td>Recorded</td><td>1h</td></tr>
    <tr><td>Acceso a n8n</td><td>—</td><td>—</td></tr>
    <tr><td rowspan="3"><strong>3</strong></td><td>Deep intro n8n (arquitectura, nodos, flujos)</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>n8n a fondo: primeros flujos end-to-end</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Q&A: Basics n8n</td><td>Mentoría</td><td>1h</td></tr>
    <tr><td rowspan="4"><strong>4</strong></td><td>Acceso a Make</td><td>—</td><td>—</td></tr>
    <tr><td>Intro Herramienta MAKE</td><td>Recorded</td><td>1h</td></tr>
    <tr><td>Automatización de tareas recurrentes</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Uso de IA para flujos diarios de productividad</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td rowspan="2"><strong>5</strong></td><td>Integración de herramientas para coordinar acciones</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Q&A — Prep Entregable M2</td><td>Mentoría</td><td>1h</td></tr>
    <tr><td><strong>6</strong></td><td>Automatización de publicaciones y nurturing</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td rowspan="2"><strong>7</strong></td><td>Generación de contenido con IA</td><td>Clase</td><td>1.5h</td></tr>
    <tr><td>Construcción de funnels de conversión automatizados</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td><strong>8</strong></td><td>Q&A — Prep Entregable M3</td><td>Mentoría</td><td>1h</td></tr>
    <tr><td><strong>9</strong></td><td>Diseño de workflows para seguimiento y cierre de ventas</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td rowspan="2"><strong>10</strong></td><td>Flujos en ventas con Notion</td><td>Clase</td><td>1h</td></tr>
    <tr><td>Alertas inteligentes y notificaciones automáticas</td><td>Clase</td><td>1.5h</td></tr>
    <tr><td><strong>11</strong></td><td>Automatización del ciclo comercial</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td rowspan="2"><strong>12</strong></td><td>Q&A — Prep Entregable M4</td><td>Mentoría</td><td>1h</td></tr>
    <tr><td>Automatización del onboarding de clientes</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td rowspan="2"><strong>13</strong></td><td>Chatbot / Agente de atención con IA (I)</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Chatbot / Agente de atención con IA (II)</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td><strong>14</strong></td><td>Q&A — Prep Entregable M5</td><td>Mentoría</td><td>1h</td></tr>
    <tr><td><strong>15</strong></td><td>Automatización en facturación</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td><strong>16</strong></td><td>Extracción de datos con OCR y traspaso a BBDD</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td rowspan="3"><strong>17</strong></td><td>Cómo implantar y mantener sistemas automatizados</td><td>Clase</td><td>2.5h</td></tr>
    <tr><td>Q&A — Prep Entregable M6</td><td>Mentoría</td><td>1h</td></tr>
    <tr><td>Escalar con lo aprendido sin aumentar personal</td><td>Clase</td><td>2.5h</td></tr>
    <tr class="total"><td></td><td><strong>Total docencia</strong></td><td></td><td><strong>~58h</strong></td></tr>
  </tbody>
</table>

<!-- ============ KICK-OFF ============ -->
<h2 id="kickoff"><span class="emoji">🎯</span> Kick-off — Welcome Day</h2>
<span class="week">📅 Semana 1 · 1h</span>
<p><strong>Objetivo:</strong> Introducir el máster, al instructor y la metodología. Generar comunidad.</p>
<ul>
  <li>Presentación del programa, expectativas y dinámica de trabajo</li>
  <li><strong>¿Qué es la automatización inteligente?</strong> ¿Por qué ahora?</li>
  <li>Diferencia entre <strong>RPA</strong>, <strong>automatización de flujos</strong> y <strong>AI Agents</strong></li>
  <li>Landscape 2024–2025: n8n, Make, Zapier, Airtable Automations</li>
</ul>
<div class="wf">
  <h4><span class="num">1</span> Workflow "Hello World"</h4>
  <p>Tu primer flujo: recibir un webhook → procesar datos → enviar un email.</p>
  <div class="flow">Webhook Trigger → Set Node → Send Email (Gmail)</div>
</div>

<!-- ============ M1 ============ -->
<h2 id="m1"><span class="emoji">🏁</span> M1 · Introducción a la Automatización e IA</h2>

<div class="mod-header">
  <div class="mod-icon">🏁</div>
  <div>
    <h3 style="margin:0">Fundamentos de Automatización</h3>
    <p>Semanas 2–3 · ~14h · Construir la arquitectura mental de los flujos y dominar n8n</p>
  </div>
</div>

<h3 id="m1-s2">Semana 2 — Fundamentos y detección de procesos</h3>
<span class="week">📅 Semana 2 · 2 clases (5h) + videos grabados (1.5h)</span>

<h3>Apuntes — Fundamentos</h3>
<ul>
  <li><strong>Principios:</strong> triggers, actions, condiciones, bucles</li>
  <li><strong>Taxonomía:</strong> procesos repetitivos, paralelos, dependientes</li>
  <li><strong>El método "Audit de Procesos":</strong> mapear tareas &gt; 30 min/semana, calcular ROI</li>
  <li><strong>Fórmula ROI:</strong> <code>(horas_ahorradas × coste_hora) / coste_setup</code></li>
  <li><strong>Buenas prácticas:</strong> idempotencia, manejo de errores, logging consistente</li>
</ul>

<h3>Hands-on — Workflows</h3>
<div class="wf">
  <h4><span class="num">2</span> Audit Logger</h4>
  <p>Formulario Google → Airtable con timestamp automático. Tu primera automatización real.</p>
  <div class="flow">Google Forms Trigger → Airtable (Create Record)</div>
</div>
<div class="wf">
  <h4><span class="num">3</span> Email → Notion Task</h4>
  <p>Gmail trigger → crear tarea automáticamente en Notion cada vez que recibes un email importante.</p>
  <div class="flow">Gmail Trigger → IF (label=important) → Notion (Create Page)</div>
</div>

<div class="box box-tip">
  <div class="box-title">📹 Recursos grabados (obligatorios antes de Semana 3)</div>
  <strong>Video 1:</strong> Instalación n8n — npx + Docker (30 min)<br>
  <strong>Video 2:</strong> Setup básicos — Airtable, Notion, Slack, API keys (60 min)
</div>

<hr>

<h3 id="m1-s3">Semana 3 — Deep intro n8n</h3>
<span class="week">📅 Semana 3 · 2 clases (5h) + Q&A (1h)</span>

<h3>Apuntes — Arquitectura de n8n</h3>
<ul>
  <li><strong>Nodos:</strong> Trigger, Action, IF, Switch, Merge, Loop, Function</li>
  <li><strong>Expresiones:</strong> <code>$json.field</code>, <code>$node["name"].json</code>, <code>$items()</code>, <code>DateTime</code></li>
  <li><strong>Error Trigger:</strong> captura fallos de cualquier workflow → notificación</li>
  <li><strong>Credenciales:</strong> OAuth2, API Key, Header Auth — cuándo usar cada uno</li>
</ul>

<!-- n8n Cheat Sheet -->
<div class="cheat" id="cheat-n8n">
  <h4>🗒️ Chuleta n8n — Expresiones más usadas</h4>
  <div class="cheat-grid">
    <div class="cheat-item"><div class="cmd">$json.email</div><div class="desc">Acceder al campo "email" del item actual</div></div>
    <div class="cheat-item"><div class="cmd">$node["Gmail"].json.from</div><div class="desc">Obtener campo de otro nodo por nombre</div></div>
    <div class="cheat-item"><div class="cmd">$items().length</div><div class="desc">Contar cuántos items hay en el batch</div></div>
    <div class="cheat-item"><div class="cmd">$now.toISO()</div><div class="desc">Fecha/hora actual en formato ISO</div></div>
    <div class="cheat-item"><div class="cmd">$json.text.includes("urgente")</div><div class="desc">Condición: ¿contiene la palabra?</div></div>
    <div class="cheat-item"><div class="cmd">$json.amount > 1000</div><div class="desc">Condición numérica en nodo IF</div></div>
    <div class="cheat-item"><div class="cmd">$input.first().json</div><div class="desc">Primer item de la entrada</div></div>
    <div class="cheat-item"><div class="cmd">$env.OPENAI_API_KEY</div><div class="desc">Acceder a variable de entorno</div></div>
  </div>
</div>

<h3>Hands-on — Workflows</h3>
<div class="wf">
  <h4><span class="num">4</span> Lead Capture Pipeline</h4>
  <p>Typeform → n8n → guardar en Notion + alerta Slack al equipo en tiempo real.</p>
  <div class="flow">Typeform Trigger → Notion (Create) → Slack (Send Message)</div>
</div>
<div class="wf">
  <h4><span class="num">5</span> Daily Digest</h4>
  <p>Schedule trigger → leer RSS → filtrar por keywords → email resumen cada mañana.</p>
  <div class="flow">Schedule (8AM) → RSS Read → IF (keyword match) → Gmail (Send)</div>
</div>
<div class="wf">
  <h4><span class="num">6</span> Error Alerting</h4>
  <p>Cualquier workflow que falle → notificación Telegram inmediata. Tu sistema de monitorización.</p>
  <div class="flow">Error Trigger → Telegram (Send Message)</div>
</div>

<div class="deliv">
  <h4>📋 Q&A Mentoría — Semana 3 (1h)</h4>
  <ul>
    <li>Revisión de workflows entregados por alumnos</li>
    <li>Debugging en vivo de flujos atascados</li>
    <li>Comparativa de soluciones entre alumnos</li>
  </ul>
</div>

<!-- ============ M2 ============ -->
<h2 id="m2"><span class="emoji">⚡</span> M2 · Automatización para mejorar la productividad</h2>

<div class="mod-header">
  <div class="mod-icon">⚡</div>
  <div>
    <h3 style="margin:0">Productividad con IA</h3>
    <p>Semanas 4–5 · ~10h · Integrar IA en flujos diarios + introducción a Make</p>
  </div>
</div>

<h3 id="m2-s4">Semana 4 — IA + Intro Make</h3>
<span class="week">📅 Semana 4 · 2 clases (5h) + video Make (1h)</span>

<h3>Apuntes</h3>
<ul>
  <li><strong>Make vs n8n vs Zapier:</strong> Make = visual + escenarios; n8n = open source + código; Zapier = SaaS + simple</li>
  <li><strong>Modelos IA en flujos:</strong> OpenAI (GPT-4o), Anthropic (Claude), Google (Gemini) via API</li>
  <li><strong>Prompt engineering para automatizaciones:</strong> system prompt + few-shot + output format (JSON)</li>
  <li><strong>Patrones:</strong> inbox-zero, daily briefing, task routing automático</li>
</ul>

<pre><span class="cm"># Ejemplo: llamada a OpenAI desde n8n (HTTP Request node)</span>
POST https://api.openai.com/v1/chat/completions
Headers: Authorization: Bearer $env.OPENAI_API_KEY
Body:
{
  "model": "gpt-4o",
  "messages": [
    {"role": "system", "content": "Clasifica el siguiente email como: URGENTE, NORMAL o SPAM. Responde solo con la categoría."},
    {"role": "user", "content": "$json.body"}
  ],
  "temperature": 0
}</pre>

<h3>Hands-on</h3>
<div class="wf">
  <h4><span class="num">7</span> AI Email Triage</h4>
  <p>Gmail → GPT-4o clasifica → etiqueta automática + borrador de respuesta. Inbox en piloto automático.</p>
  <div class="flow">Gmail Trigger → OpenAI (Classify) → IF → Gmail (Label + Draft)</div>
</div>
<div class="wf">
  <h4><span class="num">8</span> Daily Briefing Bot</h4>
  <p>Schedule 8AM → noticias RSS + agenda Calendar → resumen GPT → Slack/Telegram.</p>
  <div class="flow">Schedule → [RSS, Calendar] → Merge → OpenAI (Summary) → Slack</div>
</div>
<div class="wf">
  <h4><span class="num">9</span> Make: Form → Sheets + Email</h4>
  <p>Primera automatización en Make. Misma lógica, diferente herramienta — compara.</p>
  <div class="flow">Make: Typeform → Google Sheets → Gmail</div>
</div>

<div class="box box-tip">
  <div class="box-title">📹 Contenido recorded</div>
  <strong>Intro herramienta Make</strong> (1h) — disponible en plataforma. Ver antes de la Semana 5.
</div>

<!-- Make cheat -->
<div class="cheat" id="cheat-make">
  <h4>🗒️ Chuleta Make (ex-Integromat)</h4>
  <div class="cheat-grid">
    <div class="cheat-item"><div class="cmd">Escenario</div><div class="desc">= Workflow en n8n. Secuencia de módulos.</div></div>
    <div class="cheat-item"><div class="cmd">Módulo</div><div class="desc">= Nodo en n8n. Cada paso del flujo.</div></div>
    <div class="cheat-item"><div class="cmd">Router</div><div class="desc">= Switch/IF. Bifurcar flujo por condiciones.</div></div>
    <div class="cheat-item"><div class="cmd">Iterator</div><div class="desc">= SplitInBatches. Procesar arrays 1 a 1.</div></div>
    <div class="cheat-item"><div class="cmd">Aggregator</div><div class="desc">= Merge. Combinar resultados en uno.</div></div>
    <div class="cheat-item"><div class="cmd">Webhook</div><div class="desc">URL para recibir datos externos.</div></div>
  </div>
</div>

<hr>

<h3 id="m2-s5">Semana 5 — Integración de herramientas</h3>
<span class="week">📅 Semana 5 · Clase (2.5h) + Q&A (1h)</span>

<h3>Apuntes</h3>
<ul>
  <li><strong>Webhooks vs Polling:</strong> webhooks = push en tiempo real; polling = pull cada X minutos</li>
  <li><strong>HTTP Request node:</strong> consumir cualquier API REST que exista</li>
  <li><strong>Auth:</strong> API Key (header), OAuth2 (token flow), Bearer Token (JWT)</li>
</ul>

<!-- API Cheat -->
<div class="cheat" id="cheat-api">
  <h4>🗒️ Chuleta APIs REST</h4>
  <div class="cheat-grid">
    <div class="cheat-item"><div class="cmd">GET /resource</div><div class="desc">Leer datos (listar, buscar)</div></div>
    <div class="cheat-item"><div class="cmd">POST /resource</div><div class="desc">Crear un nuevo recurso</div></div>
    <div class="cheat-item"><div class="cmd">PUT /resource/id</div><div class="desc">Reemplazar recurso completo</div></div>
    <div class="cheat-item"><div class="cmd">PATCH /resource/id</div><div class="desc">Actualizar campos parciales</div></div>
    <div class="cheat-item"><div class="cmd">DELETE /resource/id</div><div class="desc">Eliminar un recurso</div></div>
    <div class="cheat-item"><div class="cmd">200 OK</div><div class="desc">Éxito. Datos en el body.</div></div>
    <div class="cheat-item"><div class="cmd">401 Unauthorized</div><div class="desc">API Key/Token incorrecto</div></div>
    <div class="cheat-item"><div class="cmd">429 Too Many Requests</div><div class="desc">Rate limit. Espera y reintenta.</div></div>
  </div>
</div>

<div class="wf">
  <h4><span class="num">10</span> CRM Sync</h4>
  <p>HubSpot / Airtable → Notion → Slack alert. Ecosistemas sincronizados.</p>
  <div class="flow">Airtable Trigger → Notion (Create) → Slack (Notify)</div>
</div>
<div class="wf">
  <h4><span class="num">11</span> Calendar Intelligence</h4>
  <p>Nuevo evento Calendar → brief automático con contexto del asistente (empresa, LinkedIn).</p>
  <div class="flow">Calendar Trigger → HTTP Request (LinkedIn) → OpenAI → Slack</div>
</div>

<div class="deliv">
  <h4>📋 Entregable M2</h4>
  <ul>
    <li>Workflow funcional: min 2 herramientas + 1 modelo IA</li>
    <li>Presentación de 3 min: qué automatiza, qué tiempo ahorra</li>
  </ul>
</div>

<!-- ============ M3 ============ -->
<h2 id="m3"><span class="emoji">📣</span> M3 · Automatización de Marketing</h2>

<div class="mod-header">
  <div class="mod-icon">📣</div>
  <div>
    <h3 style="margin:0">Marketing Automatizado</h3>
    <p>Semanas 6–8 · ~8h · Nurturing, contenido IA y funnels de conversión</p>
  </div>
</div>

<h3 id="m3-s6">Semana 6 — Publicaciones y Nurturing</h3>
<span class="week">📅 Semana 6 · 1 clase (2.5h)</span>

<h3>Apuntes</h3>
<ul>
  <li><strong>Stack marketing:</strong> n8n + Brevo + Typeform + Buffer</li>
  <li><strong>Nurturing:</strong> secuencias de email basadas en comportamiento (opened, clicked, no reply)</li>
  <li><strong>Social automation:</strong> ética, límites de plataformas, riesgo de ban</li>
</ul>

<div class="wf">
  <h4><span class="num">12</span> Lead Nurturing Sequence</h4>
  <p>Lead en Typeform → 3 emails automáticos en Brevo: Day 0 (bienvenida), Day 3 (valor), Day 7 (CTA).</p>
  <div class="flow">Typeform → n8n Wait (3d) → Brevo (Send × 3)</div>
</div>
<div class="wf">
  <h4><span class="num">13</span> Social Repurpose Bot</h4>
  <p>Blog post RSS → GPT reformatea para LinkedIn + Twitter → Buffer scheduling.</p>
  <div class="flow">RSS → OpenAI (Reformat × 2) → Buffer (Schedule)</div>
</div>

<hr>

<h3 id="m3-s7">Semana 7 — Contenido con IA y Funnels</h3>
<span class="week">📅 Semana 7 · 2 clases (4h)</span>

<div class="wf">
  <h4><span class="num">14</span> Content Factory</h4>
  <p>Keyword → GPT genera post largo → Notion + imagen DALL-E → Buffer.</p>
  <div class="flow">Manual Trigger → OpenAI (Post) → DALL-E (Image) → Notion → Buffer</div>
</div>
<div class="wf">
  <h4><span class="num">15</span> Funnel Completo</h4>
  <p>Typeform lead magnet → Brevo sequence → Airtable CRM → Slack notify comercial.</p>
  <div class="flow">Typeform → Brevo Sequence → Airtable → Slack</div>
</div>
<div class="wf">
  <h4><span class="num">16</span> Newsletter Automatizada</h4>
  <p>Curación RSS semanal → GPT resume artículos → Brevo envío semanal.</p>
  <div class="flow">Schedule (Weekly) → RSS × 5 → OpenAI → Brevo</div>
</div>

<div class="deliv">
  <h4>📋 Entregable M3 (Semana 8 Q&A)</h4>
  <ul>
    <li>Funnel funcional: Landing → Lead → Nurturing → CRM</li>
    <li>Métricas: open rate, CTR, tasa de conversión</li>
  </ul>
</div>

<!-- ============ M4 ============ -->
<h2 id="m4"><span class="emoji">💼</span> M4 · Automatización de Ventas</h2>

<div class="mod-header">
  <div class="mod-icon">💼</div>
  <div>
    <h3 style="margin:0">Sales Automation</h3>
    <p>Semanas 9–12 · ~8.5h · Lead scoring, follow-ups, pipeline, ciclo comercial completo</p>
  </div>
</div>

<h3>Apuntes</h3>
<ul>
  <li><strong>Lead scoring:</strong> puntuar por empresa, tamaño, fuente, engagement</li>
  <li><strong>Deal stages:</strong> mover deals automáticamente por tiempo o actividad</li>
  <li><strong>CRM:</strong> HubSpot, Pipedrive, o Notion como CRM ligero</li>
  <li><strong>Alertas inteligentes:</strong> solo notificar cuando hay que actuar</li>
</ul>

<pre><span class="cm"># Ejemplo: tabla de scoring en n8n (Function node)</span>
const lead = $json;
let score = 0;

<span class="cm">// Empresa conocida</span>
if (lead.company_size > 50) score += 30;
if (lead.source === 'referral') score += 25;
if (lead.budget > 10000) score += 20;
if (lead.timeline === 'this_month') score += 25;

<span class="cm">// Clasificar</span>
const tier = score >= 70 ? 'HOT' : score >= 40 ? 'WARM' : 'COLD';
return { json: { ...lead, score, tier } };</pre>

<div class="wf">
  <h4><span class="num">17</span> Lead Scoring Engine</h4>
  <p>Nuevo lead → puntuar → asignar automáticamente al comercial correcto.</p>
  <div class="flow">Webhook → Function (Score) → IF (Hot/Warm/Cold) → Slack / Email</div>
</div>
<div class="wf">
  <h4><span class="num">18</span> Follow-up Automático</h4>
  <p>Lead sin respuesta 48h → GPT genera email personalizado → envío automático.</p>
  <div class="flow">Schedule → Airtable (Filter: no_reply > 48h) → OpenAI → Gmail</div>
</div>
<div class="wf">
  <h4><span class="num">19</span> Notion Sales Pipeline</h4>
  <p>Actualización de deal → notificación Slack + log Airtable.</p>
  <div class="flow">Notion Trigger → Airtable (Log) → Slack (Notify)</div>
</div>
<div class="wf">
  <h4><span class="num">20</span> Deal Won Trigger</h4>
  <p>Deal cerrado → onboarding automático + factura → Slack celebración.</p>
  <div class="flow">Airtable (Status=Won) → Brevo (Onboarding) → Slack 🎉</div>
</div>

<div class="deliv">
  <h4>📋 Entregable M4</h4>
  <ul>
    <li>Pipeline de ventas completo con al menos 3 automations activas</li>
    <li>Demo de lead scoring funcionando con datos reales o mock</li>
  </ul>
</div>

<!-- ============ M5 ============ -->
<h2 id="m5"><span class="emoji">🤖</span> M5 · Automatización en Atención al Cliente</h2>

<div class="mod-header">
  <div class="mod-icon">🤖</div>
  <div>
    <h3 style="margin:0">AI Agents para Soporte</h3>
    <p>Semanas 12–14 · ~8.5h · Onboarding, chatbots y agentes con memoria</p>
  </div>
</div>

<h3>Apuntes</h3>
<ul>
  <li><strong>Chatbot vs AI Agent:</strong> script fijo vs decisiones autónomas</li>
  <li><strong>RAG (Retrieval-Augmented Generation):</strong> conectar FAQ/docs al agente</li>
  <li><strong>Memoria conversacional:</strong> el agente recuerda la charla con cada usuario</li>
  <li><strong>Escalado humano:</strong> cuándo pasar a persona real (y cómo hacerlo smooth)</li>
</ul>

<pre><span class="cm"># Arquitectura básica de un AI Agent en n8n</span>
<span class="cm"># 1. Webhook recibe mensaje del usuario</span>
<span class="cm"># 2. Buscar contexto previo (memoria) en Notion/Supabase</span>
<span class="cm"># 3. Buscar en base de conocimiento (RAG)</span>
<span class="cm"># 4. Llamar a GPT con: system prompt + contexto + FAQ + mensaje</span>
<span class="cm"># 5. Guardar respuesta en memoria</span>
<span class="cm"># 6. Enviar respuesta al usuario</span>
<span class="cm"># 7. Si confianza < 0.7 → escalar a humano</span></pre>

<div class="wf">
  <h4><span class="num">21</span> Onboarding Automatizado</h4>
  <p>Cliente firma → secuencia Brevo + acceso plataforma + booking Calendly.</p>
  <div class="flow">Webhook (firmado) → Brevo (Sequence) → Platform API → Calendly</div>
</div>
<div class="wf">
  <h4><span class="num">22</span> AI Support Agent (I)</h4>
  <p>Webhook web → n8n AI Agent con GPT-4o → respuesta inmediata + log en Notion.</p>
  <div class="flow">Webhook → AI Agent (GPT-4o) → Notion (Log) → Response</div>
</div>
<div class="wf">
  <h4><span class="num">23</span> AI Support Agent (II)</h4>
  <p>Añadir memoria conversacional + FAQ en Notion como base de conocimiento (RAG).</p>
  <div class="flow">Webhook → Memory Lookup → AI Agent + RAG → Response → Save Memory</div>
</div>

<div class="deliv">
  <h4>📋 Entregable M5</h4>
  <ul>
    <li>AI Agent funcional con al menos 5 preguntas FAQ respondidas correctamente</li>
    <li>Memoria conversacional demostrada (recordar nombre y contexto)</li>
  </ul>
</div>

<!-- ============ M6 ============ -->
<h2 id="m6"><span class="emoji">🧾</span> M6 · Automatización de Finanzas</h2>

<div class="mod-header">
  <div class="mod-icon">🧾</div>
  <div>
    <h3 style="margin:0">Automatización Financiera</h3>
    <p>Semanas 15–16 · ~5h · OCR, facturas, expense reports</p>
  </div>
</div>

<h3>Setup extra para este módulo</h3>
<pre><span class="cm"># Instalar antes de la semana 15</span>
pip install pytesseract pillow pdf2image
pip install supabase
npm install @supabase/supabase-js</pre>

<div class="wf">
  <h4><span class="num">24</span> Invoice OCR Pipeline</h4>
  <p>Email con factura adjunta → GPT-4 Vision extrae datos → Airtable/Supabase.</p>
  <div class="flow">Gmail (attachment) → OpenAI Vision (extract) → Airtable (Create Record)</div>
</div>
<div class="wf">
  <h4><span class="num">25</span> Facturación Automática</h4>
  <p>Deal cerrado → generar factura PDF → enviar por email + archivar en Drive.</p>
  <div class="flow">Airtable (Status=Won) → PDF Generator → Gmail + Google Drive</div>
</div>
<div class="wf">
  <h4><span class="num">26</span> Expense Report Bot</h4>
  <p>Foto del ticket vía Telegram → GPT extrae importe/categoría → Google Sheets.</p>
  <div class="flow">Telegram (Photo) → OpenAI Vision → Google Sheets (Append)</div>
</div>

<!-- ============ M7 ============ -->
<h2 id="m7"><span class="emoji">🚀</span> M7 · Mejoras e Implementaciones</h2>

<div class="mod-header">
  <div class="mod-icon">🚀</div>
  <div>
    <h3 style="margin:0">Escalar e Implantar en Producción</h3>
    <p>Semana 17 · ~6h · VPS, Docker, monitorización y proyecto final</p>
  </div>
</div>

<h3>Deploy de n8n en VPS — docker-compose.yml</h3>
<pre><span class="cm"># docker-compose.yml — producción</span>
version: '3.8'
services:
  n8n:
    image: n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.tudominio.com
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.tudominio.com/
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:</pre>

<h3>Nginx Reverse Proxy + SSL</h3>
<pre><span class="cm"># /etc/nginx/sites-available/n8n</span>
server {
    server_name n8n.tudominio.com;
    location / {
        proxy_pass http://localhost:5678;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

<span class="cm"># SSL automático con Let's Encrypt</span>
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d n8n.tudominio.com</pre>

<div class="wf">
  <h4><span class="num">27</span> Workflow Monitor</h4>
  <p>Cron job → chequeo de workflows activos → alerta si alguno falla.</p>
  <div class="flow">Schedule (5min) → HTTP (n8n API) → IF (error) → Telegram Alert</div>
</div>

<div class="deliv">
  <h4>🏆 Proyecto Final Integrador</h4>
  <ul>
    <li>Sistema completo combinando al menos 3 módulos</li>
    <li>Deployado en producción (n8n cloud o self-hosted)</li>
    <li>Presentación 10 min: problema → solución → demo → métricas</li>
    <li>Documentación: naming de workflows, notas en nodos, manejo de errores</li>
  </ul>
</div>

<!-- ============ RECURSOS ============ -->
<h2 id="recursos"><span class="emoji">📎</span> Recursos y Documentación</h2>
<div class="res-grid">
  <a href="https://docs.n8n.io" target="_blank" class="res-link"><span class="ri">⚙️</span><div><div class="rl">n8n Docs</div><div class="rd">Documentación oficial</div></div></a>
  <a href="https://n8n.io/workflows" target="_blank" class="res-link"><span class="ri">📋</span><div><div class="rl">n8n Templates</div><div class="rd">Workflows pre-hechos</div></div></a>
  <a href="https://academy.make.com" target="_blank" class="res-link"><span class="ri">🔄</span><div><div class="rl">Make Academy</div><div class="rd">Cursos oficiales</div></div></a>
  <a href="https://zapier.com/learn" target="_blank" class="res-link"><span class="ri">⚡</span><div><div class="rl">Zapier University</div><div class="rd">Guías y tutoriales</div></div></a>
  <a href="https://cookbook.openai.com" target="_blank" class="res-link"><span class="ri">🧠</span><div><div class="rl">OpenAI Cookbook</div><div class="rd">Recetas y patrones</div></div></a>
  <a href="https://supabase.com/docs" target="_blank" class="res-link"><span class="ri">🗄️</span><div><div class="rl">Supabase Docs</div><div class="rd">Base de datos + Auth</div></div></a>
</div>

</main>
</div>

<footer>
  <p>© 2025 Nuclio Digital School × <a href="https://www.nexusfinlabs.com">NexusFinLabs</a> · Alberto Lobo · <a href="/product">Máster Product Management →</a></p>
</footer>

</body>
</html>"""
