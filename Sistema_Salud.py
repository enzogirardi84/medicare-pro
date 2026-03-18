import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import unicodedata
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN MAESTRA ---
URL_HOJA_CALCULO = "TU_URL_AQUI" # 👈 PONÉ TU LINK DE GOOGLE SHEETS ACÁ

st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- CONSTANTES ---
hoy = datetime.today()
hace_110_anios = datetime(hoy.year - 110, 1, 1)
LISTA_DROGAS = ["Adrenalina", "Amiodarona", "Amoxicilina", "Ceftriaxona", "Clonazepam", "Dexametasona", "Diazepam", "Diclofenac", "Dipirona", "Enalapril", "Furosemida", "Ibuprofeno", "Lorazepam", "Losartan", "Morfina", "Omeprazol", "Paracetamol", "Salbutamol", "Tramadol"]

# --- MOTOR DE PDF ---
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except:
    FPDF_DISPONIBLE = False

# --- PERSISTENCIA NUBE + LOCAL ---
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

# --- INICIALIZACIÓN DE BASE DE DATOS ---
db = cargar_datos()
if db:
    for k, v in db.items(): st.session_state[k] = v

claves_iniciales = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
                    "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
for c in claves_iniciales:
    if c not in st.session_state:
        if c == "usuarios_db": 
            # USUARIO MAESTRO (VOS)
            st.session_state[c] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS ENZO", "dni": "000", "matricula": "S/D"}}
        elif c in ["detalles_pacientes_db"]: st.session_state[c] = {}
        else: st.session_state[c] = []

# --- AUDITORÍA DE INGRESOS ---
def registrar_log(u_info):
    log = {
        "Fecha": datetime.now().strftime("%d/%m/%Y"),
        "Hora": datetime.now().strftime("%H:%M:%S"),
        "Usuario": u_info["nombre"],
        "Empresa": u_info["empresa"],
        "Rol": u_info["rol"]
    }
    st.session_state["logs_db"].append(log)
    guardar_datos()

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<h1 style='text-align:center;'>⚕️ MediCare Enterprise</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar al Sistema", use_container_width=True):
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    registrar_log(st.session_state["u_actual"])
                    st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# --- CONTEXTO DE USUARIO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]

# --- FILTRADO POR EMPRESA (SEGURIDAD) ---
if user["rol"] == "SuperAdmin":
    pacientes_visibles = st.session_state["pacientes_db"]
else:
    pacientes_visibles = [p for p in st.session_state["pacientes_db"] 
                          if st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa") == mi_empresa]

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}**")
    st.caption(f"{user['rol']} | Mat: {user['matricula']}")
    st.divider()
    paciente_sel = st.selectbox("Seleccionar Paciente:", pacientes_visibles) if pacientes_visibles else None
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state["logeado"] = False; st.rerun()

# --- INTERFAZ DE TABS ---
menu = ["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetas", "🗄️ PDF", "⚙️ Equipo"]
if user["rol"] == "SuperAdmin": menu.append("🕵️ Auditoría")

tabs = st.tabs(menu)

# 1. ADMISIÓN (CON FILTRO DE EMPRESA)
with tabs[0]:
    st.subheader(f"Admisión de Pacientes - {mi_empresa}")
    with st.form("adm_form"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre y Apellido")
        o = c2.text_input("Obra Social / Cobertura")
        dni_p = c1.text_input("DNI Paciente")
        fnac = c2.date_input("Fecha de Nacimiento", value=hoy, min_value=hace_110_anios, max_value=hoy)
        if st.form_submit_button("Registrar Paciente"):
            id_p = f"{n} ({o}) - {mi_empresa}"
            if id_p not in st.session_state["pacientes_db"]:
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {
                    "dni": dni_p, "fnac": fnac.strftime("%d/%m/%Y"), "empresa": mi_empresa, "autor": user["nombre"]
                }
                guardar_datos(); st.success("Registrado correctamente"); st.rerun()

# 2. CLÍNICA / TRIAGE
with tabs[1]:
    if paciente_sel:
        with st.form("v_form"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("Tensión Arterial", "120/80")
            fc = c2.number_input("FC (lpm)", 30, 200, 75)
            sat = c3.number_input("SatO2 (%)", 50, 100, 98)
            temp = c1.number_input("Temp (°C)", 34.0, 42.0, 36.5)
            # Semáforo de Triage
            color = "🟢 Verde"
            if sat < 90 or fc > 130: color = "🔴 Rojo"
            elif sat < 94 or fc > 110: color = "🟡 Amarillo"
            st.warning(f"Prioridad Actual: {color}")
            if st.form_submit_button("Guardar Signos Vitales"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "Temp": temp, "hora": datetime.now().strftime("%d/%m %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()
    else: st.info("Seleccione un paciente en la barra lateral")

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota_e = st.text_area("Nota clínica:")
        if st.button("Firmar Evolución"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota_e, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "mat": user["matricula"]})
            guardar_datos(); st.success("Nota guardada"); st.rerun()
        for e in reversed([ev for ev in st.session_state["evoluciones_db"] if ev["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']} (Firma: {e['firma']} - Mat: {e['mat']})")

# 4. RECETARIO PRO
with tabs[3]:
    if paciente_sel:
        with st.form("rec_form"):
            med = st.selectbox("Medicamento", sorted(LISTA_DROGAS))
            dos = st.text_input("Dosis (ej: 500mg)")
            via = st.selectbox("Vía", ["Oral", "Intravenosa", "Intramuscular"])
            if st.form_submit_button("Emitir Receta"):
                presc = f"{med} {dos} via {via}"
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": presc, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"]})
                guardar_datos(); st.success("Receta guardada")

# 5. PDF CON FIRMA PROFESIONAL
with tabs[4]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf(p):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"HISTORIA CLINICA - {p}", ln=True, align='C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, f"Empresa Responsable: {mi_empresa}", ln=True, align='C')
            pdf.ln(10)
            # Notas
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "Evoluciones:", ln=True)
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, f"[{ev['fecha']}] {ev['nota']} (Firma: {ev['firma']})")
                pdf.ln(2)
            # Firma al final
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, f"Profesional: {user['nombre']}", ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, f"DNI: {user['dni']} | Matricula: {user['matricula']}", ln=True)
            return pdf.output(dest='S').encode('latin-1')

        if st.button("Descargar Informe PDF"):
            pdf_bytes = crear_pdf(paciente_sel)
            st.download_button("Bajar PDF", pdf_bytes, f"HC_{paciente_sel}.pdf", "application/pdf")

# 6. GESTIÓN DE EQUIPO (DELEGACIÓN)
with tabs[5]:
    st.subheader(f"Administrar Personal de {mi_empresa}")
    with st.form("staff_form"):
        u_id = st.text_input("Usuario (Login)")
        u_pw = st.text_input("Clave")
        u_nm = st.text_input("Nombre y Apellido")
        u_dn = st.text_input("DNI")
        u_mt = st.text_input("Matrícula")
        u_rl = st.selectbox("Rol", ["Coordinador", "Operativo"])
        if st.form_submit_button("Habilitar Profesional"):
            st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "empresa": mi_empresa}
            guardar_datos(); st.success("Usuario creado")

# 7. AUDITORÍA (SOLO ENZO)
if user["rol"] == "SuperAdmin":
    with tabs[6]:
        st.subheader("🕵️ Registro Maestro de Actividad")
        df_logs = pd.DataFrame(st.session_state["logs_db"])
        if not df_logs.empty:
            st.dataframe(df_logs.sort_index(ascending=False), use_container_width=True)
