import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import pytz
import urllib.parse
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN DE LIBRERÍAS (PDF) ---
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MediCare Enterprise PRO V3", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- ZONA HORARIA ARGENTINA ---
ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')
def ahora():
    return datetime.now(ARG_TZ)

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 🎨 DISEÑO VISUAL ADAPTATIVO ---
page_bg_css = """
<style>
.stApp {
    background-color: var(--background-color);
    background-image: radial-gradient(circle at top, var(--secondary-background-color) 0%, transparent 80%);
}
div[data-testid="stForm"] {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(150, 150, 150, 0.2);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
    -webkit-appearance: none; 
    margin: 0; 
}
input[type=number] {
    -moz-appearance: textfield;
}
.wa-btn {
    display: block; width: 100%; text-align: center; background-color: #25D366; 
    color: white !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none;
    margin-top: 10px; margin-bottom: 10px;
}
.wa-btn:hover { background-color: #128C7E; }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# --- 🎁 LOGO EXCLUSIVO E.G. ---
def render_logo_eg(size=100):
    svg_code = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="55" fill="url(#grad1)" />
        <path d="M60 25 V95 M25 60 H95" stroke="white" stroke-width="8" stroke-linecap="round"/>
        <g fill="white" font-family="Arial" font-weight="bold" font-size="30">
            <text x="35" y="62" text-anchor="middle">E.</text>
            <text x="85" y="62" text-anchor="middle">G</text>
        </g>
    </svg>
    """
    st.sidebar.markdown(f'<div style="display: flex; justify-content: center; padding: 10px;">{svg_code}</div>', unsafe_allow_html=True)

# --- MOTOR DE PERSISTENCIA ---
def cargar_datos():
    try:
        response = supabase.table('medicare_db').select('datos').eq('id', 1).execute()
        if response.data: return response.data[0]['datos']
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
    return None

def guardar_datos():
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db", "balance_db", "pediatria_db"]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    try:
        supabase.table('medicare_db').upsert({"id": 1, "datos": data}).execute()
        st.toast("✅ Base de datos sincronizada y protegida", icon="☁️")
    except Exception as e:
        st.error(f"⚠️ Error al subir a la nube: {e}")

# --- INICIALIZACIÓN ---
if "db_inicializada" not in st.session_state:
    db = cargar_datos()
    claves_base = {
        "usuarios_db": {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "matricula": "M.P 21947", "titulo": "Director de Sistemas", "estado": "Activo"}},
        "pacientes_db": [], "detalles_pacientes_db": {}, "vitales_db": [], "indicaciones_db": [], "turnos_db": [], 
        "evoluciones_db": [], "facturacion_db": [], "logs_db": [], "balance_db": [], "pediatria_db": []
    }
    if db:
        for k, v in db.items(): st.session_state[k] = v
        for k, v in claves_base.items():
            if k not in st.session_state: st.session_state[k] = v
    else:
        for k, v in claves_base.items(): st.session_state[k] = v
    st.session_state["db_inicializada"] = True

# --- LOGIN (CON BLOQUEO POR SUSCRIPCIÓN) ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False
if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise PRO V3</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            
            if st.form_submit_button("Ingresar al Sistema", width="stretch"):
                db_f = cargar_datos()
                if db_f:
                    for k, v in db_f.items(): st.session_state[k] = v
                
                u_limpio = u.strip().lower()
                p_limpio = p.strip()
                
                usuario_encontrado = None
                for key_db in st.session_state["usuarios_db"].keys():
                    if key_db.strip().lower() == u_limpio:
                        usuario_encontrado = key_db
                        break
                
                if usuario_encontrado:
                    user_data = st.session_state["usuarios_db"][usuario_encontrado]
                    # VERIFICAR SI ESTÁ BLOQUEADO POR FALTA DE PAGO
                    if user_data.get("estado", "Activo") == "Bloqueado":
                        st.error("🚫 Acceso suspendido por fin de prueba o falta de pago. Comuníquese con el Administrador (SISTEMAS E.G.).")
                    elif str(user_data["pass"]).strip() == p_limpio:
                        st.session_state["u_actual"] = user_data
                        st.session_state["logeado"] = True
                        st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user_data["nombre"], "E": user_data["empresa"], "A": "Login"})
                        guardar_datos()
                        st.rerun()
                    else: 
                        st.error("Acceso denegado: Usuario o contraseña incorrectos.")
                else:
                    st.error("Acceso denegado: Usuario o contraseña incorrectos.")
    st.stop()

# --- CONTEXTO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
rol = user["rol"]

# --- SIDEBAR ---
with st.sidebar:
    render_logo_eg(110)
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}**")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.divider()
    
    buscar = st.text_input("🔍 Buscar Paciente:")
    pacientes_visibles = st.session_state["pacientes_db"] if rol == "SuperAdmin" else [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]
    p_f = [p for p in pacientes_visibles if buscar.lower() in p.lower()]
    paciente_sel = st.selectbox("Seleccionar:", p_f) if p_f else None
    
    if paciente_sel:
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        st.caption(f"**DNI:** {det.get('dni','S/D')}")
        if st.button("🔴 DAR DE ALTA / ELIMINAR PACIENTE", width="stretch"):
            st.session_state["pacientes_db"].remove(paciente_sel)
            if paciente_sel in st.session_state["detalles_pacientes_db"]: del st.session_state["detalles_pacientes_db"][paciente_sel]
            st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user["nombre"], "E": mi_empresa, "A": f"Baja Paciente: {paciente_sel}"})
            guardar_datos()
            st.rerun()

    st.divider()
    if st.button("Cerrar Sesión", width="stretch"):
        st.session_state["logeado"] = False; st.rerun()

# --- MENU DINÁMICO ---
menu = ["👤 Admisión", "📊 Clínica", "👶 Pediatría", "📝 Evolución", "💊 Recetas", "⚖️ Balance", "📍 Visitas", "📚 Historial", "💳 Caja", "🗄️ PDF"]
if rol in ["SuperAdmin", "Coordinador"]: menu.append("⚙️ Mi Equipo")
if rol == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. ADMISIÓN 
with tabs[0]:
    st.subheader("Registrar Paciente")
    with st.form("adm_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("Nombre y Apellido")
        d = col_a.text_input("DNI")
        tel = col_a.text_input("Teléfono (Ej: 3584302024)")
        
        o = col_b.text_input("Obra Social")
        f_nac = col_b.date_input("Nacimiento", value=date(1990, 1, 1))
        dir_pac = col_b.text_input("Dirección (Ej: San Martin 123, Rio Cuarto)")
        
        empresa_destino = st.text_input("🏢 Asignar a Clínica / Empresa", placeholder="Ej: Clínica San Lucas") if rol == "SuperAdmin" else mi_empresa
        if rol != "SuperAdmin": st.info(f"🏢 Institución asignada: **{empresa_destino}**")
            
        ant = st.text_area("Antecedentes Médicos")
        
        if st.form_submit_button("Habilitar Paciente", width="stretch"):
            if n and d and empresa_destino: 
                id_p = f"{n} ({o}) - {empresa_destino.strip()}"
                if id_p not in st.session_state["pacientes_db"]:
                    st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {
                    "dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "telefono": tel, "direccion": dir_pac,
                    "antecedentes": ant, "empresa": empresa_destino.strip()
                }
                guardar_datos(); st.success(f"Registrado exitosamente"); st.rerun()
            else: st.error("⚠️ El Nombre, DNI y Empresa son obligatorios.")

# 2. CLÍNICA
with tabs[1]:
    if paciente_sel:
        st.subheader(f"Constantes Vitales: {paciente_sel}")
        vitales_p = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_sel]
        if vitales_p:
            u = vitales_p[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Tensión Arterial", u["TA"]); m2.metric("SATO2", f"{u['Sat']}%"); m3.metric("F.C.", f"{u['FC']} lpm"); m4.metric("HGT", u["HGT"])
        
        with st.form("vitales_f"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("Tensión Arterial (TA)", "120/80"); fc = c1.number_input("F.C.", 30, 200, 75)
            sat = c2.number_input("SatO2%", 50, 100, 98); fr = c2.number_input("F.R.", 10, 50, 16)
            temp = c3.number_input("Temp °C", 34.0, 42.0, 36.5); hgt = c3.text_input("HGT / Glucemia", "100")
            if sat < 90: st.error("🚨 PRIORIDAD: EMERGENCIA")
            elif sat < 94: st.warning("⚠️ PRIORIDAD: URGENCIA")
            
            if st.form_submit_button("Guardar Signos", width="stretch"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "FR": fr, "Temp": temp, "HGT": hgt, "fecha": ahora().strftime("%d/%m/%Y %H:%M")})
                guardar_datos(); st.success("Signos guardados"); st.rerun()

# 3. PEDIATRÍA
with tabs[2]:
    if paciente_sel:
        st.markdown("<h3 style='color: #10b981;'>👶 Control de Crecimiento y Percentiles</h3>", unsafe_allow_html=True)
        with st.form("pediatria_form", border=True):
            c1, c2, c3 = st.columns(3)
            edad = c1.text_input("Edad (Ej: 6 meses, 2 años)")
            peso = c2.number_input("Peso (kg)", min_value=0.0, format="%.2f")
            talla = c3.number_input("Talla / Longitud (cm)", min_value=0.0, format="%.2f")
            c4, c5, c6 = st.columns(3)
            pc = c4.number_input("Perímetro Cefálico (cm)", min_value=0.0, format="%.2f")
            perc_peso = c5.text_input("Percentil Peso (Opcional, ej: P50)")
            perc_talla = c6.text_input("Percentil Talla (Opcional, ej: P75)")
            if st.form_submit_button("Registrar Medidas Pediátricas", width="stretch"):
                imc = round(peso / ((talla/100)**2), 2) if talla > 0 else 0.0
                st.session_state["pediatria_db"].append({
                    "paciente": paciente_sel, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "edad": edad, 
                    "peso": peso, "talla": talla, "pc": pc, "imc": imc, 
                    "perc_peso": perc_peso, "perc_talla": perc_talla, "firma": user["nombre"]
                })
                guardar_datos(); st.rerun()

        ped_data = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
        if ped_data:
            df_ped = pd.DataFrame(ped_data)
            st.markdown("### 📉 Curva de Crecimiento del Paciente")
            df_graf = df_ped[["fecha", "peso", "talla"]].copy()
            df_graf["fecha_corta"] = df_graf["fecha"].apply(lambda x: x.split(" ")[0])
            df_graf = df_graf.set_index("fecha_corta")
            g1, g2 = st.columns(2)
            with g1: st.caption("Evolución del Peso (kg)"); st.line_chart(df_graf["peso"], color="#3b82f6")
            with g2: st.caption("Evolución de la Talla (cm)"); st.line_chart(df_graf["talla"], color="#10b981")

# 4. EVOLUCIÓN
with tabs[3]:
    if paciente_sel:
        st.subheader("Cargar Procedimiento o Evolución")
        nota = st.text_area("Describa el procedimiento realizado:")
        if st.button("Firmar y Guardar Evolución", width="stretch"):
            if nota:
                st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "mat": user.get("matricula", "N/A")})
                guardar_datos(); st.success("Evolución guardada permanentemente."); st.rerun()

# 5. RECETARIO
with tabs[4]:
    if paciente_sel:
        st.subheader("💊 Plan Terapéutico")
        with st.form("recet"):
            c1, c2 = st.columns([2, 1])
            drog = c1.text_input("Medicamento"); dos = c2.text_input("Dosis")
            via = st.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular", "Subcutánea"])
            frec = st.selectbox("Frecuencia", ["Cada 8 hs", "Cada 12 hs", "Dosis Única", "S.O.S"])
            dias = st.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Receta", width="stretch"):
                t_r = f"{drog} {dos} vía {via} - {frec} por {dias} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": t_r, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.success("Receta guardada"); st.rerun()

# 6. BALANCE HÍDRICO PRO
with tabs[5]:
    if paciente_sel:
        st.markdown("<h3 style='color: #3b82f6;'>⚖️ Control de Balance Hídrico (Estricto)</h3>", unsafe_allow_html=True)
        with st.form("balance_form", border=True):
            col_in, col_eg = st.columns(2)
            with col_in:
                st.markdown("#### 📥 INGRESOS")
                i_oral = st.number_input("🥤 Vía Oral (Agua, alimentos)", min_value=0, value=0)
                i_par = st.number_input("💉 Vía Parenteral (Sueros, Meds)", min_value=0, value=0)
                i_son = st.number_input("🧪 Sondas (SNG, K108)", min_value=0, value=0)
            with col_eg:
                st.markdown("#### 📤 EGRESOS")
                e_ori = st.number_input("🚽 Orina (Diuresis / Foley)", min_value=0, value=0)
                e_dep = st.number_input("💩 Deposiciones / Ostomías", min_value=0, value=0)
                e_vom = st.number_input("🤮 Vómitos / Asp. Gástrica", min_value=0, value=0)
                e_dre = st.number_input("🩸 Drenajes / Sangrados", min_value=0, value=0)
                e_ins = st.number_input("💨 Pérdidas Insensibles", min_value=0, value=0)
                
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Calculadora y Registro de Balance", width="stretch"):
                t_ingresos = i_oral + i_par + i_son
                t_egresos = e_ori + e_dep + e_vom + e_dre + e_ins
                balance_total = t_ingresos - t_egresos
                st.session_state["balance_db"].append({
                    "paciente": paciente_sel, "fecha": ahora().strftime("%d/%m/%Y %H:%M"),
                    "ingresos": t_ingresos, "egresos": t_egresos, "balance": balance_total, "firma": user["nombre"]
                })
                guardar_datos(); st.rerun()

# 7. VISITAS Y GOOGLE MAPS
with tabs[6]:
    if paciente_sel:
        st.subheader("📍 Logística de Visita Domiciliaria")
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        direccion = det.get("direccion", "")
        telefono = det.get("telefono", "")
        
        if direccion:
            st.info(f"🏠 **Dirección del paciente:** {direccion}")
            dir_url = urllib.parse.quote(direccion)
            mapa_html = f'<iframe width="100%" height="400" frameborder="0" scrolling="no" marginheight="0" marginwidth="0" src="https://maps.google.com/maps?q={dir_url}&t=&z=15&ie=UTF8&iwloc=&output=embed"></iframe>'
            st.components.v1.html(mapa_html, height=400)
        else: st.warning("⚠️ Este paciente no tiene una dirección registrada.")
            
        st.divider()
        if telefono:
            st.markdown("### 💬 Notificar al Paciente")
            msg = urllib.parse.quote(f"Hola, soy {user['nombre']} de {mi_empresa}. Te aviso que estoy en camino al domicilio para la visita médica.")
            wa_url = f"https://wa.me/{telefono.replace('+', '').replace(' ', '')}?text={msg}"
            st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">📲 AVISAR POR WHATSAPP (Ir en camino)</a>', unsafe_allow_html=True)

# 8. HISTORIAL COMPLETO
with tabs[7]:
    if paciente_sel:
        st.subheader(f"📚 Historia Clínica Digital Integral")
        with st.expander("📝 Procedimientos y Evoluciones", expanded=True):
            evs = [x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]
            if evs:
                for e in reversed(evs): st.info(f"📅 **{e['fecha']}** | 👨‍⚕️ **Dr/a. {e['firma']}**\n\n{e['nota']}")
            else: st.write("No hay procedimientos registrados.")
                
        with st.expander("👶 Registros Pediátricos"):
            peds = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
            if peds: st.dataframe(pd.DataFrame(peds).drop(columns=["paciente"]), use_container_width=True)
            else: st.write("No hay registros pediátricos.")

        with st.expander("📊 Registros de Signos Vitales"):
            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == paciente_sel]
            if vits: st.dataframe(pd.DataFrame(vits).drop(columns=["paciente"]), use_container_width=True)
            else: st.write("No hay signos vitales registrados.")
                
        with st.expander("⚖️ Registros de Balance Hídrico"):
            bals = [x for x in st.session_state["balance_db"] if x["paciente"] == paciente_sel]
            if bals:
                df_bals = pd.DataFrame(bals).drop(columns=["paciente"])
                df_bals["ingresos"] = df_bals["ingresos"].astype(str) + " ml"
                df_bals["egresos"] = df_bals["egresos"].astype(str) + " ml"
                df_bals["balance"] = df_bals["balance"].astype(str) + " ml"
                st.dataframe(df_bals, use_container_width=True)
            else: st.write("No hay balances hídricos registrados.")

        with st.expander("💊 Plan Terapéutico (Recetas)"):
            recs = [x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]
            if recs:
                for r in reversed(recs): st.success(f"📌 **{r['fecha']}** | Indicado por: **{r['firma']}**\n\n{r['med']}")
            else: st.write("No hay indicaciones registradas.")

# 9. CAJA
with tabs[8]:
    if paciente_sel:
        st.subheader("💳 Registro de Cobros")
        serv = st.text_input("Servicio / Práctica"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Pago", width="stretch"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": ahora().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado"); st.rerun()

# 10. PDF
with tabs[9]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf_pro(p):
            pdf = FPDF(); pdf.add_page()
            def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_fill_color(59, 130, 246); pdf.ellipse(10, 10, 22, 22, 'F'); pdf.set_draw_color(255, 255, 255); pdf.set_line_width(1.2)
            pdf.line(21, 14, 21, 28); pdf.line(14, 21, 28, 21)
            emp_paciente = st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa", mi_empresa)
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(38, 14); pdf.cell(0, 10, t(emp_paciente), ln=True)
            pdf.set_font("Arial", 'I', 9); pdf.set_xy(38, 20); pdf.cell(0, 10, t("MediCare Enterprise PRO - Reporte Medico"), ln=True); pdf.ln(18)
            
            det = st.session_state["detalles_pacientes_db"].get(p, {}); pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, t(f" HISTORIA CLINICA: {p}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 10); pdf.cell(0, 8, t(f" DNI: {det.get('dni')} | Empresa: {emp_paciente}"), ln=True); pdf.ln(5)

            pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("SIGNOS VITALES:"), ln=True); pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
            pdf.cell(35, 7, "FECHA", 1, 0, 'C', True); pdf.cell(22, 7, "TA", 1, 0, 'C', True); pdf.cell(22, 7, "SAT%", 1, 0, 'C', True); pdf.cell(22, 7, "FC", 1, 0, 'C', True); pdf.cell(22, 7, "TEMP", 1, 0, 'C', True); pdf.cell(22, 7, "HGT", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 8)
            for v in [x for x in st.session_state["vitales_db"] if x["paciente"] == p]:
                pdf.cell(35, 7, t(v['fecha']), 1); pdf.cell(22, 7, t(v['TA']), 1); pdf.cell(22, 7, t(v['Sat']), 1); pdf.cell(22, 7, t(v['FC']), 1); pdf.cell(22, 7, t(v['Temp']), 1); pdf.cell(22, 7, t(v['HGT']), 1, 1)
            pdf.ln(10)

            bals = [x for x in st.session_state["balance_db"] if x["paciente"] == p]
            if bals:
                pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("BALANCE HIDRICO HISTORICO:"), ln=True)
                pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
                pdf.cell(45, 7, "FECHA / HORA", 1, 0, 'C', True); pdf.cell(45, 7, "INGRESOS TOTALES", 1, 0, 'C', True); pdf.cell(45, 7, "EGRESOS TOTALES", 1, 0, 'C', True); pdf.cell(45, 7, "BALANCE NETO", 1, 1, 'C', True)
                pdf.set_font("Arial", '', 8)
                for b in bals:
                    pdf.cell(45, 7, t(b['fecha']), 1, 0, 'C'); pdf.cell(45, 7, f"+ {b['ingresos']} ml", 1, 0, 'C'); pdf.cell(45, 7, f"- {b['egresos']} ml", 1, 0, 'C'); pdf.cell(45, 7, f"{b['balance']} ml", 1, 1, 'C')
                pdf.ln(10)

            pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("EVOLUCIONES CLINICAS:"), ln=True)
            for ev in [x for x in st.session_state["evoluciones_db"] if x["paciente"] == p]:
                pdf.set_font("Arial", 'B', 8); pdf.cell(0, 6, t(f"[{ev['fecha']}] - Firma: {ev['firma']}"), ln=True)
                pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 5, t(ev['nota']), 'L'); pdf.ln(2)
            
            pdf.ln(15); pdf.line(10, pdf.get_y(), 80, pdf.get_y()); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, t(f"Firma: {user['nombre']}"), ln=True); pdf.cell(0, 6, t(f"Matricula: {user.get('matricula', 'S/D')}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')

        st.download_button("📥 Generar Historia Clínica en PDF", crear_pdf_pro(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 11. EQUIPO Y AUDITORÍA (AQUÍ ESTÁ LA MAGIA DE LA SUSCRIPCIÓN)
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"Gestión de Personal y Suscripciones")
        with st.form("new_staff"):
            col_u1, col_u2 = st.columns(2)
            u_id = col_u1.text_input("Usuario (Login)"); u_pw = col_u2.text_input("Clave")
            u_nm = st.text_input("Nombre Completo")
            col_u3, col_u4 = st.columns(2)
            u_mt = col_u3.text_input("Matrícula"); u_ti = col_u4.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Administrativo/a"])
            
            if rol == "SuperAdmin": u_emp = st.text_input("🏢 Asignar a Clínica / Empresa")
            else: u_emp = mi_empresa; st.info(f"🏢 Agregando personal a tu empresa: **{u_emp}**")
            u_rl = st.selectbox("Poder / Rol", ["Operativo", "Coordinador", "SuperAdmin"] if rol == "SuperAdmin" else ["Operativo", "Coordinador"])
            
            if st.form_submit_button("Habilitar Acceso", width="stretch"):
                if u_id and u_pw and u_emp: 
                    # El usuario nuevo nace "Activo" por defecto
                    st.session_state["usuarios_db"][u_id.strip().lower()] = {
                        "pass": u_pw.strip(), "nombre": u_nm.strip(), "rol": u_rl, 
                        "titulo": u_ti, "empresa": u_emp.strip(), "matricula": u_mt.strip(), "estado": "Activo"
                    }
                    guardar_datos(); st.success(f"¡{u_nm} habilitado/a!"); st.rerun()

        st.divider(); st.subheader("👥 Personal y Control de Accesos")
        usuarios_visibles = st.session_state["usuarios_db"] if rol == "SuperAdmin" else {k: v for k, v in st.session_state["usuarios_db"].items() if v["empresa"] == mi_empresa}
        
        for u_key, u_data in list(usuarios_visibles.items()):
            if u_key == "admin": continue 
            
            # Chequeamos si está activo o bloqueado
            estado_actual = u_data.get("estado", "Activo")
            color_estado = "🟢 Activo" if estado_actual == "Activo" else "🔴 Suspendido"
            
            col_info, col_btn1, col_btn2 = st.columns([3, 1, 1])
            with col_info: 
                st.write(f"🏢 **{u_data['empresa']}** | 👤 **{u_data['nombre']}** | Login: `{u_key}` | Estado: {color_estado}")
            
            with col_btn1:
                # Botón de suspender / reactivar (Control de Pago)
                if rol == "SuperAdmin":
                    if estado_actual == "Activo":
                        if st.button("⏸️ Suspender", key=f"susp_{u_key}"):
                            st.session_state["usuarios_db"][u_key]["estado"] = "Bloqueado"
                            guardar_datos(); st.rerun()
                    else:
                        if st.button("▶️ Reactivar", key=f"reac_{u_key}"):
                            st.session_state["usuarios_db"][u_key]["estado"] = "Activo"
                            guardar_datos(); st.rerun()
            with col_btn2:
                if st.button("❌ Bajar", key=f"del_{u_key}"):
                    del st.session_state["usuarios_db"][u_key]
                    guardar_datos(); st.rerun()

if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría de Movimientos")
        if st.session_state["logs_db"]: st.dataframe(pd.DataFrame(st.session_state["logs_db"]))
