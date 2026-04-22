RESTAURANTES_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bot de Reservas — Sistema Automatizado para Restaurantes · DravaAutomations</title>
<meta name="description" content="Bot inteligente de reservas por WhatsApp para restaurantes. Gestión dinámica de mesas, confirmación automática y recordatorio -24h.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--dark:#1a1a2e;--text:#1a1a1a;--muted:#6b7280;--muted2:#9ca3af;--border:#e5e7eb;--bg:#fff;--bg2:#f9fafb;--amber:#f59e0b;--amber-light:#fffbeb;--green:#22c55e}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text)}

nav{position:fixed;top:0;left:0;right:0;z-index:100;height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 28px;background:#fff;border-bottom:1px solid var(--border)}
.nav-brand{font-size:15px;font-weight:800;color:var(--dark);text-decoration:none;display:flex;align-items:center;gap:8px}
.nav-brand .icon{font-size:18px}
.nav-links a{color:var(--muted);text-decoration:none;padding:6px 12px;border-radius:6px;font-size:13px;font-weight:500;margin-left:4px}
.nav-links a:hover{color:var(--text);background:var(--bg2)}

.hero{background:linear-gradient(160deg,#1a1a2e,#2d1b3d);min-height:420px;display:flex;align-items:center;justify-content:center;text-align:center;padding:90px 24px 60px}
.hero-badge{background:rgba(245,158,11,.12);border:1px solid rgba(245,158,11,.25);border-radius:100px;padding:4px 14px;font-size:11px;font-weight:700;color:var(--amber);display:inline-block;margin-bottom:16px;text-transform:uppercase;letter-spacing:.08em}
.hero h1{font-size:clamp(2rem,4vw,3rem);font-weight:900;color:#fff;margin-bottom:14px;letter-spacing:-.03em;line-height:1.1}
.hero h1 span{color:var(--amber)}
.hero-sub{color:rgba(255,255,255,.5);font-size:14px;max-width:480px;margin:0 auto 30px;line-height:1.7}
.hero-stats{display:flex;gap:32px;justify-content:center;flex-wrap:wrap}
.hs{text-align:center}
.hs .n{font-size:1.6rem;font-weight:900;color:var(--amber)}
.hs .l{font-size:10px;color:rgba(255,255,255,.45);text-transform:uppercase;letter-spacing:.06em;margin-top:2px}

section{padding:64px 24px}
.container{max-width:900px;margin:0 auto}
.sec-label{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.12em;color:var(--muted2);margin-bottom:8px;display:block}
.sec-title{font-size:clamp(1.5rem,2.5vw,2rem);font-weight:900;margin-bottom:12px;letter-spacing:-.02em}
.sec-sub{font-size:14px;color:var(--muted);line-height:1.7;max-width:520px}

/* FLOW */
.flow-grid{display:grid;gap:0;margin:32px 0}
.flow-step{display:grid;grid-template-columns:48px 1fr;gap:16px;padding:20px 0;position:relative}
.flow-step:not(:last-child)::after{content:'';position:absolute;left:23px;top:68px;bottom:0;width:2px;background:var(--border)}
.flow-num{width:48px;height:48px;background:var(--dark);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:900;color:#fff;position:relative;z-index:1}
.flow-content h3{font-size:15px;font-weight:800;margin-bottom:4px}
.flow-content p{font-size:13px;color:var(--muted);line-height:1.6}

/* CHAT DEMO */
.chat-demo{background:var(--dark);border-radius:16px;padding:24px;max-width:420px;margin:28px auto;font-size:13px}
.msg{padding:10px 14px;border-radius:12px;margin-bottom:8px;max-width:85%;line-height:1.5}
.msg-bot{background:#2d2d44;color:#a5b4c7;border-bottom-left-radius:4px}
.msg-user{background:var(--amber);color:#fff;margin-left:auto;border-bottom-right-radius:4px;text-align:right}
.msg-system{background:rgba(34,197,94,.15);color:var(--green);font-size:11px;font-weight:700;text-align:center;border-radius:6px;padding:6px;margin:12px 0}

/* FEATURES */
.feat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:28px 0}
.feat-card{background:#fff;border:1px solid var(--border);border-radius:12px;padding:22px 18px;transition:.2s}
.feat-card:hover{border-color:#d1d5db;box-shadow:0 4px 16px rgba(0,0,0,.05)}
.feat-card .icon{font-size:24px;margin-bottom:10px}
.feat-card h4{font-size:14px;font-weight:700;margin-bottom:4px}
.feat-card p{font-size:12px;color:var(--muted);line-height:1.55}

/* TABLE */
.simple-table{width:100%;border-collapse:collapse;border:1px solid var(--border);border-radius:10px;overflow:hidden;margin:16px 0;font-size:13px}
.simple-table th{text-align:left;padding:10px 14px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);background:var(--bg2)}
.simple-table td{padding:10px 14px;border-bottom:1px solid var(--border)}
.simple-table tr:last-child td{border-bottom:none}

/* PRICING */
.pricing-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:28px 0}
.price-card{background:#fff;border:1px solid var(--border);border-radius:14px;padding:24px;text-align:center}
.price-card.featured{border-color:var(--amber);box-shadow:0 4px 20px rgba(245,158,11,.12)}
.price-label{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px}
.price-val{font-size:32px;font-weight:900;margin-bottom:4px}
.price-note{font-size:12px;color:var(--muted)}

/* CTA */
.cta-box{background:linear-gradient(160deg,var(--dark),#2d1b3d);border-radius:16px;padding:40px;text-align:center;margin-top:48px}
.cta-box h3{font-size:1.4rem;font-weight:900;color:#fff;margin-bottom:10px}
.cta-box p{font-size:14px;color:rgba(255,255,255,.5);margin-bottom:24px}
.cta-btn{background:var(--amber);color:#fff;text-decoration:none;padding:13px 28px;border-radius:100px;font-size:14px;font-weight:800;transition:.2s;display:inline-block}
.cta-btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(245,158,11,.3)}

.bg-gray{background:var(--bg2)}

footer{background:var(--dark);padding:28px 24px;text-align:center}
footer p{color:rgba(255,255,255,.3);font-size:12px}
footer a{color:rgba(255,255,255,.5);text-decoration:none}

@media(max-width:640px){.pricing-row{grid-template-columns:1fr}.flow-step{grid-template-columns:36px 1fr}.flow-num{width:36px;height:36px;font-size:13px}}
</style>
</head>
<body>

<nav>
  <a href="/" class="nav-brand"><span class="icon">🍽️</span> DravaAutomations</a>
  <div class="nav-links">
    <a href="/bb4x4">CRM Concesionario</a>
    <a href="#flujo">Flujo</a>
    <a href="#features">Features</a>
  </div>
</nav>

<section class="hero">
  <div>
    <div class="hero-badge">Proyecto · Restaurante</div>
    <h1>Bot de <span>Reservas</span><br>Automatizado</h1>
    <p class="hero-sub">Un bot en WhatsApp gestiona reservas, comprueba disponibilidad, confirma al cliente y libera mesas ante no-shows. Sin intervención manual.</p>
    <div class="hero-stats">
      <div class="hs"><div class="n">~20</div><div class="l">Consultas/día</div></div>
      <div class="hs"><div class="n">0</div><div class="l">Intervención manual</div></div>
      <div class="hs"><div class="n">-24h</div><div class="l">Recordatorio auto</div></div>
      <div class="hs"><div class="n">100%</div><div class="l">Auditoría</div></div>
    </div>
  </div>
</section>

<!-- PAIN -->
<section class="bg-gray">
  <div class="container">
    <span class="sec-label">Situación actual</span>
    <h2 class="sec-title">El problema que resolvemos</h2>
    <table class="simple-table" style="margin-top:16px">
      <thead><tr><th>Parámetro</th><th>Estado actual</th></tr></thead>
      <tbody>
        <tr><td><strong>Gestión de reservas</strong></td><td>Google Sheets + WhatsApp manual</td></tr>
        <tr><td><strong>Volumen de consultas</strong></td><td>~20/día (manejable pero ineficiente)</td></tr>
        <tr><td><strong>Problema principal</strong></td><td>Tareas manuales, no-shows sin seguimiento</td></tr>
        <tr><td><strong>Impacto económico</strong></td><td>Mesas vacías por cancelaciones no gestionadas</td></tr>
      </tbody>
    </table>
  </div>
</section>

<!-- FLUJO -->
<section id="flujo">
  <div class="container">
    <span class="sec-label">Arquitectura del sistema</span>
    <h2 class="sec-title">Cómo funciona el bot</h2>

    <div class="flow-grid" style="margin-top:24px">
      <div class="flow-step">
        <div class="flow-num">1</div>
        <div class="flow-content">
          <h3>Solicitud del cliente por WhatsApp</h3>
          <p>El bot recibe el mensaje y recoge datos clave: <strong>nombre, teléfono, fecha, hora, número de personas</strong>.</p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num">2</div>
        <div class="flow-content">
          <h3>Consulta de disponibilidad en Google Sheet</h3>
          <p>Verifica disponibilidad en tiempo real. Asigna mesa automáticamente según tamaño del grupo.</p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num">3</div>
        <div class="flow-content">
          <h3>Confirmación dinámica</h3>
          <p><strong>Mesa disponible:</strong> confirma al instante. <strong>Solo mesa grande:</strong> notifica al cliente y espera aceptación. <strong>Sin disponibilidad:</strong> ofrece horarios alternativos.</p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num">4</div>
        <div class="flow-content">
          <h3>Recordatorio -24h antes</h3>
          <p>El sistema envía confirmación de asistencia. Si no responde: libera la mesa automáticamente y notifica al restaurante.</p>
        </div>
      </div>
      <div class="flow-step">
        <div class="flow-num">5</div>
        <div class="flow-content">
          <h3>Almacenamiento y auditoría</h3>
          <p>Todas las conversaciones se guardan. Hay un revisor humano de respaldo para casos excepcionales.</p>
        </div>
      </div>
    </div>

    <!-- CHAT DEMO -->
    <h3 style="margin-top:32px;text-align:center;font-size:14px;color:var(--muted)">Ejemplo de conversación</h3>
    <div class="chat-demo">
      <div class="msg msg-user">Hola, quiero reservar para 4 personas el viernes a las 21h</div>
      <div class="msg msg-bot">¡Hola! 👋 Perfecto, déjame verificar la disponibilidad para el viernes 11 de abril a las 21:00 para 4 personas...</div>
      <div class="msg msg-bot">✅ ¡Hay mesa disponible! Te asigno la mesa 7 (4 personas).<br><br>📋 <strong>Reserva confirmada:</strong><br>📅 Viernes 11/04 a las 21:00<br>👥 4 personas<br>🪑 Mesa 7<br><br>¿Me confirmas tu nombre completo?</div>
      <div class="msg msg-user">María García López</div>
      <div class="msg msg-bot">¡Listo, María! Tu reserva está confirmada. Te enviaré un recordatorio 24h antes. ¡Nos vemos el viernes! 🍽️</div>
      <div class="msg msg-system">✅ Reserva #247 → Sheet actualizado · Recordatorio programado</div>
    </div>
  </div>
</section>

<!-- FEATURES -->
<section id="features" class="bg-gray">
  <div class="container">
    <span class="sec-label">Funcionalidades</span>
    <h2 class="sec-title">Features incluidas</h2>
    <div class="feat-grid" style="margin-top:24px">
      <div class="feat-card"><div class="icon">🪑</div><h4>Gestión dinámica de mesas</h4><p>Asignación automática según tamaño de grupo. Agrupación inteligente para grupos grandes.</p></div>
      <div class="feat-card"><div class="icon">📲</div><h4>Redirect para eventos</h4><p>Reservas especiales y eventos redireccionan a número específico del responsable.</p></div>
      <div class="feat-card"><div class="icon">🚨</div><h4>Alertas al staff</h4><p>El equipo recibe alertas ante fallos, anomalías o situaciones que requieren intervención humana.</p></div>
      <div class="feat-card"><div class="icon">✅</div><h4>Meta Verified</h4><p>Integración con WhatsApp Business API para cumplimiento de políticas de Meta.</p></div>
      <div class="feat-card"><div class="icon">🔒</div><h4>VPS dedicado</h4><p>Infraestructura propia del cliente. Datos bajo su control, sin dependencias externas.</p></div>
      <div class="feat-card"><div class="icon">📊</div><h4>Auditoría completa</h4><p>Todas las conversaciones y reservas quedan registradas para revisión posterior.</p></div>
    </div>
  </div>
</section>

<!-- PRICING -->
<section>
  <div class="container">
    <span class="sec-label">Propuesta</span>
    <h2 class="sec-title">Formato y precio</h2>
    <p class="sec-sub">Caso testigo: validamos el sistema contigo a precio de coste. Después lo replicamos a otros restaurantes.</p>
    <div class="pricing-row" style="margin-top:24px">
      <div class="price-card">
        <div class="price-label">Setup inicial</div>
        <div class="price-val">$0</div>
        <div class="price-note">Precio de validación — caso testigo</div>
      </div>
      <div class="price-card featured">
        <div class="price-label">Retainer mensual</div>
        <div class="price-val">$300</div>
        <div class="price-note">Infraestructura a cargo del cliente</div>
      </div>
    </div>
    <p style="font-size:12px;color:var(--muted);text-align:center;margin-top:12px">💡 Estrategia: validar rápido, documentar, replicar a otros restaurantes con costes marginales decrecientes.</p>
  </div>
</section>

<!-- CTA -->
<section class="bg-gray">
  <div class="container">
    <div class="cta-box">
      <h3>¿Quieres automatizar tus reservas?</h3>
      <p>Agenda una llamada y te mostramos el bot funcionando con datos reales de tu restaurante.</p>
      <a href="mailto:david@dravaautomations.com" class="cta-btn">Agendar demo →</a>
    </div>
  </div>
</section>

<footer>
  <p>© 2026 <a href="https://dravaautomations.com">DravaAutomations LLC</a> · David Ramos Ruiz · <a href="/bb4x4">Proyecto CRM Concesionario →</a></p>
</footer>

</body>
</html>"""
