import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from flask import Flask, render_template, request
from matplotlib.table import Table

app = Flask(__name__, template_folder='template', static_folder='static')

# Define a function to check for Bullish Volume Imbalance
def is_bullish_volume_imbalance(index, open_price, close_price, low_price, high_price):
    if (
        open_price[index] > close_price[index]
        and open_price[index-1] > close_price[index-1]
        and open_price[index-2] > close_price[index-2]
        and low_price[index-2] > high_price[index]
        and low_price[index - 1] <= high_price[index-2]
        and high_price[index - 1] >= low_price[index]
    ):
        return True
    else:
        return False

def identify_bullish_imbalances(df):
    bullish_vi_boxes = []
    for i in range(2, len(df)):
        if is_bullish_volume_imbalance(i, df['Open'], df['Close'], df['Low'], df['High']):
            box = {
                'left': i - 2,
                'top': min(df['Close'].iloc[i-2], df['Low'].iloc[i-2]),
                'right': i,
                'bottom': max(df['Open'].iloc[i], df['High'].iloc[i]),
            }
            bullish_vi_boxes.append(box)
    return bullish_vi_boxes

@app.route('/', methods=['GET', 'POST'])
def index():
    nifty_candlestick_data = []  # Initialize with an empty list
    bullish_vi_boxes = []  # Initialize with an empty list for bullish imbalances
    chart_file = None  # Initialize chart_file as None
    table_file = None  # Initialize table_file as None

    if request.method == 'POST':
        if 'fetch_nifty' in request.form:
            # Fetch historical Nifty data with user-defined start and end dates
            start_date = request.form.get('start_date', '2023-01-01')
            end_date = request.form.get('end_date', '2023-09-30')

            nifty_data = yf.Ticker('^NSEI')  # Nifty 50 index symbol
            nifty_history = nifty_data.history(period="1d", start=start_date, end=end_date)

            # Convert Nifty history to a DataFrame
            df = pd.DataFrame(nifty_history, columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits'])

            # Identify bullish imbalances
            bullish_vi_boxes = identify_bullish_imbalances(df)

            # Plot the candlestick chart
            fig, axes = mpf.plot(df, type="candle", title="Nifty Candlestick Chart with Bullish Volume Imbalance",
                                style='yahoo', ylabel='Price', returnfig=True)

            # Plot Bullish Volume Imbalance boxes as "x" markers
            for box in bullish_vi_boxes:
                left = box['left']
                top = box['top']
                right = box['right']
                bottom = box['bottom']
                axes[0].plot([left, right], [top, bottom], 'x', color='green', markersize=10)

            # Create a list of 'bottom' values for the table
            table_data = [['Bottom']]  # Initialize with a header
            for box in bullish_vi_boxes:
                bottom = box['bottom']
                table_data.append([bottom])

            # Save the graph to a file
            chart_file = 'static/nifty_candlestick_chart.png'  # Save the chart in the 'static' folder
            plt.savefig(chart_file)

            # Create a subplot for the table and plot it
            table_fig, table_axes = plt.subplots()
            table = table_axes.table(cellText=table_data, loc='center', cellLoc='center', colLabels=['Bottom'])
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1, 1.5)  # Adjust the table size if needed
            table_axes.axis('off')  # Turn off the axis for the table
            table_fig.savefig('static/table.png', bbox_inches='tight')

    return render_template('index.html', nifty_candlestick_data=nifty_candlestick_data, chart_file=chart_file, table_file='static/table.png')

if __name__ == '__main__':
    app.run(debug=True, port=5001)