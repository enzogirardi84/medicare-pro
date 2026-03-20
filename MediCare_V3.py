import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="MediCare Enterprise PRO V3", page_icon="⚕️", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    try:
        response = supabase.table('medicare_db').select('datos').eq('id', 1).execute()
        if response.data:
            return response.data[0]['datos']
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
    return {}

def guardar_datos(datos_nuevos):
    try:
        supabase.table('medicare_db').upsert({"id": 1, "datos": datos_nuevos}).execute()
    except Exception as e:
        st.error(f"Error guardando datos: {e}")

# --- INICIALIZACIÓN DE SESIÓN ---
if "db" not in st.session_state:
    datos = cargar_datos()
    if not datos: # Si está vacío, creamos la estructura base
        datos = {
            "usuarios_db": {"admin": {"pass": "37108100", "rol": "SuperAdmin", "nombre": "Enzo Girardi", "empresa": "SISTEMAS E.G."}},
            "pacientes_db": [],
            "detalles_pacientes_db": {},
            "evoluciones_db": []
        }
    st.session_state["db"] = datos

# --- LOGIN SIMPLE PARA PRUEBA ---
if "logeado" not in st.session_state: st.session_state["logeado"] = False

if not st.session_state["logeado"]:
    st.title("MediCare V3 - Acceso Profesional")
    u = st.text_input("Usuario")
    p = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        usuarios = st.session_state["db"]["usuarios_db"]
        if u in usuarios and usuarios[u]["pass"] == p:
            st.session_state["logeado"] = True
            st.session_state["user"] = usuarios[u]
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- PANEL PRINCIPAL (DEMO) ---
user = st.session_state["user"]
st.sidebar.success(f"Conectado: {user['nombre']}")
st.sidebar.info(f"Empresa: {user['empresa']}")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["logeado"] = False
    st.rerun()

st.title(f"Gestión de Pacientes - {user['empresa']}")

# Formulario rápido de prueba
with st.expander("➕ Registrar Nuevo Paciente"):
    nombre = st.text_input("Nombre Completo")
    dni = st.text_input("DNI")
    if st.button("Guardar Paciente"):
        if nombre and dni:
            st.session_state["db"]["pacientes_db"].append(nombre)
            st.session_state["db"]["detalles_pacientes_db"][nombre] = {"dni": dni}
            guardar_datos(st.session_state["db"])
            st.success("✅ Paciente guardado en Supabase!")
            st.rerun()

st.subheader("Lista de Pacientes en la Nube")
st.write(st.session_state["db"]["pacientes_db"])
