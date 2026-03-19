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

# ✅ URL DE TU EXCEL - NO TOCAR EL ID
URL_HOJA_CALCULO = "https://docs.google.com/spreadsheets/d/1zZG491mwbUgWrG_Yta7uq1vVqR0jdNhnArPSgjsQNXs/edit?gid=0#gid=0"

st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- 🎁 LOGO EXCLUSIVO E.G. (SIDEBAR) ---
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

# --- MOTOR DE PERSISTENCIA (ANTIFALLOS) ---
DB_FILE = "medicare_saas_final_db.json"

def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="0", ttl=0)
        if not df_nube.empty:
            for i in range(min(len(df_nube), 10)):
                valor = str(df_nube.iloc[i, 0])
                if '{"usuarios_db"' in valor: return json.loads(valor)
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
    except: st.error("⚠️ Sincronizando datos con la nube...")

# --- INICIALIZACIÓN ---
if "db_inicializada" not in st.session_state:
    db = cargar_datos()
    if db:
        for k, v in db.items(): st.session_state[k] = v
    else:
        for c in ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]:
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
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario"); p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                db_f = cargar_datos()
                if db_f:
                    for k, v in db_f.items(): st.session_state[k] = v
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][u]; st.session_state["logeado"] = True; st.rerun()
                else: st.error("Acceso denegado")
    st.stop()

# --- CONTEXTO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
rol = user["rol"]

# --- SIDEBAR ---
with st.sidebar:
    render_logo_eg(110)
    st.markdown(f"<h3 style='text-align:center;'>{mi_empresa}</h3>", unsafe_allow_html=True)
    st.write(f"👤 **{user['nombre']}**")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.divider()
    buscar = st.text_input("🔍 Buscar Paciente:")
    pacientes_visibles = st.session_state["pacientes_db"] if rol == "SuperAdmin" else [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]
    p_f = [p for p in pacientes_visibles if buscar.lower() in p.lower()]
    paciente_sel = st.selectbox("Seleccionar:", p_f) if p_f else None
    if st.button("Cerrar Sesión", use_container_width=True): st.session_state["logeado"] = False; st.rerun()

# --- INTERFAZ PREMIUM ---
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
            n = col_a.text_input("Nombre y Apellido"); d = col_a.text_input("DNI")
            o = col_b.text_input("Obra Social"); f_nac = col_b.date_input("Nacimiento", value=date(1990, 1, 1))
            ant = st.text_area("Antecedentes Médicos")
            if st.form_submit_button("Habilitar Paciente"):
                id_p = f"{n} ({o}) - {mi_empresa}"
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "antecedentes": ant, "empresa": mi_empresa}
                guardar_datos(); st.success("Registrado"); st.rerun()

# 2. CLÍNICA (CON DASHBOARD DE SIGNOS)
with tabs[1]:
    if paciente_sel:
        st.subheader(f"Constantes Vitales: {paciente_sel}")
        # Dashboard Visual
        v_p = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_sel]
        if v_p:
            u = v_p[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("T.A.", u["TA"]); c2.metric("SatO2", f"{u['Sat']}%"); c3.metric("F.C.", f"{u['FC']} lpm"); c4.metric("HGT", u["HGT"])
        
        with st.form("vitales_f"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("TA", "120/80"); fc = c1.number_input("FC", 30, 200, 75); sat = c2.number_input("SatO2%", 50, 100, 98)
            fr = c2.number_input("FR", 10, 50, 16); temp = c3.number_input("Temp", 34.0, 42.0, 36.5); hgt = c3.text_input("HGT", "100")
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "FR": fr, "Temp": temp, "HGT": hgt, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")})
                guardar_datos(); st.success("Guardado"); st.rerun()

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota clínica:")
        if st.button("Firmar Nota"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "mat": user["matricula"]})
            guardar_datos(); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Por: {e['firma']}*")

# 4. RECETARIO PRO
with tabs[3]:
    if paciente_sel:
        with st.form("recet"):
            c1, c2 = st.columns([2, 1])
            drog = c1.text_input("Medicamento"); dos = c2.text_input("Dosis")
            via = st.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular", "Subcutánea"])
            frec = st.selectbox("Frecuencia", ["Cada 8 hs", "Cada 12 hs", "Dosis Única"])
            if st.form_submit_button("Cargar Receta"):
                t_r = f"{drog} {dos} ({via}) - {frec}"
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": t_r, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"]})
                guardar_datos(); st.success("Receta guardada")

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        serv = st.text_input("Práctica"); mont = st.number_input("Monto", 0)
        if st.button("Cobrar"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado")

# 6. PDF (EL TOQUE FINAL PROLIJO)
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf_pro(p):
            pdf = FPDF()
            pdf.add_page()
            def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
            
            # --- LOGO MÉDICO E.G. ---
            pdf.set_fill_color(59, 130, 246) # Azul
            pdf.circle(25, 25, 12, 'F')
            pdf.set_draw_color(255, 255, 255) # Blanco
            pdf.set_line_width(1.5)
            pdf.line(25, 18, 25, 32); pdf.line(18, 25, 32, 25)
            
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(45, 20); pdf.cell(0, 10, t(mi_empresa), ln=True)
            pdf.set_font("Arial", 'I', 10); pdf.set_xy(45, 26); pdf.cell(0, 10, t("MediCare Enterprise PRO - Historia Clinica"), ln=True)
            pdf.ln(20)
            
            # Datos Paciente
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, t(f" PACIENTE: {p}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 10); pdf.cell(0, 8, t(f" DNI: {det.get('dni')} | Empresa: {mi_empresa}"), ln=True)
            pdf.ln(5)

            # TABLA SIGNOS VITALES
            pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("REGISTRO DE CONSTANTES VITALES:"), ln=True)
            pdf.set_font("Arial", 'B', 9); pdf.set_fill_color(230, 230, 230)
            pdf.cell(40, 7, "FECHA", 1, 0, 'C', True); pdf.cell(25, 7, "TA", 1, 0, 'C', True); pdf.cell(25, 7, "SAT%", 1, 0, 'C', True); pdf.cell(25, 7, "FC", 1, 0, 'C', True); pdf.cell(25, 7, "TEMP", 1, 0, 'C', True); pdf.cell(25, 7, "HGT", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 9)
            for v in [x for x in st.session_state["vitales_db"] if x["paciente"] == p]:
                pdf.cell(40, 7, t(v['fecha']), 1); pdf.cell(25, 7, t(v['TA']), 1); pdf.cell(25, 7, t(v['Sat']), 1); pdf.cell(25, 7, t(v['FC']), 1); pdf.cell(25, 7, t(v['Temp']), 1); pdf.cell(25, 7, t(v['HGT']), 1, 1)
            pdf.ln(10)

            # EVOLUCIONES
            pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("EVOLUCIONES Y NOTAS:"), ln=True)
            for ev in [x for x in st.session_state["evoluciones_db"] if x["paciente"] == p]:
                pdf.set_font("Arial", 'B', 9); pdf.cell(0, 6, t(f"[{ev['fecha']}] - Firma: {ev['firma']}"), ln=True)
                pdf.set_font("Arial", '', 10); pdf.multi_cell(0, 6, t(ev['nota']), 'L'); pdf.ln(2)
            
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y())
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, t(f"Firma: {user['nombre']}"), ln=True)
            pdf.cell(0, 6, t(f"Matricula: {user['matricula']}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')

        if st.button("📥 Generar Reporte Médico Profesional"):
            st.download_button("Bajar PDF", crear_pdf_pro(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO (JERARQUÍA DE PODER)
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader("Alta de Personal")
        with st.form("staff"):
            u_id = st.text_input("Usuario"); u_pw = st.text_input("Clave")
            u_nm = st.text_input("Nombre"); u_mt = st.text_input("Matrícula")
            u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
            u_ti = st.selectbox("Título", ["Médico/a", "Enfermero/a", "Licenciado/a"])
            if st.form_submit_button("Habilitar"):
                st.session_state["usuarios_db"][u_id] = {"pass": u_pw, "nombre": u_nm, "rol": u_rl, "empresa": mi_empresa, "matricula": u_mt, "titulo": u_ti}
                guardar_datos(); st.success("Habilitado"); st.rerun()

# 8. AUDITORÍA
if rol == "SuperAdmin":
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Logs del Sistema")
        st.dataframe(pd.DataFrame(st.session_state["logs_db"]), use_container_width=True)
