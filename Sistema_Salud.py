import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from urllib.parse import quote
import unicodedata
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. CONFIGURACIÓN CRUCIAL ---
URL_HOJA_CALCULO = "PEGA_AQUI_TU_URL_DE_GOOGLE_SHEETS"

st.set_page_config(page_title="MediCare Pro Elite", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- BÚSQUEDA IA ---
def normalizar_texto(texto):
    if not texto: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').lower()

# --- MOTOR DE PDF ---
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except:
    FPDF_DISPONIBLE = False

# --- CSS MEJORADO ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    :root { --primary: #3b82f6; --success: #10b981; --danger: #ef4444; --bg-card: rgba(255,255,255,0.05); }
    .hce-card { background: var(--bg-card); padding: 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; }
    .turno-caja { background: rgba(16,185,129,0.1); padding: 15px; border-radius: 10px; border-left: 5px solid var(--success); display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;}
    .btn-whatsapp { background: #25D366; color: white !important; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: 600; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- PERSISTENCIA DE DATOS ---
DB_FILE = "medicare_base_datos.json"

def guardar_datos():
    data = {k: st.session_state[k] for k in ["usuarios_db", "pacientes_db", "directorio_pacientes_db", "detalles_pacientes_db", "problemas_db", "indicaciones_db", "vitales_db", "insumos_db", "visitas_db", "turnos_db", "evoluciones_db", "facturacion_db"]}
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = pd.DataFrame([json.dumps(data, ensure_ascii=False)])
        conn.update(spreadsheet=URL_HOJA_CALCULO, data=df_nube)
    except Exception as e:
        st.error(f"⚠️ Error Nube: {e}")
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def cargar_datos():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df_nube = conn.read(spreadsheet=URL_HOJA_CALCULO, worksheet="0", ttl=0)
        if not df_nube.empty:
            return json.loads(df_nube.iloc[0, 0])
    except: pass
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- INICIALIZAR BASE ---
db_inicial = cargar_datos()
if db_inicial:
    for k, v in db_inicial.items(): st.session_state[k] = v

claves = ["usuarios_db", "pacientes_db", "directorio_pacientes_db", "detalles_pacientes_db", "problemas_db", "indicaciones_db", "vitales_db", "insumos_db", "visitas_db", "turnos_db", "evoluciones_db", "facturacion_db"]
for c in claves:
    if c not in st.session_state:
        if c == "usuarios_db": st.session_state[c] = {"admin": {"pass": "1234", "rol": "Administrador", "nombre": "Admin Maestro", "matricula": "ADM-00"}}
        elif c in ["directorio_pacientes_db", "detalles_pacientes_db"]: st.session_state[c] = {}
        else: st.session_state[c] = []

# --- LOGIN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False
if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<div class='hce-card' style='text-align:center;'><h1>⚕️</h1><h2>MediCare Pro Elite</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Entrar", use_container_width=True):
                if u in st.session_state["usuarios_db"] and st.session_state["usuarios_db"][u]["pass"] == p:
                    st.session_state["logeado"] = True; st.session_state.update(st.session_state["usuarios_db"][u]); st.rerun()
                else: st.error("Acceso denegado.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### 🩺 {st.session_state.get('nombre', 'Usuario')}")
    st.caption(f"Rol: {st.session_state.get('rol', 'S/D')} | Mat: {st.session_state.get('matricula', 'S/D')}")
    st.divider()
    paciente_actual = st.selectbox("Seleccionar Paciente:", st.session_state["pacientes_db"]) if st.session_state["pacientes_db"] else None
    
    if paciente_actual:
        dp = st.session_state["detalles_pacientes_db"].get(paciente_actual, {})
        st.info(f"DNI: {dp.get('dni','-')}\n\nNac: {dp.get('fnac','-')}\n\nPeso: {dp.get('peso','-')}kg | Alt: {dp.get('altura','-')}cm")

    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state.clear(); st.rerun()

st.title("MediCare: Gestión Clínica")
tabs = st.tabs(["👤 Admisión", "📅 Agenda", "📊 Clínica", "📝 Evolución", "💊 Recetario", "💳 Caja", "🗄️ PDF", "🤖 IA", "⚙️ Ajustes"])

# 1. ADMISIÓN
with tabs[0]:
    with st.form("adm"):
        n = st.text_input("Nombre y Apellido")
        o = st.text_input("Obra Social")
        t = st.text_input("WhatsApp")
        c1, c2, c3 = st.columns(3)
        dni = c1.text_input("DNI")
        fnac = c2.date_input("Fecha Nacimiento")
        sexo = c3.selectbox("Sexo", ["Femenino", "Masculino", "Otro"])
        c4, c5 = st.columns(2)
        peso = c4.number_input("Peso (kg)", 0.0)
        altura = c5.number_input("Altura (cm)", 0.0)
        
        if st.form_submit_button("Registrar / Actualizar"):
            if n and o:
                nombre_id = f"{n} ({o})"
                if nombre_id not in st.session_state["pacientes_db"]: st.session_state["pacientes_db"].append(nombre_id)
                st.session_state["directorio_pacientes_db"][nombre_id] = t
                st.session_state["detalles_pacientes_db"][nombre_id] = {"dni": dni, "fnac": fnac.strftime("%d/%m/%Y"), "sexo": sexo, "peso": peso, "altura": altura}
                guardar_datos(); st.success("Datos Guardados"); st.rerun()

# 2. AGENDA
with tabs[1]:
    with st.form("turno"):
        f = st.date_input("Fecha")
        h = st.time_input("Hora")
        m = st.text_input("Motivo")
        if st.form_submit_button("Agendar Cita"):
            st.session_state["turnos_db"].append({"paciente": paciente_actual, "fecha": str(f), "hora": str(h), "motivo": m})
            guardar_datos(); st.success("Cita Agendada")
    for cita in reversed(st.session_state["turnos_db"]):
        tel = st.session_state["directorio_pacientes_db"].get(cita['paciente'], "")
        st.markdown(f"<div class='turno-caja'><div><b>{cita['fecha']} {cita['hora']}</b><br>{cita['paciente']}</div><a href='https://wa.me/{tel}' class='btn-whatsapp'>Enviar WA</a></div>", unsafe_allow_html=True)

# 3. CLÍNICA / TRIAGE
with tabs[2]:
    c1, c2 = st.columns([1, 2])
    with c1:
        ta = st.text_input("Tensión Arterial", "120/80")
        fc = st.number_input("Frec. Cardíaca", 40, 200, 75)
        sa = st.number_input("Sat. Oxígeno %", 50, 100, 98)
        temp = st.number_input("Temperatura (°C)", 34.0, 42.0, 36.5)
        if st.button("Guardar Signos Vitales", type="primary"):
            st.session_state["vitales_db"].append({"paciente": paciente_actual, "TA": ta, "FC": fc, "Sat": sa, "Temp": temp, "hora": datetime.now().strftime("%d/%m %H:%M")})
            guardar_datos(); st.rerun()
    with c2:
        v_data = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_actual]
        if len(v_data) > 1:
            st.plotly_chart(px.line(pd.DataFrame(v_data), x="hora", y=["FC", "Sat", "Temp"], markers=True))

# 4. EVOLUCIÓN
with tabs[3]:
    txt = st.text_area("Evolución Médica / Notas de Enfermería:")
    if st.button("Firmar Nota", type="primary"):
        st.session_state["evoluciones_db"].append({"paciente": paciente_actual, "nota": txt, "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "firma": st.session_state.get("nombre", "Usuario")})
        guardar_datos(); st.success("Nota guardada"); st.rerun()
    for e in reversed([e for e in st.session_state["evoluciones_db"] if e["paciente"] == paciente_actual]):
        firma_real = e.get('firma', e.get('profesional', e.get('autor', 'Desconocido')))
        st.info(f"**{e['fecha']}** | {e.get('nota','')} (Firma: {firma_real})")

# 5. RECETAS
with tabs[4]:
    c1, c2 = st.columns(2)
    med = c1.text_input("Medicamento")
    dosis = c2.text_input("Dosis / Frecuencia (ej: cada 8hs)")
    if st.button("Generar Receta", type="primary"):
        st.session_state["indicaciones_db"].append({"paciente": paciente_actual, "med": f"{med} - {dosis}", "fecha": datetime.now().strftime("%d/%m/%Y")})
        guardar_datos(); st.rerun()
    for rec in reversed([r for r in st.session_state["indicaciones_db"] if r["paciente"] == paciente_actual]):
        st.markdown(f"<div class='hce-card'>💊 <b>{rec.get('fecha','')}</b>: {rec.get('med', '')}</div>", unsafe_allow_html=True)

# 6. CAJA
with tabs[5]:
    c_serv = st.text_input("Práctica / Servicio")
    c_monto = st.number_input("Monto $", 0)
    if st.button("Generar Cobro", type="primary"):
        st.session_state["facturacion_db"].append({"paciente": paciente_actual, "serv": c_serv, "monto": c_monto, "fecha": datetime.now().strftime("%d/%m/%Y")})
        guardar_datos(); st.success("Cobro Registrado")
    for f in reversed([f for f in st.session_state["facturacion_db"] if f["paciente"] == paciente_actual]):
        servicio = f.get('serv', f.get('practica', 'Servicio Médico'))
        st.download_button(f"Ticket: {servicio} (${f['monto']})", f"BOLETA MEDICARE\nFecha: {f.get('fecha','')}\nPaciente: {f['paciente']}\nServicio: {servicio}\nTotal: ${f['monto']}", file_name="boleta.txt")

# 7. GENERADOR DE PDF PROFESIONAL
with tabs[6]:
    st.subheader("📄 Exportar Historia Clínica a PDF")
    if not paciente_actual:
        st.warning("Seleccione un paciente para generar su PDF.")
    elif not FPDF_DISPONIBLE:
        st.error("Instale la librería ejecutando: pip install fpdf")
    else:
        def armar_pdf_completo(paciente):
            pdf = FPDF()
            pdf.add_page()
            def txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')
            
            # Título
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt(f"HISTORIA CLÍNICA"), ln=True, align="C")
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, txt(paciente.upper()), ln=True, align="C")
            pdf.ln(5)
            
            # Datos Personales
            dp = st.session_state["detalles_pacientes_db"].get(paciente, {})
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("1. DATOS PERSONALES"), ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 6, txt(f"DNI: {dp.get('dni','-')} | Nacimiento: {dp.get('fnac','-')} | Sexo: {dp.get('sexo','-')}"), ln=True)
            pdf.cell(0, 6, txt(f"Peso: {dp.get('peso','-')} kg | Altura: {dp.get('altura','-')} cm"), ln=True)
            pdf.ln(5)
            
            # Signos Vitales
            sv = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente]
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("2. ÚLTIMOS SIGNOS VITALES"), ln=True)
            pdf.set_font("Arial", '', 10)
            if sv:
                for v in sv[-5:]:
                    pdf.cell(0, 6, txt(f"[{v.get('hora','')}] TA: {v.get('TA','-')} | FC: {v.get('FC','-')} | Sat: {v.get('Sat','-')}% | Temp: {v.get('Temp','-')}°C"), ln=True)
            else: pdf.cell(0, 6, txt("Sin registros."), ln=True)
            pdf.ln(5)
            
            # Evoluciones
            evols = [e for e in st.session_state["evoluciones_db"] if e["paciente"] == paciente]
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("3. EVOLUCIONES MÉDICAS Y ENFERMERÍA"), ln=True)
            pdf.set_font("Arial", '', 10)
            if evols:
                for e in evols:
                    firma = e.get('firma', e.get('profesional', 'Desconocido'))
                    pdf.multi_cell(0, 6, txt(f"[{e.get('fecha','')}] Por {firma}: {e.get('nota','')}"))
                    pdf.ln(2)
            else: pdf.cell(0, 6, txt("Sin registros."), ln=True)
            pdf.ln(5)
            
            # Recetas
            recs = [r for r in st.session_state["indicaciones_db"] if r["paciente"] == paciente]
            pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, txt("4. RECETARIO HISTÓRICO"), ln=True)
            pdf.set_font("Arial", '', 10)
            if recs:
                for r in recs: pdf.cell(0, 6, txt(f"- {r.get('fecha','')} : {r.get('med','')}"), ln=True)
            else: pdf.cell(0, 6, txt("Sin registros."), ln=True)
            
            return pdf.output(dest="S").encode("latin-1")
            
        pdf_bytes = armar_pdf_completo(paciente_actual)
        st.download_button(label="📥 Descargar Historia Clínica PDF", data=pdf_bytes, file_name=f"HCE_{paciente_actual}.pdf", mime="application/pdf", type="primary")

# 8. BÚSQUEDA IA
with tabs[7]:
    busq = st.text_input("🔍 Buscar término en historia clínica:")
    if busq:
        q = normalizar_texto(busq)
        for e in st.session_state["evoluciones_db"]:
            if q in normalizar_texto(e.get("nota","")): st.write(f"Encontrado en fecha {e.get('fecha','')}: {e.get('nota','')}")

# 9. AJUSTES
with tabs[8]:
    st.subheader("Control de Usuarios")
    with st.form("nuevo_u"):
        c1, c2 = st.columns(2)
        un = c1.text_input("Nuevo Usuario (Login)")
        up = c2.text_input("Nueva Clave", type="password")
        c3, c4 = st.columns(2)
        unom = c3.text_input("Nombre Completo")
        umat = c4.text_input("Matrícula (MP/MN)")
        urol = st.selectbox("Rol", ["Médico", "Enfermero", "Kinesiólogo", "Administrativo"])
        
        if st.form_submit_button("Crear / Actualizar Usuario"):
            if un and up and unom:
                st.session_state["usuarios_db"][un] = {"pass": up, "nombre": unom, "rol": urol, "matricula": umat}
                guardar_datos(); st.success("Usuario Creado exitosamente"); st.rerun()
            else:
                st.error("⚠️ Usuario, Clave y Nombre son obligatorios.")
                
    st.divider()
    st.write("**Personal Activo en el Sistema:**")
    for usr, data in st.session_state["usuarios_db"].items():
        st.write(f"👤 **{data.get('nombre', usr)}** - {data.get('rol', 'S/D')} (Mat: {data.get('matricula', 'S/D')})")
