import streamlit as st
import pandas as pd
import io

# Configuración de la página web corporativa
st.set_page_config(page_title="Sistema de Auditoría y Conciliación Avanzada", page_icon="📊", layout="wide")

# ESTILOS CSS PERSONALIZADOS: Look Premium de Alta Visibilidad
custom_css = """
    <style>
    .stApp {
        background-color: #0d1b2a;
        color: #e0e1dd;
    }
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .stSelectbox label, .stFileUploader label, .stTextInput label, .stNumberInput label {
        color: #e0e1dd !important;
        font-weight: bold !important;
    }
    button[data-baseweb="tab"] p {
        color: #e0e1dd !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #00b4d8 !important;
        font-weight: bold !important;
    }
    div[data-baseweb="tab-highlight-line"] {
        background-color: #00b4d8 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #00b4d8 !important;
        font-size: 26px !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }
    .stDownloadButton button {
        background-color: #0077b6 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stDownloadButton button:hover {
        background-color: #00b4d8 !important;
        color: #0d1b2a !important;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0b132b;
        color: #bcbed8;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: 500;
        border-top: 2px solid #0077b6;
        z-index: 100;
    }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p></div>', unsafe_allow_html=True)

st.title("📊 Sistema Avanzado de Conciliación Bancaria y Control de Gestión")

# FILA 1: Datos de la Empresa
c1, c2 = st.columns(2)
with c1:
    empresa_seleccionada = st.selectbox("🏢 Seleccione la empresa a conciliar:", ["Thermo Group", "Mystic", "Keravital"])

bancos_por_empresa = {
    "Thermo Group": ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"],
    "Mystic": ["Banesco", "Venezuela", "Banplus", "Banplus Mazal"],
    "Keravital": ["Banesco", "Venezuela"]
}

with c2:
    banco_seleccionado = st.selectbox("🏦 Seleccione el banco a conciliar:", bancos_por_empresa[empresa_seleccionada])

# FILA 2: Período y Saldos de Control (El punto de partida solicitado)
st.markdown("### 📅 Período de Auditoría y Control de Saldos")
p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("静态 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

st.markdown("#### 💵 Control de Saldos en Libros (Para Cierre de Mes)")
s1, s2 = st.columns(2)
with s1:
    saldo_inicial_banco = st.number_input(f"💰 Saldo Inicial en Estado de Cuenta ({banco_seleccionado}):", value=0.0, step=100.0)
with s2:
    saldo_inicial_profit = st.number_input(f"💻 Saldo Inicial en Sistema Profit ({empresa_seleccionada}):", value=0.0, step=100.0)

st.markdown("---")

# MÓDULO DE AJUSTES MANUALES (Para forzar la conciliación de diferencias detectadas)
st.markdown("### 🛠️ Registro de Diferencias Aclaradas (Revisión Manual)")
ajustes_input = st.text_input("Ingrese las referencias separadas por coma que identificó manualmente para forzar su cruce (Ej: 14520, 998231):", "")
referencias_ajustadas = [ref.strip().lstrip('0').replace('.0', '') for ref in ajustes_input.split(',') if ref.strip()]

col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader(f"📥 Estado de Cuenta de {banco_seleccionado} (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader(f"📥 Reporte de Profit Plus (.csv)", type=["csv"])

def procesar_csv(file):
    try:
        df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
        return df
    except:
        return None

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    df_banco = procesar_csv(banco_file)
    df_profit = procesar_csv(profit_file)
    
    if df_banco is not None and df_profit is not None:
        try:
            df_banco.columns = [str(c).strip() for c in df_banco.columns]
            df_profit.columns = [str(c).strip() for c in df_profit.columns]

            while len(df_banco.columns) < 5: df_banco[f'Comodin_B_{len(df_banco.columns)}'] = ""
            while len(df_profit.columns) < 5: df_profit[f'Comodin_P_{len(df_profit.columns)}'] = 0

            cols_banco = list(df_banco.columns)
            cols_banco[0], cols_banco[1], cols_banco[2], cols_banco[3], cols_banco[4] = 'Fecha', 'Ref', 'Desc', 'Deb', 'Cred'
            df_banco.columns = cols_banco

            cols_profit = list(df_profit.columns)
            cols_profit[0], cols_profit[1], cols_profit[2], cols_profit[3], cols_profit[4] = 'Fecha', 'Ref', 'Desc', 'Debe', 'Haber'
            df_profit.columns = cols_profit
            
            df_banco['Ref'] = df_banco['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            df_profit['Ref'] = df_profit['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            
            df_banco = df_banco[df_banco['Ref'] != '']
            df_profit = df_profit[df_profit['Ref'] != '']
            
            # Base de referencias cruzadas
            refs_profit = set(df_profit['Ref'].unique())
            
            # Aplicar la lógica de ajustes manuales agregando las indicadas por Olgleidys
            if referencias_ajustadas:
                refs_profit.update(referencias_ajustadas)
            
            refs_banco = set(df_banco['Ref'].unique())
            if referencias_ajustadas:
                refs_banco.update(referencias_ajustadas)

            # Clasificación de cruces
            cruces_df = df_banco[df_banco['Ref'].isin(refs_profit)]
            solo_banco_df = df_banco[~df_banco['Ref'].isin(refs_profit)]
            solo_profit_df = df_profit[~df_profit['Ref'].isin(refs_banco)]
            
            # PESTAÑAS DEL PANEL
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo en Banco", "💻 Solo en Profit", "📈 Análisis de Gestión y KPIs", "🔒 Amarre de Saldos (Cierre)"])
            
            with tab1:
                st.subheader("Transacciones Conciliadas Correctamente")
                st.dataframe(cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab2:
                st.subheader("Movimientos en Banco pendientes por registrar")
                st.dataframe(solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab3:
                st.subheader("Movimientos en Profit pendientes por pasar por el Banco")
                st.dataframe(solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']], use_container_width=True)
                
            with tab4:
                st.subheader("📊 Línea de Flujo y KPIs Estratégicos")
                
                total_banco_ops = len(df_banco)
                ops_conciliadas = len(cruces_df)
                tasa_eficiencia = (ops_conciliadas / total_banco_ops * 100) if total_banco_ops > 0 else 0
                
                # Clasificador de Línea de Flujo para Artículos de Oficina / Papelería
                df_banco['Desc_Lower'] = df_banco['Desc'].astype(str).str.lower()
                oficina_df = df_banco[df_banco['Desc_Lower'].str.contains('oficina|papeleria|articulos|compra|libreria', na=False)]
                monto_oficina = limpiar_monto(oficina_df['Deb']).sum() + limpiar_monto(oficina_df['Cred']).sum()
                
                k1, k2, k3 = st.columns(3)
                k1.metric("🎯 Eficiencia de Conciliación", f"{tasa_eficiencia:.1f}%")
                k2.metric("📎 Flujo: Gastos de Oficina", f"{monto_oficina:,.2f} Bs", help="Monto acumulado detectado automáticamente bajo el concepto de artículos de oficina.")
                k3.metric("💼 Operaciones Totales", f"{total_banco_ops} mov.")
                
                st.markdown("#### Proporción de Conciliación Física de Datos")
                chart_data = pd.DataFrame({
                    'Estado': ['Conciliados', 'Pendiente Banco', 'Pendiente Profit'],
                    'Movimientos': [len(cruces_df), len(solo_banco_df), len(solo_profit_df)]
                })
                st.bar_chart(data=chart_data, x='Estado', y='Movimientos', color='#00b4d8')
                
            with tab5:
                st.subheader("🔒 Módulo de Cierre e Igualdad de Saldos")
                st.markdown("Este módulo consolida matemáticamente los saldos para asegurar que el Punto de Partida del mes siguiente sea exacto.")
                
                # Sumas totales conciliadas
                total_creditos_banco = limpiar_monto(cruces_df['Cred']).sum()
                total_debitos_banco = limpiar_monto(cruces_df['Deb']).sum()
                
                saldo_final_banco_calculado = saldo_inicial_banco + total_creditos_banco - total_debitos_banco
                saldo_final_profit_calculado = saldo_inicial_profit + limpiar_monto(cruces_df['Haber']).sum() - limpiar_monto(cruces_df['Debe']).sum()
                
                c_amarre1, c_amarre2 = st.columns(2)
                with c_amarre1:
                    st.metric("📋 Saldo Final Conciliado en Banco", f"{saldo_final_banco_calculado:,.2f} Bs")
                with c_amarre2:
                    st.metric("💻 Saldo Final Conciliado en Profit", f"{saldo_final_profit_calculado:,.2f} Bs")
                
                diferencia_saldos = abs(saldo_final_banco_calculado - saldo_final_profit_calculado)
                if diferencia_saldos < 0.05:
                    st.success("🎉 ¡CONCILIACIÓN CUADRADA PERFECCIÓN! Los saldos finales coinciden exactamente. Este es tu punto de partida oficial para el próximo período.")
                else:
                    st.warning(f"⚠️ Alerta: Existe una discrepancia de {diferencia_saldos:,.2f} Bs entre los saldos finales conciliados. Verifique los saldos iniciales introducidos o registre las referencias aclaradas arriba.")

            # Exportación Excel
            st.markdown("---")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Solo_en_Banco', index=False)
                solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']].to_excel(writer, sheet_name='Solo_en_Profit', index=False)
            
            emp_nom = empresa_seleccionada.replace(" ", "_")
            bnc_nom = banco_seleccionado.replace(" ", "_")
            nombre_archivo_excel = f"Conciliacion_{emp_nom}_{bnc_nom}_{frecuencia}_{mes}_{ano}.xlsx"
            
            st.download_button(label="📥 Descargar Conciliación Completa (Excel)", data=output.getvalue(), file_name=nombre_archivo_excel, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los datos: {e}")

st.markdown("<br><br><br>", unsafe_allow_html=True)
