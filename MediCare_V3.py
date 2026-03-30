import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import json
import pytz
import urllib.request
import urllib.parse
from supabase import create_client, Client
import io
import base64
import time
import os
import tempfile
from PIL import Image
import altair as alt

# --- VADEMÉCUM GLOBAL MASIVO (MÁS DE 400 INSUMOS Y FÁRMACOS ORDENADOS) ---
VADEMECUM_BASE = sorted([
    # DESCARTABLES, SUEROS E INSUMOS GENERALES
    "Abocath 14G", "Abocath 16G", "Abocath 18G", "Abocath 20G", "Abocath 22G", "Abocath 24G", 
    "Agua Bi-destilada ampolla 5ml", "Agua Oxigenada 10 vol", "Aguja 15/5", "Aguja 25/8", "Aguja 40/8", "Aguja 50/8",
    "Alcohol 70%", "Alcohol 96%", "Alcohol en gel", "Algodón paquete", "Apósito hidrocoloide", "Apósito transparente",
    "Bajalenguas descartable", "Barbijo N95", "Barbijo Quirúrgico", "Bisturí N° 11", "Bisturí N° 15", "Bisturí N° 20",
    "Bolsa colectora de orina", "Bolsa de colostomía", "Bolsa de ostomía", "Bomba de infusión (Guía)", 
    "Cánula nasal para oxígeno", "Catéter venoso central", "Cinta adhesiva de papel", "Cinta adhesiva de seda", 
    "Cinta hipoalergénica", "Clorhexidina 2%", "Clorhexidina 4%", "Dextrosa 5% 500ml", "Dextrosa 10% 500ml", "Dextrosa 50% ampolla",
    "Electrodos descartables", "Esponja jabonosa", "Gasas 10x10 estériles", "Gasas 5x5 estériles", "Gasas furacinadas",
    "Guantes de examinación L", "Guantes de examinación M", "Guantes de examinación S", "Guantes estériles 6.5", "Guantes estériles 7.0", "Guantes estériles 7.5",
    "Hemoglucotest (Tiras reactivas)", "Jeringa 1ml (Insulina)", "Jeringa 3ml", "Jeringa 5ml", "Jeringa 10ml", "Jeringa 20ml", "Jeringa 50ml (Alimentación)",
    "K108 Sonda Nasogástrica", "K110 Sonda Nasogástrica", "K30 Sonda Nelaton", "K32 Sonda Nelaton",
    "Lancetas descartables", "Llave de 3 vías", "Macrogotero (Perfuss)", "Máscara con reservorio", "Microgotero", 
    "Pañales para adultos G", "Pañales para adultos M", "Pañales para adultos XG", "Platsul A (Sulfadiazina de Plata)", "Povidona Yodada (Iodo)", 
    "Ringer Lactato 500ml", "Solución Fisiológica 0.9% 100ml", "Solución Fisiológica 0.9% 250ml", "Solución Fisiológica 0.9% 500ml", 
    "Sonda de Aspiración N° 10", "Sonda de Aspiración N° 14", "Sonda Foley N° 14 (2 vías)", "Sonda Foley N° 16 (2 vías)", "Sonda Foley N° 18 (2 vías)", "Sonda Foley N° 20 (3 vías)",
    "Tegaderm 10x12", "Tegaderm 6x7", "Tubo endotraqueal", "Venda de Cambric 10cm", "Venda elástica 10cm", "Venda elástica 15cm",

    # FARMACOLOGÍA: A
    "Acenocumarol (Sintrom) 4mg", "Aciclovir 400mg", "Aciclovir crema", "Ácido Ascórbico (Vit C) 1g", "Ácido Fólico 5mg", "Ácido Tranexámico ampolla", "Ácido Valproico 500mg",
    "Adenosina 6mg ampolla", "Adrenalina (Epinefrina) 1mg ampolla", "Albendazol 400mg", "Alopurinol 100mg", "Alopurinol 300mg", 
    "Alprazolam 0.5mg", "Alprazolam 1mg", "Alprazolam 2mg", "Amiodarona 200mg", "Amiodarona 150mg ampolla", "Amitriptilina 25mg", 
    "Amlodipina 10mg", "Amlodipina 5mg", "Amoxicilina 500mg", "Amoxicilina 875mg", "Amoxicilina+Clavulánico 875/125mg", 
    "Ampicilina 1g ampolla", "Ampicilina+Sulbactam 1.5g ampolla", "Aspirina (AAS) 100mg", "Atenolol 50mg", "Atorvastatina 10mg", "Atorvastatina 20mg", "Azitromicina 500mg",
    
    # FARMACOLOGÍA: B - C
    "Baclofeno 10mg", "Beclometasona aerosol", "Betametasona ampolla", "Betametasona crema", "Bicalutamida 50mg", 
    "Bicarbonato de Sodio 1/6 M ampolla", "Bisacodilo 5mg", "Bisoprolol 2.5mg", "Bisoprolol 5mg", "Bromhexina jarabe", 
    "Budesonida aerosol", "Bupivacaína ampolla",
    "Carbonato de Calcio 500mg", "Captopril 25mg", "Carbamazepina 200mg", "Carvedilol 12.5mg", "Carvedilol 25mg", "Carvedilol 6.25mg", 
    "Cefalexina 500mg", "Cefalotina 1g ampolla", "Cefotaxima 1g ampolla", "Ceftriaxona 1g ampolla", "Celecoxib 200mg", 
    "Cetirizina 10mg", "Cilostazol 100mg", "Ciprofloxacina 500mg", "Citalopram 20mg", "Claritromicina 500mg", "Clindamicina 300mg", "Clindamicina 600mg ampolla",
    "Clobetasol crema", "Clonazepam 0.5mg", "Clonazepam 2mg", "Clopidogrel 75mg", "Clorpromazina 25mg", "Colchicina 1mg", "Complejo B ampolla",
    
    # FARMACOLOGÍA: D - H
    "Dapagliflozina 10mg", "Desloratadina 5mg", "Dexametasona 8mg ampolla", "Dexametasona comprimido", "Diazepam 10mg ampolla", "Diazepam 5mg comprimido", 
    "Diclofenac 50mg", "Diclofenac 75mg ampolla", "Difenhidramina 50mg ampolla", "Digoxina 0.25mg", "Diltiazem 60mg", 
    "Dipirona 1g ampolla", "Dipirona 500mg comprimido", "Dobutamina ampolla", "Domperidona 10mg", "Dopamina ampolla", 
    "Doxiciclina 100mg", "Duloxetina 30mg",
    "Empagliflozina 10mg", "Enalapril 10mg", "Enalapril 5mg", "Enoxaparina 40mg jeringa", "Enoxaparina 60mg jeringa", 
    "Escitalopram 10mg", "Espironolactona 25mg", "Espironolactona 50mg", "Ezetimibe 10mg",
    "Famotidina 20mg", "Fentanilo ampolla", "Finasteride 5mg", "Fluconazol 150mg", "Fluoxetina 20mg", "Fluticasona aerosol", 
    "Furosemida 20mg ampolla", "Furosemida 40mg comprimido",
    "Gabapentina 300mg", "Gentamicina 80mg ampolla", "Glibenclamida 5mg", "Glimepirida 2mg", "Glucagón ampolla",
    "Haloperidol 5mg ampolla", "Heparina Sódica ampolla", "Hidroclorotiazida 25mg", "Hidrocortisona 100mg ampolla", "Hidrocortisona 500mg ampolla", 
    "Hierro (Sulfato Ferroso)", "Hioscina (Buscapina) 10mg", "Hioscina Compuesta ampolla", "Hioscina Simple ampolla", "Hidroxicloroquina 200mg",
    
    # FARMACOLOGÍA: I - Z
    "Ibuprofeno 400mg", "Ibuprofeno 600mg", "Ibuprofeno jarabe", "Imipenem 500mg ampolla", 
    "Insulina Aspart", "Insulina Corriente (Regular)", "Insulina Detemir", "Insulina Glargina", "Insulina Lispro", "Insulina NPH", 
    "Ipratropio aerosol", "Ipratropio gotas (Nebulización)", "Irbesartán 150mg", "Isosorbide dinitrato 10mg",
    "Ketamina ampolla", "Ketoconazol crema", "Ketorolac 10mg comprimido", "Ketorolac 30mg ampolla", "Ketorolac 60mg ampolla",
    "Labetalol ampolla", "Lactulón jarabe", "Lamotrigina 50mg", "Lansoprazol 30mg", "Levetiracetam 500mg", 
    "Levofloxacina 500mg", "Levomepromazina 25mg", "Levotiroxina 100mcg", "Levotiroxina 50mcg", "Levotiroxina 75mcg", 
    "Lidocaína 2% ampolla", "Lidocaína jalea", "Linagliptina 5mg", "Loperamida 2mg", "Loratadina 10mg", 
    "Lorazepam 1mg", "Lorazepam 2mg", "Losartán 50mg",
    "Magnesio (Sulfato) ampolla", "Mebendazol 200mg", "Meloxicam 15mg", "Meropenem 1g ampolla", "Metadona 10mg", 
    "Metformina 500mg", "Metformina 850mg", "Metildopa 500mg", "Metilprednisolona 500mg ampolla", "Metoclopramida (Reliveran) 10mg", 
    "Metoclopramida ampolla", "Metoprolol 50mg", "Metronidazol 500mg", "Metronidazol sachet 500ml", "Midazolam 15mg ampolla", 
    "Mirtazapina 30mg", "Montelukast 10mg", "Morfina 10mg ampolla", "Mupirocina ungüento",
    "Naloxona ampolla", "Naproxeno 500mg", "Neomicina crema", "Nifedipina 10mg", "Nimodipina 30mg", 
    "Nitrofurantoína 100mg", "Nitroglicerina ampolla", "Noradrenalina ampolla",
    "Olanzapina 10mg", "Omeprazol 20mg", "Omeprazol 40mg ampolla", "Ondansetrón 8mg ampolla", "Oxígeno en tubo",
    "Pantoprazol 40mg", "Paracetamol 1g", "Paracetamol 500mg", "Paroxetina 20mg", "Penicilina G Benzatínica 2.400.000 UI", 
    "Piperacilina+Tazobactam 4.5g ampolla", "Potasio (Cloruro) ampolla", "Pramipexol 1mg", "Prasugrel 10mg", "Pravastatina 20mg", 
    "Prednisona 20mg", "Pregabalina 75mg", "Prometazina ampolla", "Propanolol 40mg", "Quetiapina 25mg", "Quetiapina 100mg",
    "Ramipril 5mg", "Ranitidina 150mg", "Ranitidina ampolla", "Risperidona 2mg", "Ritonavir", "Rivaroxabán 15mg", "Rosuvastatina 10mg", "Rosuvastatina 20mg",
    "Salbutamol aerosol", "Salbutamol gotas (Nebulización)", "Sertralina 50mg", "Sildenafil 50mg", "Simvastatina 20mg", "Sitagliptina 50mg", "Sodio (Cloruro al 20%) ampolla", "Sucralfato",
    "Tamsulosina 0.4mg", "Telmisartán 40mg", "Tetraciclina 250mg", "Tirotricina", "Tobramicina gotas", "Topiramato 50mg", "Tramadol 50mg", "Tramadol ampolla",
    "Valaciclovir 500mg", "Valsartán 80mg", "Vancomicina 1g ampolla", "Venlafaxina 75mg", "Verapamilo 80mg", "Vitamina B12 ampolla", "Vitamina K ampolla",
    "Zolpidem 10mg", "Zopiclona 7.5mg"
])

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

GEO_DISPONIBLE = False
try:
    from streamlit_geolocation import streamlit_geolocation
    GEO_DISPONIBLE = True
except ImportError:
    GEO_DISPONIBLE = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MediCare Enterprise PRO V9.9", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- ZONA HORARIA ARGENTINA ---
ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')
def ahora():
    return datetime.now(ARG_TZ)

# --- TRADUCTOR GPS A CALLE REAL ---
def obtener_direccion_real(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'MediCareProApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            display_name = data.get('display_name', 'Dirección no encontrada')
            partes = display_name.split(", ")
            if len(partes) > 3:
                return ", ".join(partes[:3])
            return display_name
    except:
        return "Dirección exacta no disponible (Solo coordenadas)"

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 🎨 DISEÑO VISUAL Y OPTIMIZACIÓN MÓVIL (CSS) ---
page_bg_css = """
<style>
/* 1. Bloquear recargas accidentales en celulares (Pull-to-refresh) */
body { overscroll-behavior-y: none; }

/* 2. Aceleración de Hardware para textos más fluidos */
* { text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; }

/* 3. Fondo Adaptativo Premium */
.stApp {
    background-color: var(--background-color);
    background-image: radial-gradient(circle at top, var(--secondary-background-color) 0%, transparent 80%);
}

/* 4. Contenedores Ultra-Livianos para la GPU del celular */
div[data-testid="stForm"] {
    background-color: var(--secondary-background-color);
    border: 1px solid rgba(150, 150, 150, 0.2);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); /* Sombra suave y ligera */
}

/* 5. Botones Optimizados para Dedos (Touch Targets grandes) */
.stButton>button {
    min-height: 48px; /* Más fáciles de tocar con el pulgar */
    border-radius: 10px;
    transition: transform 0.1s ease; /* Efecto rebote nativo */
}
.stButton>button:active {
    transform: scale(0.95);
}

/* Esconder flechitas de números */
input[type=number]::-webkit-inner-spin-button, 
input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
input[type=number] { -moz-appearance: textfield; }

/* Botón de WhatsApp nativo */
.wa-btn {
    display: block; width: 100%; text-align: center; background-color: #25D366; 
    color: white !important; padding: 12px; border-radius: 10px; font-weight: bold; text-decoration: none;
    margin-top: 10px; margin-bottom: 10px;
}
.wa-btn:hover { background-color: #128C7E; }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# --- 🎁 LOGO EXCLUSIVO PROFESIONAL ---
def render_logo_eg(size=100):
    svg_code = f"""
    <svg width="{size}" height="{size}" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="egGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#1e3a8a;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#0d9488;stop-opacity:1" />
            </linearGradient>
        </defs>
        <circle cx="60" cy="60" r="55" fill="url(#egGrad)" stroke="white" stroke-width="2"/>
        <g fill="white" font-family="Arial, Helvetica, sans-serif" font-weight="bold" text-anchor="middle">
            <text x="60" y="55" font-size="36" letter-spacing="-1">E.G</text>
            <text x="60" y="80" font-size="10" font-weight="normal" letter-spacing="0.5">ENZO GIRARDI</text>
            <text x="60" y="92" font-size="8" font-weight="normal" letter-spacing="0.2">SISTEMAS SOLUTIONS</text>
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
        "agenda_db", "checkin_db", "inventario_db", "consumos_db", "nomenclador_db", "firmas_tactiles_db",
        "reportes_diarios_db"
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
        "agenda_db": [], "checkin_db": [], "inventario_db": [], "consumos_db": [], "nomenclador_db": [], "firmas_tactiles_db": [],
        "reportes_diarios_db": []
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
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise PRO V9.9</h2>", unsafe_allow_html=True)
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
    
    ver_altas = False
    if rol in ["SuperAdmin", "Coordinador"]:
        ver_altas = st.checkbox("📁 Mostrar Pacientes de Alta")

    pacientes_visibles = []
    for p in st.session_state["pacientes_db"]:
        det = st.session_state["detalles_pacientes_db"].get(p, {})
        if rol != "SuperAdmin" and det.get("empresa") != mi_empresa:
            continue
        
        estado = det.get("estado", "Activo")
        if estado == "Activo" or ver_altas:
            display_name = f"🗄️ {p} [ALTA]" if estado == "De Alta" else p
            pacientes_visibles.append((p, display_name))

    p_f = [pv for pv in pacientes_visibles if buscar.lower() in pv[1].lower()]
    paciente_sel_tuple = st.selectbox("Seleccionar Paciente:", p_f, format_func=lambda x: x[1]) if p_f else None
    
    paciente_sel = paciente_sel_tuple[0] if paciente_sel_tuple else None

    if paciente_sel and rol in ["SuperAdmin", "Coordinador"]:
        estado_actual = st.session_state["detalles_pacientes_db"].get(paciente_sel, {}).get("estado", "Activo")
        if estado_actual == "Activo":
            if st.button("📦 ARCHIVAR (Dar de Alta)", width="stretch"):
                st.session_state["detalles_pacientes_db"][paciente_sel]["estado"] = "De Alta"
                st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user["nombre"], "E": mi_empresa, "A": f"Alta Médica Archivo: {paciente_sel}"})
                guardar_datos(); st.rerun()
        else:
            if st.button("🔄 REVERTIR ALTA (Reactivar)", width="stretch"):
                st.session_state["detalles_pacientes_db"][paciente_sel]["estado"] = "Activo"
                st.session_state["logs_db"].append({"F": ahora().strftime("%d/%m/%Y"), "H": ahora().strftime("%H:%M"), "U": user["nombre"], "E": mi_empresa, "A": f"Reactivación Legajo: {paciente_sel}"})
                guardar_datos(); st.rerun()

    st.divider()
    if st.button("Cerrar Sesión", width="stretch"): st.session_state["logeado"] = False; st.rerun()

# --- MENU DINÁMICO ---
menu = ["📍 Visitas y Agenda", "👤 Admisión", "📊 Clínica", "👶 Pediatría", "📝 Evolución", "💉 Materiales", "💊 Recetas", "⚖️ Balance", "📦 Inventario", "💳 Caja", "📚 Historial", "🗄️ PDF"]

if rol in ["SuperAdmin", "Coordinador"]: 
    menu.insert(1, "📈 Dashboard") 
    menu.append("📑 Cierre Diario")
    menu.append("⚙️ Mi Equipo")
    menu.append("🕵️ Auditoría")

tabs = st.tabs(menu)

# 1. VISITAS Y AGENDA UNIFICADA
with tabs[menu.index("📍 Visitas y Agenda")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral para gestionar sus visitas y turnos.")
    else:
        st.subheader("⏱️ Fichada Legal de Visita (GPS Real)")
        estado_pac = st.session_state["detalles_pacientes_db"].get(paciente_sel, {}).get("estado", "Activo")
        if estado_pac == "De Alta":
            st.error("⚠️ Este paciente se encuentra DE ALTA. Su legajo está archivado. Solo se puede visualizar el historial.")
        else:
            det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
            dire_paciente = det.get("direccion", "No registrada")
            te = det.get("telefono", "")

            if GEO_DISPONIBLE:
                loc = streamlit_geolocation()
                lat = loc.get('latitude') if loc else None
                lon = loc.get('longitude') if loc else None

                if lat is not None and lon is not None:
                    try:
                        lat_str = str(round(float(lat), 5))
                        lon_str = str(round(float(lon), 5))
                    except:
                        lat_str = str(lat)
                        lon_str = str(lon)

                    direccion_real = obtener_direccion_real(lat_str, lon_str)
                    st.success(f"📍 **Estás físicamente en:** {direccion_real}")
                    link_mapa = f"https://www.google.com/maps/search/?api=1&query={lat_str},{lon_str}"
                    st.markdown(f"[🗺️ Ver en Google Maps]({link_mapa})")

                    c_in, c_out = st.columns(2)
                    if c_in.button("🟢 Fichar LLEGADA en esta Ubicación", use_container_width=True):
                        st.session_state["checkin_db"].append({"paciente": paciente_sel, "profesional": user["nombre"], "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"), "tipo": f"LLEGADA en: {direccion_real} (Lat: {lat_str})", "empresa": mi_empresa})
                        guardar_datos(); st.success("Llegada registrada exitosamente."); st.rerun()
                    
                    if c_out.button("🔴 Fichar SALIDA en esta Ubicación", use_container_width=True):
                        st.session_state["checkin_db"].append({"paciente": paciente_sel, "profesional": user["nombre"], "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"), "tipo": f"SALIDA de: {direccion_real} (Lat: {lat_str})", "empresa": mi_empresa})
                        guardar_datos(); st.success("Salida registrada exitosamente."); st.rerun()
                else:
                    st.error("❌ Aún no capturaste tu ubicación. Tocá la brújula de arriba 👆 y dale a 'Permitir' en tu navegador.")
            else:
                st.error("⚠️ Librería 'streamlit-geolocation' no cargó correctamente.")

            st.divider()
            
            agenda_paciente = [a for a in st.session_state["agenda_db"] if a["paciente"] == paciente_sel and a["empresa"] == mi_empresa and a["estado"] == "Pendiente"]
            hora_turno_str = ""
            if agenda_paciente:
                turno_prox = agenda_paciente[-1]
                hora_turno_str = f" a las {turno_prox['hora']} hs"
            
            if dire_paciente and dire_paciente != "No registrada":
                st.info(f"🏠 **Domicilio Asignado del Paciente:** {dire_paciente}")
                
            if te:
                num_limpio = ''.join(filter(str.isdigit, str(te)))
                if len(num_limpio) >= 10: num_limpio = "549" + num_limpio[-10:]
                if hora_turno_str:
                    msg_text = f"Hola, soy {user['nombre']} de {mi_empresa}. Me comunico para confirmar la visita médica. Estaré llegando{hora_turno_str}. ¡Saludos!"
                else:
                    msg_text = f"Hola, soy {user['nombre']} de {mi_empresa}. Estoy en camino al domicilio."
                msg = urllib.parse.quote(msg_text)
                st.markdown(f'<a href="https://wa.me/{num_limpio}?text={msg}" target="_blank" class="wa-btn">📲 AVISAR LLEGADA POR WHATSAPP</a>', unsafe_allow_html=True)
                if hora_turno_str:
                    st.caption(f"*(El mensaje de WhatsApp incluirá automáticamente el horario programado: {hora_turno_str})*")

            st.divider()
            st.subheader("📅 Agendar Próxima Visita")
            with st.form("agenda_form", clear_on_submit=True):
                c1_ag, c2_ag = st.columns(2)
                fecha_ag = c1_ag.date_input("Fecha programada")
                hora_ag = c2_ag.time_input("Hora aproximada")
                profesionales = [v['nombre'] for k, v in st.session_state["usuarios_db"].items() if v['empresa'] == mi_empresa or rol == "SuperAdmin"]
                idx_prof = profesionales.index(user['nombre']) if user['nombre'] in profesionales else 0
                prof_ag = st.selectbox("Asignar Profesional", profesionales, index=idx_prof)
                
                if st.form_submit_button("Agendar Visita", width="stretch"):
                    st.session_state["agenda_db"].append({"paciente": paciente_sel, "profesional": prof_ag, "fecha": fecha_ag.strftime("%d/%m/%Y"), "hora": hora_ag.strftime("%H:%M"), "empresa": mi_empresa, "estado": "Pendiente"})
                    guardar_datos(); st.success("✅ Turno agendado. El paciente recibirá la hora automáticamente en el próximo WhatsApp."); st.rerun()
            
            agenda_mia = [a for a in st.session_state["agenda_db"] if a["empresa"] == mi_empresa and a["paciente"] == paciente_sel]
            if agenda_mia: 
                st.caption("Próximas visitas agendadas para este paciente:")
                st.dataframe(pd.DataFrame(agenda_mia).drop(columns=["empresa", "paciente"]).tail(3), use_container_width=True)

# 2. DASHBOARD
if "📈 Dashboard" in menu:
    with tabs[menu.index("📈 Dashboard")]:
        st.markdown(f"<h3 style='color: #3b82f6;'>📈 Panel de Gestión - {mi_empresa}</h3>", unsafe_allow_html=True)
        if not st.session_state["pacientes_db"]: st.warning("No hay pacientes cargados.")
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
                    
                    chart = alt.Chart(perf_enf).mark_bar(
                        size=35, color='#3b82f6', cornerRadiusTopLeft=5, cornerRadiusTopRight=5
                    ).encode(
                        x=alt.X('Profesional:N', sort='-y', title='Profesional / Enfermero'),
                        y=alt.Y('Visitas:Q', title='Cantidad de Visitas Semanales', axis=alt.Axis(tickMinStep=1)),
                        tooltip=['Profesional', 'Visitas']
                    ).properties(height=350)
                    
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info("No hay visitas registradas en los últimos 7 días.")

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
                st.session_state["detalles_pacientes_db"][id_p] = {"dni": d, "fnac": f_nac.strftime("%d/%m/%Y"), "sexo": se, "telefono": tel, "direccion": dir_p, "empresa": emp_d.strip(), "estado": "Activo"}
                guardar_datos(); st.rerun()

# 4. CLÍNICA
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

# 5. PEDIATRÍA 
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

# 6. EVOLUCIÓN
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

# 7. MATERIALES Y DESCARTABLES
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
                    st.session_state["consumos_db"].append({"paciente": paciente_sel, "insumo": insumo_sel, "cantidad": cant_usada, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"], "empresa": mi_empresa})
                    guardar_datos(); st.success(f"✅ {cant_usada}x {insumo_sel} registrado y descontado del stock."); st.rerun()
                    
        cons_paciente = [c for c in st.session_state["consumos_db"] if c["paciente"] == paciente_sel]
        if cons_paciente:
            st.divider()
            st.caption("Últimos materiales registrados:")
            st.dataframe(pd.DataFrame(cons_paciente).drop(columns=["paciente", "empresa"], errors='ignore'), use_container_width=True)

# 8. RECETAS (CON FRECUENCIA INCORPORADA)
with tabs[menu.index("💊 Recetas")]:
    if paciente_sel:
        with st.form("recet", clear_on_submit=True):
            c_rec1, c_rec2 = st.columns([2, 1])
            lista_vademecum_receta = ["-- Seleccionar del Vademécum --"] + VADEMECUM_BASE
            
            med_vademecum = c_rec1.selectbox("1. Medicamento / Vademécum Oficial:", lista_vademecum_receta)
            med_manual = c_rec2.text_input("O 2. Cargar Manualmente:")
            
            c_rec3, c_rec4, c_rec5 = st.columns([2, 2, 1])
            lista_vias = ["Oral", "Endovenosa (EV)", "Intramuscular (IM)", "Subcutánea (SC)", "Sublingual", "Tópica", "Inhalatoria", "Oftálmica", "Ótica", "Nasal", "Rectal", "Vaginal"]
            p = c_rec3.selectbox("Vía de Administración", lista_vias)
            
            lista_frecuencias = ["Cada 4 horas", "Cada 6 horas", "Cada 8 horas", "Cada 12 horas", "Cada 24 horas", "Dosis única", "Según necesidad (SOS)"]
            frec = c_rec4.selectbox("Frecuencia (Horario)", lista_frecuencias, index=2)
            
            f = c_rec5.number_input("Días", min_value=1, max_value=90, value=7)
            
            if st.form_submit_button("Cargar Terapéutica", width="stretch"):
                med_final = med_manual.strip().title() if med_manual.strip() else med_vademecum
                
                if med_final and med_final != "-- Seleccionar del Vademécum --":
                    texto_receta = f"{med_final} | Vía: {p} | {frec} | Durante {f} días."
                    st.session_state["indicaciones_db"].append({"paciente": paciente_sel, "med": texto_receta, "fecha": ahora().strftime("%d/%m/%Y %H:%M"), "firma": user["nombre"]})
                    guardar_datos(); st.rerun()

# 9. BALANCE HÍDRICO
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

# 10. INVENTARIO 
with tabs[menu.index("📦 Inventario")]:
    inv_mio = [i for i in st.session_state["inventario_db"] if i["empresa"] == mi_empresa]
    if inv_mio:
        stock_critico = [i for i in inv_mio if i['stock'] <= 10]
        if stock_critico:
            st.error("🚨 **ALERTA DE STOCK CRÍTICO EN FARMACIA:**")
            for item in stock_critico:
                st.warning(f"⚠️ {item['item']}: Quedan solo **{item['stock']}** unidades.")
            st.divider()

    with st.form("form_inv", clear_on_submit=True):
        st.markdown("#### ➕ Ingreso de Mercadería (Suma al stock existente)")
        c1, c2, c3 = st.columns([2, 2, 1])
        
        lista_base_inv = ["-- Seleccionar del Vademécum --"] + VADEMECUM_BASE
        
        item_sel = c1.selectbox("1. Catálogo Frecuente:", lista_base_inv)
        nuevo_item_manual = c2.text_input("O 2. Escribir Insumo Nuevo:")
        cantidad_ini = c3.number_input("Cantidad", min_value=1, value=10)
        
        if st.form_submit_button("Sumar Stock", width="stretch"):
            item_final = nuevo_item_manual.strip().title() if nuevo_item_manual.strip() else item_sel
            
            if item_final and item_final != "-- Seleccionar del Vademécum --":
                encontrado = False
                for i in st.session_state["inventario_db"]:
                    if i["item"].lower() == item_final.lower() and i["empresa"] == mi_empresa:
                        i["stock"] += cantidad_ini; encontrado = True; break
                if not encontrado:
                    st.session_state["inventario_db"].append({"item": item_final, "stock": cantidad_ini, "empresa": mi_empresa})
                guardar_datos(); st.rerun()
                
    st.divider()
    
    if inv_mio: 
        st.markdown("#### 📋 Stock Actual en Farmacia")
        st.dataframe(pd.DataFrame(inv_mio).drop(columns="empresa"), use_container_width=True)
        
        st.markdown("#### ⚙️ Ajuste Manual y Corrección")
        c_ed1, c_ed2, c_ed3 = st.columns([2, 1, 1])
        item_a_editar = c_ed1.selectbox("Seleccionar Insumo a corregir:", [i["item"] for i in inv_mio], key="edit_sel")
        
        nuevo_stock_total = c_ed2.number_input("Declarar Stock Real Exacto:", min_value=0, value=0, key="new_stock")
        
        if c_ed3.button("✏️ Fijar Nuevo Stock", use_container_width=True):
            for i in st.session_state["inventario_db"]:
                if i["item"] == item_a_editar and i["empresa"] == mi_empresa:
                    i["stock"] = nuevo_stock_total
                    break
            guardar_datos(); st.rerun()

        st.divider()
        col_del1, col_del2 = st.columns([3,1])
        del_item = col_del1.selectbox("Seleccionar insumo a eliminar por completo del sistema:", [i["item"] for i in inv_mio], key="del_sel2")
        if col_del2.button("🗑️ Eliminar Insumo Definitivamente", use_container_width=True):
            st.session_state["inventario_db"] = [i for i in st.session_state["inventario_db"] if not (i["item"] == del_item and i["empresa"] == mi_empresa)]
            guardar_datos(); st.rerun()

# 11. CAJA
with tabs[menu.index("💳 Caja")]:
    if paciente_sel:
        with st.form("caja_form", clear_on_submit=True):
            serv_desc = st.text_input("Descripción del Servicio / Práctica Médica / Insumo Extra")
            mon = st.number_input("Monto a Facturar ($)", 0.0)
            
            if st.form_submit_button("Registrar Cobro / Práctica", width="stretch"):
                if serv_desc:
                    st.session_state["facturacion_db"].append({"paciente": paciente_sel, "serv": serv_desc, "monto": mon, "fecha": ahora().strftime("%d/%m/%Y"), "empresa": mi_empresa})
                    guardar_datos(); st.rerun()
        st.divider()

    if rol in ["SuperAdmin", "Coordinador"]:
        df_caja = pd.DataFrame([f for f in st.session_state["facturacion_db"] if f.get("empresa", "") == mi_empresa])
        if not df_caja.empty:
            st.markdown("#### 🔍 Filtro y Reporte de Facturación")
            filtro_caja = st.text_input("Filtrar por paciente, fecha o práctica:")
            
            if filtro_caja:
                mask = df_caja.astype(str).apply(lambda x: x.str.contains(filtro_caja, case=False, na=False)).any(axis=1)
                df_caja_filtrada = df_caja[mask]
            else:
                df_caja_filtrada = df_caja

            total_facturacion = df_caja_filtrada["monto"].sum()
            st.success(f"💰 **FACTURACIÓN TOTAL (Mostrada): ${total_facturacion:,.2f}**")
            
            st.dataframe(df_caja_filtrada.drop(columns="empresa", errors='ignore'), use_container_width=True)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer: df_caja_filtrada.drop(columns="empresa", errors='ignore').to_excel(writer, index=False, sheet_name='Caja_MediCare')
            st.download_button("📥 DESCARGAR RESULTADOS A EXCEL", data=output.getvalue(), file_name=f"Caja_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# 12. HISTORIAL COMPLETO (CONTENEDORES CON SCROLL MÓVIL)
with tabs[menu.index("📚 Historial")]:
    if paciente_sel:
        estado_badge = "🗄️ [ARCHIVADO DE ALTA]" if st.session_state["detalles_pacientes_db"].get(paciente_sel, {}).get("estado") == "De Alta" else ""
        st.subheader(f"📚 Historia Clínica Digital: {paciente_sel} {estado_badge}")
        
        st.markdown("##### ⚙️ Opciones de Visualización")
        col_filt1, col_filt2 = st.columns([1, 2])
        opcion_limite = col_filt1.selectbox("Mostrar:", ["Últimos 10 registros", "Últimos 30 registros", "Últimos 50 registros", "Ver TODO el historial"])
        
        if "10" in opcion_limite: limite = 10
        elif "30" in opcion_limite: limite = 30
        elif "50" in opcion_limite: limite = 50
        else: limite = 999999
        
        col_filt2.info(f"💡 Para que la aplicación sea súper rápida, estás viendo un máximo de **{limite if limite != 999999 else 'Todos los'}** registros por sección.")
        st.divider()

        with st.expander("⏱️ Auditoría de Presencia (GPS Real)", expanded=True):
            chks = [x for x in st.session_state["checkin_db"] if x["paciente"] == paciente_sel]
            if chks: st.dataframe(pd.DataFrame(chks[-limite:]).drop(columns=["paciente", "empresa"]), use_container_width=True)
            else: st.write("No hay registros de asistencia en este periodo.")
            
        with st.expander("📝 Procedimientos y Evoluciones"):
            evs = [x for x in st.session_state["evoluciones_db"] if x["paciente"] == paciente_sel]
            if evs:
                # Contenedor móvil con altura fija
                with st.container(height=350):
                    for e in reversed(evs[-limite:]): st.info(f"📅 **{e['fecha']}** | {e['firma']}\n\n{e['nota']}")
            else: st.write("No hay evoluciones médicas cargadas.")
            
        with st.expander("💉 Materiales Utilizados"):
            cons = [x for x in st.session_state["consumos_db"] if x["paciente"] == paciente_sel]
            if cons: st.dataframe(pd.DataFrame(cons[-limite:]).drop(columns=["paciente", "empresa"], errors='ignore'), use_container_width=True)
            else: st.write("No hay consumos de materiales registrados.")
            
        with st.expander("📸 Registro de Heridas"):
            fot_her = [x for x in st.session_state["fotos_heridas_db"] if x["paciente"] == paciente_sel]
            if fot_her:
                # Contenedor móvil con altura fija
                with st.container(height=450):
                    for fh in reversed(fot_her[-limite:]):
                        st.success(f"📅 **{fh['fecha']}** | {fh['firma']}\n\nDescripción: {fh['descripcion']}")
                        st.image(base64.b64decode(fh['base64_foto']), caption=f"Herida: {fh['descripcion']}")
            else: st.write("No hay registro fotográfico.")
            
        with st.expander("📊 Signos Vitales"):
            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == paciente_sel]
            if vits: st.dataframe(pd.DataFrame(vits[-limite:]).drop(columns="paciente"), use_container_width=True)
            else: st.write("No hay signos vitales cargados.")
            
        with st.expander("👶 Control Pediátrico"):
            peds = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
            if peds: st.dataframe(pd.DataFrame(peds[-limite:]).drop(columns="paciente"), use_container_width=True)
            else: st.write("No hay controles pediátricos.")
            
        with st.expander("⚖️ Balance Hídrico"):
            blp = [x for x in st.session_state["balance_db"] if x["paciente"] == paciente_sel]
            if blp:
                dfb = pd.DataFrame(blp[-limite:]).drop(columns="paciente")
                for c in ["ingresos", "egresos", "balance"]: dfb[c] = dfb[c].astype(str)+" ml"
                st.dataframe(dfb, use_container_width=True)
            else: st.write("No hay balances hídricos calculados.")
            
        with st.expander("💊 Plan Terapéutico (Recetas)"):
            recs = [x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]
            if recs:
                # Contenedor móvil con altura fija
                with st.container(height=350):
                    for r in reversed(recs[-limite:]): st.success(f"📌 **{r['fecha']}** | Indicado por: **{r['firma']}**\n\n{r['med']}")
            else: st.write("No hay terapéutica indicada.")

# 13. PDF 
with tabs[menu.index("🗄️ PDF")]:
    if paciente_sel and FPDF_DISPONIBLE:
        def t(txt): return str(txt).replace('⚖️', '').replace('⚠️', '').replace('📌', '').replace('📅', '').replace('📸', '').replace('🗄️', '').encode('latin-1', 'replace').decode('latin-1')

        def crear_pdf_pro(p):
            pdf = FPDF(); pdf.add_page()
            pdf.set_fill_color(59, 130, 246); pdf.ellipse(10, 10, 22, 22, 'F'); pdf.set_draw_color(255, 255, 255); pdf.set_line_width(1.2)
            pdf.line(21, 14, 21, 28); pdf.line(14, 21, 28, 21)
            emp_paciente = st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa", mi_empresa)
            pdf.set_font("Arial", 'B', 16); pdf.set_xy(38, 14); pdf.cell(0, 10, t(emp_paciente), ln=True)
            pdf.set_font("Arial", 'I', 9); pdf.set_xy(38, 20); pdf.cell(0, 10, t("Historia Clinica Digital Integral (Pro V9.9)"), ln=True); pdf.ln(15)
            
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            estado_texto = " [ARCHIVADO/ALTA]" if det.get("estado") == "De Alta" else ""
            pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, t(f" PACIENTE: {p}{estado_texto}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 6, t(f" DNI: {det.get('dni','S/D')} | Nacimiento: {det.get('fnac','S/D')} | Sexo: {det.get('sexo','S/D')}"), ln=True)
            pdf.cell(0, 6, t(f" Domicilio del Legajo: {det.get('direccion','S/D')}"), ln=True); pdf.ln(5)

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
                pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, t("AUDITORIA DE PRESENCIA GPS (Llegada/Salida):"), ln=True)
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

# 14. CIERRE DIARIO Y REPORTES DE STOCK (SOLO VISIBLE PARA ADMIN/COORDINADOR)
if "📑 Cierre Diario" in menu:
    with tabs[menu.index("📑 Cierre Diario")]:
        st.subheader("📑 Conciliación y Cierre Diario de Operaciones")
        st.info("Seleccioná un día para auditar todos los insumos consumidos, la facturación ingresada y el estado del stock de farmacia en esa fecha.")
        
        c1_rep, c2_rep = st.columns([1, 2])
        fecha_reporte = c1_rep.date_input("Filtrar por Fecha:")
        fecha_str = fecha_reporte.strftime("%d/%m/%Y")
        
        consumos_dia = [c for c in st.session_state.get("consumos_db", []) if c.get("fecha", "").startswith(fecha_str) and c.get("empresa", mi_empresa) == mi_empresa]
        facturacion_dia = [f for f in st.session_state.get("facturacion_db", []) if f.get("fecha", "") == fecha_str and f.get("empresa", "") == mi_empresa]
        stock_actual = [i for i in st.session_state.get("inventario_db", []) if i.get("empresa", "") == mi_empresa]

        with st.expander(f"📦 1. Insumos Consumidos el {fecha_str}", expanded=True):
            if consumos_dia:
                st.dataframe(pd.DataFrame(consumos_dia).drop(columns="empresa", errors='ignore'), use_container_width=True)
            else:
                st.write("No hubo registro de uso de insumos en este día.")

        with st.expander(f"💳 2. Procedimientos y Facturación el {fecha_str}", expanded=True):
            if facturacion_dia:
                total_dia = sum([f['monto'] for f in facturacion_dia])
                st.success(f"**Total Facturado en el día: ${total_dia:,.2f}**")
                st.dataframe(pd.DataFrame(facturacion_dia).drop(columns="empresa", errors='ignore'), use_container_width=True)
            else:
                st.write("No hubo facturación registrada en este día.")

        with st.expander("⚕️ 3. Estado de Stock de Farmacia Actual", expanded=False):
            if stock_actual:
                st.dataframe(pd.DataFrame(stock_actual).drop(columns="empresa", errors='ignore'), use_container_width=True)
            else:
                st.write("No hay stock cargado.")

        if FPDF_DISPONIBLE:
            st.divider()
            st.markdown("#### 🔒 Generar Documento Oficial")
            
            def t(txt): return str(txt).replace('⚖️', '').replace('⚠️', '').replace('📌', '').replace('📅', '').replace('📸', '').replace('🗄️', '').encode('latin-1', 'replace').decode('latin-1')

            def generar_pdf_cierre():
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, t(f"REPORTE DE CIERRE DIARIO Y CONCILIACION - {mi_empresa}"), ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 8, t(f"Fecha Auditada: {fecha_str} | Generado por: {user['nombre']} a las {ahora().strftime('%H:%M')} hs"), ln=True, align='C')
                pdf.ln(5)

                pdf.set_fill_color(220, 220, 220)
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 8, t("1. INSUMOS CONSUMIDOS EN EL DIA"), 1, 1, 'L', True)
                pdf.set_font("Arial", '', 9)
                if not consumos_dia:
                    pdf.cell(0, 6, t(" - Sin consumos registrados."), ln=True)
                else:
                    for c in consumos_dia:
                        pdf.cell(0, 6, t(f" > {c['cantidad']}x {c['insumo']} | Paciente: {c['paciente']} | Usado por: {c.get('firma','')} a las {c.get('fecha','').split(' ')[-1]} hs"), ln=True)
                pdf.ln(5)

                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 8, t("2. PROCEDIMIENTOS Y CAJA DEL DIA"), 1, 1, 'L', True)
                pdf.set_font("Arial", '', 9)
                if not facturacion_dia:
                    pdf.cell(0, 6, t(" - Sin facturacion registrada."), ln=True)
                else:
                    total_f = 0
                    for f in facturacion_dia:
                        pdf.cell(0, 6, t(f" > ${f['monto']} | {f['serv']} | Paciente: {f['paciente']}"), ln=True)
                        total_f += f['monto']
                    pdf.set_font("Arial", 'B', 10)
                    pdf.cell(0, 8, t(f"TOTAL FACTURADO DEL DIA: ${total_f}"), ln=True)
                pdf.ln(5)

                pdf.set_font("Arial", 'B', 11)
                pdf.cell(0, 8, t("3. BALANCE DE STOCK EN FARMACIA (AL CIERRE)"), 1, 1, 'L', True)
                pdf.set_font("Arial", '', 9)
                if not stock_actual:
                    pdf.cell(0, 6, t(" - Sin stock registrado en sistema."), ln=True)
                else:
                    for s in stock_actual:
                        pdf.cell(0, 6, t(f" > {s['item']}: {s['stock']} unidades restantes."), ln=True)

                return pdf.output(dest='S').encode('latin-1')

            if st.button(f"Generar y Guardar Reporte PDF del {fecha_str} en el Sistema", width="stretch"):
                b64_pdf = base64.b64encode(generar_pdf_cierre()).decode('utf-8')
                st.session_state["reportes_diarios_db"].append({
                    "fecha_reporte": fecha_str,
                    "fecha_generacion": ahora().strftime("%d/%m/%Y %H:%M"),
                    "generado_por": user["nombre"],
                    "empresa": mi_empresa,
                    "pdf_base64": b64_pdf
                })
                guardar_datos()
                st.success(f"✅ ¡Cierre del día {fecha_str} guardado exitosamente en la base de datos de la clínica!")
                st.rerun()

        st.divider()
        st.subheader("🗄️ Archivo Histórico de Cierres Diarios")
        reportes_mios = [r for r in reversed(st.session_state.get("reportes_diarios_db", [])) if r.get("empresa") == mi_empresa]
        
        if reportes_mios:
            for r in reportes_mios:
                c1_hist, c2_hist = st.columns([3, 1])
                c1_hist.write(f"📄 **Cierre del día:** {r['fecha_reporte']} | Generado el {r['fecha_generacion']} por {r['generado_por']}")
                pdf_bytes = base64.b64decode(r['pdf_base64'])
                c2_hist.download_button("📥 Descargar", data=pdf_bytes, file_name=f"Cierre_Diario_{r['fecha_reporte'].replace('/','-')}.pdf", mime="application/pdf", key=f"dl_{r['fecha_generacion']}")
        else:
            st.write("Aún no hay reportes de cierre diario guardados.")

# 15. EQUIPO Y SUSCRIPCIONES (SOLO VISIBLE PARA ADMIN/COORDINADOR)
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
            c1.write(f"🏢 {d['empresa']} | 👤 **{d['nombre']}** *(Rol: {d.get('rol', 'Operativo')})* | Login: `{u}` | PIN: `{d.get('pin', 'S/D')}` | Estado: **{d.get('estado', 'Activo')}**")
            if rol == "SuperAdmin":
                if d.get("estado", "Activo") == "Activo" and c2.button("⏸️ Suspender", key=f"susp_{u}"): st.session_state["usuarios_db"][u]["estado"] = "Bloqueado"; guardar_datos(); st.rerun()
                elif d.get("estado", "Activo") != "Activo" and c2.button("▶️ Reactivar", key=f"reac_{u}"): st.session_state["usuarios_db"][u]["estado"] = "Activo"; guardar_datos(); st.rerun()
            if c3.button("❌ Bajar", key=f"del_{u}"): del st.session_state["usuarios_db"][u]; guardar_datos(); st.rerun()

# 16. AUDITORÍA (SOLO VISIBLE PARA ADMIN/COORDINADOR)
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("Auditoría General de Movimientos")
        df_logs = pd.DataFrame(st.session_state["logs_db"])
        
        if not df_logs.empty:
            col_b1, col_b2 = st.columns([2, 1])
            buscar_log = col_b1.text_input("🔍 Filtrar reportes (por Acción, Usuario, etc.):")
            
            if buscar_log:
                mask = df_logs.astype(str).apply(lambda x: x.str.contains(buscar_log, case=False, na=False)).any(axis=1)
                df_logs_filtrado = df_logs[mask]
            else:
                df_logs_filtrado = df_logs
                
            st.dataframe(df_logs_filtrado, use_container_width=True)
            
            out_logs = io.BytesIO()
            with pd.ExcelWriter(out_logs, engine='openpyxl') as writer: df_logs_filtrado.to_excel(writer, index=False, sheet_name='Logs_MediCare')
            st.download_button("📥 DESCARGAR RESULTADOS A EXCEL", data=out_logs.getvalue(), file_name=f"Reporte_Logs_{ahora().strftime('%d_%m_%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("No hay registros en la auditoría.")
        
        st.divider()
        st.subheader("📄 Reporte RRHH (Auditoría de Asistencia por Profesional)")
        if FPDF_DISPONIBLE:
            profesionales_lista = list(set([v['nombre'] for k, v in st.session_state["usuarios_db"].items()]))
            profesionales_historicos = list(set([c.get("profesional", "") for c in st.session_state["checkin_db"]]))
            profesionales_lista = list(set(profesionales_lista + profesionales_historicos))
            
            if profesionales_lista:
                profesionales_lista.sort()
                prof_sel = st.selectbox("Seleccionar Profesional para liquidación:", profesionales_lista)
                
                def t(txt): return str(txt).replace('⚖️', '').replace('⚠️', '').replace('📌', '').replace('📅', '').replace('📸', '').replace('🗄️', '').encode('latin-1', 'replace').decode('latin-1')

                def crear_pdf_rrhh(profesional):
                    pdf = FPDF(); pdf.add_page()
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 10, t(f"REPORTE DE ASISTENCIA Y GPS - {mi_empresa}"), ln=True, align='C')
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 10, t(f"Profesional Auditado: {profesional}"), ln=True)
                    pdf.set_font("Arial", 'I', 9)
                    pdf.cell(0, 5, t(f"Fecha de emisión: {ahora().strftime('%d/%m/%Y %H:%M')}"), ln=True)
                    pdf.ln(5)
                    
                    pdf.set_font("Arial", '', 9)
                    chks_prof = [c for c in st.session_state["checkin_db"] if c.get("profesional", "") == profesional]
                    
                    if not chks_prof:
                        pdf.cell(0, 10, t("No hay registros de visitas (Llegada/Salida) para este profesional."), ln=True)
                    else:
                        for c in reversed(chks_prof):
                            texto_linea = f"[{c.get('fecha_hora', '')}] PACIENTE: {c.get('paciente', '')} | ACCION: {c.get('tipo', '')}"
                            pdf.multi_cell(0, 6, t(texto_linea), border=1)
                            pdf.ln(2)
                            
                    return pdf.output(dest='S').encode('latin-1')

                st.download_button("📥 DESCARGAR REPORTE RRHH (PDF)", crear_pdf_rrhh(prof_sel), f"Auditoria_RRHH_{prof_sel}.pdf", "application/pdf")
        else:
            st.error("Librería FPDF no disponible. Instalar para generar reportes.")

# --- FIN DEL SISTEMA MEDICARE PRO V9.9 ---
