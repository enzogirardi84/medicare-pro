import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN Y PDF ---
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# ⚠️ TU URL DE GOOGLE SHEETS
URL_HOJA_CALCULO = "TU_URL_AQUI" 

st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- LOGO E.G. (SVG) ---
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

# --- MOTOR DE PERSISTENCIA REFORZADO ---
DB_FILE = "medicare_enterprise_db.json"

def cargar_datos():
    # Paso 1: Intentar cargar de la nube (Prioridad Máxima)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="0", ttl=0)
        if not df_nube.empty:
            return json.loads(df_nube.iloc[0, 0])
    except Exception as e:
        st.warning(f"Sincronizando con la nube...")
    
    # Paso 2: Si no hay nube, intentar local
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def guardar_datos():
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    
    # Guardado Local (Inmediato)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    # Guardado Nube
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = pd.DataFrame([json.dumps(data, ensure_ascii=False)])
        conn.update(spreadsheet=URL_HOJA_CALCULO, data=df_nube)
    except Exception as e:
        st.error(f"Error al subir a la nube: {e}")

# --- INICIALIZACIÓN CRÍTICA (ORDEN IMPORTANTE) ---
if "db_inicializada" not in st.session_state:
    datos_recuperados = cargar_datos()
    if datos_recuperados:
        for k, v in datos_recuperados.items():
            st.session_state[k] = v
    
    # Valores por defecto SOLO si no existen tras la carga
    if "usuarios_db" not in st.session_state:
        st.session_state["usuarios_db"] = {"admin": {"pass": "admin123", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "dni": "37108100", "matricula": "M.P 21947", "titulo": "Director"}}
    if "pacientes_db" not in st.session_state: st.session_state["pacientes_db"] = []
    if "detalles_pacientes_db" not in st.session_state: st.session_state["detalles_pacientes_db"] = {}
    if "evoluciones_db" not in st.session_state: st.session_state["evoluciones_db"] = []
    if "vitales_db" not in st.session_state: st.session_state["vitales_db"] = []
    if "indicaciones_db" not in st.session_state: st.session_state["indicaciones_db"] = []
    if "facturacion_db" not in st.session_state: st.session_state["facturacion_db"] = []
    if "logs_db" not in st.session_state: st.session_state["logs_db"] = []
    if "turnos_db" not in st.session_state: st.session_state["turnos_db"] = []
    
    st.session_state["db_inicializada"] = True

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<h2 style='text-align:center;'>MediCare Pro Access</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Usuario")
            p = st.text_input("Clave", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                # Recargamos datos antes de validar para asegurar que el usuario nuevo existe
                datos = cargar_datos()
                if datos and u in datos["usuarios_db"] and datos["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = datos["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    guardar_datos()
                    st.rerun()
                elif u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]
                    st.session_state["logeado"] = True
                    st.rerun()
                else:
                    st.error("Acceso denegado: Usuario o clave incorrectos")
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
    if st.button("Cerrar Sesión"):
        st.session_state["logeado"] = False; st.rerun()

# --- TABS ---
st.title("Gestión Clínica Integrada")
tabs = st.tabs(["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF", "⚙️ Mi Equipo"])

# 1. ADMISIÓN (CORREGIDO)
with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Registrar Paciente")
        with st.form("adm_form", clear_on_submit=True):
            n = st.text_input("Nombre y Apellido")
            o = st.text_input("Obra Social")
            d = st.text_input("DNI Paciente")
            if st.form_submit_button("Registrar Paciente"):
                if n and d:
                    id_p = f"{n} ({o}) - {mi_empresa}"
                    if id_p not in st.session_state["pacientes_db"]:
                        st.session_state["pacientes_db"].append(id_p)
                        st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "empresa": mi_empresa}
                        guardar_datos()
                        st.success(f"Paciente {n} registrado!")
                        st.rerun()
                    else: st.warning("El paciente ya existe.")
                else: st.error("Completá Nombre y DNI.")
    with col2:
        st.subheader("Borrar Paciente")
        if paciente_sel:
            if st.button(f"🔴 Borrar a {paciente_sel}"):
                st.session_state["pacientes_db"].remove(paciente_sel)
                del st.session_state["detalles_pacientes_db"][paciente_sel]
                guardar_datos()
                st.success("Paciente eliminado")
                st.rerun()

# 4. RECETARIO (VÍAS Y FRECUENCIAS)
with tabs[3]:
    if paciente_sel:
        with st.form("recet_pro"):
            col1, col2 = st.columns([2, 1])
            drog = col1.text_input("Medicamento")
            dos = col2.text_input("Dosis")
            c3, c4, c5 = st.columns(3)
            via = c3.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular", "Subcutánea"])
            frec = c4.selectbox("Frecuencia", ["Cada 2 hs", "Cada 4 hs", "Cada 6 hs", "Cada 8 hs", "Cada 12 hs", "Cada 24 hs", "SOS"])
            dias = c5.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Indicación"):
                ind = f"{drog} {dos} vía {via} - {frec} por {dias} días."
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": ind, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"], "mat": user["matricula"]})
                guardar_datos()
                st.success("Cargado")
        for r in reversed([x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]):
            st.write(f"💊 {r['fecha']} | {r['med']}")

# 7. EQUIPO (CREAR USUARIOS)
with tabs[6]:
    st.subheader(f"Equipo de {mi_empresa}")
    with st.form("new_user"):
        u_id = st.text_input("ID Usuario")
        u_pw = st.text_input("Clave")
        u_nm = st.text_input("Nombre Completo")
        u_dn = st.text_input("DNI Profesional")
        u_mt = st.text_input("Matrícula")
        u_ti = st.selectbox("Título", ["Médico/a", "Enfermero/a", "Kinesiólogo/a", "Administrativo/a"])
        u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
        if st.form_submit_button("Habilitar"):
            if u_id and u_pw:
                st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "dni": u_dn, "matricula": u_mt, "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa}
                guardar_datos()
                st.success("Usuario habilitado!")
                st.rerun()
