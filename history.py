import requests
import pandas as pd

def extract_history(symbol, interval, start, end):
    df = pd.DataFrame()
    while end > start:
        url = 'https://api.binance.com/api/v3/klines?symbol=' + symbol +'&interval='+ interval +'&limit=1000&endTime=' + str(end)+ '000'
        print(url)
        data = requests.get(url).json()
        df = pd.concat([df, pd.DataFrame(data)])
        
        interval_millisec = data[1][0] - data[0][0]
        end = (data[0][0] - interval_millisec) / 1000
        end = int(end)
        
    df = df[df[0] >= start * 1000]
    return df

def save_history(symbol, interval, start, end):
    df = extract_history(symbol, interval, start, end)
    path = './history/' + symbol + ' - ' + interval + ' - ' + str(start) + ' - ' + str(end)
    df.to_csv(path, index = False)