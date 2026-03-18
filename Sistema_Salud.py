import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import unicodedata
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from PIL import Image
import io
import base64

# --- 1. CONFIGURACIÓN MAESTRA ---
# ⚠️ REEMPLAZA ESTO CON TU URL DE GOOGLE SHEETS
URL_HOJA_CALCULO = "TU_URL_AQUI" 

st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- TU LOGO EXCLUSIVO E.G. (SVG) ---
def render_logo_eg(size=100):
    svg_code = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#10b981;stop-opacity:1" />
            </linearGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="blur"/>
                <feOffset in="blur" dx="2" dy="2" result="offsetBlur"/>
                <feMerge><feMergeNode in="offsetBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
            </filter>
        </defs>
        <circle cx="60" cy="60" r="55" fill="url(#grad1)" filter="url(#shadow)" />
        <path d="M60 25 V95 M25 60 H95" stroke="white" stroke-width="8" stroke-linecap="round"/>
        <g fill="white" font-family="Arial" font-weight="bold" font-size="28">
            <text x="38" y="62" text-anchor="middle">E.</text>
            <text x="82" y="62" text-anchor="middle">G</text>
        </g>
        <path d="M15 60 H35 L45 40 L55 80 L65 55 L75 60 H105" stroke="rgba(255,255,255,0.4)" stroke-width="2" fill="none"/>
    </svg>
    """
    st.sidebar.markdown(f'<div style="text-align: center;">{svg_code}</div>', unsafe_allow_html=True)
    return svg_code

# --- MOTOR DE DATOS Y NUBE ---
DB_FILE = "medicare_enterprise_db.json"

def guardar_datos():
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = pd.DataFrame([json.dumps(data, ensure_ascii=False)])
        conn.update(spreadsheet=URL_HOJA_CALCULO, data=df_nube)
    except: pass
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="0", ttl=0)
        if not df_nube.empty: return json.loads(df_nube.iloc[0, 0])
    except: pass
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return None

# --- INICIALIZACIÓN ---
db = cargar_datos()
if db:
    for k, v in db.items(): st.session_state[k] = v

claves_iniciales = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
                    "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
for c in claves_iniciales:
    if c not in st.session_state:
        if c == "usuarios_db": 
            st.session_state[c] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "dni": "37108100", "matricula": "M.P 21947", "titulo": "Director de Sistemas"}}
        elif c == "detalles_pacientes_db": st.session_state[c] = {}
        else: st.session_state[c] = []

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>⚕️ MediCare Enterprise</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("Entrar al Sistema", use_container_width=True):
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    st.session_state["logs_db"].append({"F": datetime.now().strftime("%d/%m/%Y"), "H": datetime.now().strftime("%H:%M"), "U": st.session_state["u_actual"]["nombre"], "E": st.session_state["u_actual"]["empresa"]})
                    guardar_datos(); st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# --- CONTEXTO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
pacientes_visibles = st.session_state["pacientes_db"] if user["rol"] == "SuperAdmin" else [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]

# --- SIDEBAR ---
with st.sidebar:
    render_logo_eg(100)
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}**")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.divider()
    buscar = st.text_input("🔍 Buscar Paciente:")
    p_filtrados = [p for p in pacientes_visibles if buscar.lower() in p.lower() or buscar in st.session_state["detalles_pacientes_db"].get(p,{}).get("dni", "")]
    paciente_sel = st.selectbox("Seleccionar:", p_filtrados) if p_filtrados else None
    if st.button("Cerrar Sesión"):
        st.session_state["logeado"] = False; st.rerun()

# --- TABS ---
st.title("Panel de Control MediCare")
menu = ["👤 Admisión", "📊 Signos Vitales", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF", "⚙️ Equipo"]
if user["rol"] == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. ADMISIÓN
with tabs[0]:
    st.subheader("Admisión de Pacientes")
    with st.form("adm"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre"); o = c2.text_input("Obra Social")
        dni_p = c1.text_input("DNI"); fnac = c2.date_input("Nacimiento", value=datetime.today(), min_value=datetime(datetime.today().year-110,1,1), max_value=datetime.today())
        if st.form_submit_button("Habilitar en Empresa"):
            id_p = f"{n} ({o}) - {mi_empresa}"
            st.session_state["pacientes_db"].append(id_p)
            st.session_state["detalles_pacientes_db"][id_p] = {"dni": dni_p, "fnac": fnac.strftime("%d/%m/%Y"), "empresa": mi_empresa}
            guardar_datos(); st.success("Registrado"); st.rerun()

# 2. SIGNOS VITALES
with tabs[1]:
    if paciente_sel:
        with st.form("vitales"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("TA", "120/80"); fc = c2.number_input("FC", 30, 200, 75); fr = c3.number_input("FR", 10, 50, 16)
            sat = c1.number_input("SatO2%", 50, 100, 98); temp = c2.number_input("Temp", 34.0, 42.0, 36.5); hgt = c3.number_input("HGT", 20, 600, 100)
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "FR": fr, "Sat": sat, "Temp": temp, "HGT": hgt, "hora": datetime.now().strftime("%d/%m %H:%M")})
                guardar_datos(); st.rerun()
    else: st.warning("Seleccione un paciente")

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota clínica:")
        if st.button("Firmar Nota"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "titulo": user.get("titulo", ""), "mat": user["matricula"]})
            guardar_datos(); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Por: {e['titulo']} {e['firma']}*")

# 4. RECETARIO PRO
with tabs[3]:
    if paciente_sel:
        st.subheader("💊 Indicaciones Médicas")
        with st.form("receta"):
            drog = st.selectbox("Medicamento", ["Adrenalina", "Amiodarona", "Amoxicilina", "Ceftriaxona", "Clonazepam", "Dexametasona", "Diazepam", "Diclofenac", "Dipirona", "Enalapril", "Furosemida", "Ibuprofeno", "Lorazepam", "Losartan", "Morfina", "Omeprazol", "Paracetamol", "Salbutamol", "Tramadol"])
            conc = st.text_input("Concentración"); frec = st.selectbox("Frecuencia", ["Cada 8hs", "Cada 12hs", "Cada 24hs", "SOS"])
            via = st.selectbox("Vía", ["Oral", "EV", "IM", "SC"]); dur = st.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Emitir"):
                t_r = f"{drog} {conc}. {frec} via {via} por {dur} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": t_r, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"], "titulo": user.get("titulo", ""), "mat": user["matricula"]})
                guardar_datos(); st.success("Indicación guardada")
        for r in reversed([x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]):
            st.success(f"💊 {r['fecha']} - {r['med']}")

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        serv = st.text_input("Servicio / Práctica"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Cobro"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado")

# 6. PDF (EL MÁS COMPLETO)
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf(p):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            def txt(text): return str(text).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, txt(f"HISTORIA CLINICA - {p}"), ln=True, align='C')
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("1. EVOLUCIONES:"), ln=True)
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, txt(f"[{ev['fecha']}] {ev['nota']} (Firma: {ev.get('titulo','')} {ev['firma']})"))
                pdf.ln(2)
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("2. INDICACIONES MEDICAS:"), ln=True)
            pdf.set_font("Arial", '', 10)
            for rec in [r for r in st.session_state["indicaciones_db"] if r["paciente"] == p]:
                pdf.multi_cell(0, 6, txt(f"[{rec['fecha']}] {rec['med']}"))
                pdf.ln(2)
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y()); pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, txt(f"Profesional: {user.get('titulo','')} {user['nombre']}"), ln=True)
            pdf.cell(0, 5, txt(f"DNI: {user['dni']} | Mat: {user['matricula']}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')
        if st.button("📥 Descargar Reporte Completo PDF"):
            st.download_button("Bajar PDF", crear_pdf(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO
with tabs[6]:
    st.subheader(f"Equipo de {mi_empresa}")
    with st.form("equipo"):
        c1, c2 = st.columns(2)
        u_id = c1.text_input("Usuario"); u_pw = c2.text_input("Clave")
        u_nm = c1.text_input("Nombre"); u_dn = c2.text_input("DNI")
        u_mt = c1.text_input("Matrícula"); u_ti = c2.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Kinesiólogo/a", "Administrativo/a"])
        u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
        if st.form_submit_button("Habilitar Profesional"):
            st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa}
            guardar_datos(); st.success("Habilitado"); st.rerun()

# 8. AUDITORÍA (SOLO ENZO)
if user["rol"] == "SuperAdmin":
    with tabs[7]:
        st.subheader("🕵️ Auditoría Global")
        st.dataframe(pd.DataFrame(st.session_state["logs_db"]).sort_index(ascending=False), use_container_width=True)
