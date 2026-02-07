import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('dark_background')
plt.rcParams['figure.facecolor'] = '#121212'
plt.rcParams['axes.facecolor'] = '#1e1e1e'
plt.rcParams['grid.color'] = '#333333'

file_path = r'c:\Users\isaqu\AppData\Local\AMD\CN\data\20260207-020420.CSV'

def analyze_gpu_metrics(csv_path):
    # Carregar dados
    df = pd.read_csv(csv_path, na_values='N/A')
    
    # Mapeamento de colunas
    col_map = {
        'FPS': 'fps',
        'UTIL. DA GPU': 'gpu_usage',
        'SCLK DA GPU': 'gpu_clock',
        'ENERGIA DA GPU': 'power',
        'TEMP. DA GPU': 'gpu_temp',
        'VENT. DA GPU': 'fan_rpm',
        'UTIL. MEM. GPU': 'mem_usage',
        'MCLK DA GPU': 'mem_clock',
        'UTIL. DA CPU': 'cpu_usage',
        'UTIL. MEM. SISTEMA': 'system_mem'
    }
    
    df = df.rename(columns=col_map)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['timestamp'] = np.arange(len(df))
    
    print("\n=== ESTATÍSTICAS GERAIS ===")
    print(df.describe().transpose()[['mean', 'max', 'min']])
    
    last_idx = df.index[-1]
    crash_window = 20
    start_crash_zone = max(0, last_idx - crash_window)
    
    # Plotagem
    fig, axes = plt.subplots(6, 1, sharex=True, figsize=(14, 20))
    
    metrics = [
        ('fps', 'FPS', '#B388FF'),
        ('gpu_usage', 'GPU Usage (%)', '#4FC3F7'),
        ('gpu_clock', 'GPU Clock (MHz)', '#81C784'),
        ('gpu_temp', 'GPU Temp (°C)', '#FF8A65'),
        ('power', 'Power (W)', '#FFF176'),
        ('mem_usage', 'VRAM Usage (MB)', '#F06292')
    ]
    
    for i, (col, label, color) in enumerate(metrics):
        if col in df.columns:
            # Dados principais
            axes[i].plot(df['timestamp'], df[col], color=color, linewidth=2.5, label=label)
            
            # Zona de Crash
            axes[i].axvspan(start_crash_zone, last_idx, color='#CF6679', alpha=0.3, label='Crash Window (20s)')
            
            # Detalhes do eixo
            axes[i].set_ylabel(label, color='white', fontsize=10, fontweight='bold')
            axes[i].tick_params(colors='white')
            axes[i].grid(True, linestyle='--', alpha=0.5)
            
            # Anotação do último valor válido
            valid_data = df[col].dropna()
            if not valid_data.empty:
                last_idx_val = valid_data.index[-1]
                last_v = valid_data.iloc[-1]
                last_t = df.loc[last_idx_val, 'timestamp']
                axes[i].scatter(last_t, last_v, color='white', s=50, zorder=5)
                axes[i].annotate(f'{last_v:.1f}', (last_t, last_v), textcoords="offset points", xytext=(5,5), color='white', fontweight='bold')

    axes[-1].set_xlabel('Tempo (s)', color='white', fontsize=12, fontweight='bold')
    plt.suptitle('DEADLOCK CRASH ANALYSIS - GPU METRICS', color='#BB86FC', fontsize=22, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0.05, 0.05, 0.95, 0.96])
    
    plt.savefig('deadlock_crash_analysis.png', dpi=120)
    print("\nGrafico detalhado salvo como 'deadlock_crash_analysis.png'")
    
    # Analise detalhada dos ultimos segundos
    print("\n=== ÚLTIMOS 15 SEGUNDOS DO REGISTRO ===")
    cols_to_show = ['timestamp', 'fps', 'gpu_usage', 'gpu_clock', 'gpu_temp', 'power', 'mem_usage']
    print(df[cols_to_show].tail(15).to_string(index=False))
    
    # Diagnóstico preliminar
    last_fps_idx = df['fps'].last_valid_index()
    if last_fps_idx is not None:
        row_crash = df.loc[last_fps_idx]
        print(f"\n--- Diagnóstico no momento do Crash (t={row_crash['timestamp']}) ---")
        if row_crash['gpu_temp'] > 85:
            print("SUSPEITA: Superaquecimento da GPU.")
        if row_crash['gpu_usage'] < 10 and row_crash['fps'] > 0:
            print("SUSPEITA: Gargalo súbito ou perda de comunicação com o motor do jogo.")
        if row_crash['gpu_clock'] < 500:
            print("SUSPEITA: Downclock agressivo (possível problema de energia ou driver).")
        
        # Verificar o ponto IMEDIATAMENTE após o último FPS
        if last_fps_idx < len(df) - 1:
            after_crash = df.loc[last_fps_idx + 1]
            print(f"Ponto t+1 (pós-crash): Usage={after_crash['gpu_usage']}%, Power={after_crash['power']}W, Temp={after_crash['gpu_temp']}°C")

if __name__ == "__main__":
    analyze_gpu_metrics(file_path)
