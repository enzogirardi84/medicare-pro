import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import unicodedata
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LIBRERÍAS (PDF) ---
# Definimos esto primero para evitar errores de variables no definidas
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# ⚠️ REEMPLAZA ESTO CON TU URL DE GOOGLE SHEETS
URL_HOJA_CALCULO = "TU_URL_AQUI" 

st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- 🎁 TU LOGO EXCLUSIVO E.G. (SVG) ---
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
        <g fill="white" font-family="Arial" font-weight="bold" font-size="28">
            <text x="38" y="62" text-anchor="middle">E.</text>
            <text x="82" y="62" text-anchor="middle">G</text>
        </g>
    </svg>
    """
    st.sidebar.markdown(f'<div style="text-align: center; margin-bottom: 10px;">{svg_code}</div>', unsafe_allow_html=True)

# --- MOTOR DE PERSISTENCIA (PROTECCIÓN DE DATOS) ---
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

# --- INICIALIZAR ESTADO ---
db = cargar_datos()
if db:
    for k, v in db.items(): st.session_state[k] = v

claves_iniciales = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
                    "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
for c in claves_iniciales:
    if c not in st.session_state:
        if c == "usuarios_db": 
            st.session_state[c] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "dni": "37108100", "matricula": "M.P 21947", "titulo": "Director"}}
        elif c == "detalles_pacientes_db": st.session_state[c] = {}
        else: st.session_state[c] = []

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<h2 style='text-align:center;'>MediCare Pro Access</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    st.session_state["logs_db"].append({"Fecha": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M"), "Usuario": st.session_state["u_actual"]["nombre"], "Empresa": st.session_state["u_actual"]["empresa"]})
                    guardar_datos(); st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# --- CONTEXTO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
pacientes_visibles = st.session_state["pacientes_db"] if user["rol"] == "SuperAdmin" else [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]

# --- SIDEBAR ---
with st.sidebar:
    render_logo_eg(110)
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}**")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.divider()
    buscar = st.text_input("🔍 Buscar Paciente:")
    p_f = [p for p in pacientes_visibles if buscar.lower() in p.lower() or buscar in st.session_state["detalles_pacientes_db"].get(p,{}).get("dni", "")]
    paciente_sel = st.selectbox("Seleccionar:", p_f) if p_f else None
    if st.button("Cerrar Sesión"):
        st.session_state["logeado"] = False; st.rerun()

# --- TABS ---
st.title("MediCare PRO Enterprise")
tabs = st.tabs(["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF", "⚙️ Equipo"])

# 1. ADMISIÓN
with tabs[0]:
    st.subheader(f"Registro en {mi_empresa}")
    with st.form("adm_form"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre"); o = c2.text_input("Obra Social"); d = c1.text_input("DNI")
        fnac = c2.date_input("Nacimiento", value=datetime.today(), min_value=datetime(datetime.today().year-110,1,1), max_value=datetime.today())
        if st.form_submit_button("Registrar Paciente"):
            id_p = f"{n} ({o}) - {mi_empresa}"
            st.session_state["pacientes_db"].append(id_p)
            st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": fnac.strftime("%d/%m/%Y"), "empresa": mi_empresa}
            guardar_datos(); st.success("Registrado"); st.rerun()

# 2. CLÍNICA
with tabs[1]:
    if paciente_sel:
        with st.form("v_clin"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("TA", "120/80"); fc = c2.number_input("FC", 30, 200, 75); sat = c3.number_input("SatO2%", 50, 100, 98)
            fr = c1.number_input("FR", 10, 50, 16); temp = c2.number_input("Temp", 34.0, 42.0, 36.5); hgt = c3.number_input("HGT", 20, 600, 100)
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "FR": fr, "Temp": temp, "HGT": hgt, "hora": datetime.now().strftime("%H:%M")})
                guardar_datos(); st.success("Guardado")

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota clínica:")
        if st.button("Firmar Nota"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "mat": user["matricula"], "titulo": user.get("titulo", "")})
            guardar_datos(); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Por: {e.get('titulo','')} {e['firma']} (Mat: {e['mat']})*")

# 4. RECETARIO PRO (ESTE ES EL QUE MEJORAMOS)
with tabs[3]:
    if paciente_sel:
        st.subheader("💊 Indicaciones Médicas")
        with st.form("receta_pro"):
            col1, col2 = st.columns([2, 1])
            droga = col1.text_input("Medicamento / Droga")
            dosis = col2.text_input("Dosis (ej: 500mg)")
            c3, c4, c5 = st.columns(3)
            via = c3.selectbox("Vía de Administración", ["V.O (Oral)", "E.V (Endovenosa)", "I.M (Intramuscular)", "S.C (Subcutánea)", "Inhalatoria", "Tópica"])
            frec = c4.selectbox("Frecuencia / Horario", ["Cada 2 horas", "Cada 4 horas", "Cada 6 horas", "Cada 8 horas", "Cada 12 horas", "Cada 24 horas", "Dosis Única", "S.O.S (Si necesidad)"])
            dur = c5.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Indicación"):
                t_r = f"{droga} {dosis} vía {via} - {frec} por {dur} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": t_r, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"], "titulo": user.get("titulo", ""), "mat": user["matricula"]})
                guardar_datos(); st.success("Indicación guardada")
        for r in reversed([x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]):
            st.success(f"💊 {r['fecha']} - {r['med']}")

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        serv = st.text_input("Servicio"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Cobro"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado")

# 6. PDF (REPORTES COMPLETOS)
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf_final(p):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, t(f"HISTORIA CLINICA - {p}"), ln=True, align='C')
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, t("1. EVOLUCIONES:"), ln=True)
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, t(f"[{ev['fecha']}] {ev['nota']} \n(Firma: {ev.get('titulo','')} {ev['firma']} - Mat: {ev['mat']})"))
                pdf.ln(2)
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, t("2. INDICACIONES MEDICAS:"), ln=True)
            for rec in [r for r in st.session_state["indicaciones_db"] if r["paciente"] == p]:
                pdf.multi_cell(0, 6, t(f"[{rec['fecha']}] {rec['med']}"))
                pdf.ln(1)
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y()); pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, t(f"Profesional: {user.get('titulo','')} {user['nombre']}"), ln=True)
            pdf.cell(0, 5, t(f"DNI: {user['dni']} | Mat: {user['matricula']}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')
        if st.button("📥 Descargar Reporte Completo PDF"):
            st.download_button("Bajar PDF", crear_pdf_final(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO
with tabs[6]:
    st.subheader(f"Equipo de {mi_empresa}")
    with st.form("equipo_form"):
        c1, c2 = st.columns(2)
        u_id = c1.text_input("Usuario (Login)"); u_pw = c2.text_input("Clave"); u_nm = c1.text_input("Nombre")
        u_dn = c2.text_input("DNI"); u_mt = c1.text_input("Matrícula")
        u_ti = c2.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Kinesiólogo/a", "Administrativo/a"])
        u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
        if st.form_submit_button("Habilitar Profesional"):
            st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa}
            guardar_datos(); st.success("Habilitado"); st.rerun()

# 8. AUDITORÍA (SÓLO ENZO)
if user["rol"] == "SuperAdmin":
    with tabs[6]: # Se añade al final
        st.subheader("🕵️ Auditoría Global")
        st.dataframe(pd.DataFrame(st.session_state["logs_db"]).sort_index(ascending=False), use_container_width=True)
