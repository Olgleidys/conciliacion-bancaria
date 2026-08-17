import io
import pandas as pd
import streamlit as st

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Sistema de Auditoría y Conciliación Bancaria",
    page_icon="⚖️",
    layout="wide"
)

# --- DISEÑO Y ESTILOS CORPORATIVOS (CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 6px 6px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
        color: #333333;
        border: 1px solid #dee2e6;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1b4332 !important;
        color: #ffffff !important;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #2d6a4f;
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNCIONES DE LIMPIEZA Y SOPORTE ---
def limpiar_monto(serie):
    return pd.to_numeric(
        serie.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(), 
        errors="coerce"
    ).fillna(0.0).round(2)

def limpiar_ref(ref):
    return str(ref).replace(".0", "").strip().lstrip("0")

# --- ENCABEZADO INSTITUCIONAL ---
st.title("⚖️ Sistema Profesional de Auditoría y Conciliación Bancaria")
st.markdown("**Control Interno y Cero Diferencias** | Módulo de validación cruzada automatizada.")

# --- INSTRUCCIONES DE USO (EXPANDIBLE) ---
with st.expander("📖 Manual de Instrucciones y Reglas de Auditoría (Hacer clic para desplegar)", expanded=False):
    st.markdown("""
    ### 📋 Instrucciones de Operación:
    1. **Carga de Archivos:** Suba el Estado de Cuenta Bancario en formato Excel y el Reporte auxiliar de Profit Plus.
    2. **Secuencia de Cruce (Embudo Contable):** El sistema procesa las transacciones en orden estricto para evitar duplicidades:
       * **Regla 1 (Cruce Exacto):** Referencia limpia y monto idéntico.
       * **Regla 2 (Cruce por 3 Dígitos):** Coincidencia en los últimos 3 dígitos de la referencia y monto exacto.
       * **Regla 3 (Sumatorias):** Agrupación de partidas en Profit que forman un solo depósito o movimiento en el banco.
    3. **Auditoría Preventiva:** Detección automática de duplicados exactos y por 3 dígitos en origen (**R4 y R5**) y análisis de posibles errores de transposición de dígitos (**Regla 6**).
    4. **Meta Final:** Lograr **Cero Diferencias**, aislando los pendientes reales en pestañas independientes para su revisión analítica.
    """)

st.divider()

# --- CARGA DE ARCHIVOS ---
col_up1, col_up2 = st.columns(2)
file_b = col_up1.file_uploader("📂 Estado de Cuenta Banco (Excel)", type=["xlsx"])
file_p = col_up2.file_uploader("📂 Reporte Profit Plus (Excel)", type=["xlsx"])

if file_b and file_p:
    # Cargar Dataframes
    df_b = pd.read_excel(file_b)
    df_p = pd.read_excel(file_p)
    
    # Estandarizar nombres de columnas a minúsculas
    df_b.columns = [c.lower().strip() for c in df_b.columns]
    df_p.columns = [c.lower().strip() for c in df_p.columns]
    
    # Procesar Banco (Monto absoluto combinando débito/crédito)
    df_b["monto"] = 0.0
    if "debito" in df_b.columns:
        df_b["monto"] += limpiar_monto(df_b["debito"])
    if "credito" in df_b.columns:
        df_b["monto"] += limpiar_monto(df_b["credito"])
        
    df_b["ref_clean"] = df_b["referencia"].apply(limpiar_ref)
    df_b["ref_3"] = df_b["ref_clean"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    # Procesar Profit
    df_p["monto"] = 0.0
    if "debe" in df_p.columns:
        df_p["monto"] += limpiar_monto(df_p["debe"])
    if "haber" in df_p.columns:
        df_p["monto"] += limpiar_monto(df_p["haber"])
        
    df_p["ref_clean"] = df_p["referencia"].apply(limpiar_ref)
    df_p["ref_3"] = df_p["ref_clean"].apply(lambda x: x[-3:] if len(x) >= 3 else x)
    
    # Marcar índices originales para control de exclusión estricta
    df_b["_id_b"] = df_b.index
    df_p["_id_p"] = df_p.index
    
    # --- MOTOR DE CONCILIACIÓN SECUENCIAL ---
    conciliados = pd.DataFrame()
    pend_b = df_b.copy()
    pend_p = df_p.copy()
    
    # R1: Cruce Exacto
    m1 = pd.merge(pend_b, pend_p, on=["ref_clean", "monto"], suffixes=('_b', '_p'))
    if not m1.empty:
        m1["Regla_Aplicada"] = "R1: Cruce Exacto (Ref + Monto)"
        conciliados = pd.concat([conciliados, m1], ignore_index=True)
        pend_b = pend_b.drop(m1["_id_b"].unique())
        pend_p = pend_p.drop(m1["_id_p"].unique())
    
    # R2: Cruce por 3 Dígitos
    m2 = pd.merge(pend_b, pend_p, on=["ref_3", "monto"], suffixes=('_b', '_p'))
    if not m2.empty:
        m2["Regla_Aplicada"] = "R2: Cruce por 3 Dígitos (Ref + Monto)"
        conciliados = pd.concat([conciliados, m2], ignore_index=True)
        pend_b = pend_b.drop(m2["_id_b"].unique())
        pend_p = pend_p.drop(m2["_id_p"].unique())
    
    # R3: Sumatorias Profit vs Banco
    p_sum = pend_p.groupby(["ref_3", "monto"])["monto"].sum().reset_index(name="monto_sumado")
    m3 = pd.merge(pend_b, p_sum, left_on=["ref_3", "monto"], right_on=["ref_3", "monto_sumado"])
    if not m3.empty:
        m3["Regla_Aplicada"] = "R3: Sumatoria de Partidas Profit"
        conciliados = pd.concat([conciliados, m3], ignore_index=True)
        pend_b = pend_b.drop(m3["_id_b"].unique())
        # Nota: En sumatoria se mantiene el detalle en pendientes de profit para análisis fino.

    # R4 & R5: Alertas de Duplicados en Profit
    alertas_p = pend_p[pend_p.duplicated(subset=["ref_clean", "monto"], keep=False)].copy()
    alertas_p["Alerta"] = "R4/R5: Duplicado Detectado en Profit"
    
    # R6: Detección de Transposiciones (Diferencia múltiplo de 9)
    transposiciones = []
    for _, b in pend_b.iterrows():
        for _, p in pend_p.iterrows():
            diff = abs(b["monto"] - p["monto"])
            if diff != 0 and diff % 9 == 0:
                transposiciones.append({
                    "Ref_Banco": b["referencia"], 
                    "Ref_Profit": p["referencia"], 
                    "Monto_Banco": b["monto"], 
                    "Monto_Profit": p["monto"],
                    "Diferencia": diff
                })
    df_trans = pd.DataFrame(transposiciones)

    # --- MÉTRICAS GENERALES DE CONTROL ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Registros Banco", len(df_b))
    m_col2.metric("Total Registros Profit", len(df_p))
    m_col3.metric("Partidas Conciliadas", len(conciliados))
    m_col4.metric("Diferencias Pendientes", len(pend_b) + len(pend_p))

    st.markdown("---")

    # --- PESTAÑAS DE VISUALIZACIÓN ---
    tabs = st.tabs([
        "✅ Conciliados", 
        "🏦 Pendientes Banco", 
        "💻 Pendientes Profit", 
        "⚠️ Alertas Duplicados", 
        "🔍 Transposiciones (R6)"
    ])
    
    with tabs[0]:
        st.subheader("Transacciones Exitosamente Conciliadas")
        st.dataframe(conciliados, use_container_width=True)
        
    with tabs[1]:
        clean_pend_b = pend_b.drop(columns=["_id_b"], errors="ignore")
        st.subheader("Partidas Pendientes en el Banco (No registradas o con desviación)")
        st.dataframe(clean_pend_b, use_container_width=True)
        
    with tabs[2]:
        clean_pend_p = pend_p.drop(columns=["_id_p"], errors="ignore")
        st.subheader("Partidas Pendientes en Profit (Sin contraparte bancaria)")
        st.dataframe(clean_pend_p, use_container_width=True)
        
    with tabs[3]:
        st.subheader("Auditoría de Duplicados en Origen (Profit)")
        st.dataframe(alertas_p, use_container_width=True)
        
    with tabs[4]:
        st.subheader("Análisis de Errores por Transposición de Dígitos (Múltiplo de 9)")
        st.dataframe(df_trans, use_container_width=True)

    st.markdown("---")

    # --- BLOQUE DE FIRMAS Y CIERRE DE AUDITORÍA ---
    st.subheader("✍️ Validación y Cierre de Auditoría")
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.text_input("Preparado por (Analista / Contador):", placeholder="Ej. Lcda. Nombre Apellido")
    with f_col2:
        st.text_input("Revisado / Aprobado por (Gerencia):", placeholder="Ej. Gerente de Administración")

    # --- BOTÓN DE DESCARGA DE REPORTE ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        conciliados.to_excel(writer, index=False, sheet_name="Conciliados")
        clean_pend_b.to_excel(writer, index=False, sheet_name="Pendientes_Banco")
        clean_pend_p.to_excel(writer, index=False, sheet_name="Pendientes_Profit")
        if not alertas_p.empty:
            alertas_p.to_excel(writer, index=False, sheet_name="Alertas_Duplicados")
        if not df_trans.empty:
            df_trans.to_excel(writer, index=False, sheet_name="Transposiciones_R6")
            
    st.download_button(
        label="📥 Descargar Reporte Completo de Auditoría (Excel)", 
        data=output.getvalue(), 
        file_name="Reporte_Conciliacion_Cero_Diferencias.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
