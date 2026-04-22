# TSC Server — Infrastructure Map

> **Last verified**: 2026-04-11 17:28 CET — All 12 endpoints tested ✅  
> **Server**: MiniPC TSC · Ubuntu 22.04 · Tailscale: `tsc` · IP: `100.104.65.25`  
> **Base URL**: `https://tsc.tail8dce43.ts.net`

---

## 🚨 REGLA DE ORO

```
1 servicio = 1 puerto = 1 directorio en /home/tsc/app/
Raíz (/) = SOLO Furnace Monitor en /home/tsc/tsc_app/ → NUNCA TOCAR
```

---

## 🌐 Puerto 443 — `https://tsc.tail8dce43.ts.net`

| Path | Puerto | Servicio | Directorio TSC | Auth | Database | Tablas |
|------|--------|----------|----------------|------|----------|--------|
| `/` | **5000** | 🏭 Furnace Monitor | `/home/tsc/tsc_app/` | Flask session | `httfohqoikkptywupkrs` (Supabase) + SQLite local | temperaturas, alarmas, settings |
| `/iker` | **5050** | ⚽ FútbolGPT | `/home/tsc/app/iker/` | Flask session | — | — |
| `/classes` | **5051** | 🎓 Máster Automation & AI | `/home/tsc/app/classes/` | 🔐 `Albi`/`Classes2026!` | — | — |
| `/product` | **5052** | 📦 Máster Product Mgmt | `/home/tsc/app/product/` | 🔐 `Albi`/`Classes2026!` | — | — |
| `/sports` | **5053** | 🏃 NexusSports AI | `/home/tsc/app/sports/` | 🔐 `Albi`/`Classes2026!` | — | — |
| `/bb4x4` | **5054** | 🚗 BB4x4 Landing | `/home/tsc/app/bb4x4_landing/` | Pública | — | — |
| `/crm` | **5055** | 🚗 BB4x4 CRM (SPA) | `/home/tsc/app/crm/` | Supabase Auth | `lrtmrwsadvnchjqbeeai` | vehicles, contacts, leads, deals, interactions, pipeline_events, tasks, clients |
| `/dealflow` | **5056** | 💼 Nexus DealFlow | `/home/tsc/app/dealflow/` | Supabase Auth | `vyyzblqmpgybuzwnvgus` | deals, deal_contacts, datarooms, dataroom_documents, dataroom_members, dataroom_audit, dataroom_heartbeats |
| `/restaurants` | **5057** | 🍽️ Nómada Restaurantes | `/home/tsc/app/restaurants/` | Pública | — | — |
| `/notai` | **5058** | ⚖️ Nexus NotAI | `/home/tsc/app/notai/` | Supabase Auth | `vyyzblqmpgybuzwnvgus` (compartida con DealFlow) | — (solo auth, sin tablas propias aún) |
| `/aitor` | **5059** | 🌐 AitorTranslate | `/home/tsc/app/aitor/` | Flask session | — | — |

## Puerto 8443 — `https://tsc.tail8dce43.ts.net:8443`

| Path | Puerto | Servicio | Directorio TSC | Auth | Database | Tablas |
|------|--------|----------|----------------|------|----------|--------|
| `/` | **5060** | 🏥 Medical RAG (Flask→Streamlit) | `/home/tsc/app/medical/` | 🔐 `Albi`/`Classes2026!` | — (RAG local) | — |

> ⚠️ Medical usa Flask proxy en 5060 (auth) → Streamlit en 5061 (internal only)

---

## 🔧 Mapa de puertos

| Puerto | Servicio | Funnel | Estado |
|--------|----------|--------|--------|
| **5000** | Furnace Monitor | `/` | ✅ |
| **5050** | FútbolGPT (Iker) | `/iker` | ✅ |
| **5051** | Classes | `/classes` | ✅ |
| **5052** | Product | `/product` | ✅ |
| **5053** | NexusSports AI | `/sports` | ✅ |
| **5054** | BB4x4 Landing | `/bb4x4` | ✅ |
| **5055** | BB4x4 CRM | `/crm` | ✅ |
| **5056** | Nexus DealFlow | `/dealflow` | ✅ |
| **5057** | Nómada Restaurantes | `/restaurants` | ✅ |
| **5058** | Nexus NotAI | `/notai` | ✅ |
| **5059** | AitorTranslate | `/aitor` | ✅ |
| **5060** | Medical Flask proxy | `:8443/` | ✅ |
| **5061** | Medical Streamlit (internal) | — | ✅ (no expuesto) |
| **5062+** | 🆓 **Libres** | — | — |

---

## 🗄️ Supabase Projects

### 1. DealFlow + NotAI

| | |
|--|--|
| **ID** | `vyyzblqmpgybuzwnvgus` |
| **URL** | `https://vyyzblqmpgybuzwnvgus.supabase.co` |
| **Usado por** | `/dealflow`, `/notai` |
| **Frontend key** | `sb_publishable_aEr5gP7k5mII-yNrRu0yrA_cVJKfApm` |
| **Auth** | Email + Google OAuth |
| **RLS** | ✅ |
| **Tablas** | `deals`, `deal_contacts`, `datarooms`, `dataroom_documents`, `dataroom_members`, `dataroom_audit`, `dataroom_heartbeats` |

### 2. Furnace Monitor

| | |
|--|--|
| **ID** | `httfohqoikkptywupkrs` |
| **URL** | `https://httfohqoikkptywupkrs.supabase.co` |
| **Usado por** | `/` (Furnace) |
| **Patrón** | SQLite primary + Supabase async dual-write |
| **Credenciales** | `/home/tsc/tsc_app/.env` |

### 3. BB4x4 CRM

| | |
|--|--|
| **ID** | `lrtmrwsadvnchjqbeeai` |
| **URL** | `https://lrtmrwsadvnchjqbeeai.supabase.co` |
| **Usado por** | `/crm` |
| **Credenciales** | `ai-agents/agents/bb4x4/.env` |
| **Tablas** | `vehicles`, `contacts`, `leads`, `deals`, `interactions`, `pipeline_events`, `tasks`, `clients` |

---

## 🤖 Ollama LLM

| | |
|--|--|
| **Host** | `http://localhost:11434` |
| **Modelos** | `llama3` (text), `llava` (vision) |
| **Usado por** | `/dealflow`, `/notai`, `/sports` |

---

## 📋 Comandos

```bash
# Estado del funnel
ssh tsc "tailscale funnel status"

# Reiniciar servicio (ejemplo: notai en 5058)
ssh tsc "lsof -ti :5058 | xargs kill; cd /home/tsc/app/notai && source venv/bin/activate && PORT=5058 nohup python3 app.py > /tmp/notai.log 2>&1 &"

# Reiniciar medical (2 procesos: proxy + streamlit)
ssh tsc "lsof -ti :5060 :5061 | xargs kill; cd /home/tsc/app/medical && source venv/bin/activate && nohup streamlit run app.py --server.port=5061 --server.headless=true --server.address=127.0.0.1 --server.enableCORS=false --server.enableXsrfProtection=false --browser.gatherUsageStats=false --server.fileWatcherType=none > /tmp/medical_streamlit.log 2>&1 & sleep 3 && nohup python3 proxy.py > /tmp/medical_proxy.log 2>&1 &"

# Deploy desde Mac
rsync -avz --exclude node_modules --exclude .git --exclude .env \
  ~/Desktop/SW_AI/ai-agents/agents/<app>/ tsc:/home/tsc/app/<app>/

# Test todos los endpoints
for p in "/" "/iker/" "/classes/" "/product/" "/sports/" "/bb4x4/" "/crm/" "/dealflow/" "/restaurants/" "/notai/" "/aitor/"; do echo "$p: $(curl -s -o /dev/null -w '%{http_code}' https://tsc.tail8dce43.ts.net$p)"; done
```

---

## 🔄 Sincronización

| Sitio | Ruta |
|-------|------|
| **Mac** | `ai-agents/agents/PORTS.md` ← este archivo |
| **Mac** | `tsc-monitor/PORTS.md` |
| **TSC** | `/home/tsc/tsc_app/PORTS.md` |
| **Git** | `ai-agents` repo |
