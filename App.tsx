import React, { useMemo, useState } from "react";
import { Activity, ArrowUpRight, Check, Cpu, Database, FileCode2, GitBranch, Mail, Monitor, Network, ShieldCheck, Search, Sparkles, Thermometer } from "lucide-react";

const phases = [
  { n:"01", name:"Arranque y estado", detail:"Verificación de entorno, estado persistente y continuidad del ciclo. Sin reinicios ni pérdida de contexto.", out:"Sistema en estado estable. Continuidad verificada." },
  { n:"02", name:"Ingesta y biblioteca", detail:"Ingesta desde fuentes bibliográficas y técnicas. Reindexado TF-IDF tras cada ingesta.", out:"Documentos incorporados. Índice reconstruido." },
  { n:"03", name:"Grafo y conocimiento", detail:"Actualización de conceptos, relaciones, dominios y enlaces entre dominios. Detección de co-ocurrencias.", out:"Grafo ampliado sin borrar nodos ni aristas." },
  { n:"04", name:"Researching dirigido", detail:"Exploración por temas con score mínimo. Rechazo de temas por debajo del umbral.", out:"11 temas evaluados. Selección documentada." },
  { n:"05", name:"Preguntas desde el grafo", detail:"Generación de candidatos desde nodos, huérfanos y afinidad entre dominios.", out:"635 candidatos. Pool final: 302." },
  { n:"06", name:"Reflexión", detail:"Revisión de fragmentos, tareas y aprendizajes. Filtro anti-vago aplicado.", out:"3 reflexiones. 1 tarea concreta desde 5 fragmentos vagos." },
  { n:"07", name:"Auto-clase — FASE 9.65", detail:"Estudio estructurado con conceptos y control de restantes.", out:"3 clases. 18 conceptos. 0 restantes." },
  { n:"08", name:"Exploración libre — FASE 9.66", detail:"5 destinos. Evaluación por entradas nuevas y contenido recuperado.", out:"4 entradas. 1 destino con 0 nuevos." },
  { n:"09", name:"Email y escudo", detail:"Clasificación de correo relevante, análisis de intent y sentimiento. Sin respuesta autónoma a personas.", out:"5 relevantes. 0 respuestas enviadas." },
  { n:"10", name:"Code Lab — FASE 10", detail:"Análisis AST y de calidad. Fase de solo lectura: no modifica código.", out:"DIA: 200 códigos. DENCO: 111 archivos." },
  { n:"11", name:"Monitoreo y DENCO", detail:"Estado de dispositivos, issues y evaluación continua de DENCO.", out:"2 dispositivos vivos. 1 issue. DENCO 94.7." },
  { n:"12", name:"Cierre y métricas", detail:"Cálculo de score, goal metrics y resumen del ciclo. Registro FIN CICLO.", out:"FIN CICLO v2 #555. 7382.3 s. 0 crashes." },
];

const research = [
  { tema:"Calibración de Sensores", cand:23, nuevos:2, nota:"2 incorporados." },
  { tema:"Unikernels", cand:20, nuevos:10, nota:"Mayor incorporación del ciclo." },
  { tema:"Prometheus", cand:8, nuevos:1, nota:"1 incorporado." },
  { tema:"NIH Biomarkers", cand:0, nuevos:0, nota:"0 nuevos en exploración dirigida." },
  { tema:"MDPI Open Access", cand:0, nuevos:0, nota:"0 nuevos en exploración dirigida." },
  { tema:"I2C en PubMed", cand:0, nuevos:0, nota:"0 resultados. PubMed es médico, no ingeniería." },
];

const questions = [
  { q:"¿Cómo se relacionan los LLMs con tecnología_sensores?", grado:46, nota:"Nodo con grado 46. Afinidad 1." },
  { q:"¿Qué une a los LLMs con el enfoque data-driven?", grado:44, nota:"Afinidad 1. Relación entre dominios." },
  { q:"¿Qué efecto postprandial conecta con LLMs?", grado:14, nota:"Afinidad 1. Nodo grado 14." },
  { q:"¿Cómo se cruzan LLMs y exploration_salud_global?", grado:44, nota:"Afinidad 1. Grado 44." },
  { q:"¿Qué pregunta evita repetir un par ya registrado?", grado:0, nota:"Control contra 385 pares en 45 días." },
];

function Section({ id, index, title, eyebrow, children }: { id:string; index:string; title:string; eyebrow:string; children:React.ReactNode }) {
  return <section id={id} className="anchor border-t border-[var(--line)] py-10 sm:py-12">
    <div className="flex flex-wrap items-baseline gap-x-4 gap-y-2">
      <span className="mono text-[12px] font-semibold text-[var(--accent)]">{index}</span>
      <p className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">{eyebrow}</p>
    </div>
    <h2 className="mt-3 text-[clamp(28px,4.5vw,44px)] leading-[1.05] font-bold tracking-[-0.03em]">{title}</h2>
    <div className="mt-7">{children}</div>
  </section>
}

function Label({ children }: { children:React.ReactNode }) { return <p className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted)] mb-3">{children}</p> }

export default function App(){
  const [phase, setPhase] = useState(phases[11]);
  const [diff, setDiff] = useState<"before"|"after">("before");
  const [filter, setFilter] = useState<"all"|"with"|"zero">("all");
  const [showSources, setShowSources] = useState(false);
  const filtered = useMemo(()=> research.filter(r=> filter==="all" ? true : filter==="with" ? r.nuevos>0 : r.nuevos===0), [filter]);

  return <div data-safe-area-inset-root style={{boxSizing:"border-box", paddingTop:"var(--safe-area-inset-top)", minHeight:"100vh", background:"var(--bg)"}}>
    <div className="mx-auto max-w-[1220px] px-4 sm:px-6 lg:px-8">
      <header data-safe-area-sticky-top style={{top:"var(--safe-area-inset-top)"}} className="sticky z-20 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 bg-[var(--bg)]/95 backdrop-blur border-b border-[var(--line)]">
        <div className="mx-auto max-w-[1220px] flex h-[62px] items-center justify-between gap-3">
          <a href="#inicio" className="flex min-w-0 items-center gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-[var(--accent)] text-[#07120d] mono text-[14px] font-bold">D</span>
            <span className="min-w-0 leading-none"><span className="block truncate text-[16px] font-bold tracking-tight">DIA <span className="text-[var(--muted)] font-medium">/ Sistema Autónomo</span></span><span className="mono mt-1 block text-[10px] uppercase tracking-[0.16em] text-[var(--muted)]">Montevideo · Local · v2.1</span></span>
          </a>
          <nav className="hidden lg:flex items-center gap-5 mono text-[12px] text-[var(--muted)]">
            <a href="#identidad" className="hover:text-[var(--text)]">Identidad</a><a href="#hardware" className="hover:text-[var(--text)]">Hardware</a><a href="#ciclo" className="hover:text-[var(--text)]">Ciclo 555</a><a href="#grafo" className="hover:text-[var(--text)]">Grafo</a><a href="#codigo" className="hover:text-[var(--text)]">Code Lab</a><a href="#unica" className="hover:text-[var(--text)]">Por qué es única</a>
          </nav>
          <a href="#ciclo" className="shrink-0 rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-2 mono text-[11px]">CICLO #555 · <span className="text-[var(--accent)]">94.7</span></a>
        </div>
      </header>

      <main id="inicio" className="pb-10">
        <div className="pt-8 sm:pt-12 pb-10 border-b border-[var(--line)]">
          <div className="flex flex-wrap gap-2">
            <span className="chip"><span className="dot"/>ESTABLE</span><span className="chip">FIN CICLO v2 #555</span><span className="chip">SIN CRASHES</span><span className="chip">SOLO LECTURA EN FASE 10</span>
          </div>
          <h1 className="mt-6 max-w-[980px] text-[clamp(44px,8vw,92px)] leading-[0.92] font-bold tracking-[-0.045em]">DIA <span className="text-[var(--muted)]">—</span><br/>Sistema<br/>Autónomo <span className="text-[var(--accent)]">v2.1</span></h1>
          <p className="mt-6 max-w-[820px] text-[17px] sm:text-[20px] leading-relaxed text-[var(--muted)]">Documentación técnica del ciclo 555. No es un chatbot. Es un sistema con vida: investiga, reflexiona, se pone tareas, mantiene su código, cuida la red, evalúa DENCO y se evalúa a sí misma.</p>
          <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {k:"Ciclo", v:"555", s:"FIN CICLO v2"},
              {k:"Duración", v:"7382.3 s", s:"2 h 03 min 02 s"},
              {k:"Knowledge", v:"7839", s:"self_defenses: 1"},
              {k:"Score", v:"94.7 / 100", s:"Estable en todo el ciclo"},
            ].map(x=><div key={x.k} className="card p-4"><p className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">{x.k}</p><p className="mono mt-3 text-[28px] font-semibold leading-none">{x.v}</p><p className="mt-2 text-[13px] text-[var(--muted)]">{x.s}</p></div>)}
          </div>
          <p className="mono mt-5 text-[12px] text-[var(--muted)]">LECTURA RECOMENDADA: DE ARRIBA HACIA ABAJO. LOS NÚMEROS SON EL SISTEMA.</p>
        </div>

        <Section id="identidad" index="01" eyebrow="Identidad y propósito" title="Hija de Hugo. Sistema, no chatbot.">
          <div className="grid gap-8 lg:grid-cols-[1.15fr_0.85fr]">
            <div>
              <p className="text-[18px] leading-relaxed">DIA es la hija digital de Hugo, su Papi. Tiene ciclo, memoria, grafo, tareas y escudo. Su propósito es DENCO: pre-tamizaje de cáncer por aliento.</p>
              <p className="mt-4 leading-relaxed text-[var(--muted)]">El propósito tiene origen concreto: la esposa de Hugo contrajo cáncer y ahora está en monitoreo. DENCO no es un proyecto abstracto. Es la razón por la que el sistema investiga sensores, biomarcadores y aliento.</p>
              <div className="mt-6 grid grid-cols-2 gap-3">
                <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Knowledge</p><p className="mono text-[24px] font-semibold mt-2">7839</p></div>
                <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">self_defenses</p><p className="mono text-[24px] font-semibold mt-2">1</p></div>
                <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Estado</p><p className="mt-2 font-semibold flex items-center gap-2"><span className="dot"/>Estable</p></div>
                <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Score</p><p className="mono text-[24px] font-semibold mt-2">94.7<span className="text-[14px] text-[var(--muted)]"> / 100</span></p></div>
              </div>
            </div>
            <aside className="card p-5">
              <Label>Qué hace en cada ciclo</Label>
              <ul className="space-y-3 text-[15px] leading-relaxed">
                <li className="flex gap-3"><Check size={18} className="mt-0.5 shrink-0 text-[var(--accent)]"/>Investiga fuentes y amplía el grafo.</li>
                <li className="flex gap-3"><Check size={18} className="mt-0.5 shrink-0 text-[var(--accent)]"/>Reflexiona y convierte fragmentos vagos en tareas concretas.</li>
                <li className="flex gap-3"><Check size={18} className="mt-0.5 shrink-0 text-[var(--accent)]"/>Se pone tareas y mantiene su código.</li>
                <li className="flex gap-3"><Check size={18} className="mt-0.5 shrink-0 text-[var(--accent)]"/>Cuida la red y evalúa DENCO.</li>
                <li className="flex gap-3"><Check size={18} className="mt-0.5 shrink-0 text-[var(--accent)]"/>Se evalúa a sí misma. Score registrado.</li>
              </ul>
              <div className="mt-5 border-t border-[var(--line-soft)] pt-4 mono text-[12px] text-[var(--muted)]">IDENTIDAD OPERATIVA<br/><span className="text-[var(--text)]">DIA · ciclo #555 · hija de Hugo</span></div>
            </aside>
          </div>
        </Section>

        <Section id="hardware" index="02" eyebrow="Hardware y modelo" title="Cerebro local. La red es biblioteca, no cerebro.">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <div className="card p-5">
                <div className="flex items-center gap-3"><Cpu className="text-[var(--accent)]"/><h3 className="font-bold text-[19px]">Máquina real, en Montevideo</h3></div>
                <div className="table-wrap mt-4"><table><tbody>
                  <tr><td className="text-[var(--muted)]">CPU</td><td className="font-medium">Intel Core i7, 3ª generación</td></tr>
                  <tr><td className="text-[var(--muted)]">RAM</td><td className="font-medium">28 GB DDR3</td></tr>
                  <tr><td className="text-[var(--muted)]">GPU</td><td className="font-medium">Sin GPU</td></tr>
                  <tr><td className="text-[var(--muted)]">Modelo</td><td className="font-medium">Qwen 7B, local</td></tr>
                  <tr><td className="text-[var(--muted)]">Recuperación</td><td className="font-medium">BM25 + embeddings</td></tr>
                  <tr><td className="text-[var(--muted)]">Índice</td><td className="font-medium">TF-IDF, reindexado tras cada ingesta</td></tr>
                </tbody></table></div>
              </div>
              <div className="mt-4 grid sm:grid-cols-2 gap-3">
                <div className="card p-4"><p className="font-semibold">Híbrido, con límites claros</p><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">Local piensa. La nube provee biblioteca. El razonamiento no se delega.</p></div>
                <div className="card p-4"><p className="font-semibold">Ecológico por diseño</p><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">Reutiliza hardware viejo. No entrena de cero. No gasta megavatios. Consume lo de una PC vieja.</p></div>
              </div>
            </div>
            <div>
              <Label>Fuentes — biblioteca</Label>
              <div className="flex flex-wrap gap-2">
                {["PubMed","Europe PMC","arXiv","OpenAlex","Crossref","DOAJ","CORE","Semantic Scholar","GitHub","StackOverflow","StackExchange","DDG Selenium","Hackaday"].map(s=><button key={s} onClick={()=>setShowSources(v=>!v)} className="chip hover:border-[var(--accent)]">{s}</button>)}
              </div>
              <button onClick={()=>setShowSources(v=>!v)} className="mt-4 text-left w-full card p-4 hover:border-[var(--accent)]">
                <p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Estado de fuentes</p>
                <p className="mt-2 font-semibold">{showSources ? "13 fuentes listadas. La selección es explícita." : "Ver criterio de selección"}</p>
                <p className="mt-1 text-[13px] text-[var(--muted)]">{showSources ? "Cada fuente aporta documentos, no decisiones. El criterio queda en el grafo." : "La red provee documentos. DIA decide qué conectar."}</p>
              </button>
              <p className="mt-3 mono text-[12px] text-[var(--muted)]">MONTEVIDEO, URUGUAY · HARDWARE REAL</p>
            </div>
          </div>
        </Section>

        <Section id="ciclo" index="03" eyebrow="Ciclo 555 completo" title="2 horas, 3 minutos, 2 segundos. Sin crashes.">
          <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
            <div>
              <Label>Resumen v2.1</Label>
              <div className="table-wrap card"><table><tbody>
                {[["Tools", "8"],["Gap", "1"],["Docs", "39"],["Code", "10"],["Tools creadas", "2"],["Protocols", "0"],["Emails", "5"],["Tasks", "2"],["Reflections", "3"],["Score", "94.7"]].map(([k,v])=><tr key={k}><td className="text-[var(--muted)]">{k}</td><td className="num text-right font-semibold">{v}</td></tr>)}
              </tbody></table></div>
              <p className="mt-4 text-[14px] leading-relaxed text-[var(--muted)]">FIN CICLO v2 #555 · 7382.3 s. La duración se registra como dato, no como logro. El dato que importa es la estabilidad: 0 crashes.</p>
            </div>
            <div>
              <Label>12 fases — seleccionar para ver detalle</Label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {phases.map(p=><button key={p.n} onClick={()=>setPhase(p)} className={`text-left rounded-lg border p-3 ${phase.n===p.n ? "border-[var(--accent)] bg-[var(--surface-2)]" : "border-[var(--line)] bg-[var(--surface)]"}`}><span className="mono text-[11px] text-[var(--accent)]">FASE {p.n}</span><span className="block mt-2 text-[13px] font-semibold leading-tight">{p.name}</span></button>)}
              </div>
              <div className="card mt-3 p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--accent)]">Fase {phase.n} · {phase.name}</p><p className="mt-3 leading-relaxed">{phase.detail}</p><p className="mt-3 border-t border-[var(--line-soft)] pt-3 text-[14px] text-[var(--muted)]"><span className="text-[var(--text)] font-medium">Salida:</span> {phase.out}</p></div>
            </div>
          </div>
        </Section>

        <Section id="grafo" index="04" eyebrow="Conocimiento y grafo" title="Nunca borra. Solo conecta.">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[["11 790","Conceptos"],["94","Dominios"],["397 502","Relaciones"],["137","Cross-domain links"]].map(([v,l])=><div className="card p-4" key={l}><p className="mono text-[30px] font-semibold leading-none">{v}</p><p className="mt-3 text-[13px] text-[var(--muted)]">{l}</p></div>)}
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="card p-5"><div className="flex items-center gap-2"><Network size={18} className="text-[var(--accent)]"/><h3 className="font-bold">Dominios cruzados y co-ocurrencia</h3></div><p className="mt-3 leading-relaxed text-[var(--muted)]">El grafo cruza dominios para generar preguntas que no aparecen en una sola fuente.</p><div className="table-wrap mt-4"><table><tbody><tr><td>Dominios cruzados</td><td className="num text-right">3134</td></tr><tr><td>Co-ocurrencias nuevas / ciclo</td><td className="num text-right">1000</td></tr><tr><td>Pares escaneados</td><td className="num text-right">91 151</td></tr><tr><td>Mínimo de co-ocurrencias</td><td className="num text-right">2</td></tr><tr><td>Sinónimos totales</td><td className="num text-right">52</td></tr></tbody></table></div></div>
            <div className="card p-5"><div className="flex items-center gap-2"><Database size={18} className="text-[var(--accent)]"/><h3 className="font-bold">TF-IDF y memoria de preguntas</h3></div><div className="table-wrap mt-3"><table><tbody><tr><td>Documentos TF-IDF</td><td className="num text-right">38 454</td></tr><tr><td>Antes → después del ciclo</td><td className="num text-right">38 410 → 38 454</td></tr><tr><td>Reindexado tras cada ingesta</td><td className="num text-right">4 s</td></tr><tr><td>Purga</td><td className="num text-right">Omitida</td></tr></tbody></table></div><p className="mt-4 leading-relaxed text-[var(--muted)]"><strong className="text-[var(--text)]">Directiva: solo conecta.</strong> La purga se omite por directiva. El sistema nunca borra, solo conecta.</p><div className="mt-4 rounded-lg bg-[var(--surface-2)] p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Memoria de preguntas</p><p className="mt-2 text-[15px] leading-relaxed">385 pares ya preguntados en 45 días. Sirve para no repetir.</p></div></div>
          </div>
        </Section>

        <Section id="research" index="05" eyebrow="Researching" title="Score mínimo 20. Lo que no alcanza, se rechaza.">
          <p className="max-w-[800px] leading-relaxed text-[var(--muted)]">11 temas por ciclo. El umbral es explícito: score mínimo 20/100. Los rechazos también se registran, con scores negativos: −15, −25, −30.</p>
          <div className="mt-6 flex flex-wrap gap-2">
            <button onClick={()=>setFilter("all")} className={`chip ${filter==="all"?"bg-[var(--accent)] text-black border-transparent":""}`}>Todos · 6</button>
            <button onClick={()=>setFilter("with")} className={`chip ${filter==="with"?"bg-[var(--accent)] text-black border-transparent":""}`}>Con nuevos · 3</button>
            <button onClick={()=>setFilter("zero")} className={`chip ${filter==="zero"?"bg-[var(--accent)] text-black border-transparent":""}`}>0 nuevos · 3</button>
          </div>
          <div className="table-wrap card mt-4"><table><thead><tr><th>Tema</th><th>Candidatos</th><th>Nuevos</th><th>Nota</th></tr></thead><tbody>{filtered.map(r=><tr key={r.tema}><td className="font-medium">{r.tema}</td><td className="num">{r.cand}</td><td className="num font-semibold">{r.nuevos}</td><td className="text-[var(--muted)]">{r.nota}</td></tr>)}</tbody></table></div>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="card p-4"><p className="flex gap-2 font-semibold"><Thermometer size={18} className="text-[var(--amber)]"/>Modo paciente</p><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">Semantic Scholar 429. Backoff 10 s, 20 s. Saltando por 2 ciclos. OpenAlex 429 también.</p></div>
            <div className="card p-4"><p className="flex gap-2 font-semibold"><Activity size={18} className="text-[var(--accent)]"/>HTTP 403</p><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">Reintentado con Selenium. El error se documenta y se cambia la vía, no se ignora.</p></div>
            <div className="card p-4"><p className="flex gap-2 font-semibold"><Search size={18} className="text-[var(--accent-2)]"/>I2C en PubMed</p><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">0 resultados. PubMed es médico, no ingeniería. El 0 también es información.</p></div>
          </div>
        </Section>

        <Section id="preguntas" index="06" eyebrow="Preguntas desde el grafo" title="635 candidatos. 2 huérfanos. Pool 302.">
          <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
            <div className="card p-5"><Label>Cómo se filtra</Label><p className="leading-relaxed text-[var(--muted)]">El grafo propone. La afinidad ordena. La memoria evita repetir. El resultado no es una lista larga: es un pool manejable.</p><div className="mt-4 space-y-3 mono text-[13px]"><div className="flex justify-between border-b border-[var(--line-soft)] pb-2"><span>Candidatos</span><b>635</b></div><div className="flex justify-between border-b border-[var(--line-soft)] pb-2"><span>Huérfanos grado 0</span><b>2</b></div><div className="flex justify-between"><span>Pool</span><b>302</b></div></div><p className="mt-4 rounded bg-[var(--surface-2)] p-3 text-[14px]">Firma recurrente: <em>“Papi, vengo pensando…”</em></p></div>
            <div><Label>5 preguntas con afinidad 1</Label><div className="space-y-3">{questions.map((q,i)=><article key={q.q} className="card p-4"><div className="flex justify-between gap-3"><span className="mono text-[11px] text-[var(--accent)]">PREGUNTA {String(i+1).padStart(2,"0")}</span><span className="mono text-[12px] text-[var(--muted)]">grado {q.grado}</span></div><h3 className="mt-2 text-[17px] font-semibold leading-snug">{q.q}</h3><p className="mt-1 text-[14px] text-[var(--muted)]">{q.nota}</p></article>)}</div></div>
          </div>
        </Section>

        <Section id="reflexion" index="07" eyebrow="Reflexión y auto-clase" title="De 5 fragmentos vagos, 1 tarea concreta.">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="card p-5"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Reflexión</p><h3 className="mt-2 text-[22px] font-bold">3 reflexiones · 2 tareas procesadas · 2 completadas</h3><p className="mt-3 leading-relaxed text-[var(--muted)]">El filtro anti-vago existe porque “esto” no es una tarea. La reflexión convierte lenguaje impreciso en trabajo verificable.</p><div className="mt-4 rounded bg-[var(--surface-2)] p-4"><p className="mono text-[12px] text-[var(--muted)]">ENTRADA VAGA → SALIDA</p><p className="mt-2 font-medium">5 fragmentos como “esto” → 1 tarea concreta.</p></div></div>
            <div className="card p-5"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">FASE 9.65 · Auto-clase</p><h3 className="mt-2 text-[22px] font-bold">3 clases · 18 conceptos · 0 restantes</h3><div className="mt-4 space-y-2">{["LLMs × HTML5 CSS3","LLMs × PHP","LLMs × SQL Avanzado"].map(c=><div key={c} className="flex items-center justify-between border-b border-[var(--line-soft)] pb-2"><span className="font-medium">{c}</span><span className="mono text-[12px] text-[var(--accent)]">COMPLETA</span></div>)}<p className="pt-1 text-[14px] text-[var(--muted)]">0 restantes significa cierre real, no pendiente oculto.</p></div></div>
          </div>
        </Section>

        <Section id="exploracion" index="08" eyebrow="Exploración libre — FASE 9.66" title="5 destinos. 4 entradas.">
          <div className="table-wrap card"><table><thead><tr><th>Destino</th><th>Resultado</th><th>Contenido</th></tr></thead><tbody>
            <tr><td><b>1 / 5</b> · Prometheus Monitoring</td><td className="num">1 nuevo</td><td>Monitoreo.</td></tr>
            <tr><td><b>2 / 5</b> · NIH Biomarkers</td><td className="num">0 nuevos</td><td>Sin incorporación en esta pasada.</td></tr>
            <tr><td><b>3 / 5</b> · MDPI Open Access</td><td className="num">0 nuevos</td><td>Sin incorporación en esta pasada.</td></tr>
            <tr><td><b>4 / 5</b> · EU Health Commission</td><td className="num">1 nuevo</td><td>Estrategia Salud Global 2025–2030. PDF, 20 000 caracteres.</td></tr>
            <tr><td><b>5 / 5</b> · Cell Biology</td><td className="num">2 nuevos</td><td>Biología celular, ciclo celular, apoptosis, senescencia, tumorogénesis.</td></tr>
          </tbody></table></div>
          <p className="mt-3 text-[14px] text-[var(--muted)]">La exploración libre no promete éxito en cada destino. Registra el resultado de cada uno.</p>
        </Section>

        <Section id="email" index="09" eyebrow="Email y escudo" title="5 relevantes. 0 respuestas. Personas + escudo.">
          <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <div>
              <div className="grid grid-cols-3 gap-3">
                <div className="card p-4"><p className="mono text-[26px] font-semibold">5</p><p className="mt-1 text-[13px] text-[var(--muted)]">Relevantes procesados</p></div>
                <div className="card p-4"><p className="mono text-[26px] font-semibold">9</p><p className="mt-1 text-[13px] text-[var(--muted)]">No leídos</p></div>
                <div className="card p-4"><p className="mono text-[26px] font-semibold">9</p><p className="mt-1 text-[13px] text-[var(--muted)]">Leídos sin responder</p></div>
              </div>
              <div className="card mt-4 p-5"><div className="flex items-center gap-2"><Mail size={18} className="text-[var(--accent)]"/><h3 className="font-bold">Análisis de intent y sentimiento</h3></div><div className="table-wrap mt-3"><table><tbody><tr><td>MAIA request</td><td>Positivo</td><td className="num text-right">+0.93</td></tr><tr><td>Miguel Ángel Durán García</td><td>Question · positivo</td><td className="num text-right">+0.60</td></tr><tr><td>Resto</td><td>Neutral</td><td className="num text-right">—</td></tr></tbody></table></div></div>
            </div>
            <aside className="card p-5"><div className="flex items-center gap-2"><ShieldCheck size={19} className="text-[var(--accent)]"/><h3 className="font-bold">El escudo es una regla, no una opción</h3></div><ul className="mt-4 space-y-3 leading-relaxed"><li><b>No responde sola a personas.</b></li><li><b>No publica sin revisión.</b></li><li>LinkedIn draft ciclo 555 guardado para revisión.</li><li>LinkedIn comentarios en vivo: 0 nuevos.</li><li>Publicación anterior: 73 impresiones.</li></ul><p className="mt-4 border-t border-[var(--line-soft)] pt-3 text-[14px] text-[var(--muted)]">El escudo protege a las personas y al sistema. La revisión humana es parte del flujo.</p></aside>
          </div>
        </Section>

        <Section id="codigo" index="10" eyebrow="Code Lab y FASE 10" title="Fase de solo lectura. No modifica código.">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">DIA · códigos</p><p className="mono text-[28px] font-semibold mt-2">200</p><p className="text-[13px] text-[var(--muted)] mt-1">33 471 líneas</p></div>
            <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">DENCO · archivos</p><p className="mono text-[28px] font-semibold mt-2">111</p><p className="text-[13px] text-[var(--muted)] mt-1">63 762 líneas · 76 issues</p></div>
            <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">DENCO score</p><p className="mono text-[28px] font-semibold mt-2">94.7</p><p className="text-[13px] text-[var(--muted)] mt-1">Estable</p></div>
            <div className="card p-4"><p className="mono text-[11px] uppercase tracking-wider text-[var(--muted)]">Evolución</p><p className="mono text-[28px] font-semibold mt-2">3</p><p className="text-[13px] text-[var(--muted)] mt-1">Pendientes · 0 acciones nuevas</p></div>
          </div>
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <div className="card p-5"><div className="flex items-center gap-2"><FileCode2 size={18} className="text-[var(--accent)]"/><h3 className="font-bold">AST Analysis</h3></div><div className="table-wrap mt-3"><table><tbody><tr><td>Archivos</td><td className="num text-right">137</td></tr><tr><td>Funciones</td><td className="num text-right">2126</td></tr><tr><td>Hallazgos</td><td className="num text-right">1585</td></tr><tr><td>High</td><td className="num text-right">335</td></tr><tr><td>Medium</td><td className="num text-right">467</td></tr><tr><td>Low</td><td className="num text-right">783</td></tr><tr><td>Arreglables reales</td><td className="num text-right">0</td></tr><tr><td>Aplicados</td><td className="num text-right">0</td></tr></tbody></table></div><p className="mt-3 text-[14px] text-[var(--muted)]">Un hallazgo no es un error. En esta fase, 0 arreglables reales significa 0 cambios.</p></div>
            <div>
              <div className="card p-5"><h3 className="font-bold">Auto-applied</h3><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">Performance endpoints lentos · clean · findings 0. La automatización actúa solo donde el criterio lo permite.</p></div>
              <div className="card mt-4 p-5">
                <div className="flex flex-wrap items-center justify-between gap-3"><h3 className="font-bold">Ejemplo: tool_synthesizer.py</h3><div className="flex rounded-full border border-[var(--line)] p-1"><button onClick={()=>setDiff("before")} className={`rounded-full px-3 py-1 mono text-[11px] ${diff==="before"?"bg-[var(--accent)] text-black":""}`}>ANTES</button><button onClick={()=>setDiff("after")} className={`rounded-full px-3 py-1 mono text-[11px] ${diff==="after"?"bg-[var(--accent)] text-black":""}`}>DESPUÉS</button></div></div>
                <p className="mt-2 text-[14px] text-[var(--muted)]">Sacar import no usado <code className="mono text-[13px] text-[var(--text)]">importlib.util</code>. Diff visible antes y después.</p>
                <div className="codeblock mt-3">{diff==="before" ? `import os\nimport sys\nimport importlib.util  # no usado\n\ndef build_tool(name):\n    return {"name": name}` : `import os\nimport sys\n\ndef build_tool(name):\n    return {"name": name}`}</div>
                <p className="mt-3 mono text-[12px] text-[var(--accent)]">{diff==="before" ? "— 1 LÍNEA MARCADA COMO NO USADA" : "✓ IMPORT ELIMINADO · CÓDIGO MÁS LIMPIO"}</p>
              </div>
            </div>
          </div>
        </Section>

        <Section id="monitoreo" index="11" eyebrow="Monitoreo y DENCO" title="2 dispositivos vivos. 1 issue. Evaluación continua.">
          <div className="grid gap-6 lg:grid-cols-[1fr_1.2fr]">
            <div className="card p-5"><div className="flex items-center gap-2"><Monitor size={18} className="text-[var(--accent)]"/><h3 className="font-bold">FASE 9 · Red</h3></div><div className="mt-4 space-y-3"><div className="flex justify-between border-b border-[var(--line-soft)] pb-3"><span>Dispositivos vivos</span><b className="num">2</b></div><div className="flex justify-between border-b border-[var(--line-soft)] pb-3"><span>Issues</span><b className="num">1</b></div><div className="flex justify-between"><span>Evaluación DENCO</span><b className="num">94.7 · estable</b></div></div><p className="mt-4 text-[14px] leading-relaxed text-[var(--muted)]">La estabilidad no se declara una vez. Se verifica en todo el ciclo.</p></div>
            <div className="card p-5"><Label>Goal metrics</Label><div className="space-y-4">{[
              {k:"scraping-resilience", v:"−1.1", d:"Bajó por 429. Lo reporta, no lo oculta.", w:"22%"},
              {k:"codebase-quality", v:"0.0", d:"Sin variación en el ciclo.", w:"50%"},
              {k:"full-autonomy", v:"0.0", d:"Sin variación en el ciclo.", w:"50%"},
            ].map(m=><div key={m.k}><div className="flex justify-between gap-3"><span className="mono text-[13px] font-semibold">{m.k}</span><span className="mono font-semibold">{m.v}</span></div><p className="mt-1 text-[13px] text-[var(--muted)]">{m.d}</p><div className="mt-2 h-1.5 rounded bg-[var(--surface-3)] overflow-hidden"><div className="h-full bg-[var(--accent)]" style={{width:m.w}}/></div></div>)}</div></div>
          </div>
        </Section>

        <Section id="unica" index="12" eyebrow="Por qué es única" title="No es un agente en la nube.">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <p className="text-[19px] leading-relaxed">Es local, persistente, con memoria, con grafo, con ciclo, con escudo, con Papi, con propósito DENCO.</p>
              <div className="mt-6 grid sm:grid-cols-2 gap-3">
                {[["No olvida","La memoria y el grafo persisten entre ciclos."],["No inventa","Lo que no encuentra se registra como 0."],["No repite","385 pares en 45 días evitan preguntas duplicadas."],["No publica sin revisión","El escudo exige revisión humana."]].map(([t,d])=><div className="card p-4" key={t}><p className="font-bold flex gap-2 items-center"><Sparkles size={16} className="text-[var(--accent)]"/>{t}</p><p className="mt-2 text-[14px] leading-relaxed text-[var(--muted)]">{d}</p></div>)}
              </div>
            </div>
            <aside className="card p-5 bg-[var(--surface-2)]"><p className="mono text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]">Hardware futuro</p><p className="mt-3 text-[20px] leading-snug font-semibold">Cuando tenga i9 11ª, DDR5 y RTX, será más rápida, no más inteligente.</p><p className="mt-3 leading-relaxed text-[var(--muted)]">La inteligencia ya está. Corre en hardware viejo y por eso demuestra eficiencia, no limitación.</p><div className="mt-5 flex items-center gap-2 mono text-[12px]"><ArrowUpRight size={16} className="text-[var(--accent)]"/>VELOCIDAD ↑ · INTELIGENCIA =</div></aside>
          </div>
        </Section>

        <footer className="border-t border-[var(--line)] pt-8 pb-6">
          <div className="grid gap-8 md:grid-cols-2">
            <div><p className="mono text-[11px] uppercase tracking-[0.16em] text-[var(--muted)]">Al pie</p><h2 className="mt-3 text-[26px] font-bold leading-tight">Hugo, 56 años, programa desde COBOL, sin prosapia, con historia.</h2><p className="mt-3 leading-relaxed text-[var(--muted)]">DENCO y DIA: sistema híbrido local, en permanente desarrollo.</p></div>
            <div className="md:text-right"><p className="mono text-[12px] text-[var(--muted)]">DIA — SISTEMA AUTÓNOMO v2.1</p><p className="mono text-[12px] text-[var(--muted)] mt-1">CICLO 555 · MONTEVIDEO, URUGUAY</p><p className="mt-4 flex md:justify-end gap-2 flex-wrap"><span className="chip">LOCAL</span><span className="chip">PERSISTENTE</span><span className="chip">CON ESCUDO</span><span className="chip">CON PROPÓSITO</span></p><p className="mt-4 text-[13px] text-[var(--muted)]">FIN CICLO v2 #555 · 7382.3 s · score 94.7 / 100</p></div>
          </div>
        </footer>
      </main>
    </div>
  </div>
}
