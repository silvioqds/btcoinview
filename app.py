import cx_Oracle
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
from flask import Flask, render_template, send_file
from io import BytesIO
import base64
import os
import matplotlib.dates as mdates

app = Flask(__name__)

@app.route('/')
def index():    
    # Detalhes de conexão
    db_user = os.environ.get("USER_ORACLE_CLOUD","YOUR_USER")
    db_password =  os.environ.get("PASS_ORACLE_CLOUD", "YOUR_PASSWORD")
    host =  os.environ.get('HOST_ORACLE_CLOUD', "adb.sa-saopaulo-1.oraclecloud.com")
    port =  os.environ.get('PORT_ORACLE_CLOUD', 1522)
    service_name =  os.environ.get('SERVICE_NAME_ORACLE_CLOUD',"YOUR_SERVICE_NAME")
    dsn = f'(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port={port})(host={host}))(connect_data=(service_name={service_name}))(security=(ssl_server_dn_match=yes)))'
       
    # Conectar ao banco de dados
    connection = cx_Oracle.connect(user=db_user, password=db_password, dsn=dsn)

    # Consulta SQL para obter os dados
    query = """
        SELECT hbtc."time_close", hbtc."price_close", hbtc."price_open", hbtc."price_high", hbtc."price_low"
        FROM (
            SELECT *
            FROM "HistoryBTC"
            ORDER BY "time_close" DESC
        ) hbtc
        WHERE ROWNUM <= 1825  -- 365 * 5 (5 anos)
        ORDER BY "time_close" ASC
    """

    cursor = connection.cursor()
    cursor.execute(query)

    # Processar os dados para o gráfico de linhas
    dates = []
    prices = []

    for row in cursor.fetchall():
        time_close = row[0]
        price_close = row[1]
        dates.append(time_close)
        prices.append(price_close)

    # Criar o gráfico de linhas
    plt.figure(figsize=(10, 6))
    plt.plot(dates, prices, marker='o')
    plt.xlabel('Data')
    plt.ylabel('Preço de Fechamento')
    plt.title('Valores do Bitcoin nos Últimos 5 Anos')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    # Salvar o gráfico de linhas como imagem
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
    cursor.close()


    query = """
        SELECT hbtc."time_close", hbtc."price_close", hbtc."price_open", hbtc."price_high", hbtc."price_low"
        FROM (
            SELECT *
            FROM "HistoryBTC"
            ORDER BY "time_close" DESC
        ) hbtc
        WHERE ROWNUM <= 30  -- Últimos 30 dias
        ORDER BY "time_close" ASC
    """

    cursor = connection.cursor()
    cursor.execute(query)

    # Processar os dados para o gráfico de candlestick
    data = []
    for row in cursor.fetchall():
        date = mdates.date2num(row[0])  # Converte a data para um formato numérico
        open_price = row[2]
        high = row[3]
        low = row[4]
        close_price = row[1]  # Usar o preço de fechamento para candlestick
        data.append([date, open_price, high, low, close_price])

    # Criar o gráfico de candlestick
    fig, ax = plt.subplots(figsize=(10, 6))
    candlestick_ohlc(ax, data, width=0.6, colorup='g', colordown='r')
    ax.set_xlabel('Data')
    ax.set_ylabel('Preço')
    ax.set_title('Gráfico de Candlestick')
    ax.xaxis_date()
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Salvar o gráfico de candlestick como imagem
    img_buffer_candle = BytesIO()
    plt.savefig(img_buffer_candle, format='png')
    img_buffer_candle.seek(0)
    img_data_candle = base64.b64encode(img_buffer_candle.read()).decode('utf-8')

    # Fechar cursor e conexão
    cursor.close()
    connection.close()

    return render_template("index.html", img_data=img_data, img_data_candle=img_data_candle)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
