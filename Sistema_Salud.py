import streamlit as st
import pandas as pd
from datetime import datetime, date
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

# ✅ URL DE TU EXCEL
URL_HOJA_CALCULO = "https://docs.google.com/spreadsheets/d/1zZG491mwbUgWrG_Yta7uq1vVqR0jdNhnArPSgjsQNXs/edit?gid=0#gid=0"

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- 🎨 DISEÑO VISUAL Y COLORES TENUES (CSS) ---
# Este bloque inyecta un fondo degradado suave y mejora el aspecto de los formularios
page_bg_css = """
<style>
/* Fondo principal con degradado tenue (azul muy clarito a blanco) */
.stApp {
    background: linear-gradient(135deg, #e3f2fd 0%, #ffffff 100%);
}

/* Fondo de la barra lateral (Sidebar) un poco más definido */
[data-testid="stSidebar"] {
    background-color: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

/* Estilo tipo tarjeta para los formularios para que resalten sobre el fondo tenue */
div[data-testid="stForm"] {
    background-color: rgba(255, 255, 255, 0.65);
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* Color de los textos principales para asegurar que se lean bien */
h1, h2, h3, h4, h5, h6, p, label {
    color: #1e293b !important;
}
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
DB_FILE = "medicare_saas_final_db.json"

def cargar_datos():
    try:
        st.cache_data.clear()
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, ttl=0)
        
        celdas = list(df_nube.columns) + df_nube.values.flatten().tolist()
        
        for valor in reversed(celdas):
            v_str = str(valor).strip()
            if '{"usuarios_db"' in v_str:
                return json.loads(v_str)
    except Exception as e:
        pass
        
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
        st.toast("✅ Datos guardados en la Nube", icon="☁️")
    except Exception as e:
        st.error(f"⚠️ Error al subir a la nube: {e}")

# --- INICIALIZACIÓN ---
if "db_inicializada" not in st.session_state:
    db = cargar_datos()
    if db:
        for k, v in db.items(): st.session_state[k] = v
    else:
        for c in ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db"]:
            if c not in st.session_state:
                if c == "usuarios_db": 
                    st.session_state[c] = {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "matricula": "M.P 21947", "titulo": "Director de Sistemas"}}
                elif c == "detalles_pacientes_db": st.session_state[c] = {}
                else: st.session_state[c] = []
    st.session_state["db_inicializada"] = True

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False
if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><h2 style='text-align:center; color:#2563eb;'>MediCare Enterprise PRO</h2>", unsafe_allow_html=True)
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
                
                if usuario_encontrado and str(st.session_state["usuarios_db"][usuario_encontrado]["pass"]).strip() == p_limpio:
                    st.session_state["u_actual"] = st.session_state["usuarios_db"][usuario_encontrado]
                    st.session_state["logeado"] = True
                    st.session_state["logs_db"].append({"F": datetime.now().strftime("%d/%m/%Y"), "H": datetime.now().strftime("%H:%M"), "U": st.session_state["u_actual"]["nombre"], "E": st.session_state["u_actual"]["empresa"], "A": "Login"})
                    guardar_datos()
                    st.rerun()
                else: 
                    st.error("Acceso denegado: Usuario o contraseña incorrectos.")
    st.stop()

# --- CONTEXTO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
rol = user["rol"]

# --- SIDEBAR (CON PRIVACIDAD MULTI-TENANT) ---
with st.sidebar:
    render_logo_eg(110)
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}**")
    st.info(f"**{user.get('titulo', 'Profesional')}**")
    st.divider()
    
    buscar = st.text_input("🔍 Buscar Paciente:")
    
    # EL NÚCLEO DE LA PRIVACIDAD
    if rol == "SuperAdmin":
        pacientes_visibles = st.session_state["pacientes_db"]
    else:
        pacientes_visibles = [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]
        
    p_f = [p for p in pacientes_visibles if buscar.lower() in p.lower()]
    paciente_sel = st.selectbox("Seleccionar:", p_f) if p_f else None
    
    if paciente_sel:
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        st.caption(f"**DNI:** {det.get('dni','S/D')}")
        if st.button("🔴 DAR DE ALTA / ELIMINAR", width="stretch"):
            st.session_state["pacientes_db"].remove(paciente_sel)
            if paciente_sel in st.session_state["detalles_pacientes_db"]: del st.session_state["detalles_pacientes_db"][paciente_sel]
            guardar_datos()
            st.rerun()

    st.divider()
    if st.button("Cerrar Sesión", width="stretch"):
        st.session_state["logeado"] = False; st.rerun()

# --- MENU DINÁMICO ---
menu = ["👤 Admisión", "📊 Clínica", "📝 Evolución", "💊 Recetario PRO", "💳 Caja", "🗄️ PDF"]
if rol in ["SuperAdmin", "Coordinador"]: menu.append("⚙️ Mi Equipo")
if rol == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. ADMISIÓN (ASIGNACIÓN DE EMPRESA CORREGIDA)
with tabs[0]:
    st.subheader("Registrar Paciente")
    with st.form("adm_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("Nombre y Apellido")
        d = col_a.text_input("DNI")
        o = col_b.text_input("Obra Social")
        f_nac = col_b.date_input("Nacimiento", value=date(1990, 1, 1))
        
        # Corrección: El campo ahora está vacío para el Admin, obligando a rellenarlo
        if rol == "SuperAdmin":
            empresa_destino = st.text_input("🏢 Asignar a Clínica / Empresa", placeholder="Ej: Clínica San Lucas", help="Escribe a qué empresa pertenece este paciente. (No dejar en blanco)")
        else:
            empresa_destino = mi_empresa
            st.info(f"🏢 Institución asignada: **{empresa_destino}**")
            
        ant = st.text_area("Antecedentes Médicos")
        
        if st.form_submit_button("Habilitar Paciente", width="stretch"):
            if n and d and empresa_destino: # Se valida que la empresa no esté vacía
                id_p = f"{n} ({o}) - {empresa_destino.strip()}"
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {
                    "dni": d, 
                    "fnac": f_nac.strftime("%d/%m/%Y"), 
                    "antecedentes": ant, 
                    "empresa": empresa_destino.strip()
                }
                guardar_datos()
                st.success(f"Registrado exitosamente en {empresa_destino.strip()}")
                st.rerun()
            else:
                st.error("⚠️ El Nombre, DNI y Empresa son obligatorios.")

# 2. CLÍNICA
with tabs[1]:
    if paciente_sel:
        st.subheader(f"Constantes Vitales: {paciente_sel}")
        vitales_p = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_sel]
        if vitales_p:
            u = vitales_p[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("T.A.", u["TA"]); m2.metric("SATO2", f"{u['Sat']}%"); m3.metric("F.C.", f"{u['FC']} lpm"); m4.metric("HGT", u["HGT"])
        
        with st.form("vitales_f"):
            c1, c2, c3 = st.columns(3)
            ta = c1.text_input("T.A.", "120/80"); fc = c1.number_input("F.C.", 30, 200, 75)
            sat = c2.number_input("SatO2%", 50, 100, 98); fr = c2.number_input("F.R.", 10, 50, 16)
            temp = c3.number_input("Temp °C", 34.0, 42.0, 36.5); hgt = c3.text_input("HGT / Glucemia", "100")
            if sat < 90: st.error("🚨 PRIORIDAD: EMERGENCIA")
            elif sat < 94: st.warning("⚠️ PRIORIDAD: URGENCIA")
            
            if st.form_submit_button("Guardar Signos", width="stretch"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "FR": fr, "Temp": temp, "HGT": hgt, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")})
                guardar_datos(); st.success("Signos guardados"); st.rerun()
    else: st.info("Seleccione un paciente para cargar sus signos vitales.")

# 3. EVOLUCIÓN
with tabs[2]:
    if paciente_sel:
        nota = st.text_area("Nota clínica:")
        if st.button("Firmar Nota", width="stretch"):
            st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "mat": user.get("matricula", "N/A")})
            guardar_datos(); st.rerun()
        for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
            st.info(f"**{e['fecha']}** | {e['nota']}\n\n*Por: {e['firma']}*")

# 4. RECETARIO PRO
with tabs[3]:
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
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": t_r, "fecha": datetime.now().strftime("%d/%m/%Y"), "firma": user["nombre"]})
                guardar_datos(); st.success("Receta guardada"); st.rerun()
        for r in reversed([x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]):
            st.success(f"📌 {r['fecha']} | {r['med']}")

# 5. CAJA
with tabs[4]:
    if paciente_sel:
        st.subheader("💳 Registro de Cobros")
        serv = st.text_input("Servicio / Práctica"); mont = st.number_input("Monto", 0)
        if st.button("Registrar Pago", width="stretch"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mont, "fecha": datetime.now().strftime("%d/%m/%Y")})
            guardar_datos(); st.success("Registrado"); st.rerun()

# 6. PDF
with tabs[5]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf_pro(p):
            pdf = FPDF()
            pdf.add_page()
            def t(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_fill_color(59, 130, 246)
            pdf.ellipse(10, 10, 22, 22, 'F') 
            pdf.set_draw_color(255, 255, 255); pdf.set_line_width(1.2)
            pdf.line(21, 14, 21, 28); pdf.line(14, 21, 28, 21)
            
            emp_paciente = st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa", mi_empresa)
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(38, 14); pdf.cell(0, 10, t(emp_paciente), ln=True)
            pdf.set_font("Arial", 'I', 9); pdf.set_xy(38, 20); pdf.cell(0, 10, t("MediCare Enterprise PRO - Reporte Medico"), ln=True)
            pdf.ln(18)
            
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, t(f" HISTORIA CLINICA: {p}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 10); pdf.cell(0, 8, t(f" DNI: {det.get('dni')} | Empresa: {emp_paciente}"), ln=True); pdf.ln(5)

            pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("SIGNOS VITALES:"), ln=True)
            pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
            pdf.cell(35, 7, "FECHA", 1, 0, 'C', True); pdf.cell(22, 7, "TA", 1, 0, 'C', True); pdf.cell(22, 7, "SAT%", 1, 0, 'C', True); pdf.cell(22, 7, "FC", 1, 0, 'C', True); pdf.cell(22, 7, "TEMP", 1, 0, 'C', True); pdf.cell(22, 7, "HGT", 1, 1, 'C', True)
            pdf.set_font("Arial", '', 8)
            for v in [x for x in st.session_state["vitales_db"] if x["paciente"] == p]:
                pdf.cell(35, 7, t(v['fecha']), 1); pdf.cell(22, 7, t(v['TA']), 1); pdf.cell(22, 7, t(v['Sat']), 1); pdf.cell(22, 7, t(v['FC']), 1); pdf.cell(22, 7, t(v['Temp']), 1); pdf.cell(22, 7, t(v['HGT']), 1, 1)
            pdf.ln(10)

            pdf.set_font("Arial", 'B', 11); pdf.cell(0, 10, t("EVOLUCIONES CLINICAS:"), ln=True)
            for ev in [x for x in st.session_state["evoluciones_db"] if x["paciente"] == p]:
                pdf.set_font("Arial", 'B', 8); pdf.cell(0, 6, t(f"[{ev['fecha']}] - Firma: {ev['firma']}"), ln=True)
                pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 5, t(ev['nota']), 'L'); pdf.ln(2)
            
            pdf.ln(20); pdf.line(10, pdf.get_y(), 80, pdf.get_y())
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, t(f"Firma: {user['nombre']}"), ln=True)
            pdf.cell(0, 6, t(f"Matricula: {user.get('matricula', 'S/D')}"), ln=True)
            return pdf.output(dest='S').encode('latin-1')

        st.download_button("📥 Generar Historia Clínica en PDF", crear_pdf_pro(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 7. EQUIPO (ASIGNACIÓN DE EMPRESA CORREGIDA)
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"Gestión de Personal")
        with st.form("new_staff"):
            col_u1, col_u2 = st.columns(2)
            u_id = col_u1.text_input("Usuario (Login)")
            u_pw = col_u2.text_input("Clave")
            u_nm = st.text_input("Nombre Completo")
            
            col_u3, col_u4 = st.columns(2)
            u_mt = col_u3.text_input("Matrícula")
            u_ti = col_u4.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Administrativo/a"])
            
            # Corrección: El campo ahora está vacío para el Admin, obligando a rellenarlo
            if rol == "SuperAdmin":
                op_rol = ["Operativo", "Coordinador", "SuperAdmin"]
                u_emp = st.text_input("🏢 Asignar a Clínica / Empresa", placeholder="Ej: Clínica San Lucas", help="Escribe el nombre de la empresa a la que pertenece. (No dejar en blanco)")
            else:
                op_rol = ["Operativo", "Coordinador"]
                u_emp = mi_empresa
                st.info(f"🏢 Agregando personal a tu empresa: **{u_emp}**")
                
            u_rl = st.selectbox("Poder / Rol", op_rol)
            
            if st.form_submit_button("Habilitar Acceso", width="stretch"):
                if u_id and u_pw and u_emp: # Se valida que la empresa no esté vacía
                    id_limpio = u_id.strip().lower()
                    pw_limpia = u_pw.strip()
                    empresa_limpia = u_emp.strip()
                    
                    st.session_state["usuarios_db"][id_limpio] = {
                        "pass": pw_limpia, 
                        "nombre": u_nm.strip(), 
                        "rol": u_rl, 
                        "titulo": u_ti, 
                        "empresa": empresa_limpia, 
                        "matricula": u_mt.strip()
                    }
                    guardar_datos()
                    st.success(f"¡{u_nm} habilitado/a correctamente para {empresa_limpia}!")
                    st.rerun()
                else:
                    st.error("⚠️ El Usuario, Clave y Empresa son obligatorios.")

# 8. AUDITORÍA
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría de Movimientos")
        if st.session_state["logs_db"]:
            st.dataframe(pd.DataFrame(st.session_state["logs_db"]))
