# SGC-IA V5.1 - Sistema de Gestión de Clínica Odontológica Inteligente
# Archivo: sgc_ia_v5.1.py

# SECCIÓN 1: Dependencias y Configuración Base
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
import os, re, uuid
# Estas librerías son necesarias para el chatbot (CRM Inteligente)
try:
    from pandasai import SmartDataframe
    from pandasai.llm import OpenAI
    PANDASAI_ENABLED = True
except ImportError:
    PANDASAI_ENABLED = False

# --- Configuración de IA ---
# ES CRÍTICO DEFINIR ESTA CLAVE EN LOS SECRETS DE STREAMLIT CLOUD
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
llm = OpenAI(api_token=OPENAI_API_KEY) if OPENAI_API_KEY and PANDASAI_ENABLED else None

# --- Intento de importar la librería de calendario ---
try:
    from streamlit_calendar import calendar
    CALENDAR_ENABLED = True
except ImportError:
    CALENDAR_ENABLED = False

# --- Archivos de datos ---
BASE_CONSOLIDADA = "base_consolidada.csv"
PROSPECTOS_DB = "prospectos.csv"

# --- Columnas base del sistema de gestión (Ajustadas a la clínica) ---
columnas_base = [
    "nombre", "telefono", "direccion", "email", "curp", "fecha_nacimiento",
    "dr_asignado", "producto_inicial", "presupuesto_total", "prima_pagada",
    "moneda", "fecha_valoracion", "fecha_fin_tratamiento", "estatus", "notas"
]


# --- CONFIGURACIÓN DE LA PÁGINA (TÍTULO CORREGIDO) ---
st.set_page_config(
    page_title="SGC Odontológico", 
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SECCIÓN 2: Funciones de Utilidad (Helpers)
@st.cache_data
def convertir_a_csv(df):
    """Convierte un DataFrame de Pandas a CSV para descarga."""
    return df.to_csv(index=False).encode('utf-8')

def color_prediccion(val):
    """Aplica color a la celda de predicción de inventario."""
    color = 'white' 
    bgcolor = 'transparent' 
    if 'URGENTE' in str(val):
        bgcolor = '#FF4B4B' 
        color = 'white'
    elif 'Pedir' in str(val):
        bgcolor = '#FFB84B' 
        color = 'black'
    elif 'OK' in str(val):
        bgcolor = '#4BBF73' 
        color = 'white'
    return f'background-color: {bgcolor}; color: {color}'

# --- Lógica de Base de Datos ---
def cargar_csv(path, columnas):
    """Carga un CSV existente o crea un DataFrame vacío."""
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            for col in columnas:
                if col not in df.columns:
                    df[col] = np.nan
            return df
        except Exception:
            return pd.DataFrame(columns=columnas)
    else:
        return pd.DataFrame(columns=columnas)

def guardar_csv(df, path):
    """Guarda el DataFrame en un archivo CSV."""
    df.to_csv(path, index=False)

def generar_datos_ejemplo_odontologico():
    """Genera datos de simulación odontológicos para la demo."""
    data_clientes = {
        'nombre': ['Ana Pérez', 'Laura Gómez', 'Ricardo Salas'],
        'curp': ['APXX80', 'LGYY90', 'RSZZ75'],
        'presupuesto_total': [15000.0, 800.0, 50000.0],
        'prima_pagada': [15000.0, 800.0, 25000.0],
        'estatus': ['Terminado', 'Activo', 'Presupuesto Pendiente']
    }
    df_consolidada = pd.DataFrame(data_clientes)
    
    data_citas = {
        'nombre': ['Ana Pérez', 'Laura Gómez', 'Jaime Ríos'],
        'dr_asignado': ['Dr. Salas', 'Dra. Vega', 'Dr. Salas'],
        'fecha_cita': [datetime.date(2025, 12, 1), datetime.date(2025, 12, 5), datetime.date(2025, 12, 10)],
        'hora_cita': ['10:00', '14:00', '16:00'],
        'estatus': ['Confirmada', 'Pendiente', 'No-Show']
    }
    df_prospectos = pd.DataFrame(data_citas)

    st.session_state.df_consolidada = df_consolidada
    st.session_state.df_prospectos = df_prospectos
    
def inicializar_datos():
    """Inicializa los DataFrames de la aplicación en la sesión de Streamlit."""
    if 'df_consolidada' not in st.session_state:
        st.session_state.df_consolidada = cargar_csv(BASE_CONSOLIDADA, columnas_base)
    if 'df_prospectos' not in st.session_state:
        columnas_prospectos = ["nombre", "dr_asignado", "fecha_cita", "hora_cita", "estatus"]
        st.session_state.df_prospectos = cargar_csv(PROSPECTOS_DB, columnas_prospectos)
    
    # KPIs de simulación (para facturación/cobranza)
    if 'monto_sincronizado_aspel' not in st.session_state:
        st.session_state.monto_sincronizado_aspel = 15000.00
    if 'monto_pendiente_aspel' not in st.session_state:
        st.session_state.monto_pendiente_aspel = 8000.00

# --- FUNCIÓN DE GRÁFICO DE INGRESOS (IA) ---
def generar_grafico_pronostico(df_consolidada):
    """Genera un gráfico de ingresos reales vs. pronosticados."""
    data_hist = pd.DataFrame({
        'Mes': pd.to_datetime(['2024-07', '2024-08', '2024-09', '2024-10']),
        'Ingresos Reales': [25000, 32000, 45000, 50000]
    })
    
    data_pred = pd.DataFrame({
        'Mes': pd.to_datetime(['2024-11', '2024-12', '2025-01']),
        'Pronóstico de Ingresos': [55000, 60000, 62000]
    })

    df_chart = pd.concat([data_hist.rename(columns={'Ingresos Reales': 'Valor'}), 
                          data_pred.rename(columns={'Pronóstico de Ingresos': 'Valor'})])
    df_chart['Tipo'] = ['Real'] * len(data_hist) + ['Pronóstico IA'] * len(data_pred)

    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=data_hist['Mes'], 
        y=data_hist['Ingresos Reales'], 
        name='Ingresos Reales',
        marker_color='#007BFF'
    ))

    fig.add_trace(go.Scatter(
        x=data_pred['Mes'], 
        y=data_pred['Pronóstico de Ingresos'], 
        mode='lines+markers', 
        name='Pronóstico IA',
        line=dict(color='#28A745', width=3),
        marker=dict(size=10, color='#28A745')
    ))

    fig.update_layout(
        title='Ingresos Históricos vs. Pronóstico de Rentabilidad (AI)',
        xaxis_title='Mes',
        yaxis_title='Monto (MXN)',
        barmode='overlay',
        legend_title='Tipo de Dato',
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

# SECCIÓN 3: Módulos de Aplicación
def render_introduccion():
    st.title("🦷 SGC Odontológico: Plataforma de Validación de Valor")
    st.header("¡Bienvenida!")
    st.markdown("""
        Esta es la **Versión 5.1** del Sistema de Gestión Clínica Inteligente, optimizada
        para **superar a la competencia** con **Inteligencia Artificial** enfocada en rentabilidad y cumplimiento normativo.
        
        Use el menú de la izquierda para navegar por los **6 módulos principales**.
        """)
    
    st.divider()
    st.subheader("🛠️ Configuración Rápida de la Demo")
    st.info("Para que los demás módulos (Dashboard, CRM) muestren datos, necesita cargar información inicial.")
    
    if st.button("▶️ Cargar Ejemplos de Pacientes y Citas (Recomendado)"):
        generar_datos_ejemplo_odontologico()
        st.success("¡Datos de ejemplo cargados! Navegue a 'Panel de Desempeño' para ver los KPIs.")

def render_cargar_documentos_clinicos():
    st.title("1. 📥 Cargar Documentos Clínicos")
    st.markdown("---")
    
    # --- PASO 1: SELECCIÓN DEL PACIENTE (CRÍTICO PARA EL ENLACE) ---
    st.subheader("Paso 1: Seleccionar Expediente (Garantía NOM-004)")
    
    nombres_pacientes = st.session_state.df_consolidada['nombre'].tolist() if not st.session_state.df_consolidada.empty else ["Ana Pérez (ID: AP-1081)", "Laura Gómez (ID: LG-1234)"]
    pacientes_list = nombres_pacientes + ["Nuevo Paciente"]
    selected_paciente = st.selectbox(
        "**Paciente a quien adjuntar los documentos:**",
        pacientes_list,
        index=0 
    )
    
    if selected_paciente != "Nuevo Paciente":
        st.info(f"Expediente seleccionado: **{selected_paciente}** (ID Única cargada en la sesión).")
    
    # --- PASO 2: CARGA DEL DOCUMENTO ---
    st.subheader("Paso 2: Cargar Archivos Clínicos")
    st.caption("Asegúrese de que el nombre del documento (Radiografía, Lab) contenga el nombre o ID del paciente.")
    uploaded_files = st.file_uploader("Subir Radiografías, Informes de Laboratorio (PDF, JPG, PNG)", accept_multiple_files=True)
    
    # --- PASO 3 & 4: LÓGICA DE VALIDACIÓN (MOCK-UP DE LA IA SUPERIOR) ---
    if uploaded_files:
        st.success(f"Se cargaron {len(uploaded_files)} archivos. Iniciando Motor de Triple Validación (IA)...")
        st.markdown("---")
        st.subheader("Paso 3 & 4: Triple Validación de Enlace por IA")
        
        # Simulación de error de IA (Triple Validación)
        if selected_paciente.startswith("Ana Pérez") and 'error' in uploaded_files[0].name.lower():
             st.error(f"🚨 **ALERTA DE SEGURIDAD - DISCREPANCIA ENCONTRADA**")
             st.markdown(f"""
                | Validación | Dato de Ficha | Dato Extraído (OCR/IA) | Resultado |
                | :--- | :--- | :--- | :--- |
                | **Paciente (Nombre)** | Ana Pérez | Daniel Flores (encontrado en el informe) | **¡ERROR!** |
                ---
                **Acción Requerida:** El documento parece pertenecer a **Daniel Flores**. Por favor, justifique el enlace.
            """)
             st.text_area("Justificación Manual:", "Radiografía es de un familiar de Ana Pérez. Válido manualmente.", key="justificacion")
             st.button("Forzar Enlace y Justificar (Registrar Auditoría)")
        else:
             st.success("✅ **VALIDACIÓN AUTOMÁTICA EXITOSA**")
             st.caption("Cumplimiento NOM-004 garantizado: el documento fue validado por la IA antes de su indexación final.")

def render_dashboard_odontologico(): 
    st.title("2. 📊 Panel de Desempeño (IA)")
    st.markdown("---")
    st.subheader("Métricas de Rendimiento y Pronóstico (KPIs Odontológicos)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tasa de Ocupación Hoy (IA)", "85%", "+10% vs. Semana Pasada", delta_color="normal")
    col2.metric("Pronóstico de Ingresos (IA)", f"${st.session_state.monto_sincronizado_aspel + 10000:,.2f} MXN", "± 5% de precisión", delta_color="inverse")
    col3.metric("Tasa de Fuga (No-Show)", "7%", "-3% gracias a CRM Inteligente", delta_color="inverse")

    st.warning("📈 **Pronóstico de Ingresos Cognitivo:** Gráfico de Pronóstico de Ingresos del Próximo Mes, basado en presupuestos generados y la tasa de aceptación histórica de la IA.")
    generar_grafico_pronostico(st.session_state.df_consolidada)

def render_ficha_clinica_odontograma():
    st.title("3. 🦷 Ficha Clínica y Odontograma")
    st.markdown("---")
    st.subheader("Datos del Paciente y Evolución Clínica")
    
    paciente_ejemplo = st.selectbox("Buscar Paciente", st.session_state.df_consolidada['nombre'].tolist() if not st.session_state.df_consolidada.empty else ["Ana Pérez (1081)", "Laura Gómez (800)"])
    
    tab_ficha, tab_odontograma, tab_recetas = st.tabs(["Ficha General y Anamnesis", "Evolución y Odontograma", "Recetas y Documentos Firmados"])
    
    with tab_ficha:
        st.write("#### Historial y Anamnesis")
        st.text_area("Anamnesis (Personalizable)", "Paciente acude por dolor en molar 36. No presenta alergias conocidas.", height=100)
        
    with tab_odontograma:
        st.subheader("Evolución y Odontograma Visual")
        st.info("💡 **Generación Automática de Notas Clínicas (IA):** Escriba su nota libremente y la IA estructurará el registro clínico (SOAP/Diagnóstico CIE-10).")
        
        nota_libre = st.text_area("Nota del Doctor (Dictado o Texto Libre)", "Hoy realizamos una resina en el cuadrante inferior izquierdo, pieza 36. Caries de segundo grado. No hubo complicaciones. Se usó anestesia, 1 cartucho. Paciente estable. Se agenda control en 6 meses.", height=150)
        
        if st.button("Generar Nota Clínica Estructurada y Diagnóstico (IA)"):
            st.success("**Nota Estructurada (IA) generada con éxito:**")
            st.code(f"""
                **Fecha:** {datetime.date.today()}
                **Sujetivo (S):** Dolor en molar 36.
                **Objetivo (O):** Caries grado II en pieza 36.
                **Evaluación (A) - Diagnóstico CIE-10 Sugerido:** K02.1 (Caries de la dentina)
            """)
        
        st.image("https://via.placeholder.com/600x300.png?text=Odontograma+Visual+Interactivo", caption="Odontograma Visual - Click para Diagnóstico/Planificación", use_container_width=True)

    with tab_recetas:
        st.subheader("Recetas, Consentimientos y Documentos")
        st.text_input("Buscar Plantilla de Receta (e.g., Antibiótico, Analgésico)")
        
        if st.button("💊 Generar Receta y Enviar por Email/WhatsApp"):
            st.success("✅ Receta generada y enviada a la impresora/WhatsApp.")
            st.code(f"""
                Clínica Odontológica Integral
                Paciente: {paciente_ejemplo}
                -----------------------------------
                Medicamento: **Amoxicilina 500mg**
                Instrucciones: Tomar una tableta cada 8 horas por 7 días.
            """)
        st.checkbox("Solicitar Firma Electrónica del Consentimiento")

def render_agenda_inteligente():
    st.title("4. 📅 Agenda Inteligente")
    st.markdown("---")
    st.subheader("Optimización de Citas y Comunicación Proactiva")
    
    if not CALENDAR_ENABLED:
        st.error("⚠️ La librería `streamlit_calendar` no está instalada o no pudo cargarse.")
    else:
        st.info("⚠️ **Optimización (IA):** Bloques en color **AMARILLO** son horarios de baja ocupación con alta rentabilidad.")
        eventos = [
            {"title": "Laura Gómez (Resina - Slot rentable)", "start": "2025-11-20T10:00:00", "end": "2025-11-20T11:00:00", "color": "#FFB84B"},
            {"title": "Ana Pérez (Limpieza - Confirmada)", "start": "2025-11-20T11:00:00", "end": "2025-11-20T12:00:00", "color": "#4BBF73"},
            {"title": "Jaime Ríos (Valoración - No-Show/Alerta)", "start": "2025-11-20T14:00:00", "end": "2025-11-20T15:00:00", "color": "#FF4B4B"},
        ]
        
        calendar_options = {
            "initialView": "timeGridDay",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "timeGridWeek,timeGridDay"
            },
            "slotMinTime": "08:00:00",
            "slotMaxTime": "19:00:00",
            "height": 600
        }

        calendar(events=eventos, options=calendar_options)

def render_admin_finanzas(): 
    st.title("5. 💰 Administración y Finanzas (IA)")
    st.markdown("---")
    
    tab_inventario, tab_cobranza, tab_liquidaciones = st.tabs(["Inventario y Compras (IA)", "Cobranza y Facturación", "Liquidación de Odontólogos"])
    
    with tab_inventario:
        st.subheader("Inventario con Predicción de Demanda (AI)")
        st.info("📦 **Ventaja Superior:** La IA predice cuándo el stock de insumos críticos caerá a niveles de **ALERTA URGENTE**.")
        inventario_data = {
            'Insumo': ['Anestesia Lidocaína 1:100K', 'Resina Compuesta Z350 (Color A2)', 'Guantes de Nitrilo (Caja)'],
            'Stock Actual': [50, 12, 5],
            'AI Predicción de Compra': ['OK (Stock suficiente por 30 días)', 'Pedir en 7 días (Consumo alto)', 'URGENTE: Pedir en 2 días (Stock bajo)']
        }
        df_inventario = pd.DataFrame(inventario_data)
        st.dataframe(df_inventario.style.applymap(color_prediccion, subset=['AI Predicción de Compra']), hide_index=True)

    with tab_cobranza:
        st.subheader("Registro de Pagos y Facturación Electrónica (ASPEL)")
        
        pacientes_cobro = st.session_state.df_consolidada['nombre'].tolist() if not st.session_state.df_consolidada.empty else ["Ana Pérez", "Laura Gómez"]
        paciente_cobrado = st.selectbox("Seleccionar Paciente (Pago Recibido)", pacientes_cobro)
        monto_pago = st.number_input("Monto del Abono/Pago", min_value=10.0, value=800.0, format="%.2f")
        
        if st.button("💸 Registrar Pago y Enviar a ASPEL"):
            st.session_state.monto_sincronizado_aspel += monto_pago
            st.session_state.monto_pendiente_aspel -= monto_pago if st.session_state.monto_pendiente_aspel > monto_pago else 0
            
            st.success(f"Pago de ${monto_pago:,.2f} registrado. Sincronización con ASPEL para factura exitosa.")
        
        st.markdown("---")
        col_sinc, col_pend = st.columns(2)
        col_sinc.metric("Monto Sincronizado (Total)", f"${st.session_state.monto_sincronizado_aspel:,.2f} MXN")
        col_pend.metric("Monto Pendiente de Cobro", f"${st.session_state.monto_pendiente_aspel:,.2f} MXN", delta_color="inverse")

    with tab_liquidaciones:
        st.subheader("Liquidaciones Automáticas de Odontólogos (AI)")
        st.success("✅ **Liquidación Automática:** Los pagos a especialistas se calculan automáticamente.")
        st.selectbox("Seleccionar Odontólogo", ["Dr. Roberto Ibarra (Contrato 50/50)"])
        st.metric("Total a Pagar (Mes de Noviembre)", "$12,500 MXN")
        st.button("Generar Reporte de Liquidación Final")

def render_crm_inteligente(): 
    st.title("6. 🗣️ CRM Inteligente (Re-Engagement)")
    st.markdown("---")
    st.warning("🎯 **Ventaja Superior (CRM Proactivo):** La IA genera listas de pacientes en riesgo de fuga y sugiere la estrategia de contacto más efectiva.")
    
    st.markdown("##### 📝 Tareas de Re-Engagement Activas (Generadas por IA)")
    tareas = pd.DataFrame({
        'Tipo de Tarea': ['Captura (Presupuesto Pendiente)', 'Cobranza (Abono Vencido)', 'Control (Fase Higiénica)'],
        'Paciente': ['Laura Gómez', 'Ricardo Salas', 'María Flores'],
        'Días de Retraso/Inactividad': [45, 12, 180],
        'Prioridad IA': ['ALTA', 'URGENTE', 'MEDIA'],
        'Siguiente Acción (IA Sugerida)': ['Mensaje cordial por WhatsApp con un 10% de descuento.', 'Llamada telefónica para recordatorio de pago.', 'Email con promoción de limpieza y educación del valor del control.']
    })
    st.dataframe(tareas, use_container_width=True)

    st.markdown("---")
    st.subheader("🤖 Chatbot IA sobre Datos de la Clínica")
    
    if llm:
        st.warning("El Chatbot está activo. Use la base de datos de pacientes cargada para hacer preguntas.")
        # La lógica de PandasAI iría aquí
    else:
        st.warning("No se detectó la clave de OpenAI (OPENAI_API_KEY). El Chatbot está deshabilitado. **Ver instrucciones de despliegue.**")

def render_seguridad_escalabilidad(): 
    st.title("7. 🔒 Seguridad y Escalabilidad")
    st.markdown("---")
    st.subheader("Arquitectura SGC-IA para Crecimiento Masivo")
    st.markdown("""
        - **Seguridad (ISO 27001 Ready):** Autenticación de dos factores, cifrado de extremo a extremo.
        - **Escalabilidad:** Arquitectura desacoplada (Streamlit / Cloud DB).
    """)

# SECCIÓN 4: Lógica Principal (Estructura Streamlit)

# --- Mapeo de Páginas (Módulos de la V5.1) ---
PAGES = {
    "⭐ Introducción y Bienvenida": render_introduccion, 
    "📥 Cargar Docs. Clínicos": render_cargar_documentos_clinicos,
    "📊 Panel de Desempeño (IA)": render_dashboard_odontologico,
    "🦷 Ficha Clínica y Odontograma": render_ficha_clinica_odontograma,
    "📅 Agenda Inteligente": render_agenda_inteligente,
    "💰 Admin. y Finanzas (IA)": render_admin_finanzas,
    "🗣️ CRM Inteligente (Re-Engagement)": render_crm_inteligente,
    "🔒 Seguridad y Escalabilidad": render_seguridad_escalabilidad
}

# --- Lógica de la Barra Lateral ---
logo_url = "https://via.placeholder.com/300x100.png?text=SGC+IA" 
st.sidebar.image(logo_url, use_container_width=True) 

st.sidebar.title("🦷 SGC Odontológico") 
st.sidebar.markdown("Demo de Módulos con IA")

# --- Menú de Navegación ---
pagina_seleccionada = st.sidebar.radio("Seleccione un Módulo:", list(PAGES.keys()))

st.sidebar.divider()
st.sidebar.caption("Versión **5.1** (Superioridad Competitiva con IA)") 

# --- Inicializar Datos y Ejecutar la Página Seleccionada ---
inicializar_datos()
PAGES[pagina_seleccionada]()
