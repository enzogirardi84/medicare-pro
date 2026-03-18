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

# --- FECHAS PARA EL CALENDARIO ---
hoy = datetime.today()
hace_110_anios = datetime(hoy.year - 110, 1, 1)

# --- LISTA DE DROGAS ---
LISTA_DROGAS = ["Adrenalina", "Amiodarona", "Amoxicilina", "Ampicilina/Sulbactam", "Ceftriaxona", "Clonazepam", "Dexametasona", "Diazepam", "Diclofenac", "Dipirona (Metamizol)", "Enalapril", "Furosemida", "Haloperidol", "Hidrocortisona", "Ibuprofeno", "Ketorolaco", "Lorazepam", "Losartan", "Metoclopramida", "Morfina", "Omeprazol", "Ondansetron", "Paracetamol", "Salbutamol", "Tramadol"]

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
    :root { --primary: #3b82f6; --success: #10b981; --warning: #f59e0b; --danger: #ef4444; --bg-card: rgba(255,255,255,0.05); }
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

# 1. ADMISIÓN (CON CALENDARIO ARREGLADO)
with tabs[0]:
    with st.form("adm"):
        n = st.text_input("Nombre y Apellido")
        o = st.text_input("Obra Social")
        t = st.text_input("WhatsApp")
        c1, c2, c3 = st.columns(3)
        dni = c1.text_input("DNI")
        # El calendario ahora tiene min_value y max_value
        fnac = c2.date_input("Fecha Nacimiento", value=hoy, min_value=hace_110_anios, max_value=hoy)
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

# 3. CLÍNICA / TRIAGE (SISTEMA COMPLETO)
with tabs[2]:
    c1, c2 = st.columns([1, 1.5])
    with c1:
        with st.form("form_vitales"):
            col_v1, col_v2 = st.columns(2)
            ta = col_v1.text_input("Tensión Arterial", value="120/80")
            temp = col_v2.number_input("Temp (°C)", value=36.5, step=0.1)
            fc = col_v1.number_input("FC (lpm)", value=75)
            fr = col_v2.number_input("FR (rpm)", value=16)
            sa = col_v1.number_input("SatO2 (%)", value=98)
            hgt = col_v2.number_input("HGT (mg/dl)", value=90)
            
            # Lógica de Triage
            nivel_triage = "🟢 VERDE (Atención Estándar)"
            color_triage = "var(--success)"
            try:
                sist = int(ta.split("/")[0]) if "/" in ta else 120
                diast = int(ta.split("/")[1]) if "/" in ta else 80
            except: sist, diast = 120, 80

            if sa < 90 or sist > 200 or fc > 130 or fc < 40 or temp >= 40.0:
                nivel_triage = "🔴 ROJO (Emergencia)"; color_triage = "var(--danger)"
            elif sa < 94 or sist > 180 or diast > 110 or temp >= 38.5 or fc > 110 or fr > 24:
                nivel_triage = "🟠 AMARILLO (Urgencia)"; color_triage = "var(--warning)"
                
            st.markdown(f"<div style='background-color: {color_triage}; color: white; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 15px;'>{nivel_triage}</div>", unsafe_allow_html=True)
            
            if st.form_submit_button("Guardar Signos Vitales", type="primary", use_container_width=True):
                st.session_state["vitales_db"].append({"paciente": paciente_actual, "TA": ta, "FC": fc, "FR": fr, "Sat": sa, "Temp": temp, "HGT": hgt, "Triage": nivel_triage, "hora": datetime.now().strftime("%d/%m %H:%M")})
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

# 5. RECETARIO (SISTEMA COMPLETO RESTAURADO)
with tabs[4]:
    st.markdown("<div class='hce-card'>", unsafe_allow_html=True)
    opciones_droga = sorted(LISTA_DROGAS) + ["➕ Otro"]
    col_r1, col_r2 = st.columns([2, 1])
    droga_seleccionada = col_r1.selectbox("Medicamento", opciones_droga)
    droga_final = col_r1.text_input("Manualmente:", key="droga_manual") if droga_seleccionada == "➕ Otro" else droga_seleccionada
        
    dosis_mg = col_r2.text_input("Concentración (ej: 40mg)")
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.5])
    cant = col_d1.number_input("Cantidad", min_value=0.1, value=1.0)
    formato = col_d2.selectbox("Formato", ["ampolla(s)", "comprimido(s)", "gotas", "ml"])
    v = col_d3.selectbox("A través de", ["Vía Oral", "Intravenosa (EV)", "Intramuscular (IM)", "Subcutánea"])
    
    col_f1, col_f2 = st.columns(2)
    frec = col_f1.selectbox("Frecuencia", ["Cada 8 horas", "Cada 12 horas", "Cada 24 horas", "Dosis Única", "SOS"])
    dias = col_f2.number_input("Duración (Días)", min_value=1, value=7) if frec not in ["Dosis Única", "SOS"] else 0
    duracion_texto = f"durante {dias} día(s)" if dias > 0 else "(Aplicación Única)"
        
    if st.button("Emitir Indicación Médica", type="primary", use_container_width=True):
        if droga_final.strip() and dosis_mg.strip(): 
            prescripcion = f"{droga_final} {dosis_mg} - {cant} {formato} por {v}. Frecuencia: {frec} {duracion_texto}."
            if dias > 0: prescripcion += f" [Vence: {(datetime.now() + timedelta(days=dias)).strftime('%d/%m/%Y')}]"
            st.session_state["indicaciones_db"].append({"paciente": paciente_actual, "med": prescripcion, "fecha": datetime.now().strftime('%d/%m/%Y %H:%M'), "profesional": st.session_state.get("nombre", "Usuario")})
            guardar_datos(); st.success("Procesado."); st.rerun()
    st.divider()
    for i in reversed([ind for ind in st.session_state["indicaciones_db"] if ind["paciente"] == paciente_actual]): 
        st.markdown(f"<div class='turno-caja' style='border-left: 5px solid #3b82f6;'>💊 <b>{i.get('fecha','')}</b><br>{i.get('med', '')}<br><small>Por {i.get('profesional', '')}</small></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

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
                    pdf.cell(0, 6, txt(f"[{v.get('hora','')}] TA: {v.get('TA','-')} | FC: {v.get('FC','-')} | FR: {v.get('FR','-')} | Sat: {v.get('Sat','-')}% | Temp: {v.get('Temp','-')}°C | HGT: {v.get('HGT','-')}"), ln=True)
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
