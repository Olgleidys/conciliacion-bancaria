import streamlit as st
import pandas as pd
import io

# ... (Mantén tu configuración de CSS igual)

# Función para limpiar y estandarizar nombres de columnas
def preparar_dataframe(df, tipo):
    df.columns = [str(c).strip() for c in df.columns]
    # Renombrar Referencia a Ref si existe
    if 'Referencia' in df.columns:
        df.rename(columns={'Referencia': 'Ref'}, inplace=True)
    
    # Asegurar que existan las columnas base para el cruce
    df['Ref'] = df['Ref'].fillna('').astype(str).str.strip()
    
    # Calcular monto único para conciliación
    if tipo == 'banco':
        df['Monto_Limpio'] = limpiar_monto(df['Deb']) + limpiar_monto(df['Cred'])
    else:
        df['Monto_Limpio'] = limpiar_monto(df['Debe']) + limpiar_monto(df['Haber'])
    return df

if banco_file and profit_file:
    df_banco = preparar_dataframe(procesar_csv(banco_file), 'banco')
    df_profit = preparar_dataframe(procesar_csv(profit_file), 'profit')
    
    # --- LÓGICA DE CONCILIACIÓN ---
    # 1. Cruce 100% (Ref completa + Monto)
    cruce_1 = pd.merge(df_banco, df_profit, on=['Ref', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    # 2. Cruce por últimos 3 dígitos (Ref[-3:] + Monto)
    df_banco['Ref_3'] = df_banco['Ref'].str[-3:]
    df_profit['Ref_3'] = df_profit['Ref'].str[-3:]
    
    # Excluimos los ya conciliados en el paso 1
    rest_banco = df_banco[~df_banco.index.isin(cruce_1.index.get_level_values(0))]
    rest_profit = df_profit[~df_profit.index.isin(cruce_1.index.get_level_values(1))]
    
    cruce_2 = pd.merge(rest_banco, rest_profit, on=['Ref_3', 'Monto_Limpio'], suffixes=('_B', '_P'))
    
    # Unir ambos cruces
    cruces_final = pd.concat([cruce_1, cruce_2])
    
    # Definir pendientes sin eliminar nada
    solo_banco_df = df_banco[~df_banco.index.isin(cruces_final.index.get_level_values(0))]
    solo_profit_df = df_profit[~df_profit.index.isin(cruces_final.index.get_level_values(1))]
    
    # --- LIMPIEZA FINAL DE COLUMNAS PARA EL USUARIO ---
    # Solo dejamos las columnas originales: Fecha, Ref, Desc, Montos
    cols_b_show = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    cols_p_show = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']
    
    # En los tabs, mostramos solo estas columnas limpias
    with tab1:
        st.dataframe(cruces_final[cols_b_show], use_container_width=True)
        
    with tab2:
        st.dataframe(solo_banco_df[cols_b_show], use_container_width=True)
        
    with tab3:
        st.dataframe(solo_profit_df[cols_p_show], use_container_width=True)
        
    # En la descarga de Excel, aplicamos el mismo filtro
    # ... (En la parte de exportación usar los mismos DataFrames filtrados)
