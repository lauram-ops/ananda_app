import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ananda Kino | Calculadora Maestra",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS (Diseño Premium) ---
st.markdown("""
    <style>
    /* Fondo Degradado */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #E0F2F7 0%, #F0F8FF 100%);
    }
    /* Textos Azules */
    h1, h2, h3, h4, p, div, span, label, .stMarkdown {
        color: #004e92 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* Tarjetas */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #e1e5e8;
    }
    .big-number { font-size: 32px; font-weight: 800; color: #004e92; }
    .success-number { font-size: 32px; font-weight: 800; color: #28a745; }
    .danger-number { font-size: 32px; font-weight: 800; color: #d62728; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. BASE DE DATOS (Simulación de 44 Lotes) ---
# En el futuro, esto se puede reemplazar con: df = pd.read_csv("inventario.csv")
@st.cache_data
def generar_inventario():
    # Creamos 44 lotes simulados
    lotes = []
    for i in range(1, 45):
        # Simulamos variación de m2 entre 200 y 350
        m2 = np.random.randint(200, 350)
        # Precio base por m2 (ej. $4,500 MXN)
        precio_lista = m2 * 4500 
        lotes.append({
            "Lote": f"Lote {i}",
            "M2": m2,
            "Precio_Lista": precio_lista,
            "Estado": "Disponible"
        })
    return pd.DataFrame(lotes)

df_inventario = generar_inventario()

# Base de datos Competencia
COMPETIDORES = {
    "Punta Península (Condo)": 4550000,
    "CAAY (Depto)": 3500000,
    "Marenza (Torre)": 3200000,
    "Vistas (Solo Lote)": 1100000
}

# --- 2. SIDEBAR: COTIZADOR PROFESIONAL ---
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.header("🌊 Ananda Kino")

st.sidebar.header("1. Selecciona Propiedad")

# Selector de Lote (1 al 44)
lote_selec = st.sidebar.selectbox("Número de Lote:", df_inventario['Lote'])
datos_lote = df_inventario[df_inventario['Lote'] == lote_selec].iloc[0]

# Mostrar info del lote seleccionado
col_info1, col_info2 = st.sidebar.columns(2)
col_info1.metric("Superficie", f"{datos_lote['M2']} m²")
col_info2.metric("Precio Lista", f"${datos_lote['Precio_Lista']/1000:,.0f}k")

st.sidebar.header("2. Estrategia de Precio")

# Listas de Precios (Factor de ajuste)
lista_precio = st.sidebar.selectbox(
    "Lista de Precios a Aplicar:",
    ["Lista Pública (100%)", "Preventa (-5%)", "Friends & Family (-10%)", "Lista Cero (-15%)"]
)

# Lógica de listas
factor_lista = 1.0
if "Preventa" in lista_precio: factor_lista = 0.95
if "Family" in lista_precio: factor_lista = 0.90
if "Cero" in lista_precio: factor_lista = 0.85

# Descuento Adicional Manual
descuento_manual = st.sidebar.number_input("Descuento Adicional Negociación (%)", 0, 20, 0)
factor_final = factor_lista * (1 - (descuento_manual/100))

# Cálculo Precio Final Terreno
precio_final_lote = datos_lote['Precio_Lista'] * factor_final
ahorro_lista = datos_lote['Precio_Lista'] - precio_final_lote

if ahorro_lista > 0:
    st.sidebar.success(f"¡Descuento aplicado: -${ahorro_lista:,.0f}!")

st.sidebar.markdown("---")
st.sidebar.header("3. Construcción y Comparativa")

costo_construccion = st.sidebar.number_input("Costo Construcción (Casa)", value=2500000, step=50000)
rival = st.sidebar.selectbox("Comparar contra:", list(COMPETIDORES.keys()))
precio_rival = COMPETIDORES[rival]

# Costo Total Ananda
inversion_total = precio_final_lote + costo_construccion
plusvalia_instantanea = precio_rival - inversion_total

# --- 3. PANEL PRINCIPAL ---

# Título
st.title(f"Cotización: {lote_selec} ({datos_lote['M2']} m²)")
st.markdown(f"**Estrategia:** {lista_precio} | **Cliente:** Propuesta Personalizada")

# Tarjetas Superiores
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="metric-card">
    <div>Inversión Total Ananda</div>
    <div class="big-number">${inversion_total:,.0f}</div>
    <div style="font-size:12px">Terreno + Construcción</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card">
    <div>Precio Competencia ({rival})</div>
    <div class="danger-number">${precio_rival:,.0f}</div>
    <div style="font-size:12px">Departamento / Similar</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="metric-card" style="border: 2px solid #28a745; background: #f0fff4;">
    <div>💡 AHORRO REAL (Equity)</div>
    <div class="success-number">+${plusvalia_instantanea:,.0f}</div>
    <div style="font-size:12px; font-weight:bold; color:#28a745">Ganas al comprar</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# --- SECCIÓN DE RENTAS (MEJORADA) ---
st.header("🏖️ Potencial de Negocio (Rentas Vacacionales)")

col_rentas_input, col_rentas_graph = st.columns([1, 2])

with col_rentas_input:
    st.markdown("### Configura el Escenario")
    st.info("Ajusta estos valores para mostrarle al cliente cuánto puede ganar.")
    
    tarifa_noche = st.number_input("Tarifa por Noche (MXN)", value=4500, step=500)
    
    # Input directo de noches
    noches_rentadas = st.slider("Noches Rentadas al Año:", 0, 365, 120, help="Promedio conservador: 100-120 noches")
    ocupacion_pct = (noches_rentadas / 365) * 100
    st.caption(f"Ocupación Anual: {ocupacion_pct:.1f}%")
    
    admin_fee_pct = st.slider("Comisión Administración (%)", 15, 30, 20) / 100

with col_rentas_graph:
    # Cálculos
    ingreso_bruto_anual = tarifa_noche * noches_rentadas
    pago_admin = ingreso_bruto_anual * admin_fee_pct
    ingreso_neto_anual = ingreso_bruto_anual - pago_admin
    roi_rentas = (ingreso_neto_anual / inversion_total) * 100
    
    # Gráfico de pastel para ver a dónde va el dinero
    labels = ['Ingreso Neto (Para Ti)', 'Gasto Admin / Mant.']
    values = [ingreso_neto_anual, pago_admin]
    
    fig_pie = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, 
                                     marker_colors=['#28a745', '#d62728'])])
    fig_pie.update_layout(
        title_text=f"Flujo Anual Estimado: ${ingreso_bruto_anual:,.0f}",
        annotations=[dict(text=f'ROI<br>{roi_rentas:.1f}%', x=0.5, y=0.5, font_size=20, showarrow=False)],
        height=300,
        margin=dict(t=30, b=0, l=0, r=0)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# Resumen de Texto Rentas
st.success(f"""
    **Resumen de Rentabilidad:**
    Con solo **{noches_rentadas} noches** rentadas al año, tu propiedad generaría **${ingreso_neto_anual:,.0f} MXN** libres.
    Esto paga el mantenimiento y genera utilidad sobre tu inversión.
""")

st.markdown("---")
st.caption("Herramienta exclusiva para uso interno de Ananda Kino. Los precios de construcción y renta son estimaciones de mercado.")
