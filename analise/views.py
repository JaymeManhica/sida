import os
import base64
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from django.shortcuts import render
from django.contrib import messages
from prophet import Prophet
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from .forms import IndicatorForm

# Função para converter gráfico matplotlib em string base64 para exibição no template
def render_plot_to_base64():
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    # plt.close()  # Comentado para evitar fechamento prematuro do gráfico
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

# Função para plotar o indicador selecionado ao longo do tempo
def plot_indicator(df_moz, indicator):
    # Debug prints para verificação dos dados
    print(f"Indicator: {indicator}")
    print(f"DataFrame shape: {df_moz.shape}")
    print(f"Available indicators: {df_moz['Indicator Name'].unique()}")
    
    # Filtra os dados para o indicador selecionado
    row = df_moz[df_moz['Indicator Name'] == indicator]
    print(f"Filtered row shape: {row.shape}")
    
    if row.empty:
        print("No data found for the selected indicator")
        return None
        
    # Prepara os dados para plotagem
    years = list(map(str, range(1980, 2023)))
    data = row[years].T
    data.columns = [indicator]
    data.index = data.index.astype(int)
    data = data.dropna()
    
    if data.empty:
        print("No valid data points after processing")
        return None
    
    # Cria o gráfico
    plt.figure(figsize=(10, 5))
    data.plot(legend=False)
    plt.title(indicator)
    plt.xlabel('Ano')
    plt.ylabel('Valor')
    plt.grid(True)
    return render_plot_to_base64()

# Função para preparar dados para o modelo Prophet
def preparar_dados_prophet(df_moz, indicator):
    row = df_moz[df_moz['Indicator Name'] == indicator]
    years = list(map(str, range(1980, 2023)))
    values = row[years].T.reset_index()
    values.columns = ['ds', 'y']
    values['ds'] = pd.to_datetime(values['ds'])
    values['y'] = pd.to_numeric(values['y'], errors='coerce')
    return values.dropna()

# Função para debug do conteúdo do arquivo CSV
def debug_csv_contents():
    path = os.path.join(os.path.dirname(__file__), 'API_MOZ_DS2_en_csv_v2_100975.csv')
    try:
        df = pd.read_csv(path, skiprows=4)
        print("CSV file contents:")
        print(f"Shape: {df.shape}")
        print("\nFirst few rows:")
        print(df.head())
        print("\nUnique Country Names:")
        print(df['Country Name'].unique())
        print("\nUnique Indicator Names:")
        print(df['Indicator Name'].unique())
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")

# View principal que processa as requisições
def home(request):
    # Inicializa variáveis para armazenar resultados
    debug_csv_contents()
    plot_time_series = None
    plot_prophet = None
    plot_kmeans = None
    predicted_value = None
    plot_url = None

    if request.method == 'POST':
        form = IndicatorForm(request.POST)
        if form.is_valid():
            indicador = form.cleaned_data['indicator']
            path = os.path.join(os.path.dirname(__file__), 'API_MOZ_DS2_en_csv_v2_100975.csv')
            try:
                df = pd.read_csv(path, skiprows=4)
                print(f"CSV file loaded successfully. Shape: {df.shape}")
            except FileNotFoundError:
                messages.error(request, 'Arquivo não encontrado.')
                return render(request, 'analise/home.html', {'form': form})

            # Filtra dados para Moçambique
            df_moz = df[df['Country Name'] == 'Mozambique']
            print(f"Filtered Mozambique data shape: {df_moz.shape}")

            # === Plotagem da Série Temporal ===
            plot_time_series = plot_indicator(df_moz, indicador)
            if plot_time_series is None:
                messages.error(request, 'Não foi possível gerar o gráfico de série temporal para o indicador selecionado.')
                return render(request, 'analise/home.html', {'form': form})

            # === Análise com Prophet ===
            dados_prophet = preparar_dados_prophet(df_moz, indicador)
            if dados_prophet.empty:
                messages.error(request, 'Não há dados suficientes para gerar a previsão Prophet.')
                return render(request, 'analise/home.html', {'form': form})

            # Treina e faz previsões com Prophet
            modelo = Prophet()
            modelo.fit(dados_prophet)
            futuro = modelo.make_future_dataframe(periods=7, freq='Y')
            previsao = modelo.predict(futuro)

            # Plota resultados do Prophet
            plt.figure(figsize=(10, 6))
            modelo.plot(previsao)
            plt.title(f"Previsão: {indicador}")
            plot_prophet = render_plot_to_base64()

            # === Análise de Clusters com KMeans ===
            indicadores = [i[0] for i in form.fields['indicator'].choices]
            df_kmeans = df_moz[df_moz['Indicator Name'].isin(indicadores)]
            if df_kmeans.empty:
                messages.error(request, 'Não há dados suficientes para realizar a análise de clusters.')
                return render(request, 'analise/home.html', {'form': form})

            # Prepara dados para KMeans
            df_kmeans = df_kmeans.set_index(['Indicator Name'])
            df_kmeans = df_kmeans.loc[:, list(map(str, range(1980, 2023)))].T

            # Aplica imputação e normalização
            imputer = SimpleImputer(strategy='mean')
            df_imputed = imputer.fit_transform(df_kmeans)
            scaler = StandardScaler()
            df_scaled = scaler.fit_transform(df_imputed)

            # Aplica KMeans
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(df_scaled)

            # Prepara dados para visualização
            df_kmeans_processed = pd.DataFrame(df_imputed, index=df_kmeans.index, columns=df_kmeans.columns)
            df_kmeans_processed['Cluster'] = clusters

            # Plota resultados do KMeans
            plt.figure(figsize=(10, 5))
            sns.scatterplot(x=df_kmeans_processed.index, y=df_kmeans_processed.iloc[:, 0], hue=clusters, palette='viridis')
            plt.xticks(rotation=45)
            plt.title("Agrupamento de anos por padrão de indicadores")
            plot_kmeans = render_plot_to_base64()

            # Transforma dados para formato longo
            df_long = pd.melt(df,
                              id_vars=['Country Name', 'Country Code', 'Indicator Name', 'Indicator Code'],
                              var_name='Year',
                              value_name='Value')
            print(f"Após transformação: {len(df_long)} linhas")
            
            # Limpa e prepara os dados
            df_long['Year'] = pd.to_numeric(df_long['Year'], errors='coerce')
            df_long = df_long.dropna(subset=['Year'])
            df_long['Year'] = df_long['Year'].astype(int)
            df_long = df_long.dropna(subset=['Value'])
            print(f"Após limpeza: {len(df_long)} linhas")
            print(f"Anos disponíveis: {df_long['Year'].min()} - {df_long['Year'].max()}")

            # Prepara dados para Prophet
            mortalidade = df_long[["Year", "Value"]].copy()
            mortalidade.columns = ["ds", "y"]
            mortalidade["ds"] = pd.to_datetime(mortalidade["ds"], format='%Y')
            print(f"Dados para Prophet: {len(mortalidade)} linhas")
            print(f"Primeiros valores:\n{mortalidade.head()}")

            try:
                # Treina modelo Prophet
                model = Prophet()
                model.fit(mortalidade)
                print("Modelo Prophet treinado com sucesso")

                # Calcula períodos para previsão
                periods = year - mortalidade["ds"].dt.year.max()
                if periods <= 0:
                    messages.error(request, 'O ano solicitado deve ser maior que o último ano disponível nos dados.')
                    return render(request, 'analise/home.html', {'form': form})

                # Gera datas futuras
                future_dates = pd.date_range(
                    start=mortalidade['ds'].max(),
                    periods=periods + 1,
                    freq='YE'
                )
                future = pd.DataFrame({'ds': future_dates})
                
                # Faz previsão
                forecast = model.predict(future)
                print(f"Previsão completa:\n{forecast}")
                
                # Filtra resultado para ano específico
                resultado = forecast[forecast['ds'].dt.year == year]
                print(f"Previsão gerada para {year}")
                print(f"Resultado encontrado: {not resultado.empty}")
                print(f"Conteúdo do resultado:\n{resultado}")

                if not resultado.empty:
                    # Extrai valor previsto
                    predicted_value = round(resultado['yhat'].values[0], 2)
                    print(f"Valor previsto: {predicted_value}")

                    # Gera gráfico da previsão
                    plt.figure(figsize=(10, 6))
                    fig = model.plot(forecast)
                    plt.title(f"Previsão da Taxa de Mortalidade Infantil até {year}")
                    plt.xlabel('Ano')
                    plt.ylabel('Taxa de Mortalidade Infantil')
                    buf = BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                    plt.close(fig)
                    buf.seek(0)
                    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
                    plot_url = f'data:image/png;base64,{image_base64}'
                    print("Gráfico gerado com sucesso")
                else:
                    print("Nenhum resultado encontrado para o ano especificado")
                    messages.error(request, 'Não foi possível gerar a previsão para o ano especificado.')
            except Exception as e:
                print(f"Erro durante a previsão: {str(e)}")
                messages.error(request, f'Erro ao gerar a previsão: {str(e)}')

    else:
        form = IndicatorForm()

    # Renderiza template com resultados
    return render(request, 'analise/home.html', {
        'form': form,
        'plot_time_series': plot_time_series,
        'plot_prophet': plot_prophet,
        'plot_kmeans': plot_kmeans,
        'prediction': predicted_value if 'predicted_value' in locals() else None,
        'plot_url': plot_url if 'plot_url' in locals() else None
    })
