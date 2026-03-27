import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import pytz
import urllib.parse
from supabase import create_client, Client
import io
import base64
import time
import os
import tempfile
from PIL import Image

# --- 1. CONFIGURACIÓN DE LIBRERÍAS ---
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

CANVAS_DISPONIBLE = False
try:
    from streamlit_drawable_canvas import st_canvas
    CANVAS_DISPONIBLE = True
except ImportError:
    CANVAS_DISPONIBLE = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MediCare Enterprise PRO V7.7", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- ZONA HORARIA ARGENTINA ---
ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')
def ahora():
    return datetime.now(ARG_TZ)

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 🎨 DISEÑO VISUAL ADAPTATIVO (CSS) ---
page_bg_css = """
<style>
.stApp {
    background-color: var(--background-color);
    background-image: radial-gradient(circle at top, var(--secondary-background-color) 0%, transparent 80%);
}
div[data-testid="stForm"] {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(150, 150, 150, 0.2);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }
.wa-btn {
    display: block; width: 100%; text-align: center; background-color: #25D366; 
    color: white !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none;
    margin-top: 10px; margin-bottom: 10px;
}
.wa-btn:hover { background-color: #128C7E; }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# --- 🎁 LOGO EXCLUSIVO ---
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
def cargar_datos():
    try:
        response = supabase.table('medicare_db').select('datos').eq('id', 1).execute()
        if response.data: return response.data[0]['datos']
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
    return None

def guardar_datos():
    claves = [
        "usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
        "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db", 
        "balance_db", "pediatria_db", "fotos_heridas_db",
        "agenda_db", "checkin_db", "inventario_db", "consumos_db", "nomenclador_db", "firmas_tactiles_db"
    ]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    try:
        supabase.table('medicare_db').upsert({"id": 1, "datos": data}).execute()
        st.toast("✅ Guardado exitosamente en la nube", icon="☁️")
    except Exception as e:
        st.error(f"⚠️ Error al subir a la nube: {e}")

# --- INICIALIZACIÓN ---
if "db_inicializada" not in st.session_state:
    db = cargar_datos()
    claves_base = {
        "usuarios_db": {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "matricula": "M.P 21947", "dni": "37108100", "titulo": "Director de Sistemas", "estado": "Activo", "pin": "1234"}},
        "pacientes_db": [], "detalles_pacientes_db": {}, "vitales_db": [], "indicaciones_db": [], "turnos_db": [], 
        "evoluciones_db": [], "facturacion_db": [], "logs_db": [], "balance_db": [], "pediatria_db": [], "fotos_heridas_db": [],
        "agenda_db": [], "checkin_db": [], "inventario_db": [], "consumos_db": [], "nomenclador_db": [], "firmas_tactiles_db": []
    }
    if db:
        for k, v in db.items(): st.session_state[k] = v
        for k, v in claves_base.items():
            if k not in st.session_state: st.session_state[k] = v
    else:
        for k, v in claves_base.items(): st.session_state[k] = v
    st.session_state["db_inicializada"] = True

# --- LOGIN Y RECUPERACIÓN ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False
if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise PRO V7.7</h2>", unsafe_allow_html=True)
        tab_login, tab_recuperar = st.tabs(["🔑 Iniciar Sesión", "🆘 Olvidé mi Contraseña"])
        with tab_login:
            with st.form("login", clear_on_submit=True):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar al Sistema", width="stretch"):
                    db_f = cargar_datos()
                    if db_f:
                        for k, v in db_f.items(): st.session_state[k] = v
                    u_limpio = u.strip().lower()
                    usuario_encontrado = None
                    for key_db in st.session_state["usuarios_db"].keys():
                        if key_db.strip().lower() == u_limpio:
                            usuario_encontrado = key_db; break
                    if usuario_encontrado:
                        user_data = st.session_state["usuarios_db"][usuario_encontrado]
                        if user_data.get("estado", "Activo") == "Bloqueado": st.error("🚫 Acceso suspendido.")
                        elif str(user_data["pass"]).strip() == p.strip():
                            st.session_state["u_actual"] = user_data; st.session_state["logeado"] = True
                            st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user_data["nombre"], "E": user_data["empresa"], "A": "Login"})
                            guardar_datos(); st.rerun()
                        else: st.error("Acceso denegado.")
                    else: st.error("Acceso denegado.")
        with tab_recuperar:
            with st.form("recover", clear_on_submit=True):
                st.info("Para crear una nueva contraseña, ingresá tu PIN de 4 dígitos:")
                rec_u = st.text_input("Usuario (Login)"); rec_emp = st.text_input("Empresa / Clínica asignada")
                rec_pin = st.text_input("PIN de Seguridad", type="password", max_chars=4)
                rec_pass = st.text_input("Nueva Contraseña", type="password")
                if st.form_submit_button("Cambiar Contraseña", width="stretch"):
                    db_f = cargar_datos()
                    if db_f:
                        for k, v in db_f.items(): st.session_state[k] = v
                    u_limpio = rec_u.strip().lower()
                    if u_limpio in st.session_state["usuarios_db"]:
                        user_data = st.session_state["usuarios_db"][u_limpio]
                        if user_data["empresa"].strip().lower() == rec_emp.strip().lower():
                            if str(user_data.get("pin", "")) == str(rec_pin).strip() and str(rec_pin).strip() != "":
                                if len(rec_pass) >= 4:
                                    st.session_state["usuarios_db"][u_limpio]["pass"] = rec_pass
                                    guardar_datos(); st.success("✅ Contraseña actualizada.")
                                else: st.error("⚠️ Contraseña mínima de 4 caracteres.")
                            else: st.error("❌ PIN incorrecto.")
                        else: st.error("❌ Empresa incorrecta.")
                    else: st.error("❌ Usuario no existe.")
    st.stop()

# --- CONTEXTO ---
user = st.session_state["u_actual"]
mi_empresa = user["empresa"]
rol = user["rol"]

# --- SIDEBAR ---
with st.sidebar:
    render_logo_eg(110)
    st.header(f"🏢 {mi_empresa}")
    st.write(f"👤 **{user['nombre']}** ({user['rol']})")
    st.divider()
    
    buscar = st.text_input("🔍 Buscar Paciente:")
    pacientes_visibles = st.session_state["pacientes_db"] if rol == "SuperAdmin" else [p for p in st.session_state["pacientes_db"] if st.session_state["detalles_pacientes_db"].get(p,{}).get("empresa") == mi_empresa]
    p_f = [p for p in pacientes_visibles if buscar.lower() in p.lower()]
    paciente_sel = st.selectbox("Seleccionar Paciente:", p_f) if p_f else None
    
    if paciente_sel and st.button("🔴 ELIMINAR PACIENTE", width="stretch"):
        st.session_state["pacientes_db"].remove(paciente_sel)
        del st.session_state["detalles_pacientes_db"][paciente_sel]
        st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user["nombre"], "E": mi_empresa, "A": f"Baja Paciente: {paciente_sel}"})
        guardar_datos(); st.rerun()

    st.divider()
    if st.button("Cerrar Sesión", width="stretch"): st.session_state["logeado"] = False; st.rerun()

# --- MENU DINÁMICO ---
menu = ["📍 Visitas", "📈 Dashboard", "👤 Admisión", "📅 Agenda", "📊 Clínica", "👶 Pediatría", "📝 Evolución", "💉 Materiales", "💊 Recetas", "⚖️ Balance", "📦 Inventario", "📚 Historial", "💳 Caja", "🗄️ PDF"]
if rol in ["SuperAdmin", "Coordinador"]: 
    menu.append("📋 Nomenclador")
    menu.append("⚙️ Mi Equipo")
if rol == "SuperAdmin": 
    menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 1. VISITAS (AHORA CON DIRECCIÓN REAL)
with tabs[menu.index("📍 Visitas")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral para registrar tu llegada.")
    else:
        st.subheader("⏱️ Fichada de Domicilio Legal")
        
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        dire = det.get("direccion", "Domicilio no registrado en Admisión")
        
        c_in, c_out = st.columns(2)
        if c_in.button("🟢 Registrar LLEGADA", use_container_width=True):
            st.session_state["checkin_db"].append({"paciente": paciente_sel, "profesional": user["nombre"], "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"), "tipo": f"ENTRADA en: {dire}", "empresa": mi_empresa})
            guardar_datos(); st.success("Llegada en domicilio registrada."); st.rerun()
        if c_out.button("🔴 Registrar SALIDA", use_container_width=True):
            st.session_state["checkin_db"].append({"paciente": paciente_sel, "profesional": user["nombre"], "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"), "tipo": f"SALIDA de: {dire}", "empresa": mi_empresa})
            guardar_datos(); st.success("Salida de domicilio registrada."); st.rerun()
            
        chk_pac = [c for c in st.session_state["checkin_db"] if c["paciente"] == paciente_sel]
        if chk_pac: st.dataframe(pd.DataFrame(chk_pac).drop(columns=["paciente", "empresa"]).tail(5), use_container_width=True)

        st.divider()
        te = det.get("telefono", "")
        if dire and dire != "Domicilio no registrado en Admisión":
            mapa_html = f'<iframe width="100%" height="300" src="https://maps.google.com/maps?q={urllib.parse.quote(dire)}&z=15&output=embed"></iframe>'
            st.components.v1.html(mapa_html, height=300)
        if te:
            num_limpio = ''.join(filter(str.isdigit, str(te)))
            if len(num_limpio) >= 10: num_limpio = "549" + num_limpio[-10:]
            msg = urllib.parse.quote(f"Hola, soy {user['nombre']} de {mi_empresa}. Estoy en camino al domicilio.")
            st.markdown(f'<a href="https://wa.me/{num_limpio}?text={msg}" target="_blank" class="wa-btn">📲 AVISAR WHATSAPP</a>', unsafe_allow_html=True)

# 2. DASHBOARD
with tabs[menu.index("📈 Dashboard")]:
    st.markdown(f"<h3 style='color: #3b82f6;'>📈 Panel de Gestión - {mi_empresa}</h3>", unsafe_allow_html=True)
    if not pacientes_visibles: st.warning("No hay pacientes cargados.")
    else:
        df_evs = pd.DataFrame(st.session_state["evoluciones_db"])
        if not df_evs.empty:
            df_evs["fecha_c"] = pd.to_datetime(df_evs["fecha"], format="%d/%m/%Y %H:%M")
            hace_una_semana = (ahora() - timedelta(days=7)).replace(tzinfo=None)
            if rol == "Coordinador":
                pacs_mi_empresa = [p for p in st.session_state["detalles_pacientes_db"] if st.session_state["detalles_pacientes_db"][p]['empresa'] == mi_empresa]
                df_evs = df_evs[df_evs['paciente'].isin(pacs_mi_empresa)]
            df_evs_s = df_evs[df_evs["fecha_c"] > hace_una_semana]
            if not df_evs_s.empty:
                perf_enf = df_evs_s["firma"].value_counts().reset_index()
                perf_enf.columns = ["Profesional", "Visitas"]
                st.bar_chart(perf_enf.set_index("Profesional")["Visitas"], color="#3b82f6")

# 3. ADMISIÓN 
with tabs[menu.index("👤 Admisión")]:
    with st.form("adm_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("Nombre y Apellido"); o = col_b.text_input("Obra Social")
        d = col_a.text_input("DNI del Paciente"); f_nac = col_b.date_input("Nacimiento", value=date(2000, 1, 1))
        col_c, col_d = st.columns(2)
        se = col_c.selectbox("Sexo", ["F", "M"]); tel = col_d.text_input("WhatsApp (Ej: 3584302024)")
        dir_p = st.text_input("Dirección Exacta (Para el PDF)")
        emp_d = st.text_input("Empresa", value=mi_empresa) if rol == "SuperAdmin" else mi_empresa
        if st.form_submit_button("Habilitar Paciente", width="stretch"):
            if n and d and emp_d: 
                id_p = f"{n} ({o}) - {emp_d.strip()}"
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "sexo": se, "telefono": tel, "direccion": dir_p, "empresa": emp_d.strip()}
                guardar_datos(); st.rerun()

# 4. AGENDA 
with tabs[menu.index("📅 Agenda")]:
    with st.form("agenda_form", clear_on_submit=True):
        if pacientes_visibles:
            c1, c2 = st.columns(2)
            pac_ag = c1.selectbox("Paciente a visitar", pacientes_visibles)
            profesionales = [v['nombre'] for k, v in st.session_state["usuarios_db"].items() if v['empresa'] == mi_empresa or rol == "SuperAdmin"]
            prof_ag = c2.selectbox("Asignar Profesional", profesionales)
            c3, c4 = st.columns(2)
            fecha_ag = c3.date_input("Fecha programada"); hora_ag = c4.time_input("Hora aproximada")
            if st.form_submit_button("Agendar Visita"):
                st.session_state["agenda_db"].append({"paciente": pac_ag, "profesional": prof_ag, "fecha": fecha_ag.strftime("%d/%m/%Y"), "hora": hora_ag.strftime("%H:%M"), "empresa": mi_empresa, "estado": "Pendiente"})
                guardar_datos(); st.success("✅ Turno agendado."); st.rerun()
    st.divider()
    agenda_mia = [a for a in st.session_state["agenda_db"] if a["empresa"] == mi_empresa]
    if agenda_mia: st.dataframe(pd.DataFrame(agenda_mia), use_container_width=True)

# 5. CLÍNICA
with tabs[menu.index("📊 Clínica")]:
    if paciente_sel:
        vits = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_sel]
        if vits:
            u = vits[-1]; c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("T.A.", u.get("TA", "-")); c2.metric("F.C.", f"{u.get('FC', '-')} lpm"); c3.metric("F.R.", f"{u.get('FR', '-')} rpm")
            c4.metric("SatO2", f"{u.get('Sat', '-')}%"); c5.metric("Temp", f"{u.get('Temp', '-')} °C"); c6.metric("HGT", u.get("HGT", "-"))
        with st.form("vitales_f", clear_on_submit=True):
            ta = st.text_input("Tensión Arterial (TA)", "120/80")
            col_signos = st.columns(5)
            fc = col_signos[0].number_input("F.C.", 30, 200, 75); fr = col_signos[1].number_input("F.R.", 10, 50, 16)
            sat = col_signos[2].number_input("SatO2%", 50, 100, 98); temp = col_signos[3].number_input("Temp °C", 35.0, 42.0, 36.5)
            hgt = col_signos[4].text_input("HGT", "100")
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "FR": fr, "Sat": sat, "Temp": temp, "HGT": hgt, "fecha": ahora().strftime("%d/%m/%Y %H:%M")})
                guardar_datos()
                alerta_disparada = False
                if fc > 110: st.error(f"🚨 ALERTA ROJA: Taquicardia severa detectada (FC: {fc})."); alerta_disparada = True
                elif fc < 50: st.error(f"🚨 ALERTA ROJA: Bradicardia detectada (FC: {fc})."); alerta_disparada = True
                if sat < 90: st.error(f"🚨 ALERTA ROJA: Desaturación crítica (SatO2: {sat}%)."); alerta_disparada = True
                if temp > 38.0: st.warning(f"⚠️ ALERTA AMARILLA: Paciente febril (Temp: {temp}°C)."); alerta_disparada = True
                if not alerta_disparada: st.rerun()

# 6. PEDIATRÍA 
with tabs[menu.index("👶 Pediatría")]:
    if paciente_sel:
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        se = det.get("sexo", "F"); f_n_str = det.get("fnac", "01/01/2000")
        f_n = pd.to_datetime(f_n_str, format="%d/%m/%Y")
        eda_meses = round((ahora().replace(tzinfo=None) - f_n).days / 30.4375, 1)
        with st.form("pedia", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            pes = col_a.number_input("Peso Actual (kg)", min_value=0.0, format="%.2f")
            tal = col_b.number_input("Talla Actual (cm)", min_value=0.0, format="%.2f")
            pc = col_a.number_input("Périm. Cefálico (cm)", min_value=0.0, format="%.2f")
            desc = col_b.text_input("Descripción / Nota")
            if st.form_submit_button("Guardar Control", width="stretch"):
                imc = round(pes / ((tal/100)**2), 2) if tal > 0 else 0
                percentil_sug = ""
                if se == "F": percentil_sug = "⚖️ P3 - Bajo Peso" if imc < 14 else "⚖️ P50 - Peso Normal" if imc < 18 else "⚠️ P97 - Sobrepeso"
                else: percentil_sug = "⚖️ P3 - Bajo Peso" if imc < 14.5 else "⚖️ P50 - Peso Normal" if imc < 18.5 else "⚠️ P97 - Sobrepeso"
                st.session_state["pediatria_db"].append({"paciente": paciente_sel, "fecha": ahora().strftime("%d/%m/%Y"), "edad_meses": eda_meses, "peso": pes, "talla": tal, "pc": pc, "imc": imc, "percentil_sug": percentil_sug, "firma": user["nombre"]})
                guardar_datos(); st.rerun()
        ped = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
        if ped:
            df_g = pd.DataFrame(ped).set_index("fecha")
            c1, c2 = st.columns(2)
            if "peso" in df_g.columns: c1.line_chart(df_g["peso"], color="#3b82f6")
            if "talla" in df_g.columns: c2.line_chart(df_g["talla"], color="#10b981")

# 7. EVOLUCIÓN (LÍMPIA)
with tabs[menu.index("📝 Evolución")]:
    if paciente_sel:
        if CANVAS_DISPONIBLE:
            st.markdown("##### ✍️ Firma Digital del Paciente/Familiar en Pantalla")
            canvas_result = st_canvas(fill_color="rgba(255, 255, 255, 1)", stroke_width=2, stroke_color="#000000", background_color="#ffffff", height=150, width=400, drawing_mode="freedraw", key="canvas_firma")
            if st.button("Guardar Firma Digital", width="stretch"):
                if canvas_result.image_data is not None:
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    buf = io.BytesIO()
                    bg.save(buf, format="PNG")
                    b64_firma = base64.b64encode(buf.getvalue()).decode('utf-8')
                    st.session_state["firmas_tactiles_db"].append({"paciente": paciente_sel, "fecha": ahora().strftime("%d/%m/%Y"), "firma_img": b64_firma})
                    guardar_datos(); st.success("✅ Firma táctil registrada e inyectada al PDF.")
        
        st.divider()
        with st.form("evol", clear_on_submit=True):
            nota = st.text_area("Nota médica pura:")
            desc_w = st.text_input("Descripción de la herida (Opcional)")
            with st.expander("📷 Tomar Foto de la Herida", expanded=False): foto_w = st.camera_input("Foto")
            
            if st.form_submit_button("Firmar y Guardar Evolución", width="stretch"):
                if nota:
                    fecha_n = ahora().strftime("%d/%m/%Y %H:%M")
                    st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": fecha_n, "firma": user["nombre"]})
                    if foto_w:
                        base64_foto = base64.b64encode(foto_w.getvalue()).decode('utf-8')
                        st.session_state["fotos_heridas_db"].append({"paciente": paciente_sel, "fecha": fecha_n, "descripcion": desc_w, "base64_foto": base64_foto, "firma": user["nombre"]})
                    guardar_datos(); st.rerun()

# 8. MATERIALES Y DESCARTABLES
with tabs[menu.index("💉 Materiales")]:
    if paciente_sel:
        st.subheader("Registro de Materiales Descartables")
        with st.form("form_mat", clear_on_submit=True):
            inv_mi_empresa = [i for i in st.session_state["inventario_db"] if i["empresa"] == mi_empresa]
            if not inv_mi_empresa:
                st.warning("⚠️ No hay insumos en el inventario. Cargalos primero en la pestaña 'Inventario'.")
                st.form_submit_button("Registrar Consumo", disabled=True)
            else:
                c1, c2 = st.columns([3, 1])
                insumo_sel = c1.selectbox("Seleccionar Insumo Utilizado", [i["item"] for i in inv_mi_empresa])
                cant_usada = c2.number_input("Cantidad", min_value=1, value=1)
                
                if st.form_submit_button("Registrar Consumo", width="stretch"):
                    for i in st.session_state["inventario_db"]:
                        if i["item"] == insumo_sel and i["empresa"] == mi_empresa:
                            if i["stock"] >= cant_usada:
                                i["stock"] -= cant_usada
                            else:
                                st.warning(f"⚠️ Stock insuficiente. El stock de {insumo_sel} quedará negativo.")
                                i["stock"] -= cant_usada
                            break
                    st.session_state["consumos_db"].append({"paciente": paciente_sel, "insumo": insumo_sel, "cantidad": cant_usada, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                    guardar_datos(); st.success(f"✅ {cant_usada}x {insumo_sel} registrado y descontado del stock."); st.rerun()
                    
        cons_paciente = [c for c in st.session_state["consumos_db"] if c["paciente"] == paciente_sel]
        if cons_paciente:
            st.divider()
            st.caption("Últimos materiales registrados:")
            st.dataframe(pd.DataFrame(cons_paciente).drop(columns="paciente"), use_container_width=True)

# 9. RECETAS
with tabs[menu.index("💊 Recetas")]:
    if paciente_sel:
        with st.form("recet", clear_on_submit=True):
            d = st.text_input("Medicamento")
            lista_vias = ["Oral", "Endovenosa (EV)", "Intramuscular (IM)", "Subcutánea (SC)", "Sublingual", "Tópica", "Inhalatoria", "Oftálmica", "Ótica", "Nasal", "Rectal", "Vaginal"]
            p = st.selectbox("Vía de Administración", lista_vias)
            f = st.number_input("Días de tratamiento", 1, 30, 7)
            if st.form_submit_button("Cargar Terapéutica", width="stretch"):
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": f"{d} vía {p} por {f} días.", "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()

# 10. BALANCE HÍDRICO
with tabs[menu.index("⚖️ Balance")]:
    if paciente_sel:
        with st.form("bal", clear_on_submit=True):
            c1, c2 = st.columns(2)
            c1.markdown("#### Ingresos (ml)"); i1 = c1.number_input("Oral", 0, step=100); i2 = c1.number_input("Parenteral", 0, step=100)
            c2.markdown("#### Egresos (ml)"); e1 = c2.number_input("Orina", 0, step=100); e2 = c2.number_input("Drenajes", 0, step=100); e3 = c2.number_input("Pérdidas Insensibles", 0, step=100)
            if st.form_submit_button("Calcular Shift", width="stretch"):
                ting = i1+i2; tegr = e1+e2+e3; bal = ting-tegr
                st.session_state["balance_db"].append({"paciente": paciente_sel, "ingresos": ting, "egresos": tegr, "balance": bal, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()

# 11. INVENTARIO 
with tabs[menu.index("📦 Inventario")]:
    with st.form("form_inv", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        nuevo_item = c1.text_input("Nombre del Insumo (Ej: Gasas 10x10)")
        cantidad_ini = c2.number_input("Cantidad a agregar", min_value=1, value=10)
        if st.form_submit_button("Actualizar Stock", width="stretch"):
            if nuevo_item:
                encontrado = False
                for i in st.session_state["inventario_db"]:
                    if i["item"].lower() == nuevo_item.strip().lower() and i["empresa"] == mi_empresa:
                        i["stock"] += cantidad_ini; encontrado = True; break
                if not encontrado:
                    st.session_state["inventario_db"].append({"item": nuevo_item.strip().title(), "stock": cantidad_ini, "empresa": mi_empresa})
                guardar_datos(); st.rerun()
    st.divider()
    inv_mio = [i for i in st.session_state["inventario_db"] if i["empresa"] == mi_empresa]
    if inv_mio: 
        st.dataframe(pd.DataFrame(inv_mio).drop(columns="empresa"), use_container_width=True)
        col_del1, col_del2 = st.columns([3,1])
        del_item = col_del1.selectbox("Seleccionar insumo a eliminar", [i["item"] for i in inv_mio])
        if col_del2.button("Eliminar Insumo", use_container_width=True):
            st.session_state["inventario_db"] = [i for i in st.session_state["inventario_db"] if not (i["item"] == del_item and i["empresa"] == mi_empresa)]
            guardar_datos(); st.rerun()

# 12. HISTORIAL COMPLETO
with tabs[menu.index("📚 Historial")]:
    if paciente_sel:
        st.subheader(f"📚 Historia Clínica Digital: {paciente_sel}")
        with st.expander("⏱️ Auditoría de Presencia (Check-in/Out)", expanded=True):
            chks = [x for x in st.session_state["checkin_db"] if x["paciente"] == paciente_sel]
            if chks: st.dataframe(pd.DataFrame(chks).drop(columns=["paciente", "empresa"]), use_container_width=True)
        with st.expander("📝 Procedimientos y Evoluciones"):
            evs = [x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]
            if evs:
                for e in reversed(evs): st.info(f"📅 **{e['fecha']}** | {e['firma']}\n\n{e['nota']}")
        with st.expander("💉 Materiales Utilizados"):
            cons = [x for x in st.session_state["consumos_db"] if x["paciente"] == paciente_sel]
            if cons: st.dataframe(pd.DataFrame(cons).drop(columns=["paciente"]), use_container_width=True)
            else: st.write("No hay consumos registrados.")
        with st.expander("📸 Registro de Heridas"):
            fot_her = [x for x in st.session_state["fotos_heridas_db"] if x["paciente"] == paciente_sel]
            if fot_her:
                for fh in reversed(fot_her):
                    st.success(f"📅 **{fh['fecha']}** | {fh['firma']}\n\nDescripción: {fh['descripcion']}")
                    st.image(base64.b64decode(fh['base64_foto']), caption=f"Herida: {fh['descripcion']}")
        with st.expander("📊 Signos Vitales"):
            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == paciente_sel]
            if vits: st.dataframe(pd.DataFrame(vits).drop(columns="paciente"), use_container_width=True)
        with st.expander("👶 Control Pediátrico"):
            peds = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
            if peds: st.dataframe(pd.DataFrame(peds).drop(columns="paciente"), use_container_width=True)
        with st.expander("⚖️ Balance Hídrico"):
            blp = [x for x in st.session_state["balance_db"] if x["paciente"] == paciente_sel]
            if blp:
                dfb = pd.DataFrame(blp).drop(columns="paciente")
                for c in ["ingresos", "egresos", "balance"]: dfb[c] = dfb[c].astype(str)+" ml"
                st.dataframe(dfb, use_container_width=True)
        with st.expander("💊 Plan Terapéutico (Recetas)"):
            recs = [x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]
            if recs:
                for r in reversed(recs): st.success(f"📌 **{r['fecha']}** | Indicado por: **{r['firma']}**\n\n{r['med']}")

# 13. CAJA
with tabs[menu.index("💳 Caja")]:
    if paciente_sel:
        nom_empresa = [n for n in st.session_state["nomenclador_db"] if n["empresa"] == mi_empresa]
        with st.form("caja_form", clear_on_submit=True):
            if nom_empresa:
                opciones = [f"{n['codigo']} - {n['descripcion']} (${n['valor']})" for n in nom_empresa]
                practica_sel = st.selectbox("Seleccionar Práctica del Nomenclador", opciones)
                precio_sug = float(practica_sel.split("($")[1].replace(")", ""))
                mon = st.number_input("Monto a Facturar", value=float(precio_sug))
                serv_desc = practica_sel.split(" - ")[1].split(" ($")[0]
            else:
                serv_desc = st.text_input("Servicio / Práctica"); mon = st.number_input("Monto", 0.0)
            if st.form_submit_button("Registrar Cobro / Práctica", width="stretch"):
                if serv_desc:
                    st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv_desc, "monto": mon, "fecha": ahora().strftime("%d/%m/%Y"), "empresa": mi_empresa})
                    guardar_datos(); st.rerun()
        st.divider()
        if rol in ["SuperAdmin", "Coordinador"]:
            df_caja = pd.DataFrame([f for f in st.session_state["facturacion_db"] if f.get("empresa", "") == mi_empresa])
            if not df_caja.empty:
                st.dataframe(df_caja.drop(columns="empresa"))
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer: df_caja.drop(columns="empresa").to_excel(writer, index=False, sheet_name='Caja_MediCare')
                st.download_button("📥 DESCARGAR CAJA A EXCEL", data=output.getvalue(), file_name=f"Caja_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 14. PDF 
with tabs[menu.index("🗄️ PDF")]:
    if paciente_sel and FPDF_DISPONIBLE:
        def t(txt): return str(txt).replace('⚖️', '').replace('⚠️', '').replace('📌', '').replace('📅', '').replace('📸', '').encode('latin-1', 'replace').decode('latin-1')

        def crear_pdf_pro(p):
            pdf = FPDF(); pdf.add_page()
            pdf.set_fill_color(59, 130, 246); pdf.ellipse(10, 10, 22, 22, 'F'); pdf.set_draw_color(255, 255, 255); pdf.set_line_width(1.2)
            pdf.line(21, 14, 21, 28); pdf.line(14, 21, 28, 21)
            emp_paciente = st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa", mi_empresa)
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(38, 14); pdf.cell(0, 10, t(emp_paciente), ln=True)
            pdf.set_font("Arial", 'I', 9); pdf.set_xy(38, 20); pdf.cell(0, 10, t("Historia Clinica Digital Integral (Pro V7.7)"), ln=True); pdf.ln(15)
            
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, t(f" PACIENTE: {p}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 6, t(f" DNI: {det.get('dni','S/D')} | Nacimiento: {det.get('fnac','S/D')} | Sexo: {det.get('sexo','S/D')}"), ln=True)
            pdf.cell(0, 6, t(f" Domicilio: {det.get('direccion','S/D')}"), ln=True); pdf.ln(5)

            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == p]
            if vits:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("SIGNOS VITALES:"), ln=True); pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
                pdf.cell(30, 6, "FECHA", 1, 0, 'C', True); pdf.cell(20, 6, "TA", 1, 0, 'C', True); pdf.cell(20, 6, "FC", 1, 0, 'C', True); pdf.cell(20, 6, "FR", 1, 0, 'C', True); pdf.cell(20, 6, "SAT%", 1, 0, 'C', True); pdf.cell(20, 6, "TEMP", 1, 0, 'C', True); pdf.cell(20, 6, "HGT", 1, 1, 'C', True)
                pdf.set_font("Arial", '', 8)
                for v in vits:
                    pdf.cell(30, 6, t(v.get('fecha','')), 1, 0, 'C'); pdf.cell(20, 6, t(v.get('TA','')), 1, 0, 'C'); pdf.cell(20, 6, str(v.get('FC','')), 1, 0, 'C')
                    pdf.cell(20, 6, str(v.get('FR','')), 1, 0, 'C'); pdf.cell(20, 6, str(v.get('Sat','')), 1, 0, 'C'); pdf.cell(20, 6, str(v.get('Temp','')), 1, 0, 'C'); pdf.cell(20, 6, t(v.get('HGT','')), 1, 1, 'C')
                pdf.ln(4)

            evs = [x for x in st.session_state["evoluciones_db"] if x["paciente"] == p]
            if evs:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("EVOLUCIONES CLINICAS:"), ln=True)
                for ev in evs:
                    pdf.set_font("Arial", 'B', 8); pdf.cell(0, 5, t(f"[{ev.get('fecha','')}] - Firma: {ev.get('firma','')}"), ln=True)
                    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 5, t(ev.get('nota','')), 'L'); pdf.ln(2)

            cons = [x for x in st.session_state["consumos_db"] if x["paciente"] == p]
            if cons:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("MATERIALES DESCARTABLES UTILIZADOS:"), ln=True)
                for c in cons:
                    pdf.set_font("Arial", '', 9); pdf.cell(0, 5, t(f"[{c['fecha']}] {c['cantidad']}x {c['insumo']} - Registrado por: {c['firma']}"), ln=True)
                pdf.ln(4)

            chks = [x for x in st.session_state["checkin_db"] if x["paciente"] == p]
            if chks:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("AUDITORIA DE PRESENCIA EN DOMICILIO (Llegada/Salida):"), ln=True)
                pdf.set_font("Arial", '', 8)
                for c in chks:
                    pdf.multi_cell(0, 5, t(f"[{c['fecha_hora']}] {c['tipo']} | Por: {c['profesional']}"), align='L')
                pdf.ln(4)

            pdf.ln(10); y_firma = pdf.get_y()
            pdf.line(10, y_firma, 80, y_firma)
            pdf.set_font("Arial", 'B', 9); pdf.set_xy(10, y_firma + 2)
            pdf.cell(70, 5, t(f"Firma Profesional: {user['nombre']}"), ln=2)
            pdf.cell(70, 5, t(f"Matricula: {user.get('matricula', 'S/D')}"), ln=0)
            
            firmas_paciente = [x for x in st.session_state.get("firmas_tactiles_db", []) if x["paciente"] == p]
            if firmas_paciente:
                ultima_firma = firmas_paciente[-1]["firma_img"]
                if ultima_firma != "Firma Guardada Exitosamente":
                    try:
                        img_data = base64.b64decode(ultima_firma)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(img_data); tmp_path = tmp.name
                        pdf.image(tmp_path, x=130, y=y_firma - 15, w=40)
                        os.remove(tmp_path)
                    except Exception as e: pass

            nombre_paciente = p.split(" (")[0] 
            pdf.line(120, y_firma, 190, y_firma); pdf.set_xy(120, y_firma + 2)
            pdf.cell(70, 5, t("Conformidad Paciente / Familiar"), ln=2)
            pdf.cell(70, 5, t(f"Aclaracion: {nombre_paciente}"), ln=2)
            pdf.cell(70, 5, t(f"DNI: {det.get('dni', 'S/D')}"), ln=0)
            return pdf.output(dest='S').encode('latin-1')

        def crear_consentimiento_pdf(p):
            pdf = FPDF(); pdf.add_page()
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            emp_paciente = det.get("empresa", mi_empresa); nombre_paciente = p.split(" (")[0]
            
            pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, t("CONSENTIMIENTO INFORMADO DE INTERNACION DOMICILIARIA"), ln=True, align='C'); pdf.ln(10)
            pdf.set_font("Arial", '', 11)
            texto_legal = f"""Por la presente, yo {nombre_paciente}, con DNI {det.get('dni', 'S/D')}, con domicilio en {det.get('direccion', 'S/D')}, declaro haber sido informado/a por el personal de la empresa {emp_paciente} sobre los alcances, modalidades y pautas del servicio de internación / cuidado domiciliario que voy a recibir.

Comprendo que la atencion domiciliaria requiere de la colaboracion activa del grupo familiar y declaro mi total conformidad para que el personal de salud (medicos, enfermeros, kinesiologos, etc.) ingrese a mi domicilio para realizar las practicas establecidas en el plan terapeutico.

Asimismo, entiendo que los registros clinicos seran resguardados en formato digital a traves de la plataforma MediCare Enterprise PRO, autorizando el procesamiento de mis datos de salud segun las normativas vigentes."""
            pdf.multi_cell(0, 7, t(texto_legal)); pdf.ln(30)
            
            y_firma = pdf.get_y()
            firmas_paciente = [x for x in st.session_state.get("firmas_tactiles_db", []) if x["paciente"] == p]
            if firmas_paciente:
                ultima_firma = firmas_paciente[-1]["firma_img"]
                if ultima_firma != "Firma Guardada Exitosamente":
                    try:
                        img_data = base64.b64decode(ultima_firma)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(img_data); tmp_path = tmp.name
                        pdf.image(tmp_path, x=85, y=y_firma - 15, w=40)
                        os.remove(tmp_path)
                    except Exception as e: pass

            pdf.line(60, y_firma, 150, y_firma); pdf.set_xy(60, y_firma + 2)
            pdf.set_font("Arial", 'B', 10); pdf.cell(90, 5, t("Firma del Paciente / Responsable"), ln=2, align='C')
            pdf.cell(90, 5, t(f"Aclaracion: {nombre_paciente}"), ln=2, align='C')
            pdf.cell(90, 5, t(f"DNI: {det.get('dni', 'S/D')}"), ln=2, align='C')
            pdf.cell(90, 5, t(f"Fecha: {ahora().strftime('%d/%m/%Y')}"), ln=0, align='C')
            return pdf.output(dest='S').encode('latin-1')

        st.download_button("📥 1. Generar Historia Clínica en PDF", crear_pdf_pro(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")
        st.download_button("📄 2. Descargar Consentimiento Informado Legal", crear_consentimiento_pdf(paciente_sel), f"Consentimiento_{paciente_sel}.pdf", "application/pdf")

# 15. NOMENCLADOR 
if "📋 Nomenclador" in menu:
    with tabs[menu.index("📋 Nomenclador")]:
        st.subheader("Configuración de Códigos y Valores")
        with st.form("nom_form", clear_on_submit=True):
            col_1, col_2, col_3 = st.columns([1, 2, 1])
            n_cod = col_1.text_input("Código (Ej: 01.01)"); n_desc = col_2.text_input("Descripción de la Práctica")
            n_val = col_3.number_input("Valor ($)", min_value=0.0); n_os = st.text_input("Obra Social Asociada (Opcional)")
            if st.form_submit_button("Guardar / Actualizar", width="stretch"):
                if n_cod and n_desc:
                    encontrado = False
                    for n in st.session_state["nomenclador_db"]:
                        if n["codigo"].strip() == n_cod.strip() and n["empresa"] == mi_empresa:
                            n["descripcion"] = n_desc.strip(); n["valor"] = n_val; n["obra_social"] = n_os.strip(); encontrado = True; break
                    if not encontrado: st.session_state["nomenclador_db"].append({"codigo": n_cod.strip(), "descripcion": n_desc.strip(), "valor": n_val, "obra_social": n_os.strip(), "empresa": mi_empresa})
                    guardar_datos(); st.rerun()
        st.divider()
        nom_mio = [n for n in st.session_state["nomenclador_db"] if n["empresa"] == mi_empresa]
        if nom_mio: 
            st.dataframe(pd.DataFrame(nom_mio).drop(columns="empresa"), use_container_width=True)
            col_del1, col_del2 = st.columns([3,1])
            del_nom = col_del1.selectbox("Seleccionar código a eliminar", [n["codigo"] + " - " + n["descripcion"] for n in nom_mio])
            if col_del2.button("Eliminar Práctica", use_container_width=True):
                cod_to_del = del_nom.split(" - ")[0]
                st.session_state["nomenclador_db"] = [n for n in st.session_state["nomenclador_db"] if not (n["codigo"] == cod_to_del and n["empresa"] == mi_empresa)]
                guardar_datos(); st.rerun()

# 16. EQUIPO Y SUSCRIPCIONES
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"Gestión de Personal - {mi_empresa}")
        with st.form("equipo", clear_on_submit=True):
            col_id, col_pw, col_pin = st.columns([2, 2, 1])
            u_id = col_id.text_input("Usuario (Login)"); u_pw = col_pw.text_input("Clave"); u_pin = col_pin.text_input("PIN (4 Nros)", max_chars=4)
            u_nm = st.text_input("Nombre Completo")
            col_dni, col_mt = st.columns(2); u_dni = col_dni.text_input("DNI del Profesional"); u_mt = col_mt.text_input("Matrícula")
            u_ti = st.selectbox("Título", ["Médico/a", "Lic. en Enfermería", "Enfermero/a", "Kinesiólogo/a", "Fonoaudiólogo/a", "Nutricionista", "Psicólogo/a", "Acompañante Terapéutico", "Trabajador/a Social", "Administrativo/a", "Otro"])
            u_emp = st.text_input("🏢 Asignar a Clínica / Empresa") if rol == "SuperAdmin" else mi_empresa
            u_rl = st.selectbox("Rol", ["Operativo", "Coordinador", "SuperAdmin"] if rol == "SuperAdmin" else ["Operativo", "Coordinador"])
            if st.form_submit_button("Habilitar Acceso", width="stretch"):
                if u_id and u_pw and u_pin and u_dni:
                    st.session_state["usuarios_db"][u_id.strip().lower()] = { "pass": u_pw.strip(), "nombre": u_nm.strip(), "rol": u_rl, "titulo": u_ti, "empresa": u_emp.strip(), "matricula": u_mt.strip(), "dni": u_dni.strip(), "estado": "Activo", "pin": u_pin.strip()}
                    guardar_datos(); st.rerun()
        st.divider(); st.subheader("👥 Control de Accesos")
        for u, d in list({k: v for k, v in st.session_state["usuarios_db"].items() if v["empresa"] == mi_empresa or rol == "SuperAdmin"}.items()):
            if u == "admin": continue
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"🏢 {d['empresa']} | 👤 {d['nombre']} | Login: `{u}` | PIN: `{d.get('pin', 'S/D')}` | Estado: **{d.get('estado', 'Activo')}**")
            if rol == "SuperAdmin":
                if d.get("estado", "Activo") == "Activo" and c2.button("⏸️ Suspender", key=f"susp_{u}"): st.session_state["usuarios_db"][u]["estado"] = "Bloqueado"; guardar_datos(); st.rerun()
                elif d.get("estado", "Activo") != "Activo" and c2.button("▶️ Reactivar", key=f"reac_{u}"): st.session_state["usuarios_db"][u]["estado"] = "Activo"; guardar_datos(); st.rerun()
            if c3.button("❌ Bajar", key=f"del_{u}"): del st.session_state["usuarios_db"][u]; guardar_datos(); st.rerun()

# 17. AUDITORÍA
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría de Movimientos")
        df_logs = pd.DataFrame(st.session_state["logs_db"])
        st.dataframe(df_logs)
        if not df_logs.empty:
            out_logs = io.BytesIO()
            with pd.ExcelWriter(out_logs, engine='openpyxl') as writer: df_logs.to_excel(writer, index=False, sheet_name='Logs_MediCare')
            st.download_button("📥 DESCARGAR LOGS A EXCEL", data=out_logs.getvalue(), file_name=f"Reporte_Logs_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- FIN DEL SISTEMA MEDICARE PRO V7.7 ---
