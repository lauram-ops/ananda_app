import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ananda Kino | Calculadora de Inversión Inteligente",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS PERSONALIZADOS (CSS) ---
st.markdown("""
    <style>
    .big-font { font-size: 24px !important; font-weight: bold; color: #2E8B57; }
    .metric-label { font-size: 14px; color: #555; }
    .metric-value { font-size: 32px; font-weight: 800; color: #1f77b4; }
    .highlight-savings { background-color: #d4edda; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. GESTIÓN DE DATOS (MODELO) ---

COMPETITORS_DB = {
    "Punta Península (Condo Resort)": 4550000, 
    "CAAY (Deptos Medio-Alto)": 3500000,
    "Marenza (Torres)": 3200000,
    "Promedio de Mercado": 3750000
}

@st.cache_data
def load_inventory():
    try:
        data = {
            'Lote': [f'Lote {i}' for i in range(1, 11)],
            'M2': [200, 220, 200, 250, 210, 200, 230, 240, 200, 260],
            'Precio_Lista': [900000, 990000, 900000, 1125000, 945000, 900000, 1035000, 1080000, 880000, 1200000]
        }
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error cargando base de datos: {e}")
        return pd.DataFrame({'Lote': ['Generico'], 'Precio_Lista': [900000]})

df_inventory = load_inventory()

# --- 2. SIDEBAR: CONFIGURACIÓN INTELIGENTE ---
st.sidebar.header("🛠️ Configurador de Inversión")

st.sidebar.subheader("1. Escenario Competitivo")
selected_competitor = st.sidebar.selectbox(
    "¿Contra quién comparamos?",
    options=list(COMPETITORS_DB.keys())
)
competitor_price = COMPETITORS_DB[selected_competitor]

st.sidebar.subheader("2. Configura tu Casa en Ananda")
selected_lot_label = st.sidebar.selectbox("Selecciona Lote Disponible:", df_inventory['Lote'])
lot_price = df_inventory[df_inventory['Lote'] == selected_lot_label]['Precio_Lista'].values[0]
st.sidebar.caption(f"Precio del Terreno: ${lot_price:,.0f} MXN")

construction_cost = st.sidebar.number_input(
    "Costo de Construcción (Llave en mano)",
    min_value=1500000,
    max_value=5000000,
    value=2300000,
    step=50000,
    help="Costo estimado por una casa completa de 3 recámaras con acabados residenciales."
)

total_ananda_cost = lot_price + construction_cost
instant_equity = competitor_price - total_ananda_cost
equity_percent = (instant_equity / total_ananda_cost) * 100

# --- 3. PANEL PRINCIPAL: EL "REALITY CHECK" ---
st.title("🌊 Ananda Kino: Tierra vs. Aire")
st.markdown("### ¿Por qué comprar un departamento cuando puedes tener una casa con terreno?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"**Precio {selected_competitor}**")
    st.markdown(f"<h2 style='color: #d62728'>${competitor_price:,.0f}</h2>", unsafe_allow_html=True)

with col2:
    st.markdown("**Costo Total Ananda (Lote + Casa)**")
    st.markdown(f"<h2 style='color: #2ca02c'>${total_ananda_cost:,.0f}</h2>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='highlight-savings'>", unsafe_allow_html=True) # Corrección de string
    st.markdown("**PLUSVALÍA INSTANTÁNEA**")
    st.markdown(f"<h2 style='color: #28a745'>+ ${instant_equity:,.0f}</h2>", unsafe_allow_html=True)
    st.caption(f"Tu dinero rinde un **{equity_percent:.1f}%** más")
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# --- GRÁFICO DE CIERRE (PLOTLY) ---
st.subheader("📊 La Gráfica de la Verdad")

fig = go.Figure()

fig.add_trace(go.Bar(
    x=[selected_competitor],
    y=[competitor_price],
    name='Competencia',
    marker_color='#ef553b',
    text=[f"${competitor_price/1000000:.1f}M"],
    textposition='auto'
))

fig.add_trace(go.Bar(
    x=['Tu Casa en Ananda'],
    y=[lot_price],
    name='Costo Terreno',
    marker_color='#1f77b4',
    text=[f"${lot_price/1000000:.1f}M"],
    textposition='auto'
))

fig.add_trace(go.Bar(
    x=['Tu Casa en Ananda'],
    y=[construction_cost],
    name='Costo Construcción',
    marker_color='#00cc96',
    text=[f"${construction_cost/1000000:.1f}M"],
    textposition='auto'
))

fig.update_layout(
    barmode='stack',
    title=f"Comparativa de Inversión: {selected_competitor} vs Ananda",
    yaxis_title="Inversión Total (MXN)",
    height=500,
    showlegend=True,
    annotations=[
        dict(
            x=1,
            y=total_ananda_cost,
            xref="x",
            yref="y",
            text=f"Ahorro Real: ${instant_equity:,.0f}",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            font=dict(size=14, color="#ffffff"),
            bgcolor="#28a745",
            opacity=0.9
        )
    ]
)

st.plotly_chart(fig, use_container_width=True)

# --- 4. SECCIÓN DE RENTAS (VALIDACIÓN DE FLUJO) ---
st.markdown("---")
st.header("💰 Validación de Flujo de Efectivo (Airbnb)")

r_col1, r_col2 = st.columns([1, 2])

with r_col1:
    st.markdown("#### Parámetros de Renta")
    nightly_rate = st.slider("Tarifa Promedio por Noche (MXN)", 2500, 8000, 4500, step=100)
    base_occupancy = st.slider("Ocupación Promedio Anual (%)", 20, 80, 45) / 100
    use_seasonality = st.checkbox("Aplicar Estacionalidad Real de Kino", value=True)

with r_col2:
    months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    if use_seasonality:
        seasonality_factors = [0.6, 0.7, 1.2, 1.1, 1.0, 1.4, 1.6, 1.5, 1.0, 0.9, 0.8, 0.7]
    else:
        seasonality_factors = [1.0] * 12

    monthly_revenue = []
    for factor in seasonality_factors:
        revenue = nightly_rate * 30 * (base_occupancy * factor)
        monthly_revenue.append(revenue)

    gross_annual = sum(monthly_revenue)
    admin_fee = gross_annual * 0.20
    net_annual = gross_annual - admin_fee
    roi = (net_annual / total_ananda_cost) * 100

    fig_rentals = go.Figure()
    fig_rentals.add_trace(go.Scatter(
        x=months, 
        y=monthly_revenue, 
        mode='lines+markers', 
        name='Ingreso Mensual',
        line=dict(color='#FFA15A', width=4),
        fill='tozeroy'
    ))
    
    fig_rentals.update_layout(
        title="Proyección de Flujo de Efectivo Mensual",
        yaxis_title="Ingresos (MXN)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )
    st.plotly_chart(fig_rentals, use_container_width=True)

st.info(f"""
    **Resumen Anual Conservador:**
    - Ingreso Bruto Estimado: **${gross_annual:,.0f}**
    - Menos Admin Fee (20%): **-${admin_fee:,.0f}**
    - **Ingreso Neto Anual: ${net_annual:,.0f}**
    - **ROI Estimado (Cap Rate): {roi:.2f}%** (Sobre valor total de inversión)
""")

# Footer
st.markdown("<br><br><div style='text-align: center; color: grey;'>Desarrollado para Estrategia Comercial Ananda Kino</div>", unsafe_allow_html=True)