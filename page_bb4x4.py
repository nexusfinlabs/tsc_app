BB4X4_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BB4x4 — CRM + Agente IA de Cualificación de Leads · DravaAutomations</title>
<meta name="description" content="Sistema CRM con agente IA para concesionarios: cualificación automática de leads por WhatsApp, scoring BANT y notificación al equipo comercial.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--dark:#0f172a;--dark2:#1e293b;--text:#0f172a;--muted:#64748b;--border:#e2e8f0;--bg:#fff;--bg2:#f8fafc;--green:#22c55e;--green-light:#f0fdf4;--blue:#3b82f6;--yellow:#F5B800}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text)}

nav{position:fixed;top:0;left:0;right:0;z-index:100;height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 28px;background:#fff;border-bottom:1px solid var(--border)}
.nav-brand{font-size:15px;font-weight:800;color:var(--dark);text-decoration:none;display:flex;align-items:center;gap:8px}
.nav-brand .dot{width:8px;height:8px;background:var(--green);border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.nav-links a{color:var(--muted);text-decoration:none;padding:6px 12px;border-radius:6px;font-size:13px;font-weight:500;margin-left:4px}
.nav-links a:hover{color:var(--text);background:var(--bg2)}

/* HERO */
.hero{background:linear-gradient(160deg,var(--dark),#0f2027);min-height:420px;display:flex;align-items:center;justify-content:center;text-align:center;padding:90px 24px 60px}
.hero-badge{background:rgba(34,197,94,.12);border:1px solid rgba(34,197,94,.25);border-radius:100px;padding:4px 14px;font-size:11px;font-weight:700;color:#4ade80;display:inline-block;margin-bottom:16px;text-transform:uppercase;letter-spacing:.08em}
.hero h1{font-size:clamp(2rem,4vw,3rem);font-weight:900;color:#fff;margin-bottom:14px;letter-spacing:-.03em;line-height:1.1}
.hero h1 span{color:var(--green)}
.hero-sub{color:rgba(255,255,255,.5);font-size:14px;max-width:480px;margin:0 auto 30px;line-height:1.7}
.hero-stats{display:flex;gap:32px;justify-content:center;flex-wrap:wrap}
.hs{text-align:center}
.hs .n{font-size:1.6rem;font-weight:900;color:var(--green)}
.hs .l{font-size:10px;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.06em;margin-top:2px}

section{padding:64px 24px}
.container{max-width:900px;margin:0 auto}
.sec-label{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);margin-bottom:8px;display:block}
.sec-title{font-size:clamp(1.5rem,2.5vw,2rem);font-weight:900;margin-bottom:12px;letter-spacing:-.02em}
.sec-sub{font-size:14px;color:var(--muted);line-height:1.7;max-width:520px}

/* FLOW */
.flow-grid{display:grid;gap:0;margin:32px 0}
.flow-step{display:grid;grid-template-columns:48px 1fr;gap:16px;padding:20px 0;position:relative}
.flow-step:not(:last-child)::after{content:'';position:absolute;left:23px;top:68px;bottom:0;width:2px;background:var(--border)}
.flow-num{width:48px;height:48px;background:var(--dark);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;color:#fff;position:relative;z-index:1}
.flow-num.hot{background:#ef4444}
.flow-num.warm{background:var(--yellow)}
.flow-num.cold{background:var(--blue)}
.flow-content h3{font-size:15px;font-weight:800;margin-bottom:4px}
.flow-content p{font-size:13px;color:var(--muted);line-height:1.6}
.flow-content code{background:var(--bg2);border:1px solid var(--border);padding:2px 6px;border-radius:4px;font-size:12px;font-family:'JetBrains Mono',monospace;color:#7c3aed}

/* CHAT DEMO */
.chat-demo{background:var(--dark);border-radius:16px;padding:24px;max-width:420px;margin:28px auto;font-size:13px}
.chat-demo .msg{padding:10px 14px;border-radius:12px;margin-bottom:8px;max-width:85%;line-height:1.5}
.msg-bot{background:#1e293b;color:#94a3b8;border-bottom-left-radius:4px}
.msg-user{background:var(--green);color:#fff;margin-left:auto;border-bottom-right-radius:4px;text-align:right}
.msg-system{background:rgba(245,184,0,.15);color:var(--yellow);font-size:11px;font-weight:700;text-align:center;border-radius:6px;padding:6px;margin:12px 0}

/* METRICS TABLE */
.metrics-table{width:100%;border-collapse:collapse;border:1px solid var(--border);border-radius:10px;overflow:hidden;margin:20px 0;font-size:13px}
.metrics-table th{text-align:left;padding:10px 14px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:var(--bg2)}
.metrics-table td{padding:10px 14px;border-bottom:1px solid var(--border)}
.metrics-table tr:last-child td{border-bottom:none;font-weight:700;background:#f0fdf4}
.metrics-table .tag-hot{background:#fef2f2;color:#dc2626;font-size:10px;font-weight:800;padding:2px 8px;border-radius:100px}
.metrics-table .tag-gain{color:var(--green);font-weight:800}

/* PRICING */
.pricing-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:28px 0}
.price-card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:24px;text-align:center}
.price-card.featured{border-color:var(--green);box-shadow:0 4px 20px rgba(34,197,94,.12)}
.price-label{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px}
.price-val{font-size:32px;font-weight:900;margin-bottom:4px}
.price-note{font-size:12px;color:var(--muted)}

/* CTA */
.cta-box{background:linear-gradient(160deg,var(--dark),#0f2027);border-radius:16px;padding:40px;text-align:center;margin-top:48px}
.cta-box h3{font-size:1.4rem;font-weight:900;color:#fff;margin-bottom:10px}
.cta-box p{font-size:14px;color:rgba(255,255,255,.5);margin-bottom:24px}
.cta-btn{background:var(--green);color:#fff;text-decoration:none;padding:13px 28px;border-radius:100px;font-size:14px;font-weight:800;transition:.2s;display:inline-block}
.cta-btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(34,197,94,.3)}

footer{background:var(--dark);padding:28px 24px;text-align:center}
footer p{color:rgba(255,255,255,.3);font-size:12px}
footer a{color:rgba(255,255,255,.5);text-decoration:none}

@media(max-width:640px){.pricing-row{grid-template-columns:1fr}.flow-step{grid-template-columns:36px 1fr}.flow-num{width:36px;height:36px;font-size:13px}}
</style>
</head>
<body>

<nav>
  <a href="/" class="nav-brand"><span class="dot"></span> DravaAutomations</a>
  <div class="nav-links">
    <a href="/restaurantes">Restaurantes</a>
    <a href="#flujo">Flujo</a>
    <a href="#roi">ROI</a>
  </div>
</nav>

<section class="hero">
  <div>
    <div class="hero-badge">Proyecto · Concesionario Automotriz</div>
    <h1>CRM + Agente IA<br>de <span>Cualificación de Leads</span></h1>
    <p class="hero-sub">Un agente en WhatsApp cualifica cada lead con BANT adaptado, los puntúa y notifica al comercial solo cuando están listos para comprar.</p>
    <div class="hero-stats">
      <div class="hs"><div class="n">~50</div><div class="l">Leads/mes</div></div>
      <div class="hs"><div class="n">$115K</div><div class="l">Ticket promedio</div></div>
      <div class="hs"><div class="n">+$50K</div><div class="l">Beneficio anual extra</div></div>
      <div class="hs"><div class="n">&lt;1 mes</div><div class="l">ROI del sistema</div></div>
    </div>
  </div>
</section>

<!-- PAIN POINTS -->
<section style="background:var(--bg2)">
  <div class="container">
    <span class="sec-label">Situación actual</span>
    <h2 class="sec-title">El problema que resolvemos</h2>
    <table class="metrics-table" style="margin-top:20px">
      <thead><tr><th>Parámetro</th><th>Estado actual</th></tr></thead>
      <tbody>
        <tr><td><strong>Responsable de ventas</strong></td><td>Ignacio — gestión manual vía WhatsApp</td></tr>
        <tr><td><strong>Volumen de leads</strong></td><td>~50 leads/mes</td></tr>
        <tr><td><strong>Tasa de cierre actual</strong></td><td>10% (5 ventas/mes)</td></tr>
        <tr><td><strong>Ticket promedio</strong></td><td>$110,000 — $120,000</td></tr>
        <tr><td><strong>Problema principal</strong></td><td><span class="tag-hot">Filtrado manual, respuestas automáticas inútiles</span></td></tr>
        <tr><td><strong>Riesgo</strong></td><td>Leads calientes se enfrían por falta de seguimiento inmediato</td></tr>
      </tbody>
    </table>
  </div>
</section>

<!-- FLUJO -->
<section id="flujo">
  <div class="container">
    <span class="sec-label">Arquitectura del sistema</span>
    <h2 class="sec-title">Cómo funciona el agente</h2>
    <p class="sec-sub">El agente opera sobre WhatsApp Business con cualificación BANT adaptada y scoring automático.</p>

    <div class="flow-grid" style="margin-top:28px">
      <div class="flow-step">
        <div class="flow-num">1</div>
        <div class="flow-content">
          <h3>Entry Point — WhatsApp Business</h3>
          <p>El lead llega por WhatsApp. El agente toma control inmediato de la conversación y responde en menos de 30 segundos.</p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num">2</div>
        <div class="flow-content">
          <h3>Cualificación BANT Adaptada</h3>
          <p>El agente pregunta de forma natural y extrae: <code>vehículo buscado</code> · <code>presupuesto</code> · <code>financiación o contado</code> · <code>plazo de compra</code> · <code>vehículo a entregar</code></p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num hot">3</div>
        <div class="flow-content">
          <h3>Scoring Automático del Lead</h3>
          <p><strong style="color:#ef4444">HOT:</strong> notificación inmediata a Ignacio &nbsp;·&nbsp; <strong style="color:#eab308">WARM:</strong> secuencia de nurturing &nbsp;·&nbsp; <strong style="color:#3b82f6">COLD:</strong> seguimiento automático 7/14 días</p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num">4</div>
        <div class="flow-content">
          <h3>Carga en CRM (Airtable / NocoDB)</h3>
          <p>Ficha completa con prioridad, historial y estado. Ignacio solo ve leads ya cualificados y listos para cerrar.</p>
        </div>
      </div>
    </div>

    <!-- CHAT DEMO -->
    <h3 style="margin-top:32px;text-align:center;font-size:14px;color:var(--muted)">Ejemplo de conversación</h3>
    <div class="chat-demo">
      <div class="msg msg-user">Hola, me interesa un Toyota 4Runner 2024</div>
      <div class="msg msg-bot">¡Hola! 👋 Me alegro de tu interés en la 4Runner. Es un vehículo espectacular.<br><br>Para darte la mejor opción, ¿me podrías decir tu presupuesto aproximado?</div>
      <div class="msg msg-user">Tengo unos $115,000, quiero financiar parte</div>
      <div class="msg msg-bot">Perfecto. ¿Para cuándo necesitarías el vehículo? ¿Y tienes uno actual que quieras entregar como parte de pago?</div>
      <div class="msg msg-user">Lo antes posible. Sí, tengo un Hilux 2020</div>
      <div class="msg msg-system">🔥 LEAD HOT → Ignacio notificado · Ficha creada en CRM</div>
    </div>
  </div>
</section>

<!-- ROI -->
<section id="roi" style="background:var(--bg2)">
  <div class="container">
    <span class="sec-label">Impacto financiero</span>
    <h2 class="sec-title">Proyección de ROI</h2>
    <table class="metrics-table" style="margin-top:20px">
      <thead><tr><th>Métrica</th><th>Escenario actual</th><th>Con sistema IA</th></tr></thead>
      <tbody>
        <tr><td>Leads/mes</td><td>50</td><td>50</td></tr>
        <tr><td>Tasa de cierre</td><td>10% (5 ventas)</td><td><span class="tag-gain">+5% = 3 ventas más</span></td></tr>
        <tr><td>Ticket promedio</td><td>$115,000</td><td>$115,000</td></tr>
        <tr><td>Margen estimado</td><td>10–15%</td><td>10–15%</td></tr>
        <tr><td><strong>Beneficio adicional anual</strong></td><td>—</td><td><span class="tag-gain">~$50,000/año</span></td></tr>
      </tbody>
    </table>

    <div class="pricing-row" style="margin-top:32px">
      <div class="price-card">
        <div class="price-label">Setup + Configuración</div>
        <div class="price-val">$500–600</div>
        <div class="price-note">Configuración inicial + 2 semanas prueba gratis</div>
      </div>
      <div class="price-card featured">
        <div class="price-label">Retainer mensual</div>
        <div class="price-val">$400–500</div>
        <div class="price-note">Revisión de precio en mes 3 según resultados</div>
      </div>
    </div>
    <p style="font-size:12px;color:var(--muted);text-align:center;margin-top:12px">💡 ROI del sistema: <strong>se recupera con 1 sola venta adicional</strong> generada por el agente.</p>
  </div>
</section>

<!-- CTA -->
<section>
  <div class="container">
    <div class="cta-box">
      <h3>¿Listo para ver la demo en vivo?</h3>
      <p>Agenda una llamada y te mostramos el agente funcionando con datos reales de tu concesionario.</p>
      <a href="mailto:david@dravaautomations.com" class="cta-btn">Agendar demo →</a>
    </div>
  </div>
</section>

<footer>
  <p>© 2026 <a href="https://dravaautomations.com">DravaAutomations LLC</a> · David Ramos Ruiz · <a href="/restaurantes">Proyecto Restaurantes →</a></p>
</footer>

</body>
</html>"""
