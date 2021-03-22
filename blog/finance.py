import scipy as sp
import matplotlib.pyplot as plt
import pandas_datareader.data as getData
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import norm
import yfinance as yf
from datetime import date,timedelta

yf.pdr_override()

def var_historic(r, level=5):
  if isinstance(r, pd.DataFrame):
    return r.aggregate(var_historic, level=level)
  elif isinstance(r, pd.Series):
    return -np.percentile(r,level)
  else:
    raise TypeError("Expected DataFrame or Series !")

def var_cornish_fisher(r, level=5):
  z = norm.ppf(level/100)
  s = r.skew()
  k = r.kurtosis()
  z = z + (z**2*s/6) + (z**3-3*z)*(k)/24 - (2*z**3-5*z)*(s**2)/36

  return (r.mean() - z*r.std())

def cvar_historic(r, level=5):
  if isinstance(r, pd.Series):
    is_beyond = r <=  -var_historic(r, level=level)
    return -r[is_beyond].mean()
  elif isinstance(r, pd.DataFrame):
    return r.aggregate(cvar_historic,level=level)
  else:
    raise TypeError("Expected DataFrame or Series !")

def get_current_price(index):
  index = index + ".SI"
  today = date.today()
  stock_data = getData.DataReader(index,data_source='yahoo',start=today-timedelta(7),end=today)
  latest_price = round(stock_data.tail(1)["Close"].iloc[0],3)
  return latest_price

def get_stock_stats(stock,lookback_in_years):
      stock = stock
      today = date.today()
      stock_data = getData.DataReader(stock,data_source='yahoo',start=today-timedelta(lookback_in_years*252),end=today)
      returns = stock_data["Adj Close"].pct_change().dropna()
      #print(returns)

      number_days = returns.shape[0]

      risk_free_rate = 0.3
      daily_return = ((returns+1).prod()**(1/number_days)-1)
      annual_return = round(((daily_return+1)**252 - 1)*100,3)
      annual_std = round(returns.std()*np.sqrt(252)*100,3)
      annual_semideviation = round(returns[returns < returns.mean()].std()*np.sqrt(252)*100,3)
      daily_skew = returns.skew()
      annual_skew = daily_skew/np.sqrt(252)
      daily_kurtosis = returns.kurtosis()
      annual_kurtosis = daily_skew/252

      wealth_index = 1000*(1+returns).cumprod()
      previous_peaks = wealth_index.cummax()
      drawdown = (wealth_index - previous_peaks)/previous_peaks

      max_drawdown = drawdown.min()
      max_drawdown_date = drawdown.idxmin()

      jarque_bera_test = stats.jarque_bera(returns)

      historical_var_1 = round(var_historic(returns,1)*100,3)
      historical_var_5 = round(var_historic(returns,5)*100,3)
      cornish_fisher_var_5 = round(var_cornish_fisher(returns,5)*100,3)
      cornish_fisher_var_1 = round(var_cornish_fisher(returns,1)*100,3)
      cvar_historic_1 = round(cvar_historic(returns,1)*100,3)
      cvar_historic_5 = round(cvar_historic(returns,5)*100,3)

      sharpe = (annual_return - risk_free_rate)/annual_std

      output = pd.DataFrame({"Number of Years" : lookback_in_years,
                             "Yahoo Stock Ticker" : stock,
                             "Annual Return" : annual_return,
                             "Annual Standard Deviation" : annual_std,
                             "Annual Semi-Deviation" : annual_semideviation,
                             "Skew" : annual_skew,
                             "Excess Kurtosis" : annual_kurtosis,
                             "Maximum Drawdown" : max_drawdown,
                             "Jarque Bera Test" : jarque_bera_test[0],
                             "Jarque Bera Test p-Value" : jarque_bera_test[1],
                             "Historical Daily Var (99%)" : historical_var_1,
                             "Historical Daily Var (95%)" : historical_var_5,
                             "Cornish-Fisher Daily Var (99%)" : cornish_fisher_var_1,
                             "Cornish-Fisher Daily Var (95%)" : cornish_fisher_var_5,
                             "CVAR Historic (99%)" : cvar_historic_1,
                             "CVAR Historic (95%)" : cvar_historic_5,
                             "Sharpe Ratio (Risk-Free Rate = 0.3%)" : sharpe,
                             },index=[0])

      output = output.transpose()
      output = output.rename(columns={0:"Value"})

      return output

def extract_portfolio_data(portfolio,lookback_in_years):
    today = date.today()
    df = pd.DataFrame(columns=portfolio)
    for stock in portfolio:
        stock = stock + ".SI"
        stock_data = getData.DataReader(stock,data_source='yahoo',start=today-timedelta(lookback_in_years*252),end=today)
        returns = stock_data["Adj Close"].pct_change().dropna()
        df[stock] = returns
    df['Mean'] = df.mean(axis=1)
    df['Index'] = (1+df["Mean"]).cumprod(axis=0)
    return df

def get_portfolio_stats(portfolio,lookback_in_years):

    df = extract_portfolio_data(portfolio,lookback_in_years)
    returns = df["Mean"]
    print(returns)
    number_days = returns.shape[0]

    risk_free_rate = 0.3
    daily_return = ((returns+1).prod()**(1/number_days)-1)
    annual_return = round(((daily_return+1)**252 - 1)*100,3)
    annual_std = round(returns.std()*np.sqrt(252)*100,3)
    annual_semideviation = round(returns[returns < returns.mean()].std()*np.sqrt(252)*100,3)
    daily_skew = returns.skew()
    annual_skew = daily_skew/np.sqrt(252)
    daily_kurtosis = returns.kurtosis()
    annual_kurtosis = daily_skew/252

    wealth_index = 1000*(1+returns).cumprod()
    previous_peaks = wealth_index.cummax()
    drawdown = (wealth_index - previous_peaks)/previous_peaks

    max_drawdown = drawdown.min()
    max_drawdown_date = drawdown.idxmin()

    jarque_bera_test = stats.jarque_bera(returns)

    historical_var_1 = round(var_historic(returns,1)*100,3)
    historical_var_5 = round(var_historic(returns,5)*100,3)
    cornish_fisher_var_5 = round(var_cornish_fisher(returns,5)*100,3)
    cornish_fisher_var_1 = round(var_cornish_fisher(returns,1)*100,3)
    cvar_historic_1 = round(cvar_historic(returns,1)*100,3)
    cvar_historic_5 = round(cvar_historic(returns,5)*100,3)

    sharpe = (annual_return - risk_free_rate)/annual_std

    output = pd.DataFrame({"Number of Years" : lookback_in_years,
                           "Annual Return(%)" : annual_return,
                           "Annual Standard Deviation(%)" : annual_std,
                           "Annual Semi-Deviation (%)" : annual_semideviation,
                           "Skew" : annual_skew,
                           "Excess Kurtosis" : annual_kurtosis,
                           "Maximum Drawdown(%)" : max_drawdown*100,
                           "Maximum Drawdown Date" : max_drawdown_date,
                           "Jarque Bera Test" : jarque_bera_test[0],
                           "Jarque Bera Test p-Value" : jarque_bera_test[1],
                           "Historical Daily Var (99%)" : historical_var_1,
                           "Historical Daily Var (95%)" : historical_var_5,
                           "Cornish-Fisher Daily Var (99%)" : cornish_fisher_var_1,
                           "Cornish-Fisher Daily Var (95%)" : cornish_fisher_var_5,
                           "CVAR Historic (99%)" : cvar_historic_1,
                           "CVAR Historic (95%)" : cvar_historic_5,
                           "Sharpe Ratio (Risk-Free Rate = 0.3%)" : sharpe,
                           },index=[0])

    output = output.transpose()
    output = output.rename(columns={0:"Portfolio Statistic"})

    return output
