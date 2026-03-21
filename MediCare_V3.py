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
st.set_page_config(page_title="MediCare Enterprise PRO V4.0", page_icon="⚕️", layout="wide")
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

# --- 🎨 DISEÑO VISUAL ADAPTATIVO (CSS PARA ML Y LOOK CLÍNICO) ---
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
div[data-testid="stButton"] button {
    border-radius: 8px;
}
/* Ocultar flechas de number_input */
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { 
    -webkit-appearance: none; 
    margin: 0; 
}
input[type=number] {
    -moz-appearance: textfield;
}

/* Botones especiales */
.wa-btn {
    display: block; width: 100%; text-align: center; background-color: #25D366; 
    color: white !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none;
    margin-top: 10px; margin-bottom: 10px;
}
.wa-btn:hover { background-color: #128C7E; }
.xl-btn {
    display: block; width: 100%; text-align: center; background-color: #1D6F42; 
    color: white !important; padding: 10px; border-radius: 8px; font-weight: bold; text-decoration: none;
    margin-top: 10px; margin-bottom: 10px;
}
.xl-btn:hover { background-color: #155734; }
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
    # AGREGAMOS FOTOS_HERIDAS_DB A LA LISTA
    claves = ["usuarios_db", "pacientes_db", "detalles_pacientes_db", "vitales_db", 
              "indicaciones_db", "turnos_db", "evoluciones_db", "facturacion_db", "logs_db", "balance_db", "pediatria_db", "fotos_heridas_db"]
    data = {k: st.session_state[k] for k in claves if k in st.session_state}
    try:
        supabase.table('medicare_db').upsert({"id": 1, "datos": data}).execute()
        st.toast("✅ Base de datos sincronizada y protegida en la nube", icon="☁️")
    except Exception as e:
        st.error(f"⚠️ Error al subir a la nube: {e}")

# --- INICIALIZACIÓN BLINDADA ---
if "db_inicializada" not in st.session_state:
    db = cargar_datos()
    
    claves_base = {
        "usuarios_db": {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G.", "matricula": "M.P 21947", "titulo": "Director de Sistemas", "estado": "Activo"}},
        "pacientes_db": [], "detalles_pacientes_db": {}, "vitales_db": [], "indicaciones_db": [], "turnos_db": [], 
        "evoluciones_db": [], "facturacion_db": [], "logs_db": [], "balance_db": [], "pediatria_db": [], "fotos_heridas_db": [] # NUEVA TABLA
    }
    
    if db:
        for k, v in db.items(): st.session_state[k] = v
        for k, v in claves_base.items():
            if k not in st.session_state: st.session_state[k] = v
    else:
        for k, v in claves_base.items(): st.session_state[k] = v
            
    st.session_state["db_inicializada"] = True

# --- LOGIN (CON BLOQUEO POR SUSCRIPCIÓN) ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False
if not st.session_state["logeado"]:
    _, col, _ = st.columns([1,1.5,1])
    with col:
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise PRO V4.0</h2>", unsafe_allow_html=True)
        with st.form("login"):
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
                        st.error("🚫 Acceso suspendido por fin de prueba o falta de pago. Comuníquese con el Administrador (SISTEMAS E.G.).")
                    elif str(user_data["pass"]).strip() == p.strip():
                        st.session_state["u_actual"] = user_data
                        st.session_state["logeado"] = True
                        st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user_data["nombre"], "E": user_data["empresa"], "A": "Login"})
                        guardar_datos()
                        st.rerun()
                    else: st.error("Acceso denegado: Usuario o contraseña incorrectos.")
                else: st.error("Acceso denegado: Usuario o contraseña incorrectos.")
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
    if st.button("Cerrar Sesión", width="stretch"): st.session_state["logeado"] = False; st.rerun()

# --- MENU DINÁMICO COMERCIAL V4.0 ---
menu = ["📈 Dashboard", "👤 Admisión", "📊 Clínica", "👶 Pediatría", "📝 Evolución", "💊 Recetas", "⚖️ Balance", "📍 Visitas", "📚 Historial", "💳 Caja", "🗄️ PDF"]
if rol in ["SuperAdmin", "Coordinador"]: menu.append("⚙️ Mi Equipo")
if rol == "SuperAdmin": menu.append("🕵️ Auditoría")
tabs = st.tabs(menu)

# 0. DASHBOARD (NUEVO MÓDULO ESTADÍSTICO)
with tabs[0]:
    st.markdown(f"<h3 style='color: #3b82f6;'>📈 Panel de Gestión - {mi_empresa}</h3>", unsafe_allow_html=True)
    if not pacientes_visibles: st.warning("No hay pacientes cargados para generar estadísticas.")
    else:
        m1, m2, m3 = st.columns(3)
        
        # 📊 1. Gráfico Tortas: Pacientes por Institución
        df_p_completo = pd.DataFrame.from_dict(st.session_state["detalles_pacientes_db"], orient='index').reset_index()
        if not df_p_completo.empty and 'empresa' in df_p_completo.columns:
            st.markdown("#### Pacientes por Clínica / Institución")
            if rol == "SuperAdmin":
                dist_p = df_p_completo['empresa'].value_counts()
            else:
                dist_p = df_p_completo[df_p_completo['empresa'] == mi_empresa]['empresa'].value_counts()
            st.dataframe(dist_p, use_container_width=True) # Reemplazar por st.pie_chart si la versión lo soporta, o usar plotly

        # 💰 2. Gráfico Área: Facturación Mensual
        df_fact = pd.DataFrame(st.session_state["facturacion_db"])
        if not df_fact.empty and paciente_sel and rol in ["SuperAdmin", "Coordinador"]:
            st.markdown("#### Evolución de Ingresos")
            df_fact["fecha_c"] = pd.to_datetime(df_fact["fecha"], format="%d/%m/%Y")
            if rol == "Coordinador":
                pacs_mi_empresa = [p for p in st.session_state["detalles_pacientes_db"] if st.session_state["detalles_pacientes_db"][p]['empresa'] == mi_empresa]
                df_fact = df_fact[df_fact['paciente'].isin(pacs_mi_empresa)]
            
            df_fact_g = df_fact.groupby("fecha_c")["monto"].sum().reset_index()
            st.area_chart(df_fact_g.set_index("fecha_c")["monto"], color="#10b981")

       # 👨‍⚕️ 3. Gráfico Barras: Visitas por Enfermero (Última Semana)
        st.markdown("#### Visitas por Profesional (Última Semana)")
        df_evs = pd.DataFrame(st.session_state["evoluciones_db"])
        if not df_evs.empty:
            df_evs["fecha_c"] = pd.to_datetime(df_evs["fecha"], format="%d/%m/%Y %H:%M")
            
            # --- LA SOLUCIÓN ESTÁ EN ESTA LÍNEA (Le sacamos el tzinfo) ---
            hace_una_semana = (ahora() - timedelta(days=7)).replace(tzinfo=None)
            
            if rol == "Coordinador":
                pacs_mi_empresa = [p for p in st.session_state["detalles_pacientes_db"] if st.session_state["detalles_pacientes_db"][p]['empresa'] == mi_empresa]
                df_evs = df_evs[df_evs['paciente'].isin(pacs_mi_empresa)]
            
            df_evs_s = df_evs[df_evs["fecha_c"] > hace_una_semana]
            
            if not df_evs_s.empty:
                perf_enf = df_evs_s["firma"].value_counts().reset_index()
                perf_enf.columns = ["Profesional", "Visitas"]
                st.bar_chart(perf_enf.set_index("Profesional")["Visitas"], color="#3b82f6")
            else: st.caption("No hubo visitas registradas en los últimos 7 días.")

# 1. ADMISIÓN (Sigue igual)
with tabs[1]:
    st.subheader("Registrar Paciente")
    with st.form("adm_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("Nombre y Apellido")
        d = col_a.text_input("DNI")
        tel = col_a.text_input("WhatsApp (358430...)")
        f_nac = col_b.date_input("Nacimiento", value=date(2000, 1, 1))
        dir_pac = col_b.text_input("Dirección (Río Cuarto)")
        o = col_b.text_input("Obra Social")
        emp_d = st.text_input("Empresa", value=mi_empresa) if rol == "SuperAdmin" else mi_empresa
        if st.form_submit_button("Habilitar Paciente", width="stretch"):
            if n and d and emp_d: 
                id_p = f"{n} ({o}) - {emp_d.strip()}"
                st.session_state["pacientes_db"].append(id_p)
                st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "telefono": tel, "direccion": dir_pac, "antecedentes": "", "empresa": emp_d.strip()}
                guardar_datos(); st.rerun()

# 2. CLÍNICA (T.A. -> Tensión Arterial)
with tabs[2]:
    if paciente_sel:
        vits = [v for v in st.session_state["vitales_db"] if v["paciente"] == paciente_sel]
        if vits:
            u = vits[-1]; m1, m2, m3, m4 = st.columns(4)
            m1.metric("Tensión Arterial", u["TA"]); m2.metric("SATO2", f"{u['Sat']}%"); m3.metric("F.C.", f"{u['FC']} lpm"); m4.metric("HGT", u["HGT"])
        with st.form("vitales_f"):
            ta = st.text_input("Tensión Arterial (TA)", "120/80")
            col_signos = st.columns(4)
            fc = col_signos[0].number_input("F.C.", 30, 200, 75); sat = col_signos[1].number_input("SatO2%", 50, 100, 98); temp = col_signos[2].number_input("Temp °C", 35.0, 42.0, 36.5); hgt = col_signos[3].text_input("HGT", "100")
            if st.form_submit_button("Guardar Signos"):
                st.session_state["vitales_db"].append({"paciente": paciente_sel, "TA": ta, "FC": fc, "Sat": sat, "Temp": temp, "HGT": hgt, "fecha": ahora().strftime("%d/%m/%Y %H:%M")})
                guardar_datos(); st.rerun()

# 3. PEDIATRÍA (Curvas Automáticas)
with tabs[3]:
    if paciente_sel:
        st.markdown("<h3 style='color: #10b981;'>👶 Crecimiento y Percentiles (P3-P97)</h3>", unsafe_allow_html=True)
        with st.form("pedia"):
            col_a, col_b = st.columns(2)
            eda = col_a.text_input("Edad")
            pes = col_b.number_input("Peso (kg)", min_value=0.0, format="%.2f")
            tal = col_a.number_input("Talla (cm)", min_value=0.0, format="%.2f")
            pc = col_b.number_input("Périm. Cefálico (cm)", min_value=0.0, format="%.2f")
            p_p = col_a.text_input("Percentil Peso"); p_t = col_b.text_input("Percentil Talla")
            if st.form_submit_button("Guardar Control"):
                imc = round(pes / ((tal/100)**2), 2) if tal > 0 else 0
                st.session_state["pediatria_db"].append({"paciente": paciente_sel, "fecha": ahora().strftime("%d/%m/%Y"), "edad": eda, "peso": pes, "talla": tal, "pc": pc, "imc": imc, "perc_peso": p_p, "perc_talla": p_t, "firma": user["nombre"]})
                guardar_datos(); st.rerun()
        
        # Curvas
        ped = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
        if ped:
            df_g = pd.DataFrame(ped).set_index("fecha")
            c1, c2 = st.columns(2)
            c1.caption("Curva de Peso (kg)"); c1.line_chart(df_g["peso"], color="#3b82f6")
            c2.caption("Curva de Talla (cm)"); c2.line_chart(df_g["talla"], color="#10b981")

# 4. EVOLUCIÓN (NUEVO: REGISTRO FOTOGRÁFICO DE HERIDAS)
with tabs[4]:
    if paciente_sel:
        st.subheader("Cargar Evolución o Heridas")
        with st.form("evol"):
            nota = st.text_area("Nota clínica:")
            
            # --- AGREGADO: CÁMARA PARA HERIDAS ---
            st.markdown("#### 📸 Registro de Heridas / Escaras (Opcional)")
            foto_w = st.camera_input("Tomar foto de la herida")
            desc_w = st.text_input("Descripción de la herida (Ej: Sacra estadio II)")
            
            if st.form_submit_button("Firmar y Guardar Nota"):
                if nota:
                    # Guardar la evolución normal
                    fecha_n = ahora().strftime("%d/%m/%Y %H:%M")
                    st.session_state["evoluciones_db"].append({"paciente": paciente_sel, "nota": nota, "fecha": fecha_n, "firma": user["nombre"]})
                    
                    # Si hay foto, guardarla en base64 en la base
                    if foto_w:
                        # Convertir la foto a base64
                        base64_foto = base64.b64encode(foto_w.getvalue()).decode('utf-8')
                        st.session_state["fotos_heridas_db"].append({
                            "paciente": paciente_sel, "fecha": fecha_n, "descripcion": desc_w, 
                            "base64_foto": base64_foto, "firma": user["nombre"]
                        })
                    
                    guardar_datos(); st.rerun()

# 5. RECETAS
with tabs[5]:
    if paciente_sel:
        with st.form("recet"):
            d = st.text_input("Medicamento"); p = st.selectbox("Vía", ["Oral", "Endovenosa", "Intramuscular"]); f = st.number_input("Días", 1, 30, 7)
            if st.form_submit_button("Cargar Terapéutica"):
                st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": f"{d} {p} por {f} días.", "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()

# 6. BALANCE HÍDRICO (CON ML)
with tabs[6]:
    if paciente_sel:
        st.markdown("<h3 style='color: #3b82f6;'>⚖️ Control Estricto (ml)</h3>", unsafe_allow_html=True)
        with st.form("bal"):
            c1, c2 = st.columns(2)
            c1.markdown("#### Ingresos (ml)"); i1 = c1.number_input("Oral", 0, step=100); i2 = c1.number_input("Parenteral", 0, step=100)
            c2.markdown("#### Egresos (ml)"); e1 = c2.number_input("Orina", 0, step=100); e2 = c2.number_input("Drenajes", 0, step=100); e3 = c2.number_input("Pérdidas Insensibles", 0, step=100)
            if st.form_submit_button("Calcular Shift"):
                ting = i1+i2; tegr = e1+e2+e3; bal = ting-tegr
                st.session_state["balance_db"].append({"paciente": paciente_sel, "ingresos": ting, "egresos": tegr, "balance": bal, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                guardar_datos(); st.rerun()

# 7. VISITAS Y GOOGLE MAPS
with tabs[7]:
    if paciente_sel:
        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        dire = det.get("direccion", ""); te = det.get("telefono", "")
        if dire:
            st.info(f"🏠 **Domicilio:** {dire}")
            mapa_html = f'<iframe width="100%" height="300" src="https://maps.google.com/maps?q={urllib.parse.quote(dire)}&z=15&output=embed"></iframe>'
            st.components.v1.html(mapa_html, height=300)
        if te:
            msg = urllib.parse.quote(f"Hola, soy {user['nombre']} de {mi_empresa}. Estoy en camino al domicilio.")
            st.markdown(f'<a href="https://wa.me/{te}?text={msg}" target="_blank" class="wa-btn">📲 AVISAR WHATSAPP</a>', unsafe_allow_html=True)

# 8. HISTORIAL COMPLETO (Sigue igual + ML)
with tabs[8]:
    if paciente_sel:
        st.subheader(f"📚 Historia Clínica Digital Integral: {paciente_sel}")
        with st.expander("📝 Evoluciones", expanded=True):
            for e in reversed([x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]):
                st.info(f"📅 **{e['fecha']}** | {e['firma']}\n\n{e['nota']}")
        
        # AGREGADO: VER FOTOS DE HERIDAS
        with st.expander("📸 Registro de Heridas (Fotos)"):
            fot_her = [x for x in st.session_state["fotos_heridas_db"] if x["paciente"] == paciente_sel]
            if fot_her:
                for fh in reversed(fot_her):
                    st.success(f"📅 **{fh['fecha']}** | {fh['firm']}\n\nDescripción: {fh['descripcion']}")
                    # Decodificar y mostrar imagen
                    img_bytes = base64.b64decode(fh['base64_foto'])
                    st.image(img_bytes, caption=f"Herida: {fh['descripcion']}")
            else: st.write("No hay fotos registradas.")

        with st.expander("⚖️ Balances"):
            blp = [x for x in st.session_state["balance_db"] if x["paciente"] == paciente_sel]
            if blp:
                dfb = pd.DataFrame(blp).drop(columns="paciente")
                for c in ["ingresos", "egresos", "balance"]: dfb[c] = dfb[c].astype(str)+" ml"
                st.dataframe(dfb, use_container_width=True)

# 9. CAJA (NUEVO: EXPORTAR A EXCEL)
with tabs[9]:
    if paciente_sel:
        st.markdown(f"<h3 style='color: #3b82f6;'>💳 Caja y Facturación - {paciente_sel}</h3>", unsafe_allow_html=True)
        serv = st.text_input("Servicio"); mon = st.number_input("Monto", 0)
        if st.button("Registrar Cobro"):
            st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv, "monto": mon, "fecha": ahora().strftime("%d/%m/%Y")})
            guardar_datos(); st.rerun()
        
        st.divider()
        # --- AGREGADO: EXPORTAR CAJA A EXCEL ---
        if rol in ["SuperAdmin", "Coordinador"]:
            df_caja_completo = pd.DataFrame(st.session_state["facturacion_db"])
            if not df_caja_completo.empty:
                st.markdown("#### Descargar Reporte de Caja (XLSX)")
                
                # Filtrar si es coordinador
                if rol == "Coordinador":
                    pacs_mi_empresa = [p for p in st.session_state["detalles_pacientes_db"] if st.session_state["detalles_pacientes_db"][p]['empresa'] == mi_empresa]
                    df_caja_completo = df_caja_completo[df_caja_completo['paciente'].isin(pacs_mi_empresa)]
                
                # Generar Excel en memoria
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_caja_completo.to_excel(writer, index=False, sheet_name='Caja_MediCare')
                
                excel_bytes = output.getvalue()
                
                col_ex_1, _ = st.columns([1,3])
                col_ex_1.download_button(label="📥 DESCARGAR CAJA A EXCEL", data=excel_bytes, file_name=f"Reporte_Caja_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else: st.caption("No hay datos de caja para exportar.")

# 10. PDF
with tabs[10]:
    if paciente_sel and FPDF_DISPONIBLE:
        def crear_pdf():
            pdf = FPDF(); pdf.add_page()
            def t(tx): return str(tx).encode('latin-1','replace').decode('latin-1')
            pdf.set_font("Arial",'B',16); pdf.cell(0,10,t(mi_empresa), ln=1)
            pdf.set_font("Arial",'',12); pdf.cell(0,8,t(f"Historia Clínica: {paciente_sel}"), ln=1)
            return pdf.output(dest='S').encode('latin-1')
        st.download_button("📥 Generar Historia Clínica en PDF", crear_pdf(), f"HC_{paciente_sel}.pdf", "application/pdf")

# 11. EQUIPO Y SUSCRIPCIONES (AQUÍ ESTÁ LA MAGIA DE LA SUSCRIPCIÓN)
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"Gestión de Personal y Suscripciones - {mi_empresa}")
        with st.form("equipo"):
            c1, c2 = st.columns(2)
            u_id = c1.text_input("Usuario (Login)"); u_pw = c2.text_input("Clave")
            u_nm = st.text_input("Nombre Completo")
            c3, c4 = st.columns(2)
            u_mt = c3.text_input("Matrícula"); u_ti = c4.selectbox("Título", ["Enfermero/a", "Médico/a"])
            u_rl = st.selectbox("Rol", ["Operativo", "Coordinador"])
            if st.form_submit_button("Habilitar Acceso"):
                if u_id and u_pw:
                    st.session_state["usuarios_db"][u_id.strip().lower()] = {"pass": u_pw.strip(), "nombre": u_nm.strip(), "rol": u_rl, "titulo": u_ti, "empresa": mi_empresa, "matricula": u_mt.strip(), "estado": "Activo"}
                    guardar_datos(); st.rerun()
        
        st.divider(); st.subheader("👥 Control de Accesos (Suscripciones)")
        
        # Filtramos para mostrar solo los de tu empresa (salvo SuperAdmin)
        usuarios_visibles = st.session_state["usuarios_db"] if rol == "SuperAdmin" else {k: v for k, v in st.session_state["usuarios_db"].items() if v["empresa"] == mi_empresa}
        
        for u, d in list(usuarios_visibles.items()):
            if u == "admin": continue
            c1, c2, c3 = st.columns([3, 1, 1])
            estado = d.get("estado", "Activo")
            c1.write(f"🏢 {d['empresa']} | 👤 {d['nombre']} | Login: `{u}` | Estado: **{estado}**")
            
            # --- AGREGADO: BOTÓN DE SUSPENSIÓN (COMERCIAL) ---
            if rol == "SuperAdmin":
                if estado == "Activo":
                    if c2.button("⏸️ Suspender", key=f"susp_{u}"):
                        st.session_state["usuarios_db"][u]["estado"] = "Bloqueado"
                        guardar_datos(); st.rerun()
                else:
                    if c2.button("▶️ Reactivar", key=f"reac_{u}"):
                        st.session_state["usuarios_db"][u]["estado"] = "Activo"
                        guardar_datos(); st.rerun()
            
            if c3.button("❌ Bajar", key=f"del_{u}"): del st.session_state["usuarios_db"][u]; guardar_datos(); st.rerun()

# 12. AUDITORÍA (NUEVO: EXPORTAR LOGS A EXCEL)
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría de Movimientos")
        df_logs = pd.DataFrame(st.session_state["logs_db"])
        st.dataframe(df_logs)
        
        # --- AGREGADO: EXPORTAR LOGS A EXCEL ---
        if not df_logs.empty:
            st.markdown("#### Descargar Logs de Auditoría (XLSX)")
            
            # Generar Excel en memoria
            output_logs = io.BytesIO()
            with pd.ExcelWriter(output_logs, engine='openpyxl') as writer:
                df_logs.to_excel(writer, index=False, sheet_name='Logs_MediCare')
            
            excel_bytes_logs = output_logs.getvalue()
            
            col_ex_logs, _ = st.columns([1,3])
            col_ex_logs.download_button(label="📥 DESCARGAR LOGS A EXCEL", data=excel_bytes_logs, file_name=f"Reporte_Logs_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
