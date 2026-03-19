import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
import os
import unicodedata
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LIBRERÍAS (PDF) ---
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# ✅ URL DE TU EXCEL (ID: 1zZG491mwbUgWrG_Yta7uq1vVqR0jdNhnArPSgjsQNXs)
URL_HOJA_CALCULO = "https://docs.google.com/spreadsheets/d/1zZG491mwbUgWrG_Yta7uq1vVqR0jdNhnArPSgjsQNXs/edit?gid=0#gid=0"

st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- 🎁 LOGO EXCLUSIVO E.G. (SVG) ---
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
        <g fill="white" font-family="Arial" font-weight="bold" font-size="30">
            <text x="35" y="62" text-anchor="middle">E.</text>
            <text x="85" y="62" text-anchor="middle">G</text>
        </g>
    </svg>
    """
    st.sidebar.markdown(f'<div style="display: flex; justify-content: center; align-items: center; padding: 10px;">{svg_code}</div>', unsafe_allow_html=True)

# --- MOTOR DE PERSISTENCIA INTELIGENTE ---
DB_FILE = "medicare_saas_final_db.json"

def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="0", ttl=0)
        if not df_nube.empty:
            for i in range(min(len(df_nube), 5)):
                valor = str(df_nube.iloc[i, 0])
                if '{"usuarios_db"' in valor:
                    return json.loads(valor)
    except: pass
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return None

def guardar_datos():
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = pd.DataFrame([json.dumps(data, ensure_ascii=False)])
        conn.update(spreadsheet=URL_HOJA_CALCULO, data=df_nube)
    except:
        st.error("⚠️ Sincronizando con la nube...")

# --- INICIALIZAR ESTADO ---
if "db_inicializada" not in st.session_state:
    db = cargar_datos()
    if db:
        for k, v in db.items(): st.session_state[k] = v
    else:
        claves_iniciales = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
                            "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
        for c in claves_iniciales:
            if c not in st.session_state:
                if c == "usuarios_db": 
                    st.session_state[c] = {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "dni": "3584302024", "matricula": "M.P 21947", "titulo": "Director de Sistemas"}}
                elif c == "detalles_pacientes_db": st.session_state[c] = {}
                else: st.session_state[c] = []
    st.session_state["db_inicializada"] = True

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar al Sistema", use_container_width=True):
                db_f = cargar_datos()
                if db_f:
                    for k, v in db_f.items(): st.session_state[k] = v
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    st.session_state["logs_db"].append({"F": datetime.now().strftime("%d/%m/%Y"), "H": datetime.now().strftime("%H:%M"), "U": st.session_state["u_actual"]["nombre"], "E": st.session_state["u_actual"]["empresa"], "A": "Login"})
                    guardar_datos(); st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# --- CONTEXTO Y SEGURIDAD ---
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
    st.divider()
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state["logeado"] = False; st.rerun()

# --- INTERFAZ DINÁMICA ---
st.title("Panel Clínico Integrado")
menu = ["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF"]
if rol in ["SuperAdmin", "Coordinador"]: menu.append("⚙️ Mi Equipo")
if rol == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. ADMISIÓN
with tabs[0]:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Registrar Paciente")
        with st.form("adm_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            n = col_a.text_input("Nombre y Apellido")
            d = col_a.text_input("DNI")
            o = col_b.text_input("Obra Social")
            f_nac = col_b.date_input("Fecha de Nacimiento", value=date(1990, 1, 1))
            ant = st.text_area("Antecedentes Médicos (Alergias, etc.)")
            if st.form_submit_button("Habilitar Paciente"):
                if n and d:
                    id_p = f"{n} ({o}) - {mi_empresa}"
                    st.session_state["pacientes_db"].append(id_p)
                    st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "antecedentes": ant, "empresa": mi_empresa}
                    guardar_datos(); st.success("Paciente registrado"); st.rerun()

# 2. CLÍNICA (TRIAGE SEMÁFORO)
with tabs[1]:
    if paciente_sel:
        st.write(f"### Signos Vitales: {paciente_sel}")
        with st.form("vitales_f"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("TA", "120/80"); fc = c2.number_input("FC", 30, 200, 75); sat = c3.number_input("SatO2%", 50, 100, 98)
            fr = c1.number_input("FR", 10, 50, 16); temp = c2.number_input("Temp°C", 34.0, 42.0, 36.5); hgt = c3.number_input("HGT", 20, 600, 100)
            if sat < 90: st.error("🚨 PRIORIDAD: EMERGENCIA")
            elif sat < 94: st.warning("⚠️ PRIORIDAD: URGENCIA")
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "FR": fr, "Temp": temp, "HGT": hgt, "hora": datetime.now().strftime("%d/%m %H:%M")})
                guardar_datos(); st.success("Guardado"); st.rerun()

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota clínica (Se firmará automáticamente):")
        if st.button("Firmar Nota"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "mat": user["matricula"], "titulo": user.get("titulo", "")})
            guardar_datos(); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Por: {e.get('titulo','')} {e['firma']}*")

# 4. RECETARIO PRO
with tabs[3]:
    if paciente_sel:
        with st.form("recet_pro"):
            col1, col2 = st.columns([2, 1])
            drog = col1.text_input("Medicamento"); dos = col2.text_input("Dosis")
            via = st.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular", "Subcutánea"])
            frec = st.selectbox("Horario", ["Cada 8 hs", "Cada 12 hs", "Cada 24 hs", "Dosis Única"])
            dias = st.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Indicación"):
                t_r = f"{drog} {dos} vía {via} - {frec} por {dias} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": t_r, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"]})
                guardar_datos(); st.success("Guardado"); st.rerun()

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        serv = st.text_input("Práctica Médica"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Cobro"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Cobro registrado")

# 6. PDF
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf(p):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, t(f"HISTORIA CLÍNICA - {p}"), ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, t(f"[{ev['fecha']}] {ev['nota']} (Firma: {ev['firma']})"))
            return pdf.output(dest='S').encode('latin-1')
        if st.button("📥 Descargar Reporte Completo"):
            st.download_button("Bajar PDF", crear_pdf(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO (COORDINACIÓN)
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"Gestión de Personal - {mi_empresa}")
        with st.form("new_staff"):
            c1, c2 = st.columns(2)
            u_id = c1.text_input("Usuario (Login)"); u_pw = c2.text_input("Clave")
            u_nm = c1.text_input("Nombre"); u_dn = c2.text_input("DNI")
            u_mt = c1.text_input("Matrícula"); u_ti = c2.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Administrativo/a"])
            op_rol = ["Operativo", "Coordinador"] if rol == "Coordinador" else ["Operativo", "Coordinador", "SuperAdmin"]
            u_rl = st.selectbox("Rol / Poder", op_rol)
            if st.form_submit_button("Habilitar Profesional"):
                st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa}
                guardar_datos(); st.success(f"¡{u_nm} habilitado!"); st.rerun()

# 8. AUDITORÍA (SOLO VOS)
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría Global de Movimientos")
        if st.session_state["logs_db"]:
            st.dataframe(pd.DataFrame(st.session_state["logs_db"]), use_container_width=True)
       
