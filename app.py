import streamlit as st
import pandas as pd
import io

# Configuración de la página web corporativa
st.set_page_config(page_title="Conciliación Bancaria", page_icon="📊", layout="wide")

st.title("📊 Sistema Automatizado de Conciliación Bancaria")
st.markdown("Carga tus archivos mensuales en formato CSV para procesar la auditoría de forma inmediata.")

# Zona de carga de archivos en dos columnas
col1, col2 = st.columns(2)

with col1:
    banco_file = st.file_uploader("📥 Cargar Estado de Cuenta del Banco (.csv)", type=["csv"])
with col2:
    profit_file = st.file_uploader("📥 Cargar Reporte de Profit Plus (.csv)", type=["csv"])

def procesar_csv(file):
    try:
        bytes_data = file.getvalue()
        texto = bytes_data.decode("utf-8", errors="ignore").split('\n')
        separador = ';' if any(';' in linea for linea in texto[:5]) else ','
        file.seek(0)
        df = pd.read_csv(file, sep=separador, encoding="utf-8", on_bad_lines="skip")
        return df
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

if banco_file and profit_file:
    df_banco = procesar_csv(banco_file)
    df_profit = procesar_csv(profit_file)
    
    if df_banco is not None and df_profit is not None:
        try:
            # Estandarización de columnas fijas
            df_banco.columns = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
            df_profit.columns = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']
            
            # Limpieza exhaustiva de referencias
            df_banco['Ref'] = df_banco['Ref'].astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            df_profit['Ref'] = df_profit['Ref'].astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            
            refs_profit = set(df_profit['Ref'].unique())
            refs_banco = set(df_banco['Ref'].unique())
            
            cruces_df = df_banco[df_banco['Ref'].isin(refs_profit)]
            solo_banco_df = df_banco[~df_banco['Ref'].isin(refs_profit)]
            solo_profit_df = df_profit[~df_profit['Ref'].isin(refs_banco)]
            
            # MÓDULO VISUAL DE MÉTRICAS
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Cruces Exitosos", f"{len(cruces_df)} mov.")
            m2.metric("Pendientes en Banco", f"{len(solo_banco_df)} mov.")
            m3.metric("Pendientes en Profit", f"{len(solo_profit_df)} mov.")
            
            # PESTAÑAS INTERACTIVAS EN PANTALLA
            tab1, tab2, tab3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo en Banco", "💻 Solo en Profit"])
            
            with tab1:
                st.subheader("Transacciones Conciliadas Correctamente")
                st.dataframe(cruces_df, use_container_width=True)
                
            with tab2:
                st.subheader("Movimientos en Banco pendientes por registrar en Profit")
                st.dataframe(solo_banco_df, use_container_width=True)
                
            with tab3:
                st.subheader("Movimientos en Profit pendientes por pasar por el Banco")
                st.dataframe(solo_profit_df, use_container_width=True)
            
            # EXPORTACIÓN AUTOMÁTICA A EXCEL
            st.markdown("---")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_df.to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_df.to_excel(writer, sheet_name='Solo_en_Banco', index=False)
                solo_profit_df.to_excel(writer, sheet_name='Solo_en_Profit', index=False)
            
            st.download_button(
                label="📥 Descargar Conciliación Completa (Excel)",
                data=output.getvalue(),
                file_name="Conciliacion_Mensual.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.success("¡Conciliación procesada con éxito!")
            
        except Exception as e:
            st.error(f"Ocurrió un error al procesar las columnas: {e}")
