import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import unicodedata
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN INICIAL ---
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# ⚠️ TU URL DE GOOGLE SHEETS (DEBE ESTAR ENTRE COMILLAS)
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
    return svg_code

# --- MOTOR DE PERSISTENCIA (BLINDADO) ---
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
    # Intenta cargar de la nube primero
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="0", ttl=0)
        if not df_nube.empty:
            return json.loads(df_nube.iloc[0, 0])
    except: pass
    # Backup local si la nube falla
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- CARGA INICIAL (SOLO UNA VEZ) ---
if "db_cargada" not in st.session_state:
    db = cargar_datos()
    if db:
        for k, v in db.items():
            st.session_state[k] = v
    st.session_state["db_cargada"] = True

# --- INICIALIZACIÓN DE VARIABLES SI NO EXISTEN TRAS LA CARGA ---
claves_iniciales = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
                    "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
for c in claves_iniciales:
    if c not in st.session_state:
        if c == "usuarios_db": 
            # Este es el admin de emergencia si el Excel está vacío
            st.session_state[c] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "dni": "37108100", "matricula": "M.P 21947", "titulo": "Director"}}
        elif c == "detalles_pacientes_db": st.session_state[c] = {}
        else: st.session_state[c] = []

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;'>MediCare Enterprise PRO</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar al Sistema", use_container_width=True):
                # Verificamos si el usuario existe en lo que cargamos de la nube
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    st.session_state["logs_db"].append({"F": datetime.now().strftime("%d/%m/%Y"), "H": datetime.now().strftime("%H:%M"), "U": st.session_state["u_actual"]["nombre"]})
                    guardar_datos()
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verificá tu usuario y clave.")
    st.stop()

# --- CONTEXTO DEL USUARIO ACTUAL ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
pacientes_visibles = st.session_state["pacientes_db"] if user["rol"] == "SuperAdmin" else [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]

# --- SIDEBAR PROFESIONAL ---
with st.sidebar:
    render_logo_eg(110)
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}**")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.divider()
    buscar = st.text_input("🔍 Buscar Paciente:")
    p_filtrados = [p for p in pacientes_visibles if buscar.lower() in p.lower() or buscar in st.session_state["detalles_pacientes_db"].get(p,{}).get("dni", "")]
    paciente_sel = st.selectbox("Seleccionar:", p_filtrados) if p_filtrados else None
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state["logeado"] = False; st.rerun()

# --- INTERFAZ DE TABS ---
st.title("Panel de Control MediCare")
menu = ["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF", "⚙️ Mi Equipo"]
if user["rol"] == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. ADMISIÓN (CON OPCIÓN DE BORRAR)
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Registrar Paciente")
        with st.form("adm_form"):
            n = st.text_input("Nombre y Apellido"); o = st.text_input("Obra Social"); d = st.text_input("DNI")
            if st.form_submit_button("Habilitar en Empresa"):
                id_p = f"{n} ({o}) - {mi_empresa}"
                if id_p not in st.session_state["pacientes_db"]:
                    st.session_state["pacientes_db"].append(id_p)
                    st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "empresa": mi_empresa}
                    guardar_datos(); st.success("Registrado correctamente"); st.rerun()

    with c2:
        st.subheader("Eliminar Registro")
        if paciente_sel:
            st.warning(f"¿Borrar a {paciente_sel}?")
            if st.button("🔴 Eliminar Definitivamente"):
                st.session_state["pacientes_db"].remove(paciente_sel)
                if paciente_sel in st.session_state["detalles_pacientes_db"]: del st.session_state["detalles_pacientes_db"][paciente_sel]
                guardar_datos(); st.success("Paciente eliminado"); st.rerun()

# 2. SIGNOS VITALES (TRIAGE)
with tabs[1]:
    if paciente_sel:
        with st.form("vitales_f"):
            st.write(f"### Clínica: {paciente_sel}")
            col1, col2, col3 = st.columns(3)
            ta = col1.text_input("Tensión Arterial", "120/80"); fc = col2.number_input("FC", 30, 200, 75); fr = col3.number_input("FR", 10, 50, 16)
            sat = col1.number_input("SatO2%", 50, 100, 98); temp = col2.number_input("Temp", 34.0, 42.0, 36.5); hgt = col3.number_input("HGT", 20, 600, 100)
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "FR": fr, "Sat": sat, "Temp": temp, "HGT": hgt, "hora": datetime.now().strftime("%H:%M")})
                guardar_datos(); st.success("Guardado"); st.rerun()
    else: st.warning("Seleccioná un paciente en la barra lateral")

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota clínica:")
        if st.button("Firmar Nota"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "titulo": user.get("titulo", ""), "mat": user["matricula"]})
            guardar_datos(); st.success("Nota firmada"); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Por: {e['titulo']} {e['firma']}*")

# 4. RECETARIO PRO (VÍAS Y FRECUENCIAS)
with tabs[3]:
    if paciente_sel:
        st.subheader("💊 Indicaciones Médicas")
        with st.form("recetario"):
            c_a, c_b = st.columns([2, 1])
            drog = c_a.text_input("Droga / Medicamento"); dos = c_b.text_input("Dosis")
            c_c, c_d, c_e = st.columns(3)
            via = c_c.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular", "Subcutánea", "Inhalatoria"])
            frec = c_d.selectbox("Horario / Frecuencia", ["Cada 2 horas", "Cada 4 horas", "Cada 6 horas", "Cada 8 horas", "Cada 12 horas", "Cada 24 horas", "Dosis Única", "S.O.S"])
            dias = c_e.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Indicación"):
                ind = f"{drog} {dos} vía {via} - {frec} por {dias} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": ind, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"], "mat": user["matricula"]})
                guardar_datos(); st.success("Cargado"); st.rerun()
        for r in reversed([x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]):
            st.success(f"📌 {r['fecha']} | {r['med']}")

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        serv = st.text_input("Servicio / Práctica"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Cobro"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado"); st.rerun()

# 6. PDF (EL COMPLETO)
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf(p):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            def txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, txt(f"HISTORIA CLINICA - {p}"), ln=True, align='C')
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("1. EVOLUCIONES:"), ln=True)
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, txt(f"[{ev['fecha']}] {ev['nota']} \n(Firma: {ev['firma']})")); pdf.ln(2)
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("2. INDICACIONES:"), ln=True)
            for rec in [r for r in st.session_state["indicaciones_db"] if r["paciente"] == p]:
                pdf.multi_cell(0, 6, txt(f"[{rec['fecha']}] {rec['med']}")); pdf.ln(1)
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y()); pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, txt(f"Profesional: {user['nombre']}"), ln=True)
            pdf.cell(0, 5, txt(f"DNI: {user['dni']} | Mat: {user['matricula']}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')
        if st.button("Descargar Informe PDF Completo"):
            st.download_button("Bajar Archivo", crear_pdf(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO (CREAR USUARIOS)
with tabs[6]:
    st.subheader(f"Administrar Equipo de {mi_empresa}")
    with st.form("new_user_f"):
        u_id = st.text_input("Usuario (Login)"); u_pw = st.text_input("Clave"); u_nm = st.text_input("Nombre")
        u_dn = st.text_input("DNI"); u_mt = st.text_input("Matrícula")
        u_ti = st.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Kinesiólogo/a", "Administrativo/a"])
        u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
        if st.form_submit_button("Habilitar Profesional"):
            st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa}
            guardar_datos(); st.success("Habilitado correctamente!"); st.rerun()

# 8. AUDITORÍA (SOLO ENZO)
if user["rol"] == "SuperAdmin":
    with tabs[7]:
        st.subheader("🕵️ Auditoría Global")
        st.dataframe(pd.DataFrame(st.session_state["logs_db"]).sort_index(ascending=False), use_container_width=True)
