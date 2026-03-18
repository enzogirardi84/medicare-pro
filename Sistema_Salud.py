import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN DE LIBRERÍAS (PDF) ---
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

# --- MOTOR DE PERSISTENCIA (PROTECCIÓN DE DATOS) ---
DB_FILE = "medicare_enterprise_db.json"

def guardar_datos():
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    # Guardado Nube
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = pd.DataFrame([json.dumps(data, ensure_ascii=False)])
        conn.update(spreadsheet=URL_HOJA_CALCULO, data=df_nube)
    except: pass
    # Backup Local
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

# --- INICIALIZACIÓN CRÍTICA ---
if "db_inicializada" not in st.session_state:
    db_recuperada = cargar_datos()
    if db_recuperada:
        for k, v in db_recuperada.items(): st.session_state[k] = v
    
    # Valores base si la base está vacía
    if "usuarios_db" not in st.session_state:
        st.session_state["usuarios_db"] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "dni": "37108100", "matricula": "M.P 21947", "titulo": "Director"}}
    
    for c in ["pacientes_db", "detalles_pacientes_db", "evoluciones_db", "vitales_db", "indicaciones_db", "facturacion_db", "logs_db", "turnos_db"]:
        if c not in st.session_state:
            st.session_state[c] = {} if "detalles" in c else []
    
    st.session_state["db_inicializada"] = True

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
                # Validamos contra la DB cargada
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    st.session_state["logs_db"].append({"Fecha": datetime.now().strftime("%d/%m/%Y"), "Hora": datetime.now().strftime("%H:%M"), "Usuario": st.session_state["u_actual"]["nombre"]})
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
    p_f = [p for p in pacientes_visibles if buscar.lower() in p.lower() or (st.session_state["detalles_pacientes_db"].get(p,{}).get("dni","") and buscar in st.session_state["detalles_pacientes_db"].get(p,{}).get("dni",""))]
    paciente_sel = st.selectbox("Seleccionar:", p_f) if p_f else None
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state["logeado"] = False; st.rerun()

# --- TABS ---
st.title("MediCare PRO Enterprise")
tabs = st.tabs(["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF", "⚙️ Mi Equipo"])

# 1. ADMISIÓN (CON BORRADO)
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Registrar Paciente")
        with st.form("adm_f"):
            n = st.text_input("Nombre"); o = st.text_input("Obra Social"); d = st.text_input("DNI")
            if st.form_submit_button("Registrar"):
                id_p = f"{n} ({o}) - {mi_empresa}"
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "empresa": mi_empresa}
                guardar_datos(); st.success("Registrado!"); st.rerun()
    with c2:
        st.subheader("Eliminar")
        if paciente_sel:
            if st.button(f"🔴 Borrar a {paciente_sel}"):
                st.session_state["pacientes_db"].remove(paciente_sel)
                guardar_datos(); st.rerun()

# 2. CLÍNICA (TRIAGE)
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
            st.info(f"**{e['fecha']}** | {e['nota']} (Firma: {e['firma']})")

# 4. RECETARIO PRO (VÍAS Y HORARIOS)
with tabs[3]:
    if paciente_sel:
        st.subheader("💊 Indicación Médica")
        with st.form("receta_pro"):
            col1, col2 = st.columns([2, 1])
            drog = col1.text_input("Medicamento")
            dos = col2.text_input("Dosis")
            c3, c4, c5 = st.columns(3)
            via = c3.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular", "Subcutánea", "Inhalatoria"])
            frec = c4.selectbox("Horario", ["Cada 2 hs", "Cada 4 hs", "Cada 6 hs", "Cada 8 hs", "Cada 12 hs", "Cada 24 hs", "SOS"])
            dias = c5.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Indicación"):
                texto = f"{drog} {dos} vía {via} - {frec} por {dias} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": texto, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"]})
                guardar_datos(); st.success("Cargado!")
        for r in reversed([x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]):
            st.success(f"📌 {r['fecha']} | {r['med']}")

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        serv = st.text_input("Servicio"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Cobro"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado")

# 6. PDF (EL COMPLETO)
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf_final(p):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, t(f"HISTORIA CLINICA - {p}"), ln=True, align='C')
            pdf.ln(10); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, t("1. EVOLUCIONES:") , ln=True)
            pdf.set_font("Arial", '', 10)
            for ev in [e for e in st.session_state["evoluciones_db"] if e["paciente"] == p]:
                pdf.multi_cell(0, 6, t(f"[{ev['fecha']}] {ev['nota']} \n(Firma: {ev['firma']})")); pdf.ln(2)
            pdf.ln(5); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, t("2. INDICACIONES:"), ln=True)
            for rec in [r for r in st.session_state["indicaciones_db"] if r["paciente"] == p]:
                pdf.multi_cell(0, 6, t(f"[{rec['fecha']}] {rec['med']}"))
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y()); pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 5, t(f"Profesional: {user['nombre']}"), ln=True)
            pdf.cell(0, 5, t(f"DNI: {user['dni']} | Mat: {user['matricula']}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')
        if st.button("Descargar Informe Completo"):
            st.download_button("Bajar PDF", crear_pdf_final(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO (CREAR USUARIOS)
with tabs[6]:
    st.subheader(f"Personal de {mi_empresa}")
    with st.form("eq_f"):
        u_id = st.text_input("Usuario"); u_pw = st.text_input("Clave"); u_nm = st.text_input("Nombre")
        u_mt = st.text_input("Matrícula"); u_dn = st.text_input("DNI")
        u_ti = st.selectbox("Título", ["Médico/a", "Enfermero/a", "Kinesiólogo/a", "Administrativo/a"])
        u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
        if st.form_submit_button("Habilitar"):
            st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa}
            guardar_datos(); st.success("Habilitado!"); st.rerun()

# 8. AUDITORÍA (SOLO PARA ENZO)
if user["rol"] == "SuperAdmin":
    with tabs[6]: # Se añade dinámicamente
        st.subheader("🕵️ Auditoría Global")
        st.table(pd.DataFrame(st.session_state["logs_db"]).sort_index(ascending=False))
