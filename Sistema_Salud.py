import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import unicodedata
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN MAESTRA ---
# ⚠️ PONÉ TU LINK DE GOOGLE SHEETS ACÁ PARA QUE NO DE ERROR DE NUBE
URL_HOJA_CALCULO = "TU_URL_AQUI" 

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

# --- PERSISTENCIA ---
DB_FILE = "medicare_saas_db.json"

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
            st.session_state[c] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS ENZO", "dni": "37108100", "matricula": "M.P 21947", "titulo": "Director Técnico"}}
        elif c in ["detalles_pacientes_db"]: st.session_state[c] = {}
        else: st.session_state[c] = []

def registrar_log(u):
    st.session_state["logs_db"].append({
        "Fecha": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M:%S"),
        "Usuario": u["nombre"], "Empresa": u["empresa"], "Acceso": u["rol"]
    })
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
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    registrar_log(st.session_state["u_actual"])
                    st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# --- SEGURIDAD DE EMPRESA ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]

if user["rol"] == "SuperAdmin":
    pacientes_visibles = st.session_state["pacientes_db"]
else:
    pacientes_visibles = [p for p in st.session_state["pacientes_db"] 
                          if st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa") == mi_empresa]

# --- SIDEBAR ---
with st.sidebar:
    st.header(f"🏢 {mi_empresa}")
    st.subheader(f"👤 {user['nombre']}")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.caption(f"DNI: {user['dni']} | Mat: {user['matricula']}")
    st.divider()
    paciente_sel = st.selectbox("Paciente:", pacientes_visibles) if pacientes_visibles else None
    if st.button("Cerrar Sesión"):
        st.session_state["logeado"] = False; st.rerun()

st.title("Gestión Clínica Integrada")
menu = ["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetas", "🗄️ PDF", "⚙️ Equipo"]
if user["rol"] == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. ADMISIÓN (CON CALENDARIO DE 110 AÑOS)
with tabs[0]:
    st.subheader(f"Admisión de Paciente - {mi_empresa}")
    with st.form("adm"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nombre y Apellido")
        o = c2.text_input("Obra Social")
        dni_p = c1.text_input("DNI Paciente")
        fnac = c2.date_input("Fecha de Nacimiento", value=hoy, min_value=hace_110_anios, max_value=hoy)
        if st.form_submit_button("Registrar en Empresa"):
            id_p = f"{n} ({o}) - {mi_empresa}"
            st.session_state["pacientes_db"].append(id_p)
            st.session_state["detalles_pacientes_db"][id_p] = {"dni": dni_p, "fnac": fnac.strftime("%d/%m/%Y"), "empresa": mi_empresa}
            guardar_datos(); st.success("Registrado correctamente"); st.rerun()

# 2. CLÍNICA (CON TRIAGE COMPLETO)
with tabs[1]:
    if paciente_sel:
        with st.form("clin"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("TA", "120/80")
            fc = c2.number_input("FC (lpm)", 30, 200, 75)
            fr = c3.number_input("FR (rpm)", 10, 50, 16)
            sat = c1.number_input("SatO2%", 50, 100, 98)
            temp = c2.number_input("Temp°C", 34.0, 42.0, 36.5)
            hgt = c3.number_input("HGT (mg/dl)", 20, 600, 100)
            color = "🟢 Verde"
            if sat < 90 or fc > 130: color = "🔴 Rojo"
            elif sat < 94: color = "🟡 Amarillo"
            st.warning(f"Triage sugerido: {color}")
            if st.form_submit_button("Guardar Signos Vitales"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "FR": fr, "Sat": sat, "Temp": temp, "HGT": hgt, "hora": datetime.now().strftime("%H:%M")})
                guardar_datos(); st.rerun()

# 3. EVOLUCIÓN (FIRMA CON TÍTULO)
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota del profesional:")
        if st.button("Firmar Digitalmente"):
            st.session_state["evoluciones_db"].append({
                "paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), 
                "firma": user["nombre"], "titulo": user.get("titulo", "Profesional"), "mat": user["matricula"]
            })
            guardar_datos(); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Firmado por: {e.get('titulo','')} {e['firma']}*")

# 4. RECETARIO PRO
with tabs[3]:
    if paciente_sel:
        with st.form("rec"):
            med = st.selectbox("Droga", sorted(LISTA_DROGAS))
            dos = st.text_input("Dosis e Indicación")
            if st.form_submit_button("Emitir Receta"):
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": f"{med} {dos}", "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"]})
                guardar_datos(); st.success("Receta guardada")

# 5. PDF LEGAL (NOMBRE + DNI + MATRICULA + TITULO)
with tabs[4]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf(p):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"INFORME CLINICO - {p}", ln=True, align='C')
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "Evoluciones:", ln=True)
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, f"[{ev['fecha']}] {ev['nota']}\nFirma: {ev.get('titulo','')} {ev['firma']} - Mat: {ev['mat']}")
                pdf.ln(2)
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, f"Profesional: {user.get('titulo','')} {user['nombre']}", ln=True)
            pdf.cell(0, 5, f"DNI: {user['dni']} | Matricula: {user['matricula']}", ln=True)
            pdf.cell(0, 5, f"Empresa: {mi_empresa}", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        if st.button("Descargar Informe PDF"):
            st.download_button("Bajar PDF", crear_pdf(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 6. GESTIÓN DE EQUIPO (TÍTULO VS ROL)
with tabs[5]:
    st.subheader(f"Administrar Equipo de {mi_empresa}")
    with st.form("equipo_new"):
        c1, c2 = st.columns(2)
        u_id = c1.text_input("Nombre de Usuario (Login)")
        u_pw = c2.text_input("Clave")
        u_nm = c1.text_input("Nombre Completo (DNI)")
        u_dn = c2.text_input("DNI Profesional")
        u_mt = c1.text_input("Matrícula")
        # --- AQUÍ ESTÁ LO QUE PEDISTE ---
        u_ti = c2.selectbox("Título / Profesión", ["Médico/a", "Enfermero/a", "Lic. en Enfermería", "Kinesiólogo/a", "Administrativo/a"])
        u_rl = st.selectbox("Rol en el Sistema (Permisos)", ["Operativo", "Coordinador"])
        if st.form_submit_button("Habilitar Profesional"):
            st.session_state["usuarios_db"][u_id] = {
                "pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, 
                "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa
            }
            guardar_datos(); st.success(f"Habilitado: {u_nm} ({u_ti})"); st.rerun()

# 7. AUDITORÍA (SOLO ENZO)
if user["rol"] == "SuperAdmin":
    with tabs[6]:
        st.subheader("🕵️ Auditoría Global")
        st.dataframe(pd.DataFrame(st.session_state["logs_db"]).sort_index(ascending=False), use_container_width=True)
