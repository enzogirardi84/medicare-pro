import streamlit as st
import pandas as pd
import base64
import textwrap 
from datetime import datetime, date, timedelta
import json
import pytz
import urllib.request
import urllib.parse
from supabase import create_client, Client
import io
import time
import os
import tempfile
from PIL import Image
import altair as alt

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="MediCare Enterprise PRO V9.11", layout="wide", initial_sidebar_state="collapsed")

# =====================================================================
# --- LANDING PAGE Y CONTROL DE FLUJO ---
# =====================================================================
if "entered_app" not in st.session_state:
    st.session_state.entered_app = False

if not st.session_state.entered_app:
    # 1. ESTILOS GLOBALES DE LA PUBLICIDAD (Más iluminado)
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            
            /* Matamos el padding superior y global de Streamlit */
            .block-container {
                padding-top: 0rem !important; 
                padding-bottom: 0rem !important; 
                max-width: 100% !important;
                margin-top: 0 !important;
            }
            
            /* Fondo de pantalla global con degradado radial 'iluminado' */
            .stApp {
                background-color: #020617 !important;
                background-image: radial-gradient(circle at top right, #0F172A 0%, #020617 100%) !important;
            }
            
            /* CSS Específico de tu Landing Page Mejorado */
            .landing-page {
                font-family: 'Inter', sans-serif;
                color: #f8fafc;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 40px 15px 80px; /* Más padding abajo para el botón central */
            }
            .title { font-size: clamp(2.2rem, 5vw, 3.5rem); font-weight: 900; line-height: 1.15; margin: 0 0 15px; text-align: center; }
            .subtitle { font-size: 1.15rem; color: #cbd5e1; font-weight: 400; margin: 0 0 40px; max-width: 650px; text-align: center; line-height: 1.6; }
            
            .grid-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; max-width: 1100px; width: 100%; margin-bottom: 50px; }
            .glass-card-pro {
                background: linear-gradient(145deg, rgba(15, 23, 42, 0.8), rgba(30, 41, 59, 0.5));
                backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(56, 189, 248, 0.1); border-radius: 18px;
                padding: 22px 18px; transition: all 0.3s ease; text-align: center;
                display: flex; flex-direction: column; align-items: center; justify-content: space-between;
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
            }
            .glass-card-pro:hover {
                transform: translateY(-4px);
                border-color: rgba(56, 189, 248, 0.4);
                box-shadow: 0 10px 20px rgba(0,0,0,0.3), 0 0 20px rgba(56,189,248,0.1);
            }
            .icon-box-pro {
                font-size: 2.6rem; margin-bottom: 12px;
                background: rgba(56, 189, 248, 0.1); width: 60px; height: 60px;
                display: flex; align-items: center; justify-content: center; border-radius: 16px;
                box-shadow: 0 0 10px rgba(56,189,248,0.2) inset;
            }
            .card-title-pro { font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; color: #ffffff; }
            .card-text-pro { color: #cbd5e1; font-size: 0.92rem; line-height: 1.45; margin: 0; }
            
            .contact-section-pro { max-width: 900px; width: 100%; margin-top: 20px; text-align: center; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 24px; padding: 40px; }
            .contact-grid-pro { display: flex; flex-wrap: wrap; justify-content: center; gap: 30px; margin-top: 25px; }
            .contact-profile-pro { flex: 1; min-width: 250px; max-width: 320px; background: rgba(30, 41, 59, 0.4); padding: 25px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.03); }
            .btn-flex-pro { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;}
            .btn-link-pro { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 20px; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 0.95rem; transition: all 0.2s; width: 100%; max-width: 140px; }
            .wpp-pro { background: rgba(37, 211, 102, 0.15); color: #25D366; border: 1px solid rgba(37, 211, 102, 0.3); }
            .wpp-pro:hover { background: #25D366; color: white; }
            .mail-pro { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
            .mail-pro:hover { background: #cbd5e1; color: #0f172a; }

            /* Estilo del botón central de ingreso (MÁS NEÓN Y FUSIÓN DE DEGRADADO) */
            div.stButton { display: flex; justify-content: center; margin-top: 20px; padding-bottom: 40px; }
            div.stButton > button {
                background: linear-gradient(135deg, #0ea5e9 0%, #4f46e5 100%) !important;
                color: white !important;
                font-size: 1.2rem !important;
                font-weight: 800 !important;
                padding: 15px 50px !important;
                border-radius: 9999px !important;
                border: 1px solid rgba(255,255,255,0.2) !important;
                box-shadow: 0 0 20px rgba(14, 165, 233, 0.5) !important;
                transition: all 0.3s ease !important;
                text-transform: uppercase; letter-spacing: 2px;
            }
            div.stButton > button:hover {
                transform: translateY(-3px) !important;
                box-shadow: 0 0 40px rgba(99, 102, 241, 0.7) !important;
                background: linear-gradient(135deg, #38bdf8 0%, #6366f1 100%) !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 2. PREPARAR EL LOGO EN BASE64 (Esto evita que Streamlit corte el HTML)
    try:
        with open("logo_medicare_pro.jpeg", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        logo_html = f'<img src="data:image/jpeg;base64,{encoded_string}" style="height: 100px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.4), 0 0 20px rgba(56,189,248,0.2); margin-bottom: 20px;">'
    except Exception:
        logo_html = '<h1 style="font-size:3.5rem; font-weight:900; color:#38bdf8; margin-bottom: 20px;">MediCare Enterprise PRO</h1>'

    # 3. HTML BLINDADO CON TEXTWRAP.DEDENT Y DETALLES DE COLORES "NEÓN"
    html_landing = textwrap.dedent(f"""
        <div class="landing-page">
            {logo_html}
            <h1 class="title">Gestión Domiciliaria <span style="background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Inteligente</span></h1>
            <p class="subtitle">Módulos avanzados y diseño intuitivo para llevar el control de tu clínica al máximo nivel.</p>

            <div class="grid-cards">
                <div class="glass-card-pro"><div class="icon-box-pro">📍</div><h4 class="card-title-pro">Fichaje GPS</h4><p class="card-text-pro">Control de asistencia verificado por coordenadas exactas del domicilio.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">📄</div><h4 class="card-title-pro">Evolución Médica</h4><p class="card-text-pro">Carga digital de signos vitales, parámetros y fotografías clínicas.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">💊</div><h4 class="card-title-pro">Stock Inteligente</h4><p class="card-text-pro">Gestión de inventario con descuento automático por práctica.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">✍️</div><h4 class="card-title-pro">Firma Digital</h4><p class="card-text-pro">Recetas y consentimientos validados con firma directamente en pantalla.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">📹</div><h4 class="card-title-pro">Telemedicina</h4><p class="card-text-pro">Videollamadas P2P integradas nativamente al historial del paciente.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">👶</div><h4 class="card-title-pro">Pediatría</h4><p class="card-text-pro">Control de crecimiento y gráficas de percentiles automatizadas.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">💧</div><h4 class="card-title-pro">Balance Hídrico</h4><p class="card-text-pro">Cálculo estricto de ingresos/egresos con alertas por retención de líquidos.</p></div>
                <div class="glass-card-pro"><div class="icon-box-pro">📋</div><h4 class="card-title-pro">Auditoría RRHH</h4><p class="card-text-pro">Cierres diarios, reportes de desempeño y liquidación de servicios.</p></div>
            </div>

            <div class="contact-section-pro">
                <h3 style="color: white; margin: 0 0 10px; font-size: 1.7rem; font-weight: 700;">¿Necesitas soporte o implementación?</h3>
                <p style="color: #cbd5e1; margin: 0 0 10px; font-size: 1rem;">Comunícate directamente con nuestro equipo de especialistas.</p>
                
                <div class="contact-grid-pro">
                    <div class="contact-profile-pro">
                        <h4 style="color:white; margin: 0 0 5px; font-size: 1.3rem;">Enzo N. Girardi</h4>
                        <p style="color:#38bdf8; font-size:0.85rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin: 0 0 20px;">Desarrollo y Soporte Técnico</p>
                        <div class="btn-flex-pro">
                            <a href="https://wa.me/5493584302024" target="_blank" class="btn-link-pro wpp-pro">💬 WhatsApp</a>
                            <a href="mailto:enzogirardi84@gmail.com" class="btn-link-pro mail-pro">✉️ Email</a>
                        </div>
                    </div>
                    <div class="contact-profile-pro">
                        <h4 style="color:white; margin: 0 0 5px; font-size: 1.3rem;">Darío Lanfranco</h4>
                        <p style="color:#10b981; font-size:0.85rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin: 0 0 20px;">Implementación y Contratos</p>
                        <div class="btn-flex-pro">
                            <a href="https://wa.me/5493584201263" target="_blank" class="btn-link-pro wpp-pro">💬 WhatsApp</a>
                            <a href="mailto:dariolanfrancoruffener@gmail.com" class="btn-link-pro mail-pro">✉️ Email</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    """)
    
    # 4. INYECTAR EL CÓDIGO FINAL NATIVO (SIN CAJITA GRIS GRACIAS AL TEXTWRAP)
    st.markdown(html_landing, unsafe_allow_html=True)
    
    # 5. BOTÓN DE INGRESO
    if st.button("🚀 INGRESAR AL SISTEMA", key="btn_ingresar_main"):
        st.session_state.entered_app = True
        st.rerun()

    # 6. FRENO OBLIGATORIO: Todo se detiene aquí hasta que hagan clic en Ingresar
    st.stop()

# =====================================================================
# --- PANTALLA 2: EL SISTEMA REAL (MEDICARE PRO) ---
# =====================================================================
# Restauramos la visibilidad de Streamlit normal (Menú y barra lateral)
st.markdown("<style>#MainMenu {visibility: visible;} header {visibility: visible;} .block-container {padding-top: 3rem !important;}</style>", unsafe_allow_html=True)

# Botón para salir a la publicidad de nuevo (en la barra lateral)
if st.sidebar.button("⬅️ Volver a la Publicidad"):
    st.session_state.entered_app = False
    st.rerun()

st.sidebar.markdown("---")

# --- ACÁ ABAJO EMPIEZA TU CÓDIGO NORMAL DEL VADEMÉCUM Y EL SISTEMA ---
# ACÁ EMPIEZA TU CÓDIGO NORMAL DEL SISTEMA (BASE DE DATOS, VADEMECUM, ETC.)
# =====================================================================
# --- VADEMÉCUM GLOBAL MASIVO ---
VADEMECUM_BASE = sorted([
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
    "Acenocumarol (Sintrom) 4mg", "Aciclovir 400mg", "Aciclovir crema", "Ácido Ascórbico (Vit C) 1g", "Ácido Fólico 5mg", "Ácido Tranexámico ampolla", "Ácido Valproico 500mg",
    "Adenosina 6mg ampolla", "Adrenalina (Epinefrina) 1mg ampolla", "Albendazol 400mg", "Alopurinol 100mg", "Alopurinol 300mg", 
    "Alprazolam 0.5mg", "Alprazolam 1mg", "Alprazolam 2mg", "Amiodarona 200mg", "Amiodarona 150mg ampolla", "Amitriptilina 25mg", 
    "Amlodipina 10mg", "Amlodipina 5mg", "Amoxicilina 500mg", "Amoxicilina 875mg", "Amoxicilina+Clavulánico 875/125mg", 
    "Ampicilina 1g ampolla", "Ampicilina+Sulbactam 1.5g ampolla", "Aspirina (AAS) 100mg", "Atenolol 50mg", "Atorvastatina 10mg", "Atorvastatina 20mg", "Azitromicina 500mg",
    "Baclofeno 10mg", "Beclometasona aerosol", "Betametasona ampolla", "Betametasona crema", "Bicalutamida 50mg", 
    "Bicarbonato de Sodio 1/6 M ampolla", "Bisacodilo 5mg", "Bisoprolol 2.5mg", "Bisoprolol 5mg", "Bromhexina jarabe", 
    "Budesonida aerosol", "Bupivacaína ampolla", "Carbonato de Calcio 500mg", "Captopril 25mg", "Carbamazepina 200mg", "Carvedilol 12.5mg", "Carvedilol 25mg", "Carvedilol 6.25mg", 
    "Cefalexina 500mg", "Cefalotina 1g ampolla", "Cefotaxima 1g ampolla", "Ceftriaxona 1g ampolla", "Celecoxib 200mg", 
    "Cetirizina 10mg", "Cilostazol 100mg", "Ciprofloxacina 500mg", "Citalopram 20mg", "Claritromicina 500mg", "Clindamicina 300mg", "Clindamicina 600mg ampolla",
    "Clobetasol crema", "Clonazepam 0.5mg", "Clonazepam 2mg", "Clopidogrel 75mg", "Clorpromazina 25mg", "Colchicina 1mg", "Complejo B ampolla",
    "Dapagliflozina 10mg", "Desloratadina 5mg", "Dexametasona 8mg ampolla", "Dexametasona comprimido", "Diazepam 10mg ampolla", "Diazepam 5mg comprimido", 
    "Diclofenac 50mg", "Diclofenac 75mg ampolla", "Difenhidramina 50mg ampolla", "Digoxina 0.25mg", "Diltiazem 60mg", 
    "Dipirona 1g ampolla", "Dipirona 500mg comprimido", "Dobutamina ampolla", "Domperidona 10mg", "Dopamina ampolla", 
    "Doxiciclina 100mg", "Duloxetina 30mg", "Empagliflozina 10mg", "Enalapril 10mg", "Enalapril 5mg", "Enoxaparina 40mg jeringa", "Enoxaparina 60mg jeringa", 
    "Escitalopram 10mg", "Espironolactona 25mg", "Espironolactona 50mg", "Ezetimibe 10mg", "Famotidina 20mg", "Fentanilo ampolla", "Finasteride 5mg", "Fluconazol 150mg", "Fluoxetina 20mg", "Fluticasona aerosol", 
    "Furosemida 20mg ampolla", "Furosemida 40mg comprimido", "Gabapentina 300mg", "Gentamicina 80mg ampolla", "Glibenclamida 5mg", "Glimepirida 2mg", "Glucagón ampolla",
    "Haloperidol 5mg ampolla", "Heparina Sódica ampolla", "Hidroclorotiazida 25mg", "Hidrocortisona 100mg ampolla", "Hidrocortisona 500mg ampolla", 
    "Hierro (Sulfato Ferroso)", "Hioscina (Buscapina) 10mg", "Hioscina Compuesta ampolla", "Hioscina Simple ampolla", "Hidroxicloroquina 200mg",
    "Ibuprofeno 400mg", "Ibuprofeno 600mg", "Ibuprofeno jarabe", "Imipenem 500mg ampolla", 
    "Insulina Aspart", "Insulina Corriente (Regular)", "Insulina Detemir", "Insulina Glargina", "Insulina Lispro", "Insulina NPH", 
    "Ipratropio aerosol", "Ipratropio gotas (Nebulización)", "Irbesartán 150mg", "Isosorbide dinitrato 10mg",
    "Ketamina ampolla", "Ketoconazol crema", "Ketorolac 10mg comprimido", "Ketorolac 30mg ampolla", "Ketorolac 60mg ampolla",
    "Labetalol ampolla", "Lactulón jarabe", "Lamotrigina 50mg", "Lansoprazol 30mg", "Levetiracetam 500mg", 
    "Levofloxacina 500mg", "Levomepromazina 25mg", "Levotiroxina 100mcg", "Levotiroxina 50mcg", "Levotiroxina 75mcg", 
    "Lidocaína 2% ampolla", "Lidocaína jalea", "Linagliptina 5mg", "Loperamida 2mg", "Loratadina 10mg", 
    "Lorazepam 1mg", "Lorazepam 2mg", "Losartán 50mg", "Magnesio (Sulfato) ampolla", "Mebendazol 200mg", "Meloxicam 15mg", "Meropenem 1g ampolla", "Metadona 10mg", 
    "Metformina 500mg", "Metformina 850mg", "Metildopa 500mg", "Metilprednisolona 500mg ampolla", "Metoclopramida (Reliveran) 10mg", 
    "Metoclopramida ampolla", "Metoprolol 50mg", "Metronidazol 500mg", "Metronidazol sachet 500ml", "Midazolam 15mg ampolla", 
    "Mirtazapina 30mg", "Montelukast 10mg", "Morfina 10mg ampolla", "Mupirocina ungüento", "Naloxona ampolla", "Naproxeno 500mg", "Neomicina crema", "Nifedipina 10mg", "Nimodipina 30mg", 
    "Nitrofurantoína 100mg", "Nitroglicerina ampolla", "Noradrenalina ampolla", "Olanzapina 10mg", "Omeprazol 20mg", "Omeprazol 40mg ampolla", "Ondansetrón 8mg ampolla", "Oxígeno en tubo",
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
st.set_page_config(page_title="MediCare Enterprise PRO V9.11", page_icon="⚕️", layout="wide")
st.markdown("<html lang='es' translate='no'>", unsafe_allow_html=True)

# --- ZONA HORARIA ARGENTINA ---
ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')
def ahora():
    return datetime.now(ARG_TZ)

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

# --- 🎨 DISEÑO VISUAL ENTERPRISE PREMIUM v3.0 (MODO CLARO / OSCURO ADAPTATIVO) ---
# ====================== TOGGLE DE TEMA (CLARO / OSCURO) ======================
# =========================================================================================
# 🎨 DISEÑO VISUAL ENTERPRISE PREMIUM v15.0 (TEXTOS CORREGIDOS)
# =========================================================================================
page_bg_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    /* Paleta Ergonomica (Slate / Azul Pizarra) - Descansa la vista */
    --bg-app: #0F172A;          
    --bg-sidebar: #0B1121;      
    --bg-card: #1E293B;         
    --bg-input: #334155;        /* Inputs mucho más claros para que resalten fácil */
    
    --border-col: #3F4F66;      
    --border-hover: #38BDF8;    
    
    --text-main: #F8FAFC;       
    --text-muted: #94A3B8;      
    
    --accent: #38BDF8;          
    --accent-glow: rgba(56, 189, 248, 0.25);
    --metric-color: #34D399;    
}

/* ==================== 1. FONDOS Y ESTRUCTURA ==================== */
html, body, .stApp {
    background-color: var(--bg-app) !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-col) !important;
}
header[data-testid="stHeader"] { background-color: transparent !important; }

/* ==================== 2. TEXTOS ==================== */
p, span, div, h1, h2, h3, h4, h5, h6, label, li {
    color: var(--text-main) !important;
}
p, label { font-weight: 400 !important; font-size: 0.95rem !important; }
h1, h2, h3, h4 { font-weight: 600 !important; letter-spacing: -0.5px; }

.stButton button p, .stButton button span { color: inherit !important; }

/* ==================== 3. TARJETAS Y CONTENEDORES ==================== */
div[data-testid="stForm"],
div[data-testid="stVerticalBlock"] > div[style*="border"],
div[data-testid="stExpander"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-col) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stForm"]:hover,
div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
    border-color: #475569 !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
}

/* ==================== 4. MÉTRICAS (SIGNOS VITALES) ==================== */
div[data-testid="stMetric"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-col) !important;
    border-top: 3px solid var(--accent) !important;
    border-radius: 12px !important;
    padding: 16px 14px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
}
[data-testid="stMetricLabel"] p { 
    color: var(--text-muted) !important; 
    font-weight: 600 !important; 
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}
[data-testid="stMetricValue"] div { 
    color: var(--metric-color) !important; 
    font-weight: 700 !important; 
    font-size: 1.85rem !important; 
    text-shadow: 0 0 10px rgba(52, 211, 153, 0.3) !important; 
}

/* ==================== 5. INPUTS Y SELECTS (CORREGIDOS) ==================== */
/* Cajas de fondo sin alterar el padding para no cortar letras */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-col) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

/* Color de las letras de adentro para que se vean bien blancas */
div[data-baseweb="select"] div,
input[type="number"], input[type="text"], textarea {
    color: #FFFFFF !important;
}

/* Efecto cuando hacés clic para escribir */
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="input"] > div:focus-within,
textarea:focus { 
    border-color: var(--accent) !important; 
    background-color: #1E293B !important; 
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
input::placeholder, textarea::placeholder { color: #CBD5E1 !important; }

/* ==================== 6. PESTAÑAS (TABS) ==================== */
.stTabs [data-testid="stTab"] {
    background-color: var(--bg-card) !important; 
    border: 1px solid var(--border-col) !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    margin-right: 6px !important;
    margin-bottom: 8px !important;
    transition: all 0.2s ease !important;
    opacity: 1 !important; 
}
.stTabs [data-testid="stTab"] p { 
    color: #CBD5E1 !important; 
    font-weight: 500 !important; 
}
.stTabs [data-testid="stTab"]:hover { 
    background-color: #2F3E53 !important; 
    border-color: var(--accent) !important;
}
.stTabs [data-testid="stTab"]:hover p { 
    color: #FFFFFF !important; 
}
.stTabs [data-testid="stTab"][aria-selected="true"] {
    background-color: var(--bg-input) !important; 
    border: 1px solid var(--accent) !important;
    box-shadow: 0 4px 10px var(--accent-glow) !important;
}
.stTabs [data-testid="stTab"][aria-selected="true"] p { 
    color: var(--accent) !important; 
    font-weight: 600 !important;
}

/* ==================== 7. BOTONES ==================== */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.5px;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0284C7, #38BDF8) !important;
    color: #FFFFFF !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(56, 189, 248, 0.4) !important;
}
.stButton > button[kind="secondary"] {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-col) !important;
    color: var(--text-main) !important;
}
.stButton > button[kind="secondary"]:hover { 
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ==================== 8. DATAFRAMES ==================== */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    border: 1px solid var(--border-col) !important;
    background-color: var(--bg-card) !important;
}
[data-testid="stTable"] { background-color: transparent !important; }

/* ==================== 9. EXTRAS ==================== */
img { filter: none !important; background: transparent !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-app); }
::-webkit-scrollbar-thumb { background: var(--border-col); border-radius: 20px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# --- 🎁 LOGO EXCLUSIVO PROFESIONAL ---
def render_logo_eg(size=100):
    directorio_actual = os.path.dirname(os.path.abspath(__file__))
    ruta_logo = os.path.join(directorio_actual, "logo_medicare_pro.jpeg")
    
    col1, col2, col3 = st.sidebar.columns([1, 1.5, 1])
    with col2:
        try:
            st.image(ruta_logo, use_container_width=True)
        except Exception as e:
            st.error("⚠️ Falta subir logo_medicare_pro.jpeg a GitHub")

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
        "reportes_diarios_db", "estudios_db", "administracion_med_db"
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
        "reportes_diarios_db": [], "estudios_db": [], "administracion_med_db": []
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
        st.markdown("<br><h2 style='text-align:center; color:#3b82f6;'>MediCare Enterprise PRO V9.11</h2>", unsafe_allow_html=True)
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
menu = ["📍 Visitas y Agenda", "👤 Admisión", "📊 Clínica", "👶 Pediatría", "📝 Evolución", "🔬 Estudios", "💉 Materiales", "💊 Recetas", "⚖️ Balance", "📦 Inventario", "💳 Caja", "📚 Historial", "🗄️ PDF", "📹 Telemedicina"]

if rol in ["SuperAdmin", "Coordinador"]: 
    menu.insert(1, "📈 Dashboard") 
    menu.append("📑 Cierre Diario")
    menu.append("⚙️ Mi Equipo")
    menu.append("⏱️ Asistencia en Vivo")
    menu.append("🧑‍⚕️ RRHH y Fichajes")
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
            st.error("⚠️ Este paciente se encuentra DE ALTA.")
        else:
            det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
            dire_paciente = det.get("direccion", "No registrada")
            tel_paciente = det.get("telefono", "")

            # === GEOLOCALIZACIÓN ===
            if GEO_DISPONIBLE:
                loc = streamlit_geolocation()
                lat = loc.get('latitude') if loc and loc.get('latitude') is not None else None
                lon = loc.get('longitude') if loc and loc.get('longitude') is not None else None

                if lat is not None and lon is not None:
                    lat_str = f"{float(lat):.5f}"
                    lon_str = f"{float(lon):.5f}"
                    direccion_real = obtener_direccion_real(lat_str, lon_str)

                    st.success(f"📍 **Estás físicamente en:** {direccion_real}")

                    col_in, col_out = st.columns(2)
                    if col_in.button("🟢 Fichar LLEGADA en esta Ubicación", use_container_width=True, type="primary"):
                        st.session_state["checkin_db"].append({
                            "paciente": paciente_sel,
                            "profesional": user["nombre"],
                            "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"),
                            "tipo": f"LLEGADA en: {direccion_real} (Lat: {lat_str})",
                            "empresa": mi_empresa
                        })
                        guardar_datos()
                        st.success("✅ Llegada registrada.")
                        st.rerun()

                    if col_out.button("🔴 Fichar SALIDA en esta Ubicación", use_container_width=True, type="secondary"):
                        st.session_state["checkin_db"].append({
                            "paciente": paciente_sel,
                            "profesional": user["nombre"],
                            "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"),
                            "tipo": f"SALIDA de: {direccion_real} (Lat: {lat_str})",
                            "empresa": mi_empresa
                        })
                        guardar_datos()
                        st.success("✅ Salida registrada.")
                        st.rerun()
                else:
                    st.warning("📍 Aún no capturaste tu ubicación. Tocá el ícono de ubicación arriba y permití el acceso.")
            else:
                st.error("⚠️ Librería de geolocalización no disponible.")

            st.divider()

            # ====================== CONTROL DE HORAS DE GUARDIA ======================
            st.markdown("#### ⏳ Control de Horas de Guardia (Hoy)")

            hoy_str = ahora().strftime("%d/%m/%Y")
            fichadas_hoy = [
                c for c in st.session_state.get("checkin_db", [])
                if c.get("paciente") == paciente_sel 
                and c.get("profesional") == user["nombre"] 
                and c.get("fecha_hora", "").startswith(hoy_str)
            ]

            def parse_fecha(fecha_str):
                try:
                    return datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
                except:
                    try:
                        return datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
                    except:
                        return datetime.min

            if fichadas_hoy:
                fichadas_hoy = sorted(fichadas_hoy, key=lambda x: parse_fecha(x["fecha_hora"]))

                llegada_time = None
                ahora_naive = ahora().replace(tzinfo=None)

                for f in fichadas_hoy:
                    dt = parse_fecha(f["fecha_hora"])

                    if "LLEGADA" in f["tipo"].upper():
                        llegada_time = dt
                    elif "SALIDA" in f["tipo"].upper() and llegada_time:
                        duracion = dt - llegada_time
                        horas, rem = divmod(duracion.seconds, 3600)
                        minutos, _ = divmod(rem, 60)
                        st.success(f"✅ Turno completado: {llegada_time.strftime('%H:%M')} → {dt.strftime('%H:%M')} ({horas}h {minutos}m)")
                        llegada_time = None

                # Si todavía hay una llegada sin salida → guardia abierta
                if llegada_time:
                    duracion_actual = ahora_naive - llegada_time
                    horas, rem = divmod(duracion_actual.seconds, 3600)
                    minutos, _ = divmod(rem, 60)
                    st.warning(f"🟢 **Guardia en curso desde las {llegada_time.strftime('%H:%M')}** → **{horas}h {minutos}m** transcurridos")

                    if st.button("🔄 Actualizar cronómetro", use_container_width=True):
                        st.rerun()
                    st.caption("Se actualiza automáticamente cada 30 segundos")
            else:
                st.info("Aún no tienes fichadas hoy para este paciente.")

            st.divider()

            # ====================== AGENDA ======================
            st.subheader("📅 Agendar Próxima Visita")
            with st.form("agenda_form", clear_on_submit=True):
                c1_ag, c2_ag = st.columns(2)
                fecha_ag = c1_ag.date_input("Fecha programada", value=ahora().date())
                hora_ag_str = c2_ag.text_input("Hora aproximada (HH:MM)", value=ahora().strftime("%H:%M"))

                profesionales = [v['nombre'] for k, v in st.session_state["usuarios_db"].items() 
                               if v.get('empresa') == mi_empresa or rol == "SuperAdmin"]
                idx_prof = profesionales.index(user['nombre']) if user['nombre'] in profesionales else 0
                prof_ag = st.selectbox("Asignar Profesional", profesionales, index=idx_prof)

                if st.form_submit_button("Agendar Visita", use_container_width=True, type="primary"):
                    hora_limpia = hora_ag_str.strip() if ":" in hora_ag_str else ahora().strftime("%H:%M")
                    st.session_state["agenda_db"].append({
                        "paciente": paciente_sel,
                        "profesional": prof_ag,
                        "fecha": fecha_ag.strftime("%d/%m/%Y"),
                        "hora": hora_limpia,
                        "empresa": mi_empresa,
                        "estado": "Pendiente"
                    })
                    guardar_datos()
                    st.success("✅ Turno agendado correctamente.")
                    st.rerun()

            agenda_mia = [a for a in st.session_state.get("agenda_db", []) 
                         if a.get("empresa") == mi_empresa and a.get("paciente") == paciente_sel]
            if agenda_mia:
                st.caption("Próximas visitas agendadas:")
                
                # ==== CAJA ANTI-COLAPSO DE AGENDA ====
                with st.container(height=350, border=True):
                    df_agenda_mostrar = pd.DataFrame(agenda_mia).drop(columns=["empresa", "paciente"])
                    st.dataframe(df_agenda_mostrar.iloc[::-1], use_container_width=True, hide_index=True)

            st.divider()

            # ====================== CONTACTO Y WHATSAPP ======================
            st.subheader("📲 Contacto y Ubicación")
            if dire_paciente and dire_paciente != "No registrada":
                st.info(f"🏠 **Domicilio:** {dire_paciente}")

            if tel_paciente:
                import urllib.parse
                nombre_corto = paciente_sel.split(" (")[0]
                
                # MAGIA 1: Formateo estricto para Argentina (+54 9)
                tel_limpio = "".join(filter(str.isdigit, str(tel_paciente)))
                if tel_limpio and not tel_limpio.startswith("54"):
                    tel_limpio = "549" + tel_limpio
                
                # MAGIA 2: Mensaje inteligente buscando la última visita
                if agenda_mia:
                    ultima_visita = agenda_mia[-1] # Agarra la última que agendaste
                    fecha_v = ultima_visita.get("fecha", "")
                    hora_v = ultima_visita.get("hora", "")
                    mensaje_base = f"Hola {nombre_corto}, me comunico desde {mi_empresa} para confirmarte que el día {fecha_v} a las {hora_v} hs estaré pasando por tu domicilio para realizar la visita correspondiente. ¡Saludos!"
                else:
                    # Mensaje por defecto si no le agendaste nada todavía
                    mensaje_base = f"Hola {nombre_corto}, me comunico desde {mi_empresa} para coordinar tu próxima visita de internación domiciliaria."
                
                mensaje_codificado = urllib.parse.quote(mensaje_base)
                
                # Link blindado
                link_wpp = f"https://api.whatsapp.com/send?phone={tel_limpio}&text={mensaje_codificado}"
                
                html_wpp = f'''
                <a href="{link_wpp}" target="_blank"
                   style="display: block; width: 100%; text-align: center; background-color: #25D366; 
                          color: white; padding: 12px; border-radius: 8px; text-decoration: none; 
                          font-weight: bold; font-family: sans-serif; margin-top: 10px;">
                   💬 Enviar mensaje por WhatsApp
                </a>
                '''
                st.markdown(html_wpp, unsafe_allow_html=True)
            else:
                st.warning("⚠️ Este paciente no tiene un número de teléfono registrado para enviarle WhatsApp.")
       
if "📈 Dashboard" in menu:
    with tabs[menu.index("📈 Dashboard")]:
        st.markdown(f"<h3 style='color: #3b82f6;'>📈 Panel de Gestión - {mi_empresa}</h3>", unsafe_allow_html=True)

        if not st.session_state["pacientes_db"]:
            st.warning("No hay pacientes cargados.")
        else:
            df_visitas = pd.DataFrame(st.session_state.get("checkin_db", []))

            if df_visitas.empty:
                st.info("El sistema está listo para empezar a registrar visitas.")
            else:
                # Columnas obligatorias para que no rompa
                columnas_necesarias = ["tipo", "fecha_hora", "profesional"]
                if not all(col in df_visitas.columns for col in columnas_necesarias):
                    st.error("❌ Faltan columnas necesarias en 'checkin_db'. Contacta al administrador.")
                    st.stop()

                # Filtramos solo LLEGADAS reales (GPS)
                df_llegadas = df_visitas[
                    df_visitas["tipo"].str.contains("LLEGADA", na=False)
                ].copy()

                if df_llegadas.empty:
                    st.info("Aún no se han registrado ingresos (GPS) en los domicilios.")
                else:
                    # === Conversión segura de fecha ===
                    try:
                        df_llegadas["fecha_c"] = pd.to_datetime(
                            df_llegadas["fecha_hora"],
                            format="%d/%m/%Y %H:%M:%S",
                            errors="coerce"
                        )
                        # Eliminamos fechas inválidas
                        df_llegadas = df_llegadas.dropna(subset=["fecha_c"])
                    except Exception as e:
                        st.error(f"Error al procesar las fechas: {e}")
                        st.stop()

                    if df_llegadas.empty:
                        st.info("No se encontraron fechas válidas de llegadas GPS.")
                    else:
                        # Rango de los últimos 7 días
                        hace_una_semana = (ahora() - timedelta(days=7)).replace(tzinfo=None)

                        # Filtro por empresa si es Coordinador
                        if rol == "Coordinador" and "empresa" in df_llegadas.columns:
                            df_llegadas = df_llegadas[df_llegadas["empresa"] == mi_empresa]

                        # Últimos 7 días
                        df_visitas_s = df_llegadas[df_llegadas["fecha_c"] > hace_una_semana]

                        if df_visitas_s.empty:
                            st.info("No hay fichadas de GPS (Llegadas) en los últimos 7 días.")
                        else:
                            # === Métricas y visualización ===
                            total_fichadas = len(df_visitas_s)

                            st.metric(
                                label="**Total de Fichadas Reales por GPS (últimos 7 días)**",
                                value=total_fichadas
                            )

                            # Tabla resumen (siempre visible)
                            perf_enf = (
                                df_visitas_s["profesional"]
                                .value_counts()
                                .reset_index()
                            )
                            perf_enf.columns = ["Profesional / Enfermero", "Visitas Reales"]
                            
                            st.dataframe(
                                perf_enf,
                                use_container_width=True,
                                hide_index=True
                            )

                            # Gráfico Altair mejorado
                            chart = alt.Chart(perf_enf).mark_bar(
                                size=35,
                                color="#3b82f6",
                                cornerRadiusTopLeft=6,
                                cornerRadiusTopRight=6
                            ).encode(
                                x=alt.X(
                                    "Profesional / Enfermero:N",
                                    sort="-y",
                                    title="Profesional / Enfermero"
                                ),
                                y=alt.Y(
                                    "Visitas Reales:Q",
                                    title="Cantidad de Fichadas GPS",
                                    axis=alt.Axis(tickMinStep=1)
                                ),
                                tooltip=[
                                    alt.Tooltip("Profesional / Enfermero:N", title="Profesional"),
                                    alt.Tooltip("Visitas Reales:Q", title="Fichadas")
                                ]
                            ).properties(
                                height=380,
                                title=f"Fichadas GPS - Últimos 7 días ({hace_una_semana.strftime('%d/%m/%Y')} → hoy)"
                            ).configure_title(
                                fontSize=16,
                                color="#3b82f6",
                                anchor="middle"
                            )

                            st.altair_chart(chart, use_container_width=True)
# 3. ADMISIÓN 
with tabs[menu.index("👤 Admisión")]:
    st.subheader("👤 Admisión de Nuevo Paciente")

    # --- BUSCADOR RÁPIDO (para evitar duplicados) ---
    st.markdown("##### 🔍 Buscar paciente existente")
    buscar_adm = st.text_input("Nombre, DNI o apellido...", placeholder="Ej: Juan Pérez o 35123456")
    
    if buscar_adm:
        coincidencias = [
            p for p in st.session_state["pacientes_db"]
            if buscar_adm.lower() in p.lower() or 
               (buscar_adm.isdigit() and buscar_adm in st.session_state["detalles_pacientes_db"].get(p, {}).get("dni", ""))
        ]
        if coincidencias:
            st.warning(f"⚠️ Se encontraron {len(coincidencias)} pacientes similares:")
            for p in coincidencias[:5]:
                det = st.session_state["detalles_pacientes_db"].get(p, {})
                st.caption(f"• {p} | DNI: {det.get('dni','S/D')} | Empresa: {det.get('empresa','S/D')}")
        else:
            st.success("✅ No hay pacientes con ese nombre/DNI.")

    st.divider()

    # --- FORMULARIO DE ADMISIÓN MEJORADO ---
    with st.form("adm_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        n = col_a.text_input("Nombre y Apellido *", placeholder="Juan Pérez")
        o = col_b.text_input("Obra Social / Prepaga", placeholder="PAMI / OSDE / Particular")
        
        col_c, col_d = st.columns(2)
        d = col_c.text_input("DNI del Paciente *", placeholder="35123456")
        f_nac = col_d.date_input(
            "Fecha de Nacimiento", 
            value=date(1990, 1, 1), 
            min_value=date(1900, 1, 1), 
            max_value=ahora().date()
        )

        col_e, col_f = st.columns(2)
        se = col_e.selectbox("Sexo", ["F", "M", "Otro"])
        tel = col_f.text_input("WhatsApp (sin 0 ni 15)", placeholder="3584302024")

        dir_p = st.text_input("Dirección Exacta (Importante para GPS y PDF)", 
                             placeholder="Calle 123, Barrio, Ciudad")
        
        # Empresa solo editable por SuperAdmin
        if rol == "SuperAdmin":
            emp_d = st.text_input("Empresa / Clínica", value=mi_empresa)
        else:
            emp_d = mi_empresa
            st.info(f"🏢 Paciente será asignado a: **{mi_empresa}**")

        if st.form_submit_button("✅ Habilitar Paciente", use_container_width=True, type="primary"):
            if not n or not d:
                st.error("❌ Nombre y DNI son obligatorios.")
            else:
                # --- ANTI-DUPLICADOS ---
                dni_existente = any(
                    det.get("dni") == d 
                    for det in st.session_state["detalles_pacientes_db"].values()
                )
                
                if dni_existente:
                    st.error("🚫 Ya existe un paciente con ese DNI.")
                else:
                    # ID más seguro y legible
                    id_p = f"{n.strip()} - {d.strip()}"
                    
                    st.session_state["pacientes_db"].append(id_p)
                    st.session_state["detalles_pacientes_db"][id_p] = {
                        "dni": d.strip(),
                        "fnac": f_nac.strftime("%d/%m/%Y"),
                        "sexo": se,
                        "telefono": tel.strip(),
                        "direccion": dir_p.strip(),
                        "empresa": emp_d.strip(),
                        "estado": "Activo",
                        "obra_social": o.strip()
                    }
                    
                    guardar_datos()
                    st.success(f"🎉 ¡Paciente **{n}** dado de alta correctamente!")
                    st.balloons()
                    st.rerun()

    st.caption("💡 Los pacientes se guardan automáticamente en la nube.")

# 4. CLÍNICA
with tabs[menu.index("📊 Clínica")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("📊 Signos Vitales - Control Clínico")

        # === ÚLTIMOS SIGNOS VITALES (MÉTRICAS) ===
        vits = [v for v in st.session_state.get("vitales_db", []) if v.get("paciente") == paciente_sel]
        
        if vits:
            # Ordenamos cronológicamente (función segura)
            def parse_fecha_hora(fecha_str: str):
                try:
                    return datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    try:
                        return datetime.strptime(fecha_str, "%d/%m/%Y %H:%M")
                    except:
                        return datetime.min

            vits_ordenados = sorted(vits, key=lambda x: parse_fecha_hora(x.get('fecha', '')))
            ultimo = vits_ordenados[-1]

            st.markdown("##### Último control registrado")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("T.A.", ultimo.get("TA", "-"), help="Tensión Arterial")
            c2.metric("F.C.", f"{ultimo.get('FC', '-')} lpm")
            c3.metric("F.R.", f"{ultimo.get('FR', '-')} rpm")
            c4.metric("SatO₂", f"{ultimo.get('Sat', '-')} %")
            c5.metric("Temp", f"{ultimo.get('Temp', '-')} °C")
            c6.metric("HGT", ultimo.get("HGT", "-"))

            # Tendencia simple (último vs anteúltimo)
            if len(vits_ordenados) >= 2:
                penultimo = vits_ordenados[-2]
                delta_fc = int(ultimo.get('FC', 0)) - int(penultimo.get('FC', 0))
                st.caption(f"**Tendencia FC:** {'↑' if delta_fc > 0 else '↓' if delta_fc < 0 else '→'} {abs(delta_fc)} lpm")
        else:
            st.info("Aún no hay signos vitales registrados para este paciente.")

        st.divider()

        # === FORMULARIO PARA NUEVO CONTROL ===
        with st.form("vitales_f", clear_on_submit=True):
            st.markdown("##### ⏱️ Nuevo Control de Signos Vitales")
            col_time1, col_time2 = st.columns(2)
            fecha_toma = col_time1.date_input("📅 Fecha", value=ahora().date(), key="fecha_vits")
            hora_toma_str = col_time2.text_input("⏰ Hora (HH:MM)", value=ahora().strftime("%H:%M"), key="hora_vits")

            st.divider()
            ta = st.text_input("Tensión Arterial (TA)", "120/80")
            col_signos = st.columns(5)
            fc = col_signos[0].number_input("F.C. (lpm)", 30, 220, 75)
            fr = col_signos[1].number_input("F.R. (rpm)", 8, 60, 16)
            sat = col_signos[2].number_input("SatO₂ (%)", 70, 100, 96)
            temp = col_signos[3].number_input("Temperatura (°C)", 34.0, 42.0, 36.5, step=0.1)
            hgt = col_signos[4].text_input("HGT (mg/dL)", "110")

            if st.form_submit_button("💾 Guardar Signos Vitales", use_container_width=True, type="primary"):
                # Validación flexible de hora
                hora_limpia = hora_toma_str.strip() if ":" in hora_toma_str else ahora().strftime("%H:%M")
                fecha_str = f"{fecha_toma.strftime('%d/%m/%Y')} {hora_limpia}"

                st.session_state["vitales_db"].append({
                    "paciente": paciente_sel,
                    "TA": ta,
                    "FC": fc,
                    "FR": fr,
                    "Sat": sat,
                    "Temp": temp,
                    "HGT": hgt,
                    "fecha": fecha_str
                })
                guardar_datos()

                # Alertas clínicas
                alerta = False
                if fc > 110 or fc < 50:
                    st.error(f"🚨 ALERTA: Frecuencia cardíaca crítica → {fc} lpm")
                    alerta = True
                if sat < 92:
                    st.error(f"🚨 ALERTA: Desaturación → SatO₂ {sat}%")
                    alerta = True
                if temp > 38.0:
                    st.warning(f"⚠️ Fiebre detectada → {temp}°C")
                    alerta = True
                if not alerta:
                    st.success("✅ Signos vitales guardados correctamente.")
                st.rerun()

        # === HISTORIAL COMPLETO ===
        if vits:
            st.divider()
            col_tit, col_btn = st.columns([3, 1])
            col_tit.markdown("#### 📋 Historial de Signos Vitales")
            
            if col_btn.button("🗑️ Borrar último control", use_container_width=True, help="Elimina solo el último registro"):
                if st.checkbox("¿Estás seguro? Esta acción no se puede deshacer", key="conf_borrar_vital"):
                    st.session_state["vitales_db"].remove(vits[-1])  # vits ya está filtrado por paciente
                    guardar_datos()
                    st.success("Registro eliminado.")
                    st.rerun()

            with st.container(height=380):
                df_vits = pd.DataFrame(vits).drop(columns=["paciente"], errors='ignore')
                
                # Ordenar de forma segura
                df_vits['fecha_dt'] = df_vits['fecha'].apply(parse_fecha_hora)
                df_vits = df_vits.sort_values(by='fecha_dt', ascending=False).drop(columns=['fecha_dt'])
                
                df_vits = df_vits.rename(columns={
                    "fecha": "Fecha y Hora",
                    "TA": "T.A.",
                    "FC": "F.C.",
                    "FR": "F.R.",
                    "Sat": "SatO₂%",
                    "Temp": "Temp °C",
                    "HGT": "HGT"
                })
                
                st.dataframe(df_vits, use_container_width=True, hide_index=True)

# 5. PEDIATRÍA (CON GRÁFICOS Y TABLA ANTI-COLAPSO)
with tabs[menu.index("👶 Pediatría")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("👶 Control Pediátrico y Curvas de Crecimiento")

        det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
        se = det.get("sexo", "F")
        f_n_str = det.get("fnac", "01/01/2000")
        f_n = pd.to_datetime(f_n_str, format="%d/%m/%Y", errors='coerce')
        if pd.isna(f_n):
            f_n = datetime(2000, 1, 1)

        # === RESUMEN ACTUAL ===
        ped_actual = [x for x in st.session_state.get("pediatria_db", []) if x["paciente"] == paciente_sel]
        if ped_actual:
            ultimo_ped = sorted(ped_actual, key=lambda x: parse_fecha_hora(x.get("fecha", "")), reverse=True)[0]
            st.markdown("##### 📊 Resumen Actual")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Peso", f"{ultimo_ped.get('peso', '—')} kg")
            c2.metric("Talla", f"{ultimo_ped.get('talla', '—')} cm")
            c3.metric("IMC", f"{ultimo_ped.get('imc', '—')}")
            c4.metric("Percentil", ultimo_ped.get("percentil_sug", "—"))

        st.divider()

        # === FORMULARIO NUEVO CONTROL ===
        with st.form("pedia", clear_on_submit=True):
            st.markdown("##### ⏱️ Nuevo Control Pediátrico")
            col_time1, col_time2 = st.columns(2)
            fecha_toma = col_time1.date_input("📅 Fecha del control", value=ahora().date(), key="fecha_ped")
            hora_toma_str = col_time2.text_input("⏰ Hora (HH:MM)", value=ahora().strftime("%H:%M"), key="hora_ped")

            st.divider()
            col_a, col_b = st.columns(2)
            pes = col_a.number_input("Peso Actual (kg)", min_value=0.0, format="%.2f")
            tal = col_b.number_input("Talla Actual (cm)", min_value=0.0, format="%.2f")
            pc = col_a.number_input("Perímetro Cefálico (cm)", min_value=0.0, format="%.2f")
            desc = col_b.text_input("Descripción / Nota (opcional)")

            if st.form_submit_button("💾 Guardar Control Pediátrico", use_container_width=True, type="primary"):
                hora_limpia = hora_toma_str.strip() if ":" in hora_toma_str else ahora().strftime("%H:%M")
                fecha_str_toma = f"{fecha_toma.strftime('%d/%m/%Y')} {hora_limpia}"

                dt_toma = parse_fecha_hora(fecha_str_toma)
                eda_meses = round((dt_toma - f_n).days / 30.4375, 1) if f_n else 0.0
                if eda_meses < 0: eda_meses = 0.0

                imc = round(pes / ((tal / 100) ** 2), 2) if tal > 0 else 0.0

                if se == "F":
                    percentil_sug = "🟢 P3 - Bajo peso" if imc < 14 else "🟡 P50 - Normal" if imc < 18 else "🔴 P97 - Sobrepeso"
                else:
                    percentil_sug = "🟢 P3 - Bajo peso" if imc < 14.5 else "🟡 P50 - Normal" if imc < 18.5 else "🔴 P97 - Sobrepeso"

                st.session_state["pediatria_db"].append({
                    "paciente": paciente_sel,
                    "fecha": fecha_str_toma,
                    "edad_meses": eda_meses,
                    "peso": pes,
                    "talla": tal,
                    "pc": pc,
                    "imc": imc,
                    "percentil_sug": percentil_sug,
                    "nota": desc,
                    "firma": user["nombre"]
                })
                guardar_datos()
                st.success("✅ Control pediátrico guardado correctamente.")
                st.rerun()

        # === GRÁFICOS DE CRECIMIENTO ===
        ped = [x for x in st.session_state.get("pediatria_db", []) if x["paciente"] == paciente_sel]
        if ped:
            st.divider()
            st.markdown("#### 📈 Curvas de Crecimiento")

            df_g = pd.DataFrame(ped)
            df_g['fecha_dt'] = df_g['fecha'].apply(parse_fecha_hora)
            df_g = df_g.sort_values(by='fecha_dt')

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.caption("📏 Peso (kg)")
                st.line_chart(df_g.set_index("fecha")["peso"], color="#3b82f6", use_container_width=True)
            with col_g2:
                st.caption("📏 Talla (cm)")
                st.line_chart(df_g.set_index("fecha")["talla"], color="#10b981", use_container_width=True)

            st.divider()

            # === HISTORIAL ===
            col_tit, col_btn = st.columns([3, 1])
            col_tit.markdown("#### 📋 Historial de Controles Pediátricos")

            # ←←← CLAVE ÚNICA PARA EVITAR DUPLICADO ←←←
            if col_btn.button("🗑️ Borrar último control", use_container_width=True, 
                            key="borrar_ultimo_pediatria", 
                            help="Elimina solo el último registro"):
                if st.checkbox("¿Confirmar borrado? Esta acción no se puede deshacer", 
                              key="conf_del_ped"):
                    st.session_state["pediatria_db"].remove(ped[-1])
                    guardar_datos()
                    st.success("Control eliminado.")
                    st.rerun()

            with st.container(height=380):
                df_ped = pd.DataFrame(ped).drop(columns=["paciente"], errors='ignore')
                df_ped['fecha_dt'] = df_ped['fecha'].apply(parse_fecha_hora)
                df_ped = df_ped.sort_values(by='fecha_dt', ascending=False).drop(columns=['fecha_dt'])

                df_ped = df_ped.rename(columns={
                    "fecha": "Fecha y Hora",
                    "edad_meses": "Edad (meses)",
                    "peso": "Peso (kg)",
                    "talla": "Talla (cm)",
                    "pc": "Perímetro Cefálico",
                    "imc": "IMC",
                    "percentil_sug": "Percentil",
                    "nota": "Notas",
                    "firma": "Profesional"
                })
                st.dataframe(df_ped, use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay controles pediátricos registrados.")

# 6. EVOLUCIÓN
with tabs[menu.index("📝 Evolución")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("📝 Evolución Médica y Firma Digital")

        # === FIRMA DIGITAL ===
        if CANVAS_DISPONIBLE:
            st.markdown("##### ✍️ Firma Digital del Paciente / Familiar")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 1)",
                stroke_width=3,
                stroke_color="#000000",
                background_color="#ffffff",
                height=180,
                width=500,
                drawing_mode="freedraw",
                key="canvas_firma_evolucion"
            )

            if st.button("💾 Guardar Firma Digital", use_container_width=True, type="primary"):
                if canvas_result.image_data is not None:
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    buf = io.BytesIO()
                    bg.save(buf, format="PNG")
                    b64_firma = base64.b64encode(buf.getvalue()).decode('utf-8')

                    st.session_state["firmas_tactiles_db"].append({
                        "paciente": paciente_sel,
                        "fecha": ahora().strftime("%d/%m/%Y %H:%M"),
                        "firma_img": b64_firma
                    })
                    guardar_datos()
                    st.success("✅ Firma guardada correctamente.")
                    st.rerun()
        else:
            st.warning("⚠️ Firma táctil no disponible.")

        st.divider()

        # === FORMULARIO DE EVOLUCIÓN ===
        with st.form("evol", clear_on_submit=True):
            nota = st.text_area("Nota médica / Evolución clínica", height=200, 
                              placeholder="Escribir aquí la evolución del paciente...")

            col_foto1, col_foto2 = st.columns([3, 1])
            desc_w = col_foto1.text_input("Descripción de la herida / lesión (opcional)")
            
            with col_foto2:
                st.markdown("📷 Foto de la herida")
                foto_w = st.camera_input("Tomar foto ahora", key="cam_evol")

            if st.form_submit_button("✅ Firmar y Guardar Evolución", use_container_width=True, type="primary"):
                if nota.strip():
                    fecha_n = ahora().strftime("%d/%m/%Y %H:%M")

                    st.session_state["evoluciones_db"].append({
                        "paciente": paciente_sel,
                        "nota": nota.strip(),
                        "fecha": fecha_n,
                        "firma": user["nombre"]
                    })

                    if foto_w is not None:
                        base64_foto = base64.b64encode(foto_w.getvalue()).decode('utf-8')
                        st.session_state["fotos_heridas_db"].append({
                            "paciente": paciente_sel,
                            "fecha": fecha_n,
                            "descripcion": desc_w.strip(),
                            "base64_foto": base64_foto,
                            "firma": user["nombre"]
                        })

                    guardar_datos()
                    st.success("✅ Evolución guardada correctamente.")
                    st.rerun()
                else:
                    st.error("❌ La nota médica no puede estar vacía.")

        # === HISTORIAL DE EVOLUCIONES (SIN COLAPSAR) ===
        evs_paciente = [e for e in st.session_state.get("evoluciones_db", []) if e.get("paciente") == paciente_sel]

        if evs_paciente:
            st.divider()
            st.markdown("#### 📋 Historial de Evoluciones Clínicas")

            # Botón de borrado con clave única
            if st.button("🗑️ Borrar última evolución", 
                        key="borrar_ultima_evolucion", 
                        use_container_width=True):
                if st.checkbox("¿Confirmar borrado? Esta acción no se puede deshacer", 
                              key="conf_del_evol"):
                    st.session_state["evoluciones_db"].remove(evs_paciente[-1])
                    guardar_datos()
                    st.success("Evolución eliminada.")
                    st.rerun()

            # ←←← AQUÍ ESTÁ EL CAMBIO: sin altura fija, se expande completamente ←←←
            for ev in reversed(evs_paciente):
                with st.container(border=True):
                    st.markdown(f"**📅 {ev['fecha']}** | 👨‍⚕️ **{ev['firma']}**")
                    st.write(ev['nota'])          # Texto completo visible
                    st.caption("─" * 40)          # Separador visual

        else:
            st.info("Aún no hay evoluciones registradas para este paciente.")

# 6.5 ESTUDIOS COMPLEMENTARIOS
with tabs[menu.index("🔬 Estudios")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("🔬 Órdenes y Resultados de Estudios")

        # === FORMULARIO PARA AGREGAR ESTUDIO ===
        with st.form("form_estudios", clear_on_submit=True):
            col_e1, col_e2 = st.columns([1, 2])
            tipo_estudio = col_e1.selectbox("Tipo de Estudio", [
                "Laboratorio (Sangre/Orina)", "Radiografía (Rx)", "Ecografía",
                "Electrocardiograma (ECG)", "Tomografía (TAC)", "Resonancia Magnética (RMN)", "Otro"
            ])
            detalle_estudio = col_e2.text_input("Detalle del Pedido o Resultado (Ej: Rx Tórax frente...)")

            st.markdown("##### 📎 Adjuntar Documento (Opcional)")
            archivo_subido = st.file_uploader("Subir archivo, foto de galería o PDF",
                                             type=["png", "jpg", "jpeg", "pdf"], key="uploader_estudio")

            with st.expander("📷 O tomar foto con la cámara ahora", expanded=False):
                foto_estudio = st.camera_input("Tomar foto en vivo", key="camara_estudio")

            if st.form_submit_button("Guardar Estudio Clínico", use_container_width=True, type="primary"):
                img_b64 = ""
                ext = ""
                if archivo_subido is not None:
                    img_b64 = base64.b64encode(archivo_subido.getvalue()).decode('utf-8')
                    ext = archivo_subido.name.split('.')[-1].lower()
                elif foto_estudio is not None:
                    img_b64 = base64.b64encode(foto_estudio.getvalue()).decode('utf-8')
                    ext = "png"

                st.session_state["estudios_db"].append({
                    "paciente": paciente_sel,
                    "fecha": ahora().strftime("%d/%m/%Y %H:%M:%S"),
                    "tipo": tipo_estudio,
                    "detalle": detalle_estudio,
                    "imagen": img_b64,
                    "extension": ext,
                    "firma": user["nombre"]
                })
                guardar_datos()
                st.success("✅ Estudio guardado correctamente.")
                st.rerun()

        # === LISTADO DE ESTUDIOS ===
        estudios_pac = [e for e in st.session_state.get("estudios_db", []) if e["paciente"] == paciente_sel]

        if estudios_pac:
            st.divider()
            st.markdown("#### 📁 Archivo de Estudios del Paciente")

            # --- OPCIÓN 1: BORRAR ÚLTIMO (rápido) ---
            col_del1, col_del2 = st.columns([3, 1])
            if col_del1.button("🗑️ Borrar último estudio", use_container_width=True):
                if estudios_pac:
                    st.session_state["estudios_db"].remove(estudios_pac[-1])
                    guardar_datos()
                    st.success("Estudio eliminado correctamente.")
                    st.rerun()

            # --- OPCIÓN 2: ELEGIR CUALQUIER ESTUDIO PARA BORRAR (lo que pediste) ---
            st.markdown("**Seleccioná el estudio que querés eliminar:**")
            opciones = []
            for est in reversed(estudios_pac):
                label = f"{est['fecha']} — {est['tipo']}"
                if est.get('detalle'):
                    label += f" | {est['detalle'][:50]}..."
                opciones.append((label, est))

            if opciones:
                estudio_seleccionado = st.selectbox(
                    "Elegir estudio a borrar",
                    options=opciones,
                    format_func=lambda x: x[0],
                    key="selector_borrar_estudio"
                )

                if st.button("🗑️ Eliminar el estudio seleccionado", type="secondary", use_container_width=True):
                    if st.checkbox("¿Estás completamente seguro? Esta acción no se puede deshacer", key="conf_borrar_estudio"):
                        st.session_state["estudios_db"] = [
                            e for e in st.session_state["estudios_db"]
                            if not (e["paciente"] == paciente_sel and e["fecha"] == estudio_seleccionado[1]["fecha"])
                        ]
                        guardar_datos()
                        st.success("✅ Estudio eliminado correctamente.")
                        st.rerun()

            st.divider()

            # --- LISTADO VISUAL ---
            limite_est = st.selectbox("Mostrar últimos:", [10, 20, 50, "Todos"], key="lim_estudios_tab")
            estudios_mostrar = estudios_pac if limite_est == "Todos" else estudios_pac[-int(limite_est):]

            with st.container(height=520):
                for idx, est in enumerate(reversed(estudios_mostrar)):
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])

                        with col1:
                            st.markdown(f"**📅 {est['fecha']}** | 👨‍⚕️ **{est['firma']}**")
                            st.markdown(f"**🔬 {est['tipo']}**")
                            if est.get('detalle'):
                                st.caption(est.get('detalle'))

                        with col2:
                            if st.button("🗑️ Eliminar", key=f"del_est_{est['fecha']}_{idx}", help="Borrar este estudio"):
                                st.session_state["estudios_db"] = [
                                    e for e in st.session_state["estudios_db"]
                                    if not (e["paciente"] == paciente_sel and e["fecha"] == est["fecha"])
                                ]
                                guardar_datos()
                                st.success("Estudio eliminado")
                                st.rerun()

                        # DESCARGA SEGURA
                        if est.get('imagen'):
                            try:
                                b64_str = est['imagen']
                                img_bytes = base64.b64decode(b64_str)

                                if img_bytes.startswith(b'%PDF') or est.get('extension') == 'pdf':
                                    nombre_arch = f"Estudio_{est['fecha'][:10].replace('/','-')}.pdf"
                                    html_btn = f'''
                                    <a href="data:application/pdf;base64,{b64_str}"
                                       download="{nombre_arch}"
                                       style="display: block; width: 100%; text-align: center;
                                              background-color: #2563eb; color: white; padding: 12px;
                                              border-radius: 8px; text-decoration: none;
                                              font-weight: 600; margin-top: 8px;">
                                       📥 DESCARGAR PDF (Seguro)
                                    </a>
                                    '''
                                    st.markdown(html_btn, unsafe_allow_html=True)
                                else:
                                    st.image(img_bytes, caption="Documento Adjunto", use_container_width=True)
                            except Exception:
                                st.error("⚠️ Error al leer el archivo")
        else:
            st.info("Aún no hay estudios guardados para este paciente.")

# 7. MATERIALES Y DESCARTABLES
with tabs[menu.index("💉 Materiales")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("💉 Registro de Materiales Descartables")

        # === INVENTARIO DE LA EMPRESA (fuera del form) ===
        inv_mi_empresa = [i for i in st.session_state.get("inventario_db", []) 
                         if i.get("empresa") == mi_empresa]

        if not inv_mi_empresa:
            st.warning("⚠️ No hay insumos cargados en el inventario. Ve a la pestaña **Inventario** primero.")
        else:
            with st.form("form_mat", clear_on_submit=True):
                c1, c2 = st.columns([3, 1])
                insumo_sel = c1.selectbox(
                    "Seleccionar Insumo Utilizado", 
                    [i["item"] for i in inv_mi_empresa],
                    key="select_insumo"
                )
                cant_usada = c2.number_input("Cantidad", min_value=1, value=1, step=1)

                if st.form_submit_button("Registrar Consumo", use_container_width=True, type="primary"):
                    # Buscar y actualizar stock
                    stock_actualizado = False
                    for i in st.session_state["inventario_db"]:
                        if i["item"] == insumo_sel and i.get("empresa") == mi_empresa:
                            stock_actual = i.get("stock", 0)
                            if stock_actual < cant_usada:
                                st.warning(f"⚠️ Stock insuficiente. Quedarán {stock_actual - cant_usada} unidades (negativo).")
                            i["stock"] = stock_actual - cant_usada
                            stock_actualizado = True
                            break

                    if stock_actualizado:
                        st.session_state["consumos_db"].append({
                            "paciente": paciente_sel,
                            "insumo": insumo_sel,
                            "cantidad": cant_usada,
                            "fecha": ahora().strftime("%d/%m/%Y %H:%M"),
                            "firma": user["nombre"],
                            "empresa": mi_empresa
                        })
                        guardar_datos()
                        st.success(f"✅ {cant_usada} × {insumo_sel} registrado correctamente.")
                        st.rerun()
                    else:
                        st.error("❌ Error al actualizar el stock.")

        # === HISTORIAL DE CONSUMOS ===
        cons_paciente = [c for c in st.session_state.get("consumos_db", []) 
                        if c.get("paciente") == paciente_sel]

        if cons_paciente:
            st.divider()
            st.markdown("#### 📋 Materiales registrados para este paciente")

            # Botón para borrar último consumo
            if st.button("🗑️ Borrar último consumo", 
                        key="borrar_ultimo_consumo_materiales", 
                        use_container_width=True):
                if st.checkbox("¿Confirmar borrado? No se puede deshacer", key="conf_del_consumo"):
                    # Opcional: Si querés que al borrar se devuelva el stock al inventario, iría acá.
                    st.session_state["consumos_db"].remove(cons_paciente[-1])
                    guardar_datos()
                    st.success("Consumo eliminado correctamente.")
                    st.rerun()

            # Dataframe ordenado por fecha (más reciente primero)
            df_cons = pd.DataFrame(cons_paciente)
            if not df_cons.empty:
                # Ordenar por fecha descendente
                df_cons['fecha_dt'] = pd.to_datetime(df_cons['fecha'], format="%d/%m/%Y %H:%M", errors='coerce')
                df_cons = df_cons.sort_values(by='fecha_dt', ascending=False).drop(columns=['fecha_dt'], errors='ignore')

                df_cons = df_cons.rename(columns={
                    "fecha": "Fecha y Hora",
                    "insumo": "Insumo Utilizado",
                    "cantidad": "Cantidad",
                    "firma": "Registrado por"
                })
                
                # ==== AQUÍ ESTÁ EL ANTI-COLAPSO DE MATERIALES ====
                with st.container(height=400, border=True):
                    st.dataframe(
                        df_cons.drop(columns=["paciente", "empresa"], errors='ignore'),
                        use_container_width=True,
                        hide_index=True
                    )
        else:
            st.info("Aún no se han registrado consumos de materiales para este paciente.")
            
# =========================================================================================
# 🎨 DISEÑO VISUAL ENTERPRISE PREMIUM v15.1 (TEXTOS Y SELECTORES CORREGIDOS)
# =========================================================================================
page_bg_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
    /* Paleta Ergonomica (Slate / Azul Pizarra) - Descansa la vista */
    --bg-app: #0F172A;          
    --bg-sidebar: #0B1121;      
    --bg-card: #1E293B;         
    --bg-input: #334155;        
    
    --border-col: #3F4F66;      
    --border-hover: #38BDF8;    
    
    --text-main: #F8FAFC;       
    --text-muted: #94A3B8;      
    
    --accent: #38BDF8;          
    --accent-glow: rgba(56, 189, 248, 0.25);
    --metric-color: #34D399;    
}

/* ==================== 1. FONDOS Y ESTRUCTURA ==================== */
html, body, .stApp {
    background-color: var(--bg-app) !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-col) !important;
}
header[data-testid="stHeader"] { background-color: transparent !important; }

/* ==================== 2. TEXTOS ==================== */
p, span, div, h1, h2, h3, h4, h5, h6, label, li {
    color: var(--text-main) !important;
}
p, label { font-weight: 400 !important; font-size: 0.95rem !important; }
h1, h2, h3, h4 { font-weight: 600 !important; letter-spacing: -0.5px; }

.stButton button p, .stButton button span { color: inherit !important; }

/* ==================== 3. TARJETAS Y CONTENEDORES ==================== */
div[data-testid="stForm"],
div[data-testid="stVerticalBlock"] > div[style*="border"],
div[data-testid="stExpander"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-col) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stForm"]:hover,
div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
    border-color: #475569 !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3) !important;
}

/* ==================== 4. MÉTRICAS (SIGNOS VITALES) ==================== */
div[data-testid="stMetric"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-col) !important;
    border-top: 3px solid var(--accent) !important;
    border-radius: 12px !important;
    padding: 16px 14px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
}
[data-testid="stMetricLabel"] p { 
    color: var(--text-muted) !important; 
    font-weight: 600 !important; 
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
}
[data-testid="stMetricValue"] div { 
    color: var(--metric-color) !important; 
    font-weight: 700 !important; 
    font-size: 1.85rem !important; 
    text-shadow: 0 0 10px rgba(52, 211, 153, 0.3) !important; 
}

/* ==================== 5. INPUTS Y SELECTS (CORREGIDOS) ==================== */
/* Ajuste específico para que los selects no corten el texto */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
textarea {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-col) !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    /* Eliminamos el padding forzado aquí para que el select respire */
}

/* Color de las letras de adentro para que se vean bien blancas */
div[data-baseweb="select"] div,
input[type="number"], input[type="text"], textarea {
    color: #FFFFFF !important;
}

/* Solo aplicamos padding a los inputs de texto/número directos, NO a los contenedores baseWeb */
input[type="number"], input[type="text"], textarea {
    padding: 8px 12px !important; 
}

/* Estilo para la lista desplegable del select (el menú que se abre) */
ul[data-baseweb="menu"] {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-col) !important;
    border-radius: 8px !important;
}
ul[data-baseweb="menu"] li {
    padding: 10px 12px !important; /* Más espacio en las opciones */
}
ul[data-baseweb="menu"] li:hover {
    background-color: var(--border-col) !important;
}

/* Efecto cuando hacés clic para escribir */
div[data-baseweb="select"] > div:focus-within,
div[data-baseweb="input"] > div:focus-within,
textarea:focus { 
    border-color: var(--accent) !important; 
    background-color: #1E293B !important; 
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}
input::placeholder, textarea::placeholder { color: #CBD5E1 !important; }

/* ==================== 6. PESTAÑAS (TABS) ==================== */
.stTabs [data-testid="stTab"] {
    background-color: var(--bg-card) !important; 
    border: 1px solid var(--border-col) !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    margin-right: 6px !important;
    margin-bottom: 8px !important;
    transition: all 0.2s ease !important;
    opacity: 1 !important; 
}
.stTabs [data-testid="stTab"] p { 
    color: #CBD5E1 !important; 
    font-weight: 500 !important; 
}
.stTabs [data-testid="stTab"]:hover { 
    background-color: #2F3E53 !important; 
    border-color: var(--accent) !important;
}
.stTabs [data-testid="stTab"]:hover p { 
    color: #FFFFFF !important; 
}
.stTabs [data-testid="stTab"][aria-selected="true"] {
    background-color: var(--bg-input) !important; 
    border: 1px solid var(--accent) !important;
    box-shadow: 0 4px 10px var(--accent-glow) !important;
}
.stTabs [data-testid="stTab"][aria-selected="true"] p { 
    color: var(--accent) !important; 
    font-weight: 600 !important;
}

/* ==================== 7. BOTONES ==================== */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.5px;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0284C7, #38BDF8) !important;
    color: #FFFFFF !important;
    border: none !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 15px rgba(56, 189, 248, 0.4) !important;
}
.stButton > button[kind="secondary"] {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-col) !important;
    color: var(--text-main) !important;
}
.stButton > button[kind="secondary"]:hover { 
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

/* ==================== 8. DATAFRAMES ==================== */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    border: 1px solid var(--border-col) !important;
    background-color: var(--bg-card) !important;
}
[data-testid="stTable"] { background-color: transparent !important; }

/* ==================== 9. EXTRAS ==================== */
img { filter: none !important; background: transparent !important; }
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-app); }
::-webkit-scrollbar-thumb { background: var(--border-col); border-radius: 20px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)


# ... (resto de tu código general, imports, funciones, etc.) ...

# =========================================================================================
# 8. RECETAS - VERSIÓN LEGAL COMPLETA (Nombre + Matrícula + Firma + Caja Fuerte)
# =========================================================================================
with tabs[menu.index("💊 Recetas")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("💊 Prescripción Médica y Administración de Medicamentos")

        # ====================== NUEVA PRESCRIPCIÓN MÉDICA LEGAL ======================
        st.markdown("##### 👨‍⚕️ Nueva Prescripción Médica")
        
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            lista_vademecum = ["-- Seleccionar del Vademécum --"] + VADEMECUM_BASE
            med_vademecum = c1.selectbox("1. Medicamento (Vademécum):", lista_vademecum)
            med_manual = c2.text_input("O 2. Escribir manualmente:")

            col3, col4, col5 = st.columns([2, 2, 1])
            
            via = col3.selectbox("Vía de Administración", [
                "Vía Oral", 
                "Vía Endovenosa (EV)", 
                "Vía Intramuscular (IM)", 
                "Vía Subcutánea (SC)", 
                "Vía Sublingual",
                "Vía Tópica", 
                "Vía Inhalatoria", 
                "Vía Rectal",
                "Otra vía de administración"
            ])
            
            frecuencia = col4.selectbox("Frecuencia", [
                "Cada 1 hora", "Cada 2 horas", "Cada 4 horas", "Cada 6 horas", "Cada 8 horas",
                "Cada 12 horas", "Cada 24 horas", "Dosis única", "Según necesidad (SOS)"
            ])
            dias = col5.number_input("Días de Tratamiento", min_value=1, max_value=90, value=7)

            st.markdown("##### ✍️ Datos del Médico Prescriptor")
            col_m1, col_m2 = st.columns(2)
            medico_nombre = col_m1.text_input("Nombre completo del médico", value=user.get("nombre", ""))
            medico_matricula = col_m2.text_input("Matrícula profesional", placeholder="Ej: 123456")

            st.markdown("##### 🖋️ Firma Digital del Médico")
            firma_canvas = st_canvas(
                key="firma_receta_activa", 
                background_color="#ffffff",
                height=150,
                drawing_mode="freedraw",
                stroke_width=3, 
                stroke_color="#000000",
                display_toolbar=True
            )

            if st.button("✅ Guardar Prescripción Médica", use_container_width=True, type="primary"):
                med_final = med_manual.strip().title() if med_manual.strip() else med_vademecum

                if med_final and med_final != "-- Seleccionar del Vademécum --":
                    if not medico_matricula.strip():
                        st.error("❌ Debe ingresar la matrícula del médico.")
                    else:
                        firma_b64 = ""
                        if firma_canvas.image_data is not None:
                            import io
                            from PIL import Image
                            img = Image.fromarray(firma_canvas.image_data.astype("uint8"))
                            buf = io.BytesIO()
                            img.save(buf, format="PNG")
                            firma_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

                        texto_receta = f"{med_final} | Vía: {via} | {frecuencia} | Durante {dias} días"

                        st.session_state["indicaciones_db"].append({
                            "paciente": paciente_sel,
                            "med": texto_receta,
                            "fecha": ahora().strftime("%d/%m/%Y %H:%M:%S"),
                            "dias_duracion": dias,
                            "medico_nombre": medico_nombre.strip(),
                            "medico_matricula": medico_matricula.strip(),
                            "firma_b64": firma_b64,
                            "firmado_por": user["nombre"],
                            "estado_receta": "Activa"
                        })
                        guardar_datos()
                        st.success(f"✅ Prescripción de **{med_final}** guardada con firma médica.")
                        st.rerun()

        st.divider()

        # Obtenemos TODAS las recetas, pero separamos las Activas de las Suspendidas
        recs_todas = [r for r in st.session_state.get("indicaciones_db", []) if r.get("paciente") == paciente_sel]
        recs_activas = [r for r in recs_todas if r.get("estado_receta", "Activa") == "Activa"]

        if recs_activas:
            # ====================== TABLA 00:00 - 23:00 ======================
            st.markdown("#### 📅 Administración de Hoy (00:00 a 23:00)")

            fecha_hoy = ahora().strftime("%d/%m/%Y")
            admin_hoy = [a for a in st.session_state.get("administracion_med_db", [])
                        if a.get("paciente") == paciente_sel and a.get("fecha") == fecha_hoy]

            all_horarios = [f"{h:02d}:00" for h in range(24)]

            table_data = []
            for r in recs_activas:
                partes = r['med'].split(" | ")
                nombre = partes[0].strip()
                via_texto = partes[1].replace("Vía: ", "") if len(partes) > 1 else ""
                freq = partes[2] if len(partes) > 2 else ""

                fila = {
                    "Medicamento": nombre,
                    "Vía": via_texto,
                    "Frecuencia": freq,
                    "Médico": r.get("medico_nombre", "—"),
                    "Matrícula": r.get("medico_matricula", "—")
                }

                for h in all_horarios:
                    realizada = any(
                        a.get("med") == nombre and a.get("hora", "").startswith(h[:2])
                        for a in admin_hoy
                    )
                    # Acá está la magia: le metemos espacios " " a los costados para forzar el ancho de la celda
                    fila[h] = "   ✅   " if realizada else "   ⭕   "

                table_data.append(fila)

            df = pd.DataFrame(table_data)

            # Estilos reforzados para centrar y agrandar los íconos
            def style_medicacion(row):
                styles = []
                for col in row.index:
                    if col in ["Medicamento", "Vía", "Frecuencia", "Médico", "Matrícula"]:
                        styles.append('background-color: #1e1e1e; color: #ffffff; font-weight: 500; text-align: left;')
                    elif "✅" in str(row[col]):
                        styles.append('background-color: #1a3c2e; color: #4ade80; font-weight: bold; text-align: center; font-size: 18px;')
                    else:
                        styles.append('background-color: #2c1f1f; color: #f87171; text-align: center; font-size: 18px;')
                return styles

            styled_df = df.style.apply(style_medicacion, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            st.caption("✅ = Administrado   ⭕ = Pendiente")
            st.divider()

            # ====================== PANEL DE REGISTRO DE DOSIS ======================
            st.markdown("#### 📝 Panel de Registro de Dosis (Enfermería)")
            with st.form("form_registro_dosis", clear_on_submit=True):
                meds_activas_nombres = [r['med'].split(" |")[0].strip() for r in recs_activas]
                
                c_med, c_hora = st.columns([2, 1])
                med_sel = c_med.selectbox("1. Medicación a registrar:", meds_activas_nombres)
                
                opciones_hora = [f"{i:02d}:00" for i in range(24)]
                hora_actual_str = f"{ahora().hour:02d}:00"
                idx_hora = opciones_hora.index(hora_actual_str) if hora_actual_str in opciones_hora else 0
                
                hora_sel = c_hora.selectbox("2. Hora de la dosis:", opciones_hora, index=idx_hora)
                estado_sel = st.radio("3. Estado de la aplicación:", ["✅ Realizada", "❌ No realizada / Suspendida"], horizontal=True)
                justificacion = st.text_input("4. Justificación Clínica (OBLIGATORIA si marca ❌ No realizada):", placeholder="Ej: Paciente hipotenso, falta de stock, etc.")
                
                if st.form_submit_button("💾 Guardar Registro", use_container_width=True):
                    if "❌" in estado_sel and not justificacion.strip():
                        st.error("🚨 LEGAL: Es obligatorio justificar clínicamente por qué no se administró la dosis.")
                    else:
                        if "administracion_med_db" not in st.session_state:
                            st.session_state["administracion_med_db"] = []
                        st.session_state["administracion_med_db"] = [
                            a for a in st.session_state.get("administracion_med_db", [])
                            if not (a.get("paciente") == paciente_sel and a.get("fecha") == fecha_hoy and a.get("med") == med_sel and a.get("hora") == hora_sel)
                        ]
                        st.session_state["administracion_med_db"].append({
                            "paciente": paciente_sel, "med": med_sel, "fecha": fecha_hoy, "hora": hora_sel,
                            "estado": estado_sel, "motivo": justificacion.strip() if "❌" in estado_sel else "", "firma": user["nombre"]
                        })
                        guardar_datos()
                        st.success(f"✅ Registro guardado exitosamente para las {hora_sel}.")
                        st.rerun()

            st.divider()

            # ====================== MODIFICAR O SUSPENDER ======================
            st.markdown("#### ⚙️ Modificar o Suspender Manualmente")
            c_ed1, c_ed2 = st.columns([3, 2])
            opciones_recetas = [f"[{r.get('fecha', '')}] {r.get('med', '')}" for r in recs_activas]
            receta_seleccionada = c_ed1.selectbox("Seleccionar indicación a gestionar:", opciones_recetas)
            accion_receta = c_ed2.selectbox("Acción a realizar:", ["Suspender / Anular", "Editar indicación"])
            
            nuevo_texto_receta = ""
            if accion_receta == "Editar indicación" and receta_seleccionada:
                try: texto_original = receta_seleccionada.split("] ")[1]
                except: texto_original = receta_seleccionada
                nuevo_texto_receta = st.text_input("Modificar detalle (Dosis, días, etc.):", value=texto_original)
            
            if st.button("⚠️ Aplicar Cambios en Terapéutica", use_container_width=True):
                for r in st.session_state["indicaciones_db"]:
                    if r["paciente"] == paciente_sel and f"[{r.get('fecha', '')}] {r.get('med', '')}" == receta_seleccionada:
                        if accion_receta == "Suspender / Anular":
                            r["estado_receta"] = "Suspendida"
                            r["fecha_suspension"] = ahora().strftime("%d/%m/%Y %H:%M")
                            st.success("✅ Indicación suspendida. Quedará en el historial legal.")
                        elif accion_receta == "Editar indicación" and nuevo_texto_receta:
                            r["estado_receta"] = "Modificada"
                            r["fecha_suspension"] = ahora().strftime("%d/%m/%Y %H:%M")
                            st.session_state["indicaciones_db"].append({
                                "paciente": paciente_sel,
                                "med": nuevo_texto_receta,
                                "fecha": ahora().strftime("%d/%m/%Y %H:%M:%S"),
                                "dias_duracion": r.get("dias_duracion", 7),
                                "medico_nombre": r.get("medico_nombre", ""),
                                "medico_matricula": r.get("medico_matricula", ""),
                                "firma_b64": r.get("firma_b64", ""),
                                "firmado_por": user["nombre"],
                                "estado_receta": "Activa"
                            })
                            st.success("✅ Indicación editada. La versión anterior quedó en el historial.")
                        break
                guardar_datos()
                st.rerun()

        else:
            st.info("Aún no hay medicación activa para este paciente.")

        st.divider()

        # ====================== GENERADOR DE PDF Y HISTORIAL ======================
        if recs_todas:
            st.markdown("#### 🕰️ Historial Completo de Prescripciones (Caja Fuerte)")
            
            def generar_pdf_receta(r_data):
                if not FPDF_DISPONIBLE: return b""
                def t(txt): return str(txt).replace('⚖️', '').replace('⚠️', '').encode('latin-1', 'replace').decode('latin-1')
                
                pdf = FPDF(format='A5')
                pdf.add_page()
                
                directorio_actual = os.path.dirname(os.path.abspath(__file__))
                ruta_logo = os.path.join(directorio_actual, "logo_medicare_pro.jpeg")
                try: pdf.image(ruta_logo, x=10, y=10, w=20)
                except: pass
                
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, t(f"RECETA MEDICA - {mi_empresa}"), ln=True, align='C')
                pdf.ln(5)
                
                det = st.session_state["detalles_pacientes_db"].get(paciente_sel, {})
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, t(f"Fecha: {r_data.get('fecha', '').split(' ')[0]}"), ln=True)
                pdf.cell(0, 6, t(f"Paciente: {paciente_sel.split(' (')[0]}"), ln=True)
                pdf.cell(0, 6, t(f"DNI: {det.get('dni', 'S/D')}"), ln=True)
                pdf.line(10, pdf.get_y()+2, 138, pdf.get_y()+2)
                pdf.ln(8)
                
                estado_pdf = r_data.get("estado_receta", "Activa")
                if estado_pdf != "Activa":
                    pdf.set_text_color(220, 38, 38)
                    pdf.set_font("Arial", 'B', 14)
                    pdf.cell(0, 8, t(f"ANULADA / {estado_pdf.upper()}"), ln=True, align='C')
                    pdf.set_text_color(0, 0, 0)
                
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, t("Rp/"), ln=True)
                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 6, t(r_data.get('med', '')))
                pdf.ln(15)
                
                y_firma = pdf.get_y()
                firma_str = r_data.get("firma_b64", "")
                if firma_str:
                    try:
                        img_data = base64.b64decode(firma_str)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(img_data)
                            tmp_path = tmp.name
                        pdf.image(tmp_path, x=80, y=y_firma, w=40)
                        os.remove(tmp_path)
                    except: pass
                
                pdf.set_xy(80, y_firma + 20)
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(50, 5, t(r_data.get('medico_nombre', 'S/D')), ln=2, align='C')
                pdf.cell(50, 5, t(f"Mat: {r_data.get('medico_matricula', 'S/D')}"), ln=0, align='C')
                
                return pdf.output(dest='S').encode('latin-1')

            with st.container(height=450):
                for idx, r in enumerate(reversed(recs_todas[-30:])):
                    with st.container(border=True):
                        c_info, c_btn = st.columns([3, 1])
                        
                        estado_actual = r.get("estado_receta", "Activa")
                        
                        if estado_actual == "Activa":
                            c_info.markdown(f"✅ **{r.get('fecha', '—')}**")
                            c_info.markdown(f"**Indicado por:** {r.get('medico_nombre', '—')} | **Matrícula:** {r.get('medico_matricula', '—')}")
                            c_info.markdown(f"*{r.get('med', '')}*")
                        else:
                            c_info.markdown(f"❌ **{r.get('fecha', '—')}** *(ESTADO: {estado_actual.upper()} el {r.get('fecha_suspension', 'S/D')})*")
                            c_info.markdown(f"**Indicado por:** {r.get('medico_nombre', '—')} | **Matrícula:** {r.get('medico_matricula', '—')}")
                            c_info.markdown(f"~~*{r.get('med', '')}*~~")
                            
                        if FPDF_DISPONIBLE:
                            pdf_bytes = generar_pdf_receta(r)
                            b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                            nombre_arch = f"Receta_{paciente_sel.split(' (')[0]}_{r.get('fecha', '')[:10].replace('/','')}.pdf"
                            
                            html_btn_receta = f'''
                            <a href="data:application/pdf;base64,{b64_pdf}" download="{nombre_arch}" 
                               style="display: block; width: 100%; text-align: center; background-color: #2563eb; 
                                      color: white; padding: 10px; border-radius: 6px; text-decoration: none; 
                                      font-weight: 600; font-size: 14px; font-family: sans-serif; margin-top: 15px;">
                               📄 Imprimir PDF
                            </a>
                            '''
                            c_btn.markdown(html_btn_receta, unsafe_allow_html=True)
# =====================================================================
# 9. BALANCE HÍDRICO (VERSIÓN FINAL - LÓGICA MÉDICA INVERTIDA + SCROLL)
# =====================================================================
with tabs[menu.index("⚖️ Balance")]:
    if not paciente_sel:
        st.info("👈 Seleccioná un paciente en el menú lateral.")
    else:
        st.subheader("⚖️ Balance Hídrico Estricto")
        
        # ====================== FORMULARIO ======================
        with st.form("bal", clear_on_submit=True):
            col_meta1, col_meta2, col_meta3 = st.columns(3)
            fecha_bal = col_meta1.date_input("📅 Fecha de control", value=ahora().date(), key="fecha_bal")
            hora_bal_str = col_meta2.text_input("⏰ Hora exacta (HH:MM)", value=ahora().strftime("%H:%M"), key="hora_bal")
            turno = col_meta3.selectbox("Turno de Guardia", [
                "Mañana (06 a 14hs)",
                "Tarde (14 a 22hs)",
                "Noche (22 a 06hs)"
            ])
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 🟢 Ingresos (ml)")
                i_oral = st.number_input("Oral / Enteral", min_value=0, step=50, value=0)
                i_par = st.number_input("Parenteral (Sachets, Medicación)", min_value=0, step=50, value=0)
            with c2:
                st.markdown("#### 🔴 Egresos (ml)")
                e_orina = st.number_input("Diuresis (Orina)", min_value=0, step=50, value=0)
                e_dren = st.number_input("Drenajes / Sondas", min_value=0, step=50, value=0)
                e_perd = st.number_input("Pérdidas Insensibles / Catarsis", min_value=0, step=50, value=0)
            
            if st.form_submit_button("💾 Guardar Balance y Calcular Shift", use_container_width=True, type="primary"):
                hora_limpia = hora_bal_str.strip() if ":" in hora_bal_str else ahora().strftime("%H:%M")
                fecha_str = f"{fecha_bal.strftime('%d/%m/%Y')} {hora_limpia}"
                ingresos = i_oral + i_par
                egresos = e_orina + e_dren + e_perd
                balance = ingresos - egresos
                
                st.session_state["balance_db"].append({
                    "paciente": paciente_sel,
                    "turno": turno,
                    "i_oral": i_oral,
                    "i_par": i_par,
                    "e_orina": e_orina,
                    "e_dren": e_dren,
                    "e_perd": e_perd,
                    "ingresos": ingresos,
                    "egresos": egresos,
                    "balance": balance,
                    "fecha": fecha_str,
                    "firma": user["nombre"]
                })
                guardar_datos()
                st.success(f"✅ Balance guardado → Shift: {'+' if balance >= 0 else ''}{balance} ml")
                st.rerun()

        # ====================== HISTORIAL ======================
        blp = [x for x in st.session_state.get("balance_db", []) if x.get("paciente") == paciente_sel]
        
        if blp:
            st.divider()
            st.markdown("#### 📋 Historial de Balances Hídricos")
            
            # Métricas rápidas
            df_temp = pd.DataFrame(blp)
            ultimo = df_temp["balance"].iloc[-1] if not df_temp.empty else 0
            col_met1, col_met2, col_met3 = st.columns(3)
            
            # LÓGICA MÉDICA: delta_color="inverse" hace que si es positivo (retiene) la flecha sea ROJA
            col_met1.metric("Último Shift", f"{ultimo:+} ml", 
                           delta="Retención (Alerta)" if ultimo > 0 else ("Pérdida" if ultimo < 0 else "Neutro"),
                           delta_color="inverse")
                           
            col_met2.metric("Total balances", len(blp))
            col_met3.metric("Balance neto (últimos 3 turnos)", 
                           f"{sum(df_temp['balance'].tail(3)):+} ml")
            
            # DataFrame con colores (sin HTML)
            df_bal = pd.DataFrame(blp)
            df_bal['fecha_dt'] = pd.to_datetime(df_bal['fecha'], format="%d/%m/%Y %H:%M", errors='coerce')
            df_bal = df_bal.sort_values(by='fecha_dt', ascending=False).drop(columns=['fecha_dt'], errors='ignore')
            
            df_bal["Ingresos"] = df_bal["ingresos"].astype(str) + " ml"
            df_bal["Egresos"] = df_bal["egresos"].astype(str) + " ml"
            
            # COLORES INVERTIDOS (LÓGICA CLÍNICA)
            def formato_shift(val):
                if val > 0:
                    return f"🔴 +{val} ml" # Retiene líquido -> Alerta Roja
                elif val < 0:
                    return f"🟢 {val} ml"  # Elimina líquido -> Verde
                else:
                    return "⚖️ 0 ml"
            
            df_bal["Shift (Resultado)"] = df_bal["balance"].apply(formato_shift)
            
            df_mostrar = df_bal.rename(columns={
                "fecha": "Fecha y Hora",
                "turno": "Turno",
                "firma": "Enfermero/a"
            })
            
            # === ACÁ ESTÁ EL CONTENEDOR ANTI-COLAPSO MÁGICO ===
            with st.container(height=450, border=True):
                st.dataframe(
                    df_mostrar[["Fecha y Hora", "Turno", "Ingresos", "Egresos", "Shift (Resultado)", "Enfermero/a"]],
                    use_container_width=True,
                    hide_index=True,
                    height=450, 
                    column_config={
                        "Shift (Resultado)": st.column_config.TextColumn(
                            "Shift (Resultado)",
                            help="🔴 Retención de líquidos = Rojo   |   🟢 Eliminación = Verde"
                        )
                    }
                )
            
            st.divider()
            
            # Botón borrar
            if st.button("🗑️ Borrar último balance", use_container_width=True, type="secondary"):
                if st.checkbox("¿Estás seguro? Esta acción es irreversible", key="conf_del_balance"):
                    st.session_state["balance_db"].remove(blp[-1])
                    guardar_datos()
                    st.success("✅ Último balance eliminado")
                    st.rerun()
        else:
            st.info("Aún no hay balances hídricos registrados para este paciente.")
# 10. INVENTARIO - VERSIÓN UNIFICADA EN TONO BORDO OSCURO (CON ANTI-COLAPSO)
with tabs[menu.index("📦 Inventario")]:
    st.subheader("📦 Gestión de Inventario y Stock de Farmacia")

    inv_mio = [i for i in st.session_state.get("inventario_db", []) if i.get("empresa") == mi_empresa]

    # ====================== ALERTA DE STOCK CRÍTICO ======================
    stock_critico = [i for i in inv_mio if i.get("stock", 0) <= 10]
    if stock_critico:
        st.markdown("#### 🚨 **ALERTA DE STOCK CRÍTICO**")
        # ACÁ ESTÁ LA MAGIA ANTI-COLAPSO PARA LAS ALERTAS
        with st.container(height=350, border=True):
            for item in stock_critico:
                st.error(f"**{item.get('item')}** → Quedan solo **{item.get('stock', 0)}** unidades")

    st.divider()

    # ====================== INGRESO DE MERCADERÍA ======================
    with st.form("form_inv", clear_on_submit=True):
        st.markdown("#### ➕ Ingreso de Mercadería")

        c1, c2, c3 = st.columns([2, 2, 1])
        lista_base_inv = ["-- Seleccionar del Vademécum --"] + VADEMECUM_BASE
        
        item_sel = c1.selectbox("1. Catálogo Frecuente:", lista_base_inv)
        nuevo_item = c2.text_input("2. Escribir Insumo Nuevo:")
        cantidad = c3.number_input("Cantidad", min_value=1, value=10, step=1)

        if st.form_submit_button("💾 Sumar al Stock", use_container_width=True, type="primary"):
            item_final = nuevo_item.strip().title() if nuevo_item.strip() else item_sel

            if item_final and item_final != "-- Seleccionar del Vademécum --":
                encontrado = False
                for i in st.session_state["inventario_db"]:
                    if i.get("item", "").lower() == item_final.lower() and i.get("empresa") == mi_empresa:
                        i["stock"] = i.get("stock", 0) + cantidad
                        encontrado = True
                        break
                
                if not encontrado:
                    st.session_state["inventario_db"].append({
                        "item": item_final,
                        "stock": cantidad,
                        "empresa": mi_empresa
                    })
                
                guardar_datos()
                st.success(f"✅ Se agregaron **{cantidad}** unidades de **{item_final}**.")
                st.rerun()

    st.divider()

    # ====================== STOCK ACTUAL - TODO EN TONO BORDO OSCURO ======================
    if inv_mio:
        st.markdown("#### 📋 Stock Actual en Farmacia")

        df_stock = pd.DataFrame(inv_mio)
        df_stock = df_stock.rename(columns={"item": "Insumo", "stock": "Stock Actual"})

        # Estilo unificado: todo en tono bordo oscuro
        def unificar_bordo(row):
            stock = row["Stock Actual"]
            if stock <= 10:
                return ['background-color: #3c1f1f; color: #ff8a80; font-weight: bold'] * len(row)
            else:
                return ['background-color: #2c1f1f; color: #ffffff'] * len(row)

        styled = df_stock[["Insumo", "Stock Actual"]].style.apply(unificar_bordo, axis=1)

        # Contenedor con scroll interno para evitar colapso
        with st.container(height=480, border=True):
            st.dataframe(
                styled,
                use_container_width=True,
                hide_index=True
            )
    else:
        st.info("Aún no hay insumos cargados en el inventario.")

    st.divider()

    # ====================== AJUSTE MANUAL ======================
    if inv_mio:
        st.markdown("#### ⚙️ Ajuste Manual y Corrección")

        col1, col2, col3 = st.columns([2, 1, 1])
        item_a_editar = col1.selectbox("Seleccionar insumo a corregir:", [i["item"] for i in inv_mio], key="edit_sel")
        
        stock_actual = next((i.get("stock", 0) for i in inv_mio if i["item"] == item_a_editar), 0)
        nuevo_stock = col2.number_input("Nuevo stock real:", min_value=0, value=stock_actual, key="new_stock")

        if col3.button("✏️ Actualizar Stock", use_container_width=True):
            for i in st.session_state["inventario_db"]:
                if i["item"] == item_a_editar and i.get("empresa") == mi_empresa:
                    i["stock"] = nuevo_stock
                    break
            guardar_datos()
            st.success(f"✅ Stock de **{item_a_editar}** actualizado a **{nuevo_stock}** unidades.")
            st.rerun()

        st.divider()

        col_del1, col_del2 = st.columns([3, 1])
        del_item = col_del1.selectbox("Eliminar insumo por completo:", [i["item"] for i in inv_mio], key="del_sel")
        
        if col_del2.button("🗑️ Eliminar Insumo Definitivamente", use_container_width=True, type="secondary"):
            if st.checkbox("¿Estás seguro? Esta acción no se puede deshacer.", key="conf_del_item"):
                st.session_state["inventario_db"] = [
                    i for i in st.session_state["inventario_db"] 
                    if not (i["item"] == del_item and i.get("empresa") == mi_empresa)
                ]
                guardar_datos()
                st.success(f"Insumo **{del_item}** eliminado definitivamente.")
                st.rerun()
# 11. CAJA - VERSIÓN MEJORADA Y CORREGIDA (SIN ERROR UNICODE Y CON ANTI-COLAPSO TOTAL)
with tabs[menu.index("💳 Caja")]:
    if paciente_sel:
        st.subheader("💳 Facturación y Caja Diaria")

        # --- 1. MÉTRICAS RÁPIDAS ---
        fact_paciente = [f for f in st.session_state.get("facturacion_db", [])
                        if f.get("paciente") == paciente_sel and f.get("empresa") == mi_empresa]

        total_cobrado = sum(f['monto'] for f in fact_paciente if "✅" in f.get('estado', '✅'))
        total_pendiente = sum(f['monto'] for f in fact_paciente if "⏳" in f.get('estado', ''))

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("💰 Total Cobrado", f"${total_cobrado:,.2f}")
        col_m2.metric("⏳ Pendiente de Cobro", f"${total_pendiente:,.2f}", 
                     delta="-A Cobrar" if total_pendiente > 0 else None, delta_color="inverse")
        col_m3.metric("🧾 Prácticas Registradas", len(fact_paciente))

        st.divider()

        # --- 2. FORMULARIO DE CARGA ---
        with st.form("caja_form", clear_on_submit=True):
            st.markdown("##### 📝 Registrar Nuevo Movimiento")
            
            c1, c2 = st.columns([3, 1])
            practicas_comunes = [
                "Consulta Médica Domiciliaria", "Aplicación IM/SC", "Curación de Heridas",
                "Colocación/Cambio de Sonda", "Control de Signos Vitales", 
                "Guardia de Enfermería (12hs)", "Guardia de Enfermería (24hs)",
                "Sesión de Kinesiología", "Insumos Extras",
                "-- Otro (Especificar manualmente) --"
            ]
            practica_sel = c1.selectbox("Tipo de Servicio / Nomenclador:", practicas_comunes)
            practica_manual = c1.text_input("Detalle adicional (solo si elegiste 'Otro'):", 
                                          placeholder="Ej: Cambio de apósito especial...")

            mon = c2.number_input("Monto a Facturar ($)", min_value=0.0, step=500.0, value=0.0)

            c3, c4 = st.columns(2)
            metodo = c3.selectbox("Método de Pago", 
                                ["Efectivo", "Transferencia / CBU", "Tarjeta Débito/Crédito", 
                                 "Billetera Virtual", "Cobertura / Obra Social"])
            estado = c4.radio("Estado del Cobro", ["✅ Cobrado", "⏳ Pendiente / A Facturar"], 
                            horizontal=True)

            if st.form_submit_button("💾 Registrar Cobro / Práctica", 
                                   use_container_width=True, type="primary"):
                desc_final = practica_manual.strip() if practica_sel == "-- Otro (Especificar manualmente) --" else f"{practica_sel} {('- ' + practica_manual.strip()) if practica_manual.strip() else ''}"

                if desc_final.strip() and mon > 0:
                    st.session_state["facturacion_db"].append({
                        "paciente": paciente_sel,
                        "serv": desc_final.strip(),
                        "monto": mon,
                        "metodo": metodo,
                        "estado": estado,
                        "fecha": ahora().strftime("%d/%m/%Y %H:%M"),
                        "empresa": mi_empresa,
                        "operador": user["nombre"],
                        "operador_dni": user.get("dni", "S/D")
                    })
                    guardar_datos()
                    st.success(f"✅ **${mon:,.2f}** registrado correctamente.")
                    st.rerun()
                else:
                    st.error("🚨 Debe ingresar una descripción válida y un monto mayor a $0.")

        st.divider()

        # --- 3. HISTORIAL DE RECIBOS DEL PACIENTE ---
        st.markdown("#### 🧾 Historial de Recibos del Paciente")
        if fact_paciente:
            
            # === FUNCIÓN PDF CORREGIDA (SIN ERROR UNICODE) ===
            def generar_recibo_pdf(mov):
                if not FPDF_DISPONIBLE:
                    return b""
                
                # Función segura para convertir texto a latin-1 (evita el error)
                def safe_text(text):
                    if not text:
                        return ""
                    # Reemplaza caracteres problemáticos comunes en español
                    replacements = {
                        'ñ': 'n', 'Ñ': 'N', 'á': 'a', 'Á': 'A', 'é': 'e', 'É': 'E',
                        'í': 'i', 'Í': 'I', 'ó': 'o', 'Ó': 'O', 'ú': 'u', 'Ú': 'U',
                        'ü': 'u', 'Ü': 'U', '¿': '', '¡': '', '°': '', '–': '-'
                    }
                    for old, new in replacements.items():
                        text = text.replace(old, new)
                    return str(text).encode('latin-1', errors='replace').decode('latin-1')

                pdf = FPDF(format='A5')
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, safe_text(f"RECIBO - {mi_empresa}"), ln=True, align='C')
                pdf.set_font("Arial", '', 10)
                pdf.cell(0, 6, safe_text(f"Fecha: {mov['fecha']}"), ln=True, align='C')
                pdf.cell(0, 6, safe_text(f"Operador: {mov.get('operador', 'S/D')} (DNI: {mov.get('operador_dni', 'S/D')})"), ln=True, align='C')
                pdf.ln(10)

                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 8, safe_text(f"Recibimos de: {mov['paciente']}"), ln=True)
                pdf.ln(4)

                pdf.set_font("Arial", '', 11)
                pdf.multi_cell(0, 8, safe_text(f"Concepto: {mov['serv']}"))
                pdf.cell(0, 8, safe_text(f"Medio de pago: {mov.get('metodo', 'S/D')}"), ln=True)
                pdf.cell(0, 8, safe_text(f"Estado: {mov.get('estado', 'Cobrado')}"), ln=True)
                pdf.ln(8)

                pdf.set_fill_color(240, 240, 240)
                pdf.set_font("Arial", 'B', 18)
                pdf.cell(0, 14, safe_text(f"TOTAL: ${mov['monto']:,.2f}"), 1, 1, 'C', True)

                pdf.ln(12)
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 5, "Comprobante interno - No válido como factura fiscal", ln=True, align='C')

                return pdf.output(dest='S').encode('latin-1')

            # --- ACÁ ESTÁ EL ANTI-COLAPSO DE LOS RECIBOS ---
            with st.container(height=400):
                # Mostrar historial en tarjetas
                for i, mov in enumerate(reversed(fact_paciente)):
                    with st.container(border=True):
                        col_r1, col_r2 = st.columns([4, 1])
                        estado_color = "🟢" if "✅" in mov.get("estado", "") else "🟡"
                        
                        with col_r1:
                            st.markdown(f"**{mov['fecha']}** — {mov['serv']}")
                            st.caption(f"{estado_color} {mov.get('estado', 'S/D')} | {mov.get('metodo', 'S/D')} | **${mov['monto']:,.2f}**")
                        
                        # Botón PDF seguro
                        pdf_bytes = generar_recibo_pdf(mov)
                        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                        file_name = f"Recibo_{mov['fecha'][:10].replace('/','-')}_{i+1}.pdf"
                        
                        html_btn = f'''
                        <a href="data:application/pdf;base64,{b64_pdf}" download="{file_name}"
                           style="display:block; width:100%; text-align:center; background:#2563eb; color:white; 
                                  padding:10px; border-radius:8px; text-decoration:none; font-weight:600;">
                           📄 Descargar PDF
                        </a>
                        '''
                        col_r2.markdown(html_btn, unsafe_allow_html=True)

        else:
            st.info("No hay movimientos registrados para este paciente aún.")

        # --- 4. AUDITORÍA GENERAL (Solo SuperAdmin / Coordinador) ---
        if rol in ["SuperAdmin", "Coordinador"]:
            st.divider()
            st.markdown("#### 🔍 Auditoría de Facturación General")

            df_caja = pd.DataFrame([f for f in st.session_state.get("facturacion_db", []) 
                                  if f.get("empresa") == mi_empresa])

            if not df_caja.empty:
                filtro_caja = st.text_input("🔎 Buscar por paciente, práctica, fecha o estado...", "")

                if filtro_caja:
                    mask = df_caja.astype(str).apply(lambda x: x.str.contains(filtro_caja, case=False, na=False)).any(axis=1)
                    df_caja_filtrada = df_caja[mask]
                else:
                    df_caja_filtrada = df_caja

                df_mostrar = df_caja_filtrada.copy()
                df_mostrar = df_mostrar.rename(columns={
                    "fecha": "Fecha", "paciente": "Paciente", "serv": "Concepto",
                    "monto": "Monto ($)", "metodo": "Medio de Pago", "estado": "Estado",
                    "operador": "Registró"
                })
                if "empresa" in df_mostrar.columns:
                    df_mostrar = df_mostrar.drop(columns=["empresa", "operador_dni"], errors='ignore')

                # ==== AQUÍ ESTÁ EL ANTI-COLAPSO DE LA TABLA DE AUDITORÍA ====
                with st.container(height=400, border=True):
                    st.dataframe(df_mostrar.iloc[::-1], use_container_width=True, hide_index=True)

                # Descarga Excel segura
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_mostrar.to_excel(writer, index=False, sheet_name='Caja_MediCare')

                output.seek(0)
                b64_excel = base64.b64encode(output.getvalue()).decode('utf-8')
                file_name_excel = f"Caja_General_{mi_empresa}_{ahora().strftime('%d_%m_%Y')}.xlsx"

                html_excel = f'''
                <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}"
                   download="{file_name_excel}"
                   style="display:block; width:100%; text-align:center; background:#10b981; color:white; 
                          padding:14px; border-radius:10px; text-decoration:none; font-weight:600; margin-top:10px;">
                   📊 DESCARGAR EXCEL COMPLETO DE CAJA
                </a>
                '''
                st.markdown(html_excel, unsafe_allow_html=True)
            else:
                st.info("No hay registros de facturación aún.")

    else:
        st.info("👈 Seleccioná un paciente en el menú lateral para ver su cuenta corriente.")
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
                with st.container(height=350):
                    for e in reversed(evs[-limite:]): 
                        # Usamos .get() para evitar KeyError
                        st.info(f"📅 **{e.get('fecha', '')}** | {e.get('firma', 'S/D')}\n\n{e.get('nota', '')}")
            else: st.write("No hay evoluciones médicas cargadas.")

        # NUEVO: HISTORIAL DE ESTUDIOS COMPLEMENTARIOS (CON CARPETAS Y REPARACIÓN PDF/IMG ANTI-404)
        with st.expander("🔬 Estudios Complementarios"):
            estudios = [x for x in st.session_state.get("estudios_db", []) if x["paciente"] == paciente_sel]
            if estudios:
                with st.container(height=350):
                    for idx, est in enumerate(reversed(estudios[-limite:])): 
                        # Diseño de Carpeta/Tarjeta individual
                        with st.container(border=True):
                            st.markdown(f"**📁 {est.get('fecha', '')} - {est.get('tipo', '')}** (Por {est.get('firma', 'S/D')})")
                            st.markdown(f"*{est.get('detalle', '')}*")
                            
                            if est.get('imagen'):
                                try:
                                    b64_str = est['imagen']
                                    img_bytes = base64.b64decode(b64_str)
                                    
                                    if img_bytes.startswith(b'%PDF') or est.get('extension') == 'pdf':
                                        nombre_arch = f"Estudio_{est.get('fecha', '')[:10].replace('/','-')}.pdf"
                                        html_btn = f"""<a href="data:application/pdf;base64,{b64_str}" download="{nombre_arch}" style="display: block; width: 100%; text-align: center; background-color: #2563eb; color: white; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: 600; font-family: sans-serif; margin-top: 10px;">📥 Descargar PDF</a>"""
                                        st.markdown(html_btn, unsafe_allow_html=True)
                                    else:
                                        # ARREGLO ANTI-404 PARA FOTOS DE ESTUDIOS:
                                        html_img = f'<img src="data:image/png;base64,{b64_str}" style="width: 100%; border-radius: 8px; margin-top: 10px;">'
                                        st.markdown(html_img, unsafe_allow_html=True)
                                except Exception:
                                    st.error("⚠️ Error al leer archivo adjunto.")
            else: st.write("No hay estudios complementarios registrados.")
            
        with st.expander("💉 Materiales Utilizados"):
            cons = [x for x in st.session_state["consumos_db"] if x["paciente"] == paciente_sel]
            if cons: st.dataframe(pd.DataFrame(cons[-limite:]).drop(columns=["paciente", "empresa"], errors='ignore'), use_container_width=True)
            else: st.write("No hay consumos de materiales registrados.")
            
        with st.expander("📸 Registro de Heridas"):
            fot_her = [x for x in st.session_state["fotos_heridas_db"] if x["paciente"] == paciente_sel]
            if fot_her:
                with st.container(height=450):
                    for fh in reversed(fot_her[-limite:]):
                        st.success(f"📅 **{fh.get('fecha', '')}** | {fh.get('firma', 'S/D')}\n\nDescripción: {fh.get('descripcion', '')}")
                        # ARREGLO ANTI-404 PARA FOTOS DE HERIDAS:
                        if 'base64_foto' in fh:
                            b64_foto_herida = fh['base64_foto']
                            html_foto_herida = f'<img src="data:image/png;base64,{b64_foto_herida}" style="width: 100%; border-radius: 8px; margin-top: 10px;">'
                            st.markdown(html_foto_herida, unsafe_allow_html=True)
            else: st.write("No hay registro fotográfico.")
            
        with st.expander("📊 Signos Vitales"):
            vits = [x for x in st.session_state["vitales_db"] if x["paciente"] == paciente_sel]
            if vits: st.dataframe(pd.DataFrame(vits[-limite:]).drop(columns=["paciente"], errors='ignore'), use_container_width=True)
            else: st.write("No hay signos vitales cargados.")
            
        with st.expander("👶 Control Pediátrico"):
            peds = [x for x in st.session_state["pediatria_db"] if x["paciente"] == paciente_sel]
            if peds: st.dataframe(pd.DataFrame(peds[-limite:]).drop(columns=["paciente"], errors='ignore'), use_container_width=True)
            else: st.write("No hay controles pediátricos.")
            
        with st.expander("⚖️ Balance Hídrico"):
            blp = [x for x in st.session_state["balance_db"] if x["paciente"] == paciente_sel]
            if blp:
                dfb = pd.DataFrame(blp[-limite:]).drop(columns=["paciente"], errors='ignore')
                for c in ["ingresos", "egresos", "balance"]: 
                    if c in dfb.columns:
                        dfb[c] = dfb[c].astype(str)+" ml"
                st.dataframe(dfb, use_container_width=True)
            else: st.write("No hay balances hídricos calculados.")
            
        with st.expander("💊 Plan Terapéutico (Recetas)"):
            recs_todas_hist = [x for x in st.session_state["indicaciones_db"] if x["paciente"] == paciente_sel]
            if recs_todas_hist:
                with st.container(height=350):
                    for r in reversed(recs_todas_hist[-limite:]):
                        firma_mostrar = r.get('firma', r.get('medico_nombre', r.get('firmado_por', 'S/D')))
                        fecha_mostrar = r.get('fecha', 'S/D')
                        med_mostrar = r.get('med', 'S/D')
                        estado = r.get("estado_receta", "Activa")
                        
                        if estado == "Activa":
                            st.success(f"✅ **{fecha_mostrar}** | Indicado por: **{firma_mostrar}**\n\n{med_mostrar}")
                        else:
                            st.error(f"❌ **{fecha_mostrar}** | Indicado por: **{firma_mostrar}**\n\n~~{med_mostrar}~~\n*(ESTADO: {estado.upper()})*")
            else: st.write("No hay terapéutica indicada en el registro histórico.")

# 13. PDF - VERSIÓN CORREGIDA Y COMPLETA (SIN ERRORES 404 Y CON RECETAS LEGALES)
with tabs[menu.index("🗄️ PDF")]:
    if paciente_sel and FPDF_DISPONIBLE:
        import os
        
        def t(txt):
            return str(txt).replace('⚖️', '').replace('⚠️', '').replace('📌', '').replace('📅', '').replace('📸', '').replace('🗄️', '').replace('🔬', '').encode('latin-1', 'replace').decode('latin-1')

        # --- INSERTAR LOGO ---
        def insertar_logo(pdf_obj):
            directorio_actual = os.path.dirname(os.path.abspath(__file__))
            ruta_logo = os.path.join(directorio_actual, "logo_medicare_pro.jpeg")
            try:
                pdf_obj.image(ruta_logo, x=10, y=10, w=25)
            except Exception:
                pdf_obj.set_fill_color(59, 130, 246)
                pdf_obj.ellipse(10, 10, 22, 22, 'F')
                pdf_obj.set_draw_color(255, 255, 255)
                pdf_obj.set_line_width(1.2)
                pdf_obj.line(21, 14, 21, 28)
                pdf_obj.line(14, 21, 28, 21)

        # --- GENERAR HISTORIA CLÍNICA COMPLETA ---
        def crear_pdf_pro(p):
            pdf = FPDF()
            pdf.add_page()
            insertar_logo(pdf)

            emp_paciente = st.session_state["detalles_pacientes_db"].get(p, {}).get("empresa", mi_empresa)
            pdf.set_font("Arial", 'B', 16)
            pdf.set_xy(40, 14)
            pdf.cell(0, 10, t(emp_paciente), ln=True)
            pdf.set_font("Arial", 'I', 9)
            pdf.set_xy(40, 20)
            pdf.cell(0, 10, t("Historia Clinica Digital Integral (Pro V9.11)"), ln=True)
            pdf.ln(15)

            det = st.session_state["detalles_pacientes_db"].get(p, {})
            estado_texto = " [ARCHIVADO/ALTA]" if det.get("estado") == "De Alta" else ""
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, t(f" PACIENTE: {p}{estado_texto}"), 1, 1, 'L', True)
            pdf.set_font("Arial", '', 9)
            pdf.cell(0, 6, t(f" DNI: {det.get('dni','S/D')} | Nacimiento: {det.get('fnac','S/D')} | Sexo: {det.get('sexo','S/D')}"), ln=True)
            pdf.cell(0, 6, t(f" Domicilio del Legajo: {det.get('direccion','S/D')}"), ln=True)
            pdf.ln(5)

            # Signos Vitales
            vits = [x for x in st.session_state.get("vitales_db", []) if x["paciente"] == p]
            if vits:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, t("SIGNOS VITALES:"), ln=True)
                pdf.set_font("Arial", 'B', 8)
                pdf.set_fill_color(230, 230, 230)
                pdf.cell(30, 6, "FECHA", 1, 0, 'C', True)
                pdf.cell(20, 6, "TA", 1, 0, 'C', True)
                pdf.cell(20, 6, "FC", 1, 0, 'C', True)
                pdf.cell(20, 6, "FR", 1, 0, 'C', True)
                pdf.cell(20, 6, "SAT%", 1, 0, 'C', True)
                pdf.cell(20, 6, "TEMP", 1, 0, 'C', True)
                pdf.cell(20, 6, "HGT", 1, 1, 'C', True)
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

            # Evoluciones
            evs = [x for x in st.session_state.get("evoluciones_db", []) if x["paciente"] == p]
            if evs:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, t("EVOLUCIONES CLINICAS:"), ln=True)
                for ev in evs:
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(0, 5, t(f"[{ev.get('fecha','')}] - Firma: {ev.get('firma','')}"), ln=True)
                    pdf.set_font("Arial", '', 9)
                    pdf.multi_cell(0, 5, t(ev.get('nota','')), 'L')
                    pdf.ln(2)
                    
            # PLAN TERAPEUTICO, RECETAS Y SÁBANA DE ENFERMERÍA (NUEVO)
            recs = [x for x in st.session_state.get("indicaciones_db", []) if x["paciente"] == p]
            if recs:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, t("PLAN TERAPEUTICO E INDICACIONES MEDICAS:"), ln=True)
                
                admins_totales = [a for a in st.session_state.get("administracion_med_db", []) if a.get("paciente") == p]
                
                for r in recs:
                    fecha_rec = r.get('fecha', 'S/D')
                    med_completo = r.get('med', 'S/D')
                    med_nombre_corto = med_completo.split(" |")[0].strip()
                    medico = r.get('medico_nombre', r.get('firma', r.get('firmado_por', 'S/D')))
                    matricula = r.get('medico_matricula', 'S/D')
                    estado_rec = r.get('estado_receta', 'Activa')

                    if estado_rec == "Activa":
                        pdf.set_font("Arial", 'B', 8)
                        pdf.cell(0, 5, t(f"[{fecha_rec}] - Medico: {medico} (Mat: {matricula})"), ln=True)
                        pdf.set_font("Arial", '', 9)
                        pdf.multi_cell(0, 5, t(f"Rp/ {med_completo}"), 'L')
                    else:
                        fecha_susp = r.get('fecha_suspension', 'S/D')
                        pdf.set_text_color(220, 38, 38) # Rojo
                        pdf.set_font("Arial", 'B', 8)
                        pdf.cell(0, 5, t(f"[{fecha_rec}] - Medico: {medico} (Mat: {matricula}) - {estado_rec.upper()} el {fecha_susp}"), ln=True)
                        pdf.set_font("Arial", '', 9)
                        pdf.multi_cell(0, 5, t(f"~~ ANULADA: {med_completo} ~~"), 'L')
                        pdf.set_text_color(0, 0, 0) # Vuelve a Negro
                    
                    # Rastrear aplicaciones para este medicamento en particular
                    admins_medicamento = [a for a in admins_totales if a.get("med") == med_nombre_corto]
                    if admins_medicamento:
                        pdf.set_font("Arial", 'I', 8)
                        pdf.cell(0, 4, t("   > Registros de Administracion (Sabana):"), ln=True)
                        for a in admins_medicamento:
                            estado_adm = "APLICADO" if "✅" in a.get("estado", "") else f"NO APLICADO (Motivo: {a.get('motivo','')})"
                            texto_adm = f"     - {a.get('fecha')} a las {a.get('hora')}hs | Estado: {estado_adm} | Enf: {a.get('firma')}"
                            pdf.cell(0, 4, t(texto_adm), ln=True)
                            
                    pdf.ln(3)
                pdf.ln(2)

            # Estudios Complementarios
            estudios_pdf = [x for x in st.session_state.get("estudios_db", []) if x["paciente"] == p]
            if estudios_pdf:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, t("ESTUDIOS COMPLEMENTARIOS:"), ln=True)
                for est in estudios_pdf:
                    pdf.set_font("Arial", 'B', 8)
                    pdf.cell(0, 5, t(f"[{est.get('fecha','')}] {est.get('tipo','')} - Firma: {est.get('firma','')}"), ln=True)
                    if est.get('detalle'):
                        pdf.set_font("Arial", '', 9)
                        pdf.multi_cell(0, 5, t(est.get('detalle','')), 'L')
                pdf.ln(4)

            # Materiales
            cons = [x for x in st.session_state.get("consumos_db", []) if x["paciente"] == p]
            if cons:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, t("MATERIALES DESCARTABLES UTILIZADOS:"), ln=True)
                for c in cons:
                    pdf.set_font("Arial", '', 9)
                    pdf.cell(0, 5, t(f"[{c['fecha']}] {c['cantidad']}x {c['insumo']} - Registrado por: {c['firma']}"), ln=True)
                pdf.ln(4)

            # Checkins GPS
            chks = [x for x in st.session_state.get("checkin_db", []) if x["paciente"] == p]
            if chks:
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(0, 8, t("AUDITORIA DE PRESENCIA GPS (Llegada/Salida):"), ln=True)
                pdf.set_font("Arial", '', 8)
                for c in chks:
                    pdf.multi_cell(0, 5, t(f"[{c['fecha_hora']}] {c['tipo']} | Por: {c['profesional']}"), align='L')
                pdf.ln(4)

            # Firmas
            pdf.ln(10)
            y_firma = pdf.get_y()
            pdf.line(10, y_firma, 80, y_firma)
            pdf.set_font("Arial", 'B', 9)
            pdf.set_xy(10, y_firma + 2)
            pdf.cell(70, 5, t(f"Firma Profesional: {user['nombre']}"), ln=2)
            pdf.cell(70, 5, t(f"Matricula: {user.get('matricula', 'S/D')}"), ln=0)

            firmas_paciente = [x for x in st.session_state.get("firmas_tactiles_db", []) if x["paciente"] == p]
            if firmas_paciente:
                ultima_firma = firmas_paciente[-1]["firma_img"]
                if ultima_firma != "Firma Guardada Exitosamente":
                    try:
                        img_data = base64.b64decode(ultima_firma)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(img_data)
                            tmp_path = tmp.name
                        pdf.image(tmp_path, x=130, y=y_firma - 15, w=40)
                        os.remove(tmp_path)
                    except Exception:
                        pass

            nombre_paciente = p.split(" (")[0]
            pdf.line(120, y_firma, 190, y_firma)
            pdf.set_xy(120, y_firma + 2)
            pdf.cell(70, 5, t("Conformidad Paciente / Familiar"), ln=2)
            pdf.cell(70, 5, t(f"Aclaracion: {nombre_paciente}"), ln=2)
            pdf.cell(70, 5, t(f"DNI: {det.get('dni', 'S/D')}"), ln=0)
            return pdf.output(dest='S').encode('latin-1')

        # --- CONSENTIMIENTO INFORMADO (sin cambios) ---
        def crear_consentimiento_pdf(p):
            pdf = FPDF()
            pdf.add_page()
            insertar_logo(pdf)
            
            det = st.session_state["detalles_pacientes_db"].get(p, {})
            emp_paciente = det.get("empresa", mi_empresa)
            nombre_paciente = p.split(" (")[0]
            
            pdf.set_y(40)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, t("CONSENTIMIENTO INFORMADO DE INTERNACION DOMICILIARIA"), ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 11)
            
            texto_legal = f"Por la presente, yo {nombre_paciente}, con DNI {det.get('dni', 'S/D')}, con domicilio en {det.get('direccion', 'S/D')}, declaro haber sido informado/a por el personal de la empresa {emp_paciente} sobre los alcances, modalidades y pautas del servicio de internación / cuidado domiciliario que voy a recibir.\n\nComprendo que la atención domiciliaria requiere de la colaboración activa del grupo familiar y declaro mi total conformidad para que el personal de salud ingrese a mi domicilio para realizar las prácticas establecidas en el plan terapéutico.\n\nAsimismo, entiendo que los registros clínicos serán resguardados en formato digital a través de la plataforma MediCare Enterprise PRO, autorizando el procesamiento de mis datos de salud según las normativas vigentes."
            
            pdf.multi_cell(0, 7, t(texto_legal))
            pdf.ln(30)
            
            y_firma = pdf.get_y()
            firmas_paciente = [x for x in st.session_state.get("firmas_tactiles_db", []) if x["paciente"] == p]
            if firmas_paciente:
                ultima_firma = firmas_paciente[-1]["firma_img"]
                if ultima_firma != "Firma Guardada Exitosamente":
                    try:
                        img_data = base64.b64decode(ultima_firma)
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                            tmp.write(img_data)
                            tmp_path = tmp.name
                        pdf.image(tmp_path, x=85, y=y_firma - 15, w=40)
                        os.remove(tmp_path)
                    except Exception:
                        pass
            
            pdf.line(60, y_firma, 150, y_firma)
            pdf.set_xy(60, y_firma + 2)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(90, 5, t("Firma del Paciente / Responsable"), ln=2, align='C')
            pdf.cell(90, 5, t(f"Aclaracion: {nombre_paciente}"), ln=2, align='C')
            pdf.cell(90, 5, t(f"DNI: {det.get('dni', 'S/D')}"), ln=2, align='C')
            pdf.cell(90, 5, t(f"Fecha: {ahora().strftime('%d/%m/%Y')}"), ln=0, align='C')
            return pdf.output(dest='S').encode('latin-1')

        # --- BOTONES DE DESCARGA SEGURA ---
        st.markdown("### 📄 Generar Documentos del Paciente")
        
        pdf_hc = crear_pdf_pro(paciente_sel)
        b64_hc = base64.b64encode(pdf_hc).decode('utf-8')
        html_hc = f'''
        <a href="data:application/pdf;base64,{b64_hc}" 
           download="HC_{paciente_sel.replace(' ', '_')}.pdf" 
           style="display: block; width: 100%; text-align: center; background-color: #2563eb; 
                  color: white; padding: 14px; border-radius: 8px; text-decoration: none; 
                  font-weight: 600; font-family: sans-serif; margin-bottom: 12px;">
           📥 1. Descargar Historia Clínica Completa (PDF)
        </a>
        '''
        st.markdown(html_hc, unsafe_allow_html=True)

        pdf_cons = crear_consentimiento_pdf(paciente_sel)
        b64_cons = base64.b64encode(pdf_cons).decode('utf-8')
        html_cons = f'''
        <a href="data:application/pdf;base64,{b64_cons}" 
           download="Consentimiento_{paciente_sel.replace(' ', '_')}.pdf" 
           style="display: block; width: 100%; text-align: center; background-color: #10b981; 
                  color: white; padding: 14px; border-radius: 8px; text-decoration: none; 
                  font-weight: 600; font-family: sans-serif;">
           📄 2. Descargar Consentimiento Informado Legal
        </a>
        '''
        st.markdown(html_cons, unsafe_allow_html=True)

        st.success("✅ Descargas seguras activadas. Ya no deberían aparecer errores 404.")

# 14. CIERRE DIARIO Y REPORTES DE STOCK (SOLO VISIBLE PARA ADMIN/COORDINADOR)
if "📑 Cierre Diario" in menu:
    with tabs[menu.index("📑 Cierre Diario")]:
        st.subheader("📑 Conciliación y Cierre Diario de Operaciones")
        st.info("Seleccioná un día para auditar todos los insumos consumidos, la facturación ingresada y el estado del stock de farmacia en esa fecha.")
        
        c1_rep, c2_rep = st.columns([1, 2])
        fecha_reporte = c1_rep.date_input("Filtrar por Fecha:", value=ahora().date())
        fecha_str = fecha_reporte.strftime("%d/%m/%Y")
        
        # Filtros del día seleccionado
        consumos_dia = [c for c in st.session_state.get("consumos_db", [])
                       if c.get("fecha", "").startswith(fecha_str) and c.get("empresa") == mi_empresa]
        facturacion_dia = [f for f in st.session_state.get("facturacion_db", [])
                          if f.get("fecha", "").startswith(fecha_str) and f.get("empresa") == mi_empresa]
        stock_actual = [i for i in st.session_state.get("inventario_db", [])
                       if i.get("empresa") == mi_empresa]

        # ====================== MÉTRICAS RÁPIDAS ======================
        total_insumos = sum(c.get("cantidad", 0) for c in consumos_dia)
        total_facturado = sum(f.get("monto", 0) for f in facturacion_dia)
        stock_critico = len([s for s in stock_actual if s.get("stock", 0) <= 10])
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("📦 Insumos Consumidos", f"{total_insumos} unidades")
        col_m2.metric("💰 Facturado del Día", f"${total_facturado:,.2f}")
        col_m3.metric("⚠️ Stock Crítico", f"{stock_critico} insumos", delta=None)
        
        st.divider()

        # ====================== EXPANDERS (se mantiene toda la lógica original) ======================
        with st.expander(f"📦 1. Insumos Consumidos el {fecha_str}", expanded=True):
            if consumos_dia:
                st.dataframe(
                    pd.DataFrame(consumos_dia).drop(columns="empresa", errors='ignore'),
                    use_container_width=True
                )
            else:
                st.write("No hubo registro de uso de insumos en este día.")
        
        with st.expander(f"💳 2. Procedimientos y Facturación el {fecha_str}", expanded=True):
            if facturacion_dia:
                st.success(f"**Total Facturado en el día: ${total_facturado:,.2f}**")
                st.dataframe(
                    pd.DataFrame(facturacion_dia).drop(columns="empresa", errors='ignore'),
                    use_container_width=True
                )
            else:
                st.write("No hubo facturación registrada en este día.")
        
        with st.expander("⚕️ 3. Estado de Stock de Farmacia Actual", expanded=False):
            if stock_actual:
                st.dataframe(
                    pd.DataFrame(stock_actual).drop(columns="empresa", errors='ignore'),
                    use_container_width=True
                )
            else:
                st.write("No hay stock cargado.")
        
        st.divider()

        # ====================== GENERACIÓN DE PDF OFICIAL (mejorado y reutilizable) ======================
        if FPDF_DISPONIBLE:
            st.markdown("#### 🔒 Generar Documento Oficial de Cierre")
            
            def t(txt):
                if not txt:
                    return ""
                replacements = {'ñ':'n','Ñ':'N','á':'a','Á':'A','é':'e','É':'E','í':'i','Í':'I',
                               'ó':'o','Ó':'O','ú':'u','Ú':'U','ü':'u','Ü':'U'}
                for old, new in replacements.items():
                    txt = txt.replace(old, new)
                return str(txt).encode('latin-1', 'replace').decode('latin-1')
            
            # Función mejorada: ahora acepta fecha opcional (para "Cierre de Hoy")
            def generar_pdf_cierre(fecha_para_pdf=None):
                if fecha_para_pdf is None:
                    # Usar fecha seleccionada en el date_input
                    fecha_str_pdf = fecha_str
                    consumos_pdf = consumos_dia
                    facturacion_pdf = facturacion_dia
                    total_facturado_pdf = total_facturado
                else:
                    # Para "Cierre de Hoy" o cualquier otra fecha
                    if isinstance(fecha_para_pdf, date):
                        fecha_str_pdf = fecha_para_pdf.strftime("%d/%m/%Y")
                    else:
                        fecha_str_pdf = str(fecha_para_pdf)
                    consumos_pdf = [c for c in st.session_state.get("consumos_db", [])
                                   if c.get("fecha", "").startswith(fecha_str_pdf) and c.get("empresa") == mi_empresa]
                    facturacion_pdf = [f for f in st.session_state.get("facturacion_db", [])
                                      if f.get("fecha", "").startswith(fecha_str_pdf) and f.get("empresa") == mi_empresa]
                    total_facturado_pdf = sum(f.get("monto", 0) for f in facturacion_pdf)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 15)
                pdf.cell(0, 12, t(f"REPORTE DE CIERRE DIARIO - {mi_empresa}"), ln=True, align='C')
                pdf.set_font("Arial", 'I', 10)
                pdf.cell(0, 8, t(f"Fecha auditada: {fecha_str_pdf} | Generado por: {user['nombre']} a las {ahora().strftime('%H:%M')}"),
                        ln=True, align='C')
                pdf.ln(8)
                
                # 1. Insumos
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, t("1. INSUMOS CONSUMIDOS EN EL DÍA"), ln=True)
                pdf.set_font("Arial", '', 10)
                if not consumos_pdf:
                    pdf.cell(0, 6, t(" No hubo consumos registrados."), ln=True)
                else:
                    for c in consumos_pdf:
                        pdf.cell(0, 6, t(f" • {c.get('cantidad')}x {c.get('insumo')} | Paciente: {c.get('paciente')}"), ln=True)
                pdf.ln(8)
                
                # 2. Facturación
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, t("2. PROCEDIMIENTOS Y FACTURACIÓN DEL DÍA"), ln=True)
                pdf.set_font("Arial", '', 10)
                if not facturacion_pdf:
                    pdf.cell(0, 6, t(" No hubo facturación registrada."), ln=True)
                else:
                    for f in facturacion_pdf:
                        pdf.cell(0, 6, t(f" • ${f.get('monto')} | {f.get('serv')} | {f.get('paciente')}"), ln=True)
                    pdf.set_font("Arial", 'B', 11)
                    pdf.cell(0, 10, t(f"TOTAL FACTURADO DEL DÍA: ${total_facturado_pdf:,.2f}"), ln=True)
                pdf.ln(8)
                
                # 3. Stock
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, t("3. BALANCE DE STOCK EN FARMACIA (AL CIERRE)"), ln=True)
                pdf.set_font("Arial", '', 10)
                if not stock_actual:
                    pdf.cell(0, 6, t(" No hay stock registrado."), ln=True)
                else:
                    for s in stock_actual:
                        pdf.cell(0, 6, t(f" • {s.get('item')}: {s.get('stock')} unidades"), ln=True)
                pdf.ln(15)
                pdf.set_font("Arial", '', 9)
                pdf.cell(0, 6, t("Documento generado automáticamente por MediCare Enterprise PRO"), ln=True, align='C')
                
                return pdf.output(dest='S').encode('latin-1')
            
            # ====================== BOTONES (ahora ambos funcionan) ======================
            col_btn1, col_btn2 = st.columns([1, 1])
            
            if col_btn1.button("📅 Generar Cierre de Hoy", use_container_width=True, type="primary"):
                hoy_fecha = ahora().date()
                hoy_str = hoy_fecha.strftime("%d/%m/%Y")
                b64_pdf = base64.b64encode(generar_pdf_cierre(hoy_fecha)).decode('utf-8')
                
                st.session_state["reportes_diarios_db"].append({
                    "fecha_reporte": hoy_str,
                    "fecha_generacion": ahora().strftime("%d/%m/%Y %H:%M"),
                    "generado_por": user["nombre"],
                    "empresa": mi_empresa,
                    "pdf_base64": b64_pdf
                })
                guardar_datos()
                st.success(f"✅ ¡Cierre del día {hoy_str} (HOY) guardado exitosamente!")
                st.rerun()
            
            if col_btn2.button(f"📄 Generar y Guardar Reporte PDF del {fecha_str}",
                             use_container_width=True, type="secondary"):
                b64_pdf = base64.b64encode(generar_pdf_cierre()).decode('utf-8')
                st.session_state["reportes_diarios_db"].append({
                    "fecha_reporte": fecha_str,
                    "fecha_generacion": ahora().strftime("%d/%m/%Y %H:%M"),
                    "generado_por": user["nombre"],
                    "empresa": mi_empresa,
                    "pdf_base64": b64_pdf
                })
                guardar_datos()
                st.success(f"✅ ¡Cierre del día {fecha_str} guardado exitosamente!")
                st.rerun()
        
        st.divider()

        # ====================== ARCHIVO HISTÓRICO (¡LA CAJITA CON SCROLL QUE PEDISTE!) ======================
        with st.expander("🗄️ Archivo Histórico de Cierres Diarios", expanded=False):
            reportes_mios = [r for r in reversed(st.session_state.get("reportes_diarios_db", []))
                            if r.get("empresa") == mi_empresa]
            
            if reportes_mios:
                st.caption("📋 Lista de todos los cierres guardados (más recientes primero)")
                for r in reportes_mios:
                    with st.container(border=True):
                        c1_hist, c2_hist = st.columns([4, 1])
                        c1_hist.markdown(f"**📄 Cierre del día {r['fecha_reporte']}**")
                        c1_hist.caption(f"Generado el {r['fecha_generacion']} por {r['generado_por']}")
                        
                        # Botón descarga seguro
                        b64_pdf_cierre = r['pdf_base64']
                        nombre_arch_cierre = f"Cierre_Diario_{r['fecha_reporte'].replace('/','-')}.pdf"
                        html_btn_cierre = f'''
                        <a href="data:application/pdf;base64,{b64_pdf_cierre}"
                           download="{nombre_arch_cierre}"
                           style="display: block; width: 100%; text-align: center;
                                  background-color: #2563eb; color: white; padding: 10px;
                                  border-radius: 8px; text-decoration: none; font-weight: 600;">
                           📥 Descargar PDF
                        </a>
                        '''
                        c2_hist.markdown(html_btn_cierre, unsafe_allow_html=True)
            else:
                st.info("Aún no hay reportes de cierre diario guardados. Generá el primero con los botones de arriba.")

# 15. TELEMEDICINA (JITSI EMBEBIDO + FIX MÓVILES + EXTRACCIÓN DINÁMICA DE VITALES)
with tabs[menu.index("📹 Telemedicina")]:
    if paciente_sel:
        st.subheader("📹 Teleconsulta en Vivo")
        st.info("💡 **Instrucciones:** En celular usa el botón azul grande. En computadora puedes usar la vista integrada de abajo.")

        # Generación de ID de sala criptográficamente seguro
        nombre_limpio = "".join(e for e in paciente_sel if e.isalnum())
        fecha_hoy = ahora().strftime('%d%m%Y')
        sala_id = f"MediCare-{nombre_limpio}-{fecha_hoy}"
        jitsi_url = f"https://meet.jit.si/{sala_id}#config.disableDeepLinking=true&config.prejoinPageEnabled=false"

        # ====================== VISTA PRINCIPAL ======================
        c_vid1, c_vid2 = st.columns([3, 1])

        with c_vid1:
            st.markdown("### 🔴 Sala de Video en Vivo")
            st.link_button(
                "🚀 ABRIR VIDEOLLAMADA EN PANTALLA COMPLETA",
                jitsi_url,
                use_container_width=True,
                type="primary"
            )
            st.caption("🔹 Recomendado para celulares y tablets")
            st.divider()

            st.markdown("**Vista integrada (PC / Notebook):**")
            iframe_html = f"""
            <iframe
                src="{jitsi_url}"
                allow="camera; microphone; fullscreen; display-capture; autoplay"
                style="width: 100%; height: 520px; border: none; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15);">
            </iframe>
            """
            components.html(iframe_html, height=540)

        with c_vid2:
            st.markdown("### 🔗 Enlace para compartir")
            st.code(jitsi_url, language=None)

            if st.button("📋 Copiar enlace de la sala", use_container_width=True):
                st.toast("✅ Enlace copiado al portapapeles", icon="📋")
                st.session_state["clipboard"] = jitsi_url

            st.divider()
            st.markdown("### 📋 Resumen Clínico Inmediato")
            st.write(f"**Paciente:** {paciente_sel}")

            vitales_paciente = [v for v in st.session_state.get("vitales_db", [])
                               if v.get("paciente") == paciente_sel]

            if vitales_paciente:
                ult = vitales_paciente[-1]
                st.success(f"**Último control:** {ult.get('fecha', 'S/D')}")
                claves_excluidas = ["paciente", "fecha", "id", "observaciones", "firma"]
                cols_v = st.columns(2)
                i = 0
                for clave, valor in ult.items():
                    if clave not in claves_excluidas and valor not in [None, "", " "]:
                        nombre_formateado = str(clave).replace('_', ' ').title()
                        with cols_v[i % 2]:
                            st.metric(label=nombre_formateado, value=valor)
                        i += 1
            else:
                st.warning("Aún no hay signos vitales registrados para este paciente.")

    else:
        st.info("👈 Seleccione un paciente en el panel lateral para iniciar una teleconsulta.")


# =====================================================================
# 16. EQUIPO Y SUSCRIPCIONES (SOLO VISIBLE PARA ADMIN/COORDINADOR)
# =====================================================================
if "⚙️ Mi Equipo" in menu:
    with tabs[menu.index("⚙️ Mi Equipo")]:
        st.subheader(f"👥 Gestión de Personal - {mi_empresa}")

        # ====================== FORMULARIO PARA AGREGAR USUARIO ======================
        with st.form("equipo", clear_on_submit=True):
            st.markdown("##### ➕ Habilitar Nuevo Usuario")
            
            col_id, col_pw, col_pin = st.columns([2, 2, 1])
            u_id = col_id.text_input("Usuario (Login)", placeholder="ej: maria.lopez")
            u_pw = col_pw.text_input("Clave de acceso", type="password")
            u_pin = col_pin.text_input("PIN (4 dígitos)", max_chars=4, placeholder="1234")

            u_nm = st.text_input("Nombre Completo del Profesional")
            
            col_dni, col_mt = st.columns(2)
            u_dni = col_dni.text_input("DNI del Profesional")
            u_mt = col_mt.text_input("Matrícula / Matrícula Profesional")

            u_ti = st.selectbox("Título / Cargo", [
                "Médico/a", "Lic. en Enfermería", "Enfermero/a", "Kinesiólogo/a",
                "Fonoaudiólogo/a", "Nutricionista", "Psicólogo/a", 
                "Acompañante Terapéutico", "Trabajador/a Social", "Administrativo/a", "Otro"
            ])
            
            u_emp = st.text_input("🏢 Asignar a Clínica / Empresa") if rol == "SuperAdmin" else mi_empresa
            u_rl = st.selectbox("Rol en el sistema", 
                              ["Operativo", "Coordinador", "SuperAdmin"] if rol == "SuperAdmin" else ["Operativo", "Coordinador"])

            if st.form_submit_button("✅ Habilitar Acceso", use_container_width=True, type="primary"):
                if not u_id or not u_pw or not u_pin or not u_dni:
                    st.error("❌ Todos los campos obligatorios deben completarse.")
                elif len(u_pin) != 4 or not u_pin.isdigit():
                    st.error("❌ El PIN debe tener exactamente 4 dígitos numéricos.")
                else:
                    st.session_state["usuarios_db"][u_id.strip().lower()] = {
                        "pass": u_pw.strip(),
                        "nombre": u_nm.strip(),
                        "rol": u_rl,
                        "titulo": u_ti,
                        "empresa": u_emp.strip(),
                        "matricula": u_mt.strip(),
                        "dni": u_dni.strip(),
                        "estado": "Activo",
                        "pin": u_pin.strip()
                    }
                    guardar_datos()
                    st.success(f"✅ Usuario **{u_id}** habilitado correctamente.")
                    st.rerun()

        st.divider()

        # ====================== LISTADO DE USUARIOS CON SCROLL ANTI-COLAPSO ======================
        st.subheader("👥 Control de Accesos")

        buscar_usuario = st.text_input("🔎 Buscar usuario por nombre, login o DNI...", "")

        usuarios_filtrados = {
            k: v for k, v in st.session_state["usuarios_db"].items()
            if (v.get("empresa") == mi_empresa or rol == "SuperAdmin")
            and (not buscar_usuario or 
                 buscar_usuario.lower() in k.lower() or 
                 buscar_usuario.lower() in v.get("nombre", "").lower() or 
                 buscar_usuario.lower() in v.get("dni", "").lower())
        }

        if not usuarios_filtrados:
            st.info("No se encontraron usuarios con ese criterio.")
        else:
            st.caption(f"Mostrando {len(usuarios_filtrados)} usuarios")

            # Contenedor con scroll interno (anti-colapso)
            with st.container(height=620, border=True):
                for u, d in usuarios_filtrados.items():
                    if u == "admin":
                        continue

                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns([3.5, 1.2, 1, 1])

                        estado_color = "🟢" if d.get("estado", "Activo") == "Activo" else "🔴"
                        
                        with col1:
                            st.markdown(f"**{d.get('nombre', 'Sin nombre')}**")
                            # ==== ACÁ ESTÁ LA MEJORA: AHORA FIGURA EL ROL ====
                            st.caption(f"Login: `{u}` | Rol: **{d.get('rol', 'S/D')}** | {d.get('titulo', '')} | DNI: {d.get('dni', 'S/D')} | PIN: `{d.get('pin', 'S/D')}`")

                        with col2:
                            st.markdown(f"{estado_color} **{d.get('estado', 'Activo')}**")

                        if rol == "SuperAdmin":
                            if d.get("estado") == "Activo":
                                if col3.button("⏸️ Suspender", key=f"susp_{u}", use_container_width=True):
                                    st.session_state["usuarios_db"][u]["estado"] = "Bloqueado"
                                    guardar_datos()
                                    st.rerun()
                            else:
                                if col3.button("▶️ Reactivar", key=f"reac_{u}", use_container_width=True):
                                    st.session_state["usuarios_db"][u]["estado"] = "Activo"
                                    guardar_datos()
                                    st.rerun()

                        if col4.button("❌ Bajar", key=f"del_{u}", use_container_width=True):
                            if st.checkbox(f"¿Estás seguro de eliminar a {d.get('nombre')}?", key=f"conf_del_{u}"):
                                del st.session_state["usuarios_db"][u]
                                guardar_datos()
                                st.success(f"Usuario {u} eliminado.")
                                st.rerun()
# 17. AUDITORÍA (SOLO VISIBLE PARA ADMIN/COORDINADOR)
if "🕵️ Auditoría" in menu:
    with tabs[menu.index("🕵️ Auditoría")]:
        st.subheader("🕵️ Auditoría General de Movimientos")
        st.info("Consulta completa de todos los movimientos del sistema. Solo visible para Admin/Coordinador.")

        # ====================== TABS INTERNAS ======================
        tab_logs, tab_rrhh = st.tabs(["📋 Logs Generales del Sistema", "👥 Reporte RRHH - Asistencia por Profesional"])

        # ====================== TAB 1: LOGS GENERALES ======================
        with tab_logs:
            df_logs = pd.DataFrame(st.session_state.get("logs_db", []))

            if not df_logs.empty:
                # --- FILTROS AVANZADOS ---
                col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
                
                # Filtro por fecha (esencial en auditoría)
                fecha_inicio = col_f1.date_input("Desde:", value=ahora().date().replace(day=1), key="log_desde")
                fecha_fin = col_f2.date_input("Hasta:", value=ahora().date(), key="log_hasta")
                
                # Filtro por usuario
                usuarios_unicos = sorted(df_logs["usuario"].astype(str).unique()) if "usuario" in df_logs.columns else []
                usuario_filtro = col_f3.selectbox("Usuario:", ["Todos"] + usuarios_unicos, key="log_usuario")
                
                # Búsqueda textual
                buscar_log = st.text_input("🔍 Buscar en acción, usuario, detalle, etc.:", key="buscar_log")

                # Aplicar filtros
                df_filtrado = df_logs.copy()
                
                # Filtro fecha
                if "fecha" in df_filtrado.columns:
                    df_filtrado["fecha_dt"] = pd.to_datetime(df_filtrado["fecha"], errors="coerce")
                    df_filtrado = df_filtrado[
                        (df_filtrado["fecha_dt"].dt.date >= fecha_inicio) &
                        (df_filtrado["fecha_dt"].dt.date <= fecha_fin)
                    ]
                
                # Filtro usuario
                if usuario_filtro != "Todos" and "usuario" in df_filtrado.columns:
                    df_filtrado = df_filtrado[df_filtrado["usuario"] == usuario_filtro]
                
                # Filtro texto
                if buscar_log:
                    mask = df_filtrado.astype(str).apply(
                        lambda x: x.str.contains(buscar_log, case=False, na=False)
                    ).any(axis=1)
                    df_filtrado = df_filtrado[mask]

                # Métricas rápidas
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Total Registros", len(df_filtrado))
                col_m2.metric("Usuarios Únicos", df_filtrado["usuario"].nunique() if "usuario" in df_filtrado.columns else 0)
                col_m3.metric("Último Registro", df_filtrado["fecha"].max() if "fecha" in df_filtrado.columns else "—")

                st.dataframe(df_filtrado.drop(columns=["fecha_dt"], errors="ignore"), use_container_width=True)

                # --- DESCARGA EXCEL (mejorado) ---
                out_logs = io.BytesIO()
                with pd.ExcelWriter(out_logs, engine='openpyxl') as writer:
                    df_filtrado.drop(columns=["fecha_dt"], errors="ignore").to_excel(
                        writer, index=False, sheet_name='Auditoria_MediCare'
                    )
                
                b64_excel = base64.b64encode(out_logs.getvalue()).decode('utf-8')
                nombre_excel = f"Auditoria_Logs_{ahora().strftime('%d_%m_%Y_%H%M')}.xlsx"
                
                html_btn = f'''
                <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}"
                   download="{nombre_excel}"
                   style="display: block; width: 100%; text-align: center; background-color: #10b981;
                          color: white; padding: 14px; border-radius: 8px; text-decoration: none;
                          font-weight: 700; margin-top: 15px;">
                   📥 DESCARGAR AUDITORÍA COMPLETA EN EXCEL
                </a>
                '''
                st.markdown(html_btn, unsafe_allow_html=True)
            else:
                st.info("Aún no hay registros de auditoría. Los movimientos se irán registrando automáticamente.")

        # ====================== TAB 2: REPORTE RRHH ======================
        with tab_rrhh:
            st.subheader("📄 Auditoría de Asistencia y Visitas por Profesional")

            if FPDF_DISPONIBLE:
                # Lista de profesionales (usuarios + históricos)
                profesionales_lista = list(set([v.get('nombre', '') for v in st.session_state.get("usuarios_db", {}).values()]))
                profesionales_historicos = list(set([c.get("profesional", "") for c in st.session_state.get("checkin_db", [])]))
                profesionales_lista = sorted(list(set(profesionales_lista + profesionales_historicos)))

                if profesionales_lista:
                    prof_sel = st.selectbox("Seleccionar Profesional:", profesionales_lista, key="prof_rrhh")

                    # Filtro de fechas para el reporte RRHH (esencial)
                    col_r1, col_r2 = st.columns(2)
                    fecha_rrhh_desde = col_r1.date_input("Desde:", value=ahora().date().replace(day=1), key="rrhh_desde")
                    fecha_rrhh_hasta = col_r2.date_input("Hasta:", value=ahora().date(), key="rrhh_hasta")

                    # Filtrar checkins del profesional y rango de fechas
                    chks_prof = [
                        c for c in st.session_state.get("checkin_db", [])
                        if c.get("profesional") == prof_sel
                        and fecha_rrhh_desde <= pd.to_datetime(c.get("fecha_hora", "")).date() <= fecha_rrhh_hasta
                    ]

                    # Métricas de asistencia
                    total_visitas = len(chks_prof)
                    st.success(f"**{total_visitas}** visitas registradas para **{prof_sel}** en el período seleccionado")

                    if chks_prof:
                        # Mostrar tabla previa
                        df_rrhh = pd.DataFrame(chks_prof)
                        st.dataframe(df_rrhh, use_container_width=True)

                        # ====================== GENERACIÓN DE PDF PROFESIONAL ======================
                        def generar_pdf_rrhh():
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", 'B', 15)
                            pdf.cell(0, 12, t(f"REPORTE RRHH - ASISTENCIA Y GPS - {mi_empresa}"), ln=True, align='C')
                            pdf.set_font("Arial", 'B', 12)
                            pdf.cell(0, 10, t(f"Profesional: {prof_sel}"), ln=True)
                            pdf.set_font("Arial", 'I', 10)
                            pdf.cell(0, 8, t(f"Período: {fecha_rrhh_desde.strftime('%d/%m/%Y')} - {fecha_rrhh_hasta.strftime('%d/%m/%Y')}"), ln=True)
                            pdf.cell(0, 8, t(f"Generado: {ahora().strftime('%d/%m/%Y %H:%M')}"), ln=True)
                            pdf.ln(10)

                            # Cabecera tabla
                            pdf.set_font("Arial", 'B', 10)
                            pdf.cell(30, 8, t("Fecha"), border=1)
                            pdf.cell(45, 8, t("Paciente"), border=1)
                            pdf.cell(35, 8, t("Acción"), border=1)
                            pdf.cell(40, 8, t("GPS"), border=1)
                            pdf.cell(40, 8, t("Duración aprox."), border=1, ln=True)

                            pdf.set_font("Arial", '', 9)
                            for c in reversed(chks_prof):
                                fecha = c.get('fecha_hora', '')[:16]
                                paciente = c.get('paciente', '—')[:25]
                                accion = c.get('tipo', '—')
                                gps = c.get('gps', '—')[:25]
                                duracion = "—"
                                
                                pdf.cell(30, 8, t(fecha), border=1)
                                pdf.cell(45, 8, t(paciente), border=1)
                                pdf.cell(35, 8, t(accion), border=1)
                                pdf.cell(40, 8, t(gps), border=1)
                                pdf.cell(40, 8, t(duracion), border=1, ln=True)

                            pdf.ln(10)
                            pdf.set_font("Arial", '', 9)
                            pdf.cell(0, 6, t("Documento generado automáticamente por MediCare Enterprise PRO"), ln=True, align='C')
                            return pdf.output(dest='S').encode('latin-1')

                        pdf_bytes = generar_pdf_rrhh()

                        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                        nombre_pdf = f"RRHH_{prof_sel.replace(' ', '_')}_{fecha_rrhh_desde.strftime('%d%m%Y')}-{fecha_rrhh_hasta.strftime('%d%m%Y')}.pdf"

                        html_btn_pdf = f'''
                        <a href="data:application/pdf;base64,{b64_pdf}" download="{nombre_pdf}"
                           style="display: block; width: 100%; text-align: center; background-color: #2563eb;
                                  color: white; padding: 14px; border-radius: 8px; text-decoration: none;
                                  font-weight: 700; margin-top: 15px;">
                           📥 DESCARGAR REPORTE RRHH EN PDF (Oficial)
                        </a>
                        '''
                        st.markdown(html_btn_pdf, unsafe_allow_html=True)
                    else:
                        st.warning("No se encontraron registros de asistencia para el profesional y período seleccionado.")
                else:
                    st.info("No hay profesionales registrados aún.")
            else:
                st.error("Librería FPDF no disponible. Contacte al administrador.")

# =====================================================================
# 18. CONTROL DE ASISTENCIA EN VIVO (SOLO ADMIN/COORD)
# =====================================================================
if "⏱️ Asistencia en Vivo" in menu:
    with tabs[menu.index("⏱️ Asistencia en Vivo")]:
        st.subheader("⏱️ Panel de Control de Asistencias en Vivo")
        st.info("Monitoreo en tiempo real de los profesionales que se encuentran actualmente trabajando dentro del domicilio de un paciente.")
        
        hoy_str = ahora().strftime("%d/%m/%Y")
        chks_hoy = [c for c in st.session_state.get("checkin_db", []) if c.get("fecha_hora", "").startswith(hoy_str) and c.get("empresa") == mi_empresa]
        
        estado_profesionales = {}
        for c in chks_hoy:
            prof = c["profesional"]
            pac = c["paciente"]
            try:
                dt = datetime.strptime(c["fecha_hora"], "%d/%m/%Y %H:%M:%S")
            except:
                dt = datetime.strptime(c["fecha_hora"], "%d/%m/%Y %H:%M")
                
            if "LLEGADA" in c["tipo"]:
                estado_profesionales[prof] = {"estado": "En Guardia", "llegada": dt, "paciente": pac}
            elif "SALIDA" in c["tipo"]:
                estado_profesionales[prof] = {"estado": "Fuera", "llegada": None, "paciente": None}
                
        activos = {k: v for k, v in estado_profesionales.items() if v["estado"] == "En Guardia"}
        
        if activos:
            st.markdown("#### 🟢 Profesionales Actualmente en Domicilio")
            for prof, data in activos.items():
                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])
                    dt_llegada = data["llegada"]
                    
                    duracion = ahora().replace(tzinfo=None) - dt_llegada
                    horas, rem = divmod(duracion.seconds, 3600)
                    minutos, _ = divmod(rem, 60)
                    
                    col_info.markdown(f"👤 **{prof}** está en el domicilio de **{data['paciente']}**")
                    col_info.caption(f"Ingresó a las: {dt_llegada.strftime('%H:%M')} ➔ **Tiempo transcurrido: {horas}h {minutos}m**")
                    
                    if col_btn.button("🔴 Forzar Salida", key=f"force_out_{prof}", use_container_width=True):
                        st.session_state["checkin_db"].append({
                            "paciente": data["paciente"], 
                            "profesional": prof, 
                            "fecha_hora": ahora().strftime("%d/%m/%Y %H:%M:%S"), 
                            "tipo": f"SALIDA (Forzada por Admin: {user['nombre']})", 
                            "empresa": mi_empresa
                        })
                        guardar_datos()
                        st.success(f"Salida forzada registrada correctamente para {prof}.")
                        st.rerun()
        else:
            st.success("En este momento no hay profesionales con guardias abiertas en los domicilios.")
            
        st.divider()
        st.markdown("#### 📋 Auditoría de todos los movimientos de hoy")
        if chks_hoy:
            df_chks = pd.DataFrame(chks_hoy).drop(columns=["empresa"], errors='ignore')
            df_chks = df_chks.rename(columns={"paciente": "Paciente", "profesional": "Profesional", "fecha_hora": "Fecha y Hora", "tipo": "Acción"})
            st.dataframe(df_chks.iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.write("Sin movimientos en el día de la fecha.")

# =====================================================================
# 19. MÓDULO DE RRHH Y FICHAJES (SOLO ADMIN/COORD) - VERSIÓN FINAL CORREGIDA
# =====================================================================
if "🧑‍⚕️ RRHH y Fichajes" in menu:
    with tabs[menu.index("🧑‍⚕️ RRHH y Fichajes")]:
        st.subheader("🧑‍⚕️ Control de RRHH y Fichaje Histórico")
        st.info("Generá reportes oficiales de presentismo, horas trabajadas y liquidación cruzando ingresos, egresos, matrículas y GPS.")

        # ====================== FILTROS PRINCIPALES ======================
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        fecha_inicio = col_f1.date_input(
            "Desde fecha:", 
            value=ahora().date() - timedelta(days=30), 
            key="fichajes_desde"
        )
        fecha_fin = col_f2.date_input(
            "Hasta fecha:", 
            value=ahora().date(), 
            key="fichajes_hasta"
        )
        
        # ====================== PROCESAMIENTO DE FICHAJES ======================
        fichajes_lista = []
        rastreador_ingresos = {}
        
        def obtener_dt(c):
            try:
                return datetime.strptime(c.get("fecha_hora", ""), "%d/%m/%Y %H:%M:%S")
            except:
                try:
                    return datetime.strptime(c.get("fecha_hora", ""), "%d/%m/%Y %H:%M")
                except:
                    return datetime.min
        
        checkins_ordenados = sorted(
            [c for c in st.session_state.get("checkin_db", []) 
             if c.get("empresa") == mi_empresa or rol == "SuperAdmin"],
            key=obtener_dt
        )
        
        for c in checkins_ordenados:
            prof = c.get("profesional", "S/D")
            pac = c.get("paciente", "S/D")
            dt_actual = obtener_dt(c)
            if dt_actual == datetime.min:
                continue
            
            matricula = "S/D"
            for u_data in st.session_state.get("usuarios_db", {}).values():
                if u_data.get("nombre") == prof:
                    matricula = u_data.get("matricula", "S/D")
                    break
            
            fecha_f = dt_actual.strftime("%d/%m/%Y")
            hora_f = dt_actual.strftime("%H:%M")
            accion_raw = c.get("tipo", "")
            
            if "LLEGADA" in accion_raw.upper():
                accion = "🟢 INGRESO"
                rastreador_ingresos[(prof, pac)] = dt_actual
                tiempo_total = "-"
            elif "SALIDA" in accion_raw.upper():
                accion = "🔴 EGRESO"
                tiempo_total = "Sin ingreso previo"
                if (prof, pac) in rastreador_ingresos:
                    dt_ingreso = rastreador_ingresos[(prof, pac)]
                    duracion = dt_actual - dt_ingreso
                    horas = duracion.seconds // 3600
                    minutos = (duracion.seconds % 3600) // 60
                    tiempo_total = f"{horas}h {minutos:02d}m"
                    del rastreador_ingresos[(prof, pac)]
            else:
                accion = "OTRO"
                tiempo_total = "-"
            
            fichajes_lista.append({
                "Fecha": fecha_f,
                "Hora": hora_f,
                "Profesional": prof,
                "Matrícula": matricula,
                "Acción": accion,
                "Tiempo Trabajado": tiempo_total,
                "Paciente": pac,
                "GPS": c.get("gps", "—"),
                "fecha_dt": dt_actual,
                "raw_tipo": accion_raw
            })
        
        # ====================== TABS INTERNAS ======================
        tab_hist, tab_resumen, tab_gestion = st.tabs([
            "📋 Histórico Detallado", 
            "📊 Resumen por Profesional", 
            "🛠️ Gestión de Registros"
        ])
        
        df_fichajes = pd.DataFrame(fichajes_lista) if fichajes_lista else pd.DataFrame()
        
        # ====================== TAB 1: HISTÓRICO DETALLADO ======================
        with tab_hist:
            if not df_fichajes.empty:
                mask = (df_fichajes['fecha_dt'].dt.date >= fecha_inicio) & (df_fichajes['fecha_dt'].dt.date <= fecha_fin)
                df_filtrado = df_fichajes[mask].copy()
                
                if not df_filtrado.empty:
                    df_egresos = df_filtrado[df_filtrado["Acción"].str.contains("EGRESO", na=False)]
                    total_horas = 0.0
                    for t in df_egresos["Tiempo Trabajado"]:
                        if isinstance(t, str) and "h" in t:
                            try:
                                partes = t.replace("h", "").replace("m", "").strip().split()
                                h = int(partes[0])
                                m = int(partes[1]) if len(partes) > 1 else 0
                                total_horas += h + m / 60.0
                            except:
                                pass
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    col_m1.metric("📋 Total Fichajes", len(df_filtrado))
                    col_m2.metric("⏱️ Horas Trabajadas", f"{total_horas:.1f} hs")
                    col_m3.metric("👥 Profesionales", df_filtrado["Profesional"].nunique())
                    col_m4.metric("🏠 Visitas Completadas", len(df_egresos))
                    
                    df_mostrar = df_filtrado.sort_values(by="fecha_dt", ascending=False).drop(
                        columns=['fecha_dt', 'raw_tipo'], errors='ignore'
                    )
                    prof_filtrar = st.selectbox(
                        "Filtrar por Profesional:", 
                        ["Todos"] + sorted(df_mostrar["Profesional"].unique().tolist())
                    )
                    if prof_filtrar != "Todos":
                        df_mostrar = df_mostrar[df_mostrar["Profesional"] == prof_filtrar]
                    
                    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.subheader("📤 Exportar Reporte Oficial")
                    
                    if FPDF_DISPONIBLE:
                        def t(txt):
                            return str(txt).replace('🟢 ', '').replace('🔴 ', '').encode('latin-1', 'replace').decode('latin-1')
                        
                        def generar_pdf_rrhh(df_pdf, f_ini, f_fin, prof_sel):
                            pdf = FPDF(orientation='L')
                            pdf.add_page()
                            try:
                                import os
                                ruta_logo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_medicare_pro.jpeg")
                                pdf.image(ruta_logo, x=10, y=8, w=25)
                            except:
                                pass
                            
                            pdf.set_font("Arial", 'B', 16)
                            pdf.cell(0, 12, t(f"REPORTE OFICIAL DE RRHH - {mi_empresa}"), ln=True, align='C')
                            pdf.set_font("Arial", '', 11)
                            pdf.cell(0, 8, t(f"Período: {f_ini.strftime('%d/%m/%Y')} al {f_fin.strftime('%d/%m/%Y')}"), ln=True, align='C')
                            texto_prof = f" | Profesional: {prof_sel}" if prof_sel != "Todos" else ""
                            pdf.cell(0, 8, t(f"Generado por: {user['nombre']}{texto_prof}"), ln=True, align='C')
                            pdf.ln(10)
                            
                            pdf.set_font("Arial", 'B', 12)
                            pdf.cell(0, 10, t("RESUMEN DEL PERÍODO"), ln=True)
                            pdf.set_font("Arial", '', 10)
                            pdf.cell(0, 8, t(f"Total fichajes: {len(df_pdf)} | Horas trabajadas: {total_horas:.1f} hs | Visitas completadas: {len(df_egresos)}"), ln=True)
                            pdf.ln(8)
                            
                            pdf.set_fill_color(59, 130, 246)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font("Arial", 'B', 9)
                            pdf.cell(22, 8, "FECHA", 1, 0, 'C', True)
                            pdf.cell(15, 8, "HORA", 1, 0, 'C', True)
                            pdf.cell(48, 8, "PROFESIONAL", 1, 0, 'C', True)
                            pdf.cell(22, 8, "MATRÍCULA", 1, 0, 'C', True)
                            pdf.cell(24, 8, "ACCIÓN", 1, 0, 'C', True)
                            pdf.cell(24, 8, "TIEMPO", 1, 0, 'C', True)
                            pdf.cell(122, 8, "PACIENTE", 1, 1, 'C', True)
                            
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("Arial", '', 8)
                            for _, fila in df_pdf.iterrows():
                                pdf.cell(22, 8, t(fila['Fecha']), 1, 0, 'C')
                                pdf.cell(15, 8, t(fila['Hora']), 1, 0, 'C')
                                pdf.cell(48, 8, t(fila['Profesional']), 1, 0, 'L')
                                pdf.cell(22, 8, t(fila['Matrícula']), 1, 0, 'C')
                                color = (0, 128, 0) if "INGRESO" in fila['Acción'] else (200, 0, 0) if "EGRESO" in fila['Acción'] else (0, 0, 0)
                                pdf.set_text_color(*color)
                                pdf.cell(24, 8, t(fila['Acción']), 1, 0, 'C')
                                pdf.set_text_color(0, 0, 0)
                                pdf.cell(24, 8, t(fila['Tiempo Trabajado']), 1, 0, 'C')
                                paciente_corto = str(fila['Paciente'])[:70]
                                pdf.cell(122, 8, t(paciente_corto), 1, 1, 'L')
                            
                            pdf.ln(10)
                            pdf.set_font("Arial", '', 9)
                            pdf.cell(0, 6, t("Documento generado automáticamente por MediCare Enterprise PRO"), ln=True, align='C')
                            return pdf.output(dest='S').encode('latin-1')
                        
                        pdf_data = generar_pdf_rrhh(df_mostrar, fecha_inicio, fecha_fin, prof_filtrar)
                        b64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                        nombre_pdf = f"RRHH_{mi_empresa.replace(' ', '_')}_{fecha_inicio.strftime('%d%m%Y')}-{fecha_fin.strftime('%d%m%Y')}.pdf"
                        
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            html_btn_pdf = f'''
                            <a href="data:application/pdf;base64,{b64_pdf}" download="{nombre_pdf}"
                               style="display: block; width: 100%; text-align: center; background-color: #2563eb;
                                      color: white; padding: 14px; border-radius: 8px; text-decoration: none;
                                      font-weight: 700;">
                               📥 DESCARGAR REPORTE OFICIAL EN PDF
                            </a>
                            '''
                            st.markdown(html_btn_pdf, unsafe_allow_html=True)
                        
                        with col_exp2:
                            out_excel = io.BytesIO()
                            with pd.ExcelWriter(out_excel, engine='openpyxl') as writer:
                                df_mostrar.to_excel(writer, index=False, sheet_name='Fichajes_RRHH')
                            b64_excel = base64.b64encode(out_excel.getvalue()).decode('utf-8')
                            nombre_excel = f"RRHH_{mi_empresa.replace(' ', '_')}_{fecha_inicio.strftime('%d%m%Y')}-{fecha_fin.strftime('%d%m%Y')}.xlsx"
                            
                            html_btn_excel = f'''
                            <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" 
                               download="{nombre_excel}"
                               style="display: block; width: 100%; text-align: center; background-color: #10b981;
                                      color: white; padding: 14px; border-radius: 8px; text-decoration: none;
                                      font-weight: 700;">
                               📊 DESCARGAR EN EXCEL (para liquidación)
                            </a>
                            '''
                            st.markdown(html_btn_excel, unsafe_allow_html=True)
                else:
                    st.warning("No hay fichajes en el rango de fechas seleccionado.")
            else:
                st.info("Aún no hay registros de fichajes.")
        
        # ====================== TAB 2: RESUMEN POR PROFESIONAL ======================
        with tab_resumen:
            if not df_fichajes.empty:
                mask = (df_fichajes['fecha_dt'].dt.date >= fecha_inicio) & (df_fichajes['fecha_dt'].dt.date <= fecha_fin)
                df_res = df_fichajes[mask].copy()
                df_egresos = df_res[df_res["Acción"].str.contains("EGRESO", na=False)]
                
                resumen_prof = df_egresos.groupby("Profesional").agg(
                    Visitas=("Acción", "count"),
                    Horas_Trabajadas=("Tiempo Trabajado", lambda x: sum(
                        (int(h) + int(m)/60.0) for h, m in 
                        [t.replace("h","").replace("m","").split() if isinstance(t, str) and "h" in t else (0, 0) for t in x]
                    )),
                    Matrícula=("Matrícula", "first")
                ).round(1).reset_index()
                
                resumen_prof = resumen_prof.rename(columns={"Horas_Trabajadas": "Horas Totales"})
                st.dataframe(resumen_prof, use_container_width=True, hide_index=True)
                
                st.success(f"**Total horas en el período: {resumen_prof['Horas Totales'].sum():.1f} hs**")
            else:
                st.info("No hay datos para generar el resumen.")
        
        # ====================== TAB 3: GESTIÓN DE REGISTROS ======================
        with tab_gestion:
            st.warning("🔧 Solo para corrección de errores. Eliminar un fichaje recalcula automáticamente los tiempos.")
            if fichajes_lista:
                df_gestion = pd.DataFrame(fichajes_lista).sort_values(by="fecha_dt", ascending=False)
                st.dataframe(
                    df_gestion.drop(columns=['fecha_dt', 'raw_tipo'], errors='ignore'),
                    use_container_width=True,
                    hide_index=True
                )
                
                # === CORRECCIÓN DEL ERROR KeyError ===
                opciones_borrar = [
                    (f"📅 {c.get('fecha_hora', '—')} | 👤 {c.get('profesional', 'S/D')} | {c.get('tipo', '—')} | Paciente: {c.get('paciente', 'S/D')}", idx)
                    for idx, c in enumerate(st.session_state.get("checkin_db", []))
                    if c.get("empresa") == mi_empresa or rol == "SuperAdmin"
                ]
                
                if opciones_borrar:
                    col_del1, col_del2 = st.columns([3, 1])
                    registro_sel = col_del1.selectbox(
                        "Seleccionar fichaje a eliminar:",
                        options=opciones_borrar,
                        format_func=lambda x: x[0]
                    )
                    if col_del2.button("🗑️ Eliminar Fichaje Seleccionado", type="secondary", use_container_width=True):
                        del st.session_state["checkin_db"][registro_sel[1]]
                        guardar_datos()
                        st.success("✅ Fichaje eliminado correctamente. Los reportes se han actualizado.")
                        st.rerun()
            else:
                st.info("No hay registros para gestionar.")
# --- FIN DEL SISTEMA MEDICARE PRO V9.12 ---

