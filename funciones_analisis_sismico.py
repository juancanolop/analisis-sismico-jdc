import numpy as np
import pandas as pd
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def df_to_numpy_array(df):
    """Convierte un DataFrame de pandas a un array de numpy"""
    return df.to_numpy()

def calcular_periodo_fundamental(pisos, h, Ct):
    """Calcula el periodo fundamental de vibración"""
    T = (pisos * h) / Ct
    return T

def calcular_factor_amplificacion(T, Tp, Tl):
    """Calcula el factor de amplificación sísmica"""
    if T < Tp:
        C = 2.5
    elif T > Tl:
        C = 2.5 * (Tp / T)
    else:
        C = 2.5 * ((Tp * Tl) / T**2)
    return C

def calcular_pseudo_aceleracion(Z, uso, C, S, R):
    """Calcula la pseudo-aceleración espectral (Sa)"""
    Sa = (Z * uso * C * S) / R
    return Sa

def calcular_frecuencias_estructurales(periodos):
    """Calcula las frecuencias estructurales W"""
    W_matriz = []
    for Ti in periodos:
        W = (2 * math.pi) / Ti
        W_matriz.append(W)
    return W_matriz

def calcular_desplazamientos_espectrales(Sa, W_matriz):
    """Calcula los desplazamientos espectrales Sd"""
    Sd = []
    for i in W_matriz:
        Sdi = Sa / i**2
        Sd.append(Sdi)
    return Sd

def calcular_participacion_masa(X, masas):
    """Calcula la participación de masa"""
    m = masas
    M = np.diag(m)
    r = []
    
    for i in X:
        ri = (i.T @ m) / (i.T @ M @ i)
        r.append(ri)
    
    return r, M

def calcular_aceleracion_por_piso(X, r, Sa):
    """Calcula la aceleración por piso U"""
    U = []
    for i in range(len(X)):
        Ui = np.dot(Sa, np.dot(r[i], X[i]))
        U.append(Ui)
    return U

def calcular_fuerzas_sismicas(M, U):
    """Calcula las fuerzas sísmicas"""
    F = []
    for i in range(len(U)):
        Fi = M @ U[i]
        F.append(Fi)
    return F

def calcular_cortante_sismica(F):
    """Calcula la cortante sísmica"""
    V = []
    for num_modo in range(len(F)):
        F_modo = F[num_modo]
        cortantes_modo = []
        
        for i in range(len(F_modo)):
            Vi = sum(F_modo[i:])
            cortantes_modo.append(Vi)
        
        V.append(cortantes_modo)
    
    return V

def calcular_cortante_suma_absolutos(V):
    """Calcula la cortante de la suma de valores absolutos"""
    pisos = len(V[0])
    V_sum_abs = []
    
    for piso in range(pisos):
        suma_piso = 0
        for modo in range(len(V)):
            valor_abs = abs(V[modo][piso])
            suma_piso += valor_abs
        V_sum_abs.append(suma_piso)
    
    return V_sum_abs

def calcular_cortante_rcsc(V):
    """Calcula la cortante raíz cuadrada de la suma de los cuadrados"""
    pisos = len(V[0])
    V_rcsc = []
    
    for piso in range(pisos):
        suma_piso = 0
        for modo in range(len(V)):
            valor_cuadrado = (V[modo][piso]) ** 2
            suma_piso += valor_cuadrado
        raiz_cuadrada = np.sqrt(suma_piso)
        V_rcsc.append(raiz_cuadrada)
    
    return V_rcsc

def calcular_cortante_respuesta_maxima(V_sum_abs, V_rcsc):
    """Calcula la cortante de respuesta máxima"""
    Vrnc_h = []
    
    for elemento in range(len(V_rcsc)):
        maxima = 0.25 * V_sum_abs[elemento] + 0.75 * V_rcsc[elemento]
        Vrnc_h.append(maxima)
    
    return Vrnc_h

def calcular_cortante_real(Vrnc_h, R):
    """Calcula la cortante real"""
    Vreal = []
    
    for elemento in range(len(Vrnc_h)):
        real = 0.75 * Vrnc_h[elemento] * R
        Vreal.append(real)
    
    return Vreal

def generar_grafico_fuerzas_cortantes(F, V, pisos_nombres):
    """Genera un gráfico de fuerzas y cortantes sísmicas por modo por piso"""
    colores = ['yellow', 'blue', 'red', 'green', 'purple']
    colores_limitados = colores[:len(F)]
    
    # Crear la figura con dos subgráficos
    fig = make_subplots(
        rows=1, cols=2, 
        subplot_titles=("Fuerzas Sísmicas (Tonf)", "Cortante Sísmico (Tonf)"), 
        column_widths=[0.5, 0.5]
    )
    
    # Agregar datos de Fuerzas Sísmicas
    for i, modo in enumerate(F):
        fig.add_trace(go.Scatter(
            x=[f"Modo {i+1}"] * len(pisos_nombres), 
            y=pisos_nombres, 
            mode='lines+markers+text',
            name=f'Modo {i+1}', 
            marker=dict(color=colores_limitados[i]),
            text=[f'{val:.2f}T' for val in modo], 
            textposition='middle right'
        ), row=1, col=1)
    
    # Agregar datos de Cortante Sísmico
    for i, modo in enumerate(V):
        fig.add_trace(go.Scatter(
            x=[f"Modo {i+1}"] * len(pisos_nombres), 
            y=pisos_nombres, 
            mode='lines+markers+text',
            name=f'Modo {i+1}', 
            marker=dict(color=colores_limitados[i]),
            text=[f'{val:.2f}T' for val in modo], 
            textposition='middle right'
        ), row=1, col=2)
    
    # Ajustes finales
    fig.update_layout(
        title_text="Análisis Sísmico", 
        height=600, 
        width=1100
    )
    fig.update_xaxes(
        title_text="Modos", 
        tickvals=[f"Modo {i+1}" for i in range(len(F))]
    )
    fig.update_yaxes(title_text="Pisos")
    
    return fig

def generar_grafico_cortantes(V_sum_abs, V_rcsc, Vrnc_h, Vreal, pisos_nombres):
    """Genera gráficos de diferentes tipos de cortantes por piso"""
    # Crear la figura con cuatro subgráficos
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Cortante de la Suma de Valores Absolutos", 
            "Raíz Cuadrada de la Suma de los Cuadrados", 
            "Cortante de Respuesta Máxima", 
            "Cortante Real"
        ),
        column_widths=[0.5, 0.5], 
        row_heights=[0.5, 0.5]
    )
    
    # Agregar datos de Suma de Valores Absolutos
    fig.add_trace(go.Scatter(
        x=V_sum_abs, 
        y=pisos_nombres, 
        mode='lines+markers+text',
        name='Suma Abs', 
        marker=dict(color='purple', size=8),
        text=[f'{val:.2f}T' for val in V_sum_abs], 
        textposition='middle right'
    ), row=1, col=1)
    
    # Agregar datos de Raíz Cuadrada de la Suma de los Cuadrados
    fig.add_trace(go.Scatter(
        x=V_rcsc, 
        y=pisos_nombres, 
        mode='lines+markers+text',
        name='RCSC', 
        marker=dict(color='green', size=8),
        text=[f'{val:.2f}T' for val in V_rcsc], 
        textposition='middle right'
    ), row=1, col=2)
    
    # Agregar datos de Cortante de Respuesta Máxima
    fig.add_trace(go.Scatter(
        x=Vrnc_h, 
        y=pisos_nombres, 
        mode='lines+markers+text',
        name='Cortante Máx', 
        marker=dict(color='orange', size=8),
        text=[f'{val:.2f}T' for val in Vrnc_h], 
        textposition='middle right'
    ), row=2, col=1)
    
    # Agregar datos de Cortante Real
    fig.add_trace(go.Scatter(
        x=Vreal, 
        y=pisos_nombres, 
        mode='lines+markers+text',
        name='Cortante Real', 
        marker=dict(color='red', size=8),
        text=[f'{val:.2f}T' for val in Vreal], 
        textposition='middle right'
    ), row=2, col=2)
    
    # Ajustes finales
    fig.update_layout(
        title_text="Análisis Sísmico Completo", 
        height=800, 
        width=1100
    )
    fig.update_xaxes(title_text="Toneladas fuerza")
    fig.update_yaxes(title_text="Pisos")
    
    return fig

def generar_grafico_cortante_real(Vreal, pisos_nombres):
    """Genera un gráfico de cortante real por piso"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=pisos_nombres,
        x=Vreal,
        orientation='h',
        marker=dict(color='red'),
        text=[f'{val:.2f}T' for val in Vreal],
        textposition='auto',
        name='Cortante Real'
    ))
    
    fig.update_layout(
        title_text="Cortante Real por Piso",
        xaxis_title="Cortante Real (Tonf)",
        yaxis_title="Pisos",
        height=600,
        width=800
    )
    
    return fig
