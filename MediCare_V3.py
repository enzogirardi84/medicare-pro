import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import pytz
import urllib.parse
from supabase import create_client, Client
import io
import base64

# --- 1. CONFIGURACIÓN DE LIBRERÍAS (PDF Y FOTOS) ---
FPDF_DISPONIBLE = False
try:
    from fpdf import FPDF
    FPDF_DISPONIBLE = True
except ImportError:
    FPDF_DISPONIBLE = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MediCare Enterprise PRO", page_icon="⚕️", layout="wide")
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
input[type=number]::-webkit-outer-spin-button { 
    -webkit-appearance: none; 
    margin: 0; 
}
input[type=number] {
    -moz-appearance: textfield;
}
.wa-btn {
    display: block; width: 100%; text-align: center; background-color: #25D366; 
    color: white !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none;
    margin-top: 10px; margin-bottom: 10px;
}
.wa-btn:hover { background-color: #128C7E; }
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
def cargar_datos():
    try:
        response = supabase.table('medicare_db').select('datos').eq('id', 1).execute()
        if response.data: return response.data[0]['datos']
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
    return None

def guardar_datos():
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db", "balance_db", "pediatria_db", "fotos_heridas_db"]
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
        "usuarios_db": {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "matricula": "M.P 21947", "titulo": "Director de Sistemas", "estado": "Activo", "pin": "1234"}},
        "pacientes_db": [], "detalles_pacientes_db": {}, "vitales_db": [], "indicaciones_db": [], "turnos_db": [], 
        "evoluciones_db": [], "facturacion_db": [], "logs_db": [], "balance_db": [], "pediatria_db": [], "fotos_heridas_db": []
    }
    if db:
        for k, v in db.items(): st.session_state[k] = v
        for k, v in claves_base.items():
            if k not in st.session_state: st.session_state[k] = v
    else:
        for k, v in claves_base.items(): st.session_state[k] = v
    st.session_state["db_inicializada"] = True

# --- LOGIN Y RECUPERACIÓN DE CONTRASEÑA ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False
if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise PRO</h2>", unsafe_allow_html=True)
        
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
                            usuario_encontrado = key_db
                            break
                    
                    if usuario_encontrado:
                        user_data = st.session_state["usuarios_db"][usuario_encontrado]
                        if user_data.get("estado", "Activo") == "Bloqueado":
                            st.error("🚫 Acceso suspendido por fin de prueba o falta de pago.")
                        elif str(user_data["pass"]).strip() == p.strip():
                            st.session_state["u_actual"] = user_data
                            st.session_state["logeado"] = True
                            st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user_data["nombre"], "E": user_data["empresa"], "A": "Login"})
                            guardar_datos()
                            st.rerun()
                        else: st.error("Acceso denegado: Usuario o contraseña incorrectos.")
                    else: st.error("Acceso denegado: Usuario o contraseña incorrectos.")
        
        with tab_recuperar:
            with st.form("recover", clear_on_submit=True):
                st.info("Para crear una nueva contraseña, ingresá tu PIN de Seguridad de 4 dígitos:")
                rec_u = st.text_input("Usuario (Login)")
                rec_emp = st.text_input("Empresa / Clínica asignada")
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
                            pin_guardado = str(user_data.get("pin", ""))
                            if pin_guardado == str(rec_pin).strip() and pin_guardado != "":
                                if len(rec_pass) >= 4:
                                    st.session_state["usuarios_db"][u_limpio]["pass"] = rec_pass
                                    guardar_datos()
                                    st.success("✅ Contraseña actualizada correctamente. ¡Ya podés iniciar sesión!")
                                else:
                                    st.error("⚠️ La nueva contraseña debe tener al menos 4 caracteres.")
                            else:
                                st.error("❌ PIN de Seguridad incorrecto.")
                        else:
                            st.error("❌ La empresa no coincide con nuestros registros.")
                    else:
                        st.error("❌ El usuario no existe en el sistema.")
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
    
    if paciente_sel and st.button("🔴 DAR DE ALTA / ELIMINAR PACIENTE", width="stretch"):
        st.session_state["pacientes_db"].remove(paciente_sel)
        del st.session_state["detalles_pacientes_db"][paciente_sel]
        st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user["nombre"], "E": mi_empresa, "A": f"Baja Paciente: {paciente_sel}"})
        guardar_datos(); st.rerun()

    st.divider()
    
    with st.expander("🔒 Cambiar mi Contraseña (Interno)"):
        with st.form("cambio_pass", clear_on_submit=True):
            p_actual = st.text_input("Contraseña Actual", type="password")
            p_nueva = st.text_input("Nueva Contraseña", type="password")
            p_rep = st.text_input("Repetir Nueva Contraseña", type="password")
            if st.form_submit_button("Actualizar Clave", width="stretch"):
                u_key_actual = None
                for k, v in st.session_state["usuarios_db"].items():
                    if v["nombre"] == user["nombre"] and v["empresa"] == user["empresa"]:
                        u_key_actual = k
                        break
                if u_key_actual:
                    if p_actual == st.session_state["usuarios_db"][u_key_actual]["pass"]:
                        if p_nueva == p_rep and len(p_nueva) >= 4:
                            st.session_state["usuarios_db"][u_key_actual]["pass"] = p_nueva
                            guardar_datos()
                            st.success("✅ ¡Contraseña actualizada!")
                        else: st.error("⚠️ Claves no coinciden o son cortas.")
                    else: st.error("❌ Contraseña actual incorrecta.")

    if st.button("Cerrar Sesión", width="stretch"): st.session_state["logeado"] = False; st.rerun()

# --- MENU DINÁMICO ---
menu = ["📈 Dashboard", "👤 Admisión", "📊 Clínica", "👶 Pediatría", "📝 Evolución", "💊 Recetas", "⚖️ Balance", "📍 Visitas", "📚 Historial", "💳 Caja", "🗄️ PDF"]
if rol in ["SuperAdmin", "Coordinador"]: menu.append("⚙️ Mi Equipo")
if rol == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 0. DASHBOARD
with tabs[0]:
    st.markdown(f"<h3 style='color: #3b82f6;'>📈 Panel de Gestión - {mi_empresa}</h3>", unsafe_allow_html=True)
    if not pacientes_visibles: st.warning("No hay pacientes cargados.")
    else:
        st.markdown("#### Visitas por Profesional (Última Semana)")
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
            else: st.caption("No hubo visitas registradas.")

# 1. ADMISIÓN 
with tabs[1]:
    st.subheader("Registrar Paciente")
    with st.form("adm_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("Nombre y Apellido"); o = col_b.text_input("Obra Social")
        d = col_a.text_input("DNI"); f_nac = col_b.date_input("Nacimiento", value=date(2000, 1, 1))
        
        col_c, col_d = st.columns(2)
        se = col_c.selectbox("Sexo", ["F", "M"])
        tel = col_d.text_input("WhatsApp (Ej: 3584302024)")
        
        dir_p = st.text_input("Dirección (Río Cuarto)")
        emp_d = st.text_input("Empresa", value=mi_empresa) if rol == "SuperAdmin" else mi_empresa
        
        if st.form_submit_button("Habilitar Paciente", width="stretch"):
            if n and d and emp_d: 
                id_p = f"{n} ({o}) - {emp_d.strip()}"
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "sexo": se, "telefono": tel, "direccion": dir_p, "empresa": emp_d.strip()}
                guardar_datos(); st.rerun()

# 2. CLÍNICA 
with tabs[2]:
    if paciente_sel:
        vits = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_sel]
        if vits:
            u = vits[-1]; 
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("T.A.", u.get("TA", "-"))
            c2.metric("F.C.", f"{u.get('FC', '-')} lpm")
            c3.metric("F.R.", f"{u.get('FR', '-')} rpm")
            c4.metric("SatO2", f"{u.get('Sat', '-')}%")
            c5.metric("Temp", f"{u.get('Temp', '-')} °C")
            c6.metric("HGT", u.get("HGT", "-"))
            
        with st.form("vitales_f", clear_on_submit=True):
            ta = st.text_input("Tensión Arterial (TA)", "120/80")
            col_signos = st.columns(5)
            fc = col_signos[0].number_input("F.C.", 30, 200, 75)
            fr = col_signos[1].number_input("F.R.", 10, 50, 16)
            sat = col_signos[2].number_input("SatO2%", 50, 100, 98)
            temp = col_signos[3].number_input("Temp °C", 35.0, 42.0, 36.5)
            hgt = col_signos[4].text_input("HGT", "100")
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "FR": fr, "Sat": sat, "Temp": temp, "HGT": hgt, "fecha": ahora().strftime("%d/%m/%Y %H:%M")})
                guardar_datos(); st.rerun()

# 3. PEDIATRÍA 
with tabs[3]:
    if paciente_sel:
        st.markdown("<h3 style='color: #10b981;'>👶 Crecimiento y Control</h3>", unsafe_allow_html=True)
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
                if se == "F":
                    if imc < 14: percentil_sug = "⚖️ P3 - Bajo Peso"
                    elif imc < 18: percentil_sug = "⚖️ P50 - Peso Normal"
                    else: percentil_sug = "⚠️ P97 - Sobrepeso"
                else:
                    if imc < 14.5: percentil_sug = "⚖️ P3 - Bajo Peso"
                    elif imc < 18.5: percentil_sug = "⚖️ P50 - Peso Normal"
                    else: percentil_sug = "⚠️ P97 - Sobrepeso"

                st.session_state["pediatria_db"].append({"paciente": paciente_sel, "fecha": ahora().strftime("%d/%m/%Y"), "edad_meses": eda_meses, "peso": pes, "talla": tal, "pc": pc, "imc": imc, "percentil_sug": percentil_sug, "firma": user["nombre"]})
                guardar_datos(); st.rerun()
        
        ped = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
        if ped:
            u_p = ped[-1]; c1, c2, c3 = st.columns(3)
            c1.metric("IMC", u_p.get("imc", "S/D"))
            c2.metric("⚖️ Percentil Sugerido", u_p.get("percentil_sug", "S/D"))
            c3.write(f"Edad al control: {u_p.get('edad_meses', 'S/D')} meses")
            df_g = pd.DataFrame(ped).set_index("fecha")
            c1, c2 = st.columns(2)
            if "peso" in df_g.columns: c1.caption("Curva de Peso (kg)"); c1.line_chart(df_g["peso"], color="#3b82f6")
            if "talla" in df_g.columns: c2.caption("Curva de Talla (cm)"); c2.line_chart(df_g["talla"], color="#10b981")

# 4. EVOLUCIÓN
with tabs[4]:
    if paciente_sel:
        st.subheader("Cargar Evolución / Heridas")
        with st.form("evol", clear_on_submit=True):
            nota = st.text_area("Nota clínica:")
            desc_w = st.text_input("Descripción de la herida (Opcional)")
            with st.expander("📷 Tomar Foto de la Herida", expanded=False):
                st.caption("Se pedirá permiso para usar la cámara.")
                foto_w = st.camera_input("Foto")
            if st.form_submit_button("Firmar y Guardar Nota"):
                if nota:
                    fecha_n = ahora().strftime("%d/%m/%Y %H:%M")
                    st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": fecha_n, "firma": user["nombre"]})
                    if foto_w:
                        base64_foto = base64.b64encode(foto_w.getvalue()).decode('utf-8')
                        st.session_state["fotos_heridas_db"].append({"paciente": paciente_sel, "fecha": fecha_n, "descripcion": desc_w, "base64_foto": base64_foto, "firma": user["nombre"]})
                    guardar_datos(); st.rerun()

# 5. RECETAS
with tabs[5]:
    if paciente_sel:
        with st.form("recet", clear_on_submit=True):
            d = st.text_input("Medicamento")
            lista_vias = [
                "Oral", "Endovenosa (EV)", "Intramuscular (IM)", "Subcutánea (SC)", 
                "Sublingual", "Tópica", "Inhalatoria", "Oftálmica", "Ótica", 
                "Nasal", "Rectal", "Vaginal"
            ]
            p = st.selectbox("Vía de Administración", lista_vias)
            f = st.number_input("Días de tratamiento", 1, 30, 7)
            if st.form_submit_button("Cargar Terapéutica", width="stretch"):
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": f"{d} vía {p} por {f} días.", "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()

# 6. BALANCE HÍDRICO
with tabs[6]:
    if paciente_sel:
        st.markdown("<h3 style='color: #3b82f6;'>⚖️ Control Estricto (ml)</h3>", unsafe_allow_html=True)
        with st.form("bal", clear_on_submit=True):
            c1, c2 = st.columns(2)
            c1.markdown("#### Ingresos (ml)"); i1 = c1.number_input("Oral", 0, step=100); i2 = c1.number_input("Parenteral", 0, step=100)
            c2.markdown("#### Egresos (ml)"); e1 = c2.number_input("Orina", 0, step=100); e2 = c2.number_input("Drenajes", 0, step=100); e3 = c2.number_input("Pérdidas Insensibles", 0, step=100)
            if st.form_submit_button("Calcular Shift"):
                ting = i1+i2; tegr = e1+e2+e3; bal = ting-tegr
                st.session_state["balance_db"].append({"paciente": paciente_sel, "ingresos": ting, "egresos": tegr, "balance": bal, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()

# 7. VISITAS Y GOOGLE MAPS (CON FILTRO INTELIGENTE DE WHATSAPP PARA ARGENTINA)
with tabs[7]:
    if paciente_sel:
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        dire = det.get("direccion", ""); te = det.get("telefono", "")
        if dire:
            st.info(f"🏠 **Domicilio:** {dire}")
            mapa_html = f'<iframe width="100%" height="300" src="https://maps.google.com/maps?q={urllib.parse.quote(dire)}&z=15&output=embed"></iframe>'
            st.components.v1.html(mapa_html, height=300)
        if te:
            # Filtro inteligente para Whatsapp Argentina
            num_limpio = ''.join(filter(str.isdigit, str(te)))
            if len(num_limpio) >= 10:
                # Nos quedamos con los últimos 10 dígitos (ignora el 0 o el 15 si los pusieron mal)
                num_limpio = "549" + num_limpio[-10:]
                
            msg = urllib.parse.quote(f"Hola, soy {user['nombre']} de {mi_empresa}. Estoy en camino al domicilio.")
            st.markdown(f'<a href="https://wa.me/{num_limpio}?text={msg}" target="_blank" class="wa-btn">📲 AVISAR WHATSAPP</a>', unsafe_allow_html=True)

# 8. HISTORIAL COMPLETO
with tabs[8]:
    if paciente_sel:
        st.subheader(f"📚 Historia Clínica Digital Integral: {paciente_sel}")
        
        with st.expander("📝 Procedimientos y Evoluciones", expanded=True):
            evs = [x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]
            if evs:
                for e in reversed(evs): st.info(f"📅 **{e['fecha']}** | {e['firma']}\n\n{e['nota']}")
            else: st.write("No hay procedimientos registrados.")
            
        with st.expander("📸 Registro de Heridas (Fotos)"):
            fot_her = [x for x in st.session_state["fotos_heridas_db"] if x["paciente"] == paciente_sel]
            if fot_her:
                for fh in reversed(fot_her):
                    st.success(f"📅 **{fh['fecha']}** | {fh['firma']}\n\nDescripción: {fh['descripcion']}")
                    st.image(base64.b64decode(fh['base64_foto']), caption=f"Herida: {fh['descripcion']}")
            else: st.write("No hay fotos registradas.")

        with st.expander("📊 Signos Vitales"):
            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == paciente_sel]
            if vits: st.dataframe(pd.DataFrame(vits).drop(columns="paciente"), use_container_width=True)
            else: st.write("No hay signos vitales registrados.")

        with st.expander("👶 Control Pediátrico"):
            peds = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
            if peds: st.dataframe(pd.DataFrame(peds).drop(columns="paciente"), use_container_width=True)
            else: st.write("No hay registros pediátricos.")
            
        with st.expander("⚖️ Balance Hídrico (ml)"):
            blp = [x for x in st.session_state["balance_db"] if x["paciente"] == paciente_sel]
            if blp:
                dfb = pd.DataFrame(blp).drop(columns="paciente")
                for c in ["ingresos", "egresos", "balance"]: dfb[c] = dfb[c].astype(str)+" ml"
                st.dataframe(dfb, use_container_width=True)
            else: st.write("No hay balances hídricos registrados.")

        with st.expander("💊 Plan Terapéutico (Recetas)"):
            recs = [x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]
            if recs:
                for r in reversed(recs): st.success(f"📌 **{r['fecha']}** | Indicado por: **{r['firma']}**\n\n{r['med']}")
            else: st.write("No hay indicaciones registradas.")

# 9. CAJA 
with tabs[9]:
    if paciente_sel:
        with st.form("caja_form", clear_on_submit=True):
            serv = st.text_input("Servicio"); mon = st.number_input("Monto", 0)
            if st.form_submit_button("Registrar Cobro", width="stretch"):
                st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mon, "fecha": ahora().strftime("%d/%m/%Y")})
                guardar_datos(); st.rerun()
        st.divider()
        if rol in ["SuperAdmin", "Coordinador"]:
            df_caja_completo = pd.DataFrame(st.session_state["facturacion_db"])
            if not df_caja_completo.empty:
                if rol == "Coordinador":
                    pacs_mi_empresa = [p for p in st.session_state["detalles_pacientes_db"] if st.session_state["detalles_pacientes_db"][p]['empresa'] == mi_empresa]
                    df_caja_completo = df_caja_completo[df_caja_completo['paciente'].isin(pacs_mi_empresa)]
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer: df_caja_completo.to_excel(writer, index=False, sheet_name='Caja_MediCare')
                st.download_button("📥 DESCARGAR CAJA A EXCEL", data=output.getvalue(), file_name=f"Caja_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 10. PDF (AHORA CON FIRMA LEGAL DEL PACIENTE)
with tabs[10]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf_pro(p):
            pdf = FPDF(); pdf.add_page()
            def t(txt): 
                txt = str(txt).replace('⚖️', '').replace('⚠️', '').replace('📌', '').replace('📅', '').replace('📸', '')
                return txt.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_fill_color(59, 130, 246); pdf.ellipse(10, 10, 22, 22, 'F'); pdf.set_draw_color(255, 255, 255); pdf.set_line_width(1.2)
            pdf.line(21, 14, 21, 28); pdf.line(14, 21, 28, 21)
            emp_paciente = st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa", mi_empresa)
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(38, 14); pdf.cell(0, 10, t(emp_paciente), ln=True)
            pdf.set_font("Arial", 'I', 9); pdf.set_xy(38, 20); pdf.cell(0, 10, t("Historia Clinica Digital Integral"), ln=True); pdf.ln(15)
            
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, t(f" PACIENTE: {p}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 6, t(f" DNI: {det.get('dni','S/D')} | Nacimiento: {det.get('fnac','S/D')} | Sexo: {det.get('sexo','S/D')} | WhatsApp: {det.get('telefono','S/D')}"), ln=True)
            pdf.cell(0, 6, t(f" Domicilio: {det.get('direccion','S/D')}"), ln=True); pdf.ln(5)

            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == p]
            if vits:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("SIGNOS VITALES:"), ln=True)
                pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
                pdf.cell(30, 6, "FECHA", 1, 0, 'C', True); pdf.cell(20, 6, "TA", 1, 0, 'C', True); pdf.cell(20, 6, "FC", 1, 0, 'C', True); pdf.cell(20, 6, "FR", 1, 0, 'C', True); pdf.cell(20, 6, "SAT%", 1, 0, 'C', True); pdf.cell(20, 6, "TEMP", 1, 0, 'C', True); pdf.cell(20, 6, "HGT", 1, 1, 'C', True)
                pdf.set_font("Arial", '', 8)
                for v in vits:
                    pdf.cell(30, 6, t(v.get('fecha','')), 1, 0, 'C')
                    pdf.cell(20, 6, t(v.get('TA','')), 1, 0, 'C')
                    pdf.cell(20, 6, str(v.get('FC','')), 1, 0, 'C')
                    pdf.cell(20, 6, str(v.get('FR','')), 1, 0, 'C')
                    pdf.cell(20, 6, str(v.get('Sat','')), 1, 0, 'C')
                    pdf.cell(20, 6, str(v.get('Temp','')), 1, 0, 'C')
                    pdf.cell(20, 6, t(v.get('HGT','')), 1, 1, 'C')
                pdf.ln(4)

            peds = [x for x in st.session_state["pediatria_db"] if x["paciente"] == p]
            if peds:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("CONTROL PEDIATRICO:"), ln=True)
                pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
                pdf.cell(30, 6, "FECHA", 1, 0, 'C', True); pdf.cell(25, 6, "PESO", 1, 0, 'C', True); pdf.cell(25, 6, "TALLA", 1, 0, 'C', True); pdf.cell(25, 6, "PC", 1, 0, 'C', True); pdf.cell(25, 6, "IMC", 1, 0, 'C', True); pdf.cell(60, 6, "PERCENTIL", 1, 1, 'C', True)
                pdf.set_font("Arial", '', 8)
                for pe in peds:
                    pdf.cell(30, 6, t(pe.get('fecha','')), 1, 0, 'C')
                    pdf.cell(25, 6, f"{pe.get('peso','')} kg", 1, 0, 'C')
                    pdf.cell(25, 6, f"{pe.get('talla','')} cm", 1, 0, 'C')
                    pdf.cell(25, 6, f"{pe.get('pc','')} cm", 1, 0, 'C')
                    pdf.cell(25, 6, str(pe.get('imc','')), 1, 0, 'C')
                    pdf.cell(60, 6, t(pe.get('percentil_sug','')), 1, 1, 'C')
                pdf.ln(4)

            bals = [x for x in st.session_state["balance_db"] if x["paciente"] == p]
            if bals:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("BALANCE HIDRICO (ml):"), ln=True)
                pdf.set_font("Arial", 'B', 8); pdf.set_fill_color(230, 230, 230)
                pdf.cell(40, 6, "FECHA / HORA", 1, 0, 'C', True); pdf.cell(40, 6, "INGRESOS", 1, 0, 'C', True); pdf.cell(40, 6, "EGRESOS", 1, 0, 'C', True); pdf.cell(40, 6, "BALANCE NETO", 1, 1, 'C', True)
                pdf.set_font("Arial", '', 8)
                for b in bals:
                    pdf.cell(40, 6, t(b.get('fecha','')), 1, 0, 'C')
                    pdf.cell(40, 6, f"+ {b.get('ingresos','')} ml", 1, 0, 'C')
                    pdf.cell(40, 6, f"- {b.get('egresos','')} ml", 1, 0, 'C')
                    pdf.cell(40, 6, f"{b.get('balance','')} ml", 1, 1, 'C')
                pdf.ln(4)

            recs = [x for x in st.session_state["indicaciones_db"] if x["paciente"] == p]
            if recs:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("PLAN TERAPEUTICO:"), ln=True)
                for r in recs:
                    pdf.set_font("Arial", 'B', 8); pdf.cell(0, 5, t(f"[{r.get('fecha','')}] - Firma: {r.get('firma','')}"), ln=True)
                    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 5, t(r.get('med','')), 'L'); pdf.ln(2)

            evs = [x for x in st.session_state["evoluciones_db"] if x["paciente"] == p]
            if evs:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("EVOLUCIONES CLINICAS:"), ln=True)
                for ev in evs:
                    pdf.set_font("Arial", 'B', 8); pdf.cell(0, 5, t(f"[{ev.get('fecha','')}] - Firma: {ev.get('firma','')}"), ln=True)
                    pdf.set_font("Arial", '', 9); pdf.multi_cell(0, 5, t(ev.get('nota','')), 'L'); pdf.ln(2)
            
            fot_her = [x for x in st.session_state["fotos_heridas_db"] if x["paciente"] == p]
            if fot_her:
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("REGISTRO FOTOGRAFICO DE HERIDAS:"), ln=True)
                for fh in fot_her:
                    pdf.set_font("Arial", 'B', 8); pdf.cell(0, 5, t(f"[{fh.get('fecha','')}] - Firma: {fh.get('firma','')}"), ln=True)
                    pdf.set_font("Arial", 'I', 9); pdf.multi_cell(0, 5, t(f"Descripcion: {fh.get('descripcion','')}. (Ver foto en el Historial Digital)."), 'L'); pdf.ln(2)

            # 6. FIRMAS LEGALES (PROFESIONAL Y PACIENTE)
            pdf.ln(15)
            y_firma = pdf.get_y()
            
            # Firma Profesional (Izquierda)
            pdf.line(10, y_firma, 80, y_firma)
            pdf.set_font("Arial", 'B', 9)
            pdf.set_xy(10, y_firma + 2)
            pdf.cell(70, 5, t(f"Firma Profesional: {user['nombre']}"), ln=2)
            pdf.cell(70, 5, t(f"Matricula: {user.get('matricula', 'S/D')}"), ln=0)
            
            # Firma Paciente (Derecha)
            nombre_paciente = p.split(" (")[0] # Extraemos solo el nombre del string
            pdf.line(120, y_firma, 190, y_firma)
            pdf.set_xy(120, y_firma + 2)
            pdf.cell(70, 5, t("Conformidad Paciente / Familiar"), ln=2)
            pdf.cell(70, 5, t(f"Aclaracion: {nombre_paciente}"), ln=2)
            pdf.cell(70, 5, t(f"DNI: {det.get('dni', 'S/D')}"), ln=0)
            
            return pdf.output(dest='S').encode('latin-1')

        st.download_button("📥 Generar Historia Clínica en PDF", crear_pdf_pro(paciente_sel), f"HC_{paciente_sel}.pdf", "application/pdf")

# 11. EQUIPO Y SUSCRIPCIONES
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"Gestión de Personal - {mi_empresa}")
        with st.form("equipo", clear_on_submit=True):
            col_id, col_pw, col_pin = st.columns([2, 2, 1])
            u_id = col_id.text_input("Usuario (Login)")
            u_pw = col_pw.text_input("Clave")
            u_pin = col_pin.text_input("PIN (4 Nros)", max_chars=4)
            
            u_nm = st.text_input("Nombre Completo")
            c3, c4 = st.columns(2)
            u_mt = c3.text_input("Matrícula")
            
            lista_titulos = [
                "Médico/a", "Lic. en Enfermería", "Enfermero/a", "Kinesiólogo/a", 
                "Fonoaudiólogo/a", "Nutricionista", "Psicólogo/a", "Acompañante Terapéutico", 
                "Trabajador/a Social", "Administrativo/a", "Otro"
            ]
            u_ti = c4.selectbox("Título", lista_titulos)
            
            if rol == "SuperAdmin": u_emp = st.text_input("🏢 Asignar a Clínica / Empresa")
            else: u_emp = mi_empresa; st.info(f"🏢 Agregando personal a tu empresa: **{u_emp}**")
            
            u_rl = st.selectbox("Rol", ["Operativo", "Coordinador", "SuperAdmin"] if rol == "SuperAdmin" else ["Operativo", "Coordinador"])
            
            if st.form_submit_button("Habilitar Acceso", width="stretch"):
                if u_id and u_pw and u_pin:
                    st.session_state["usuarios_db"][u_id.strip().lower()] = {
                        "pass": u_pw.strip(), "nombre": u_nm.strip(), "rol": u_rl, 
                        "titulo": u_ti, "empresa": u_emp.strip(), "matricula": u_mt.strip(), 
                        "estado": "Activo", "pin": u_pin.strip()
                    }
                    guardar_datos(); st.rerun()
                else:
                    st.error("⚠️ Por favor, completá todos los campos (incluyendo el PIN de 4 dígitos).")
        
        st.divider(); st.subheader("👥 Control de Accesos (Suscripciones)")
        usuarios_visibles = st.session_state["usuarios_db"] if rol == "SuperAdmin" else {k: v for k, v in st.session_state["usuarios_db"].items() if v["empresa"] == mi_empresa}
        for u, d in list(usuarios_visibles.items()):
            if u == "admin": continue
            c1, c2, c3 = st.columns([3, 1, 1])
            estado = d.get("estado", "Activo")
            c1.write(f"🏢 {d['empresa']} | 👤 {d['nombre']} | Login: `{u}` | PIN: `{d.get('pin', 'S/D')}` | Estado: **{estado}**")
            if rol == "SuperAdmin":
                if estado == "Activo":
                    if c2.button("⏸️ Suspender", key=f"susp_{u}"): st.session_state["usuarios_db"][u]["estado"] = "Bloqueado"; guardar_datos(); st.rerun()
                else:
                    if c2.button("▶️ Reactivar", key=f"reac_{u}"): st.session_state["usuarios_db"][u]["estado"] = "Activo"; guardar_datos(); st.rerun()
            if c3.button("❌ Bajar", key=f"del_{u}"): del st.session_state["usuarios_db"][u]; guardar_datos(); st.rerun()

# 12. AUDITORÍA
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría de Movimientos")
        df_logs = pd.DataFrame(st.session_state["logs_db"])
        st.dataframe(df_logs)
        if not df_logs.empty:
            out_logs = io.BytesIO()
            with pd.ExcelWriter(out_logs, engine='openpyxl') as writer: df_logs.to_excel(writer, index=False, sheet_name='Logs_MediCare')
            st.download_button("📥 DESCARGAR LOGS A EXCEL", data=out_logs.getvalue(), file_name=f"Reporte_Logs_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
