#################################
# Imports
################################

import streamlit as st  # Web App
import pandas as pd  # Dataframes
import numpy as np  # Maths functions
import datetime as dt  # Time Functions
import sqlalchemy  # SQL and Credentials
import os
import io
import dotenv  # Protect db creds
dotenv.load_dotenv()

# Charting
import seaborn as sns
from matplotlib import pyplot as plt

# SKLearn
from sklearn.metrics import mean_squared_error  # Mean Squared Error Function (Needs np.sqrt for units)

# SQL Connection
DATABASE_URL = os.environ.get('DATABASE_URL')
# Cache func for loading Database.


@st.cache(allow_output_mutation=True)
def get_database_connection():
    engine = sqlalchemy.create_engine(DATABASE_URL)
    query = 'SELECT date, forecast, temp_max, issue, extended_text FROM "bom-weather"'
    
    # Store db in memory for speed up?
    copy_sql = "COPY ({query}) TO STDOUT WITH CSV {head}".format(
       query=query, head="HEADER"
    )
    conn = engine.raw_connection()
    cur = conn.cursor()
    store = io.StringIO()
    cur.copy_expert(copy_sql, store)
    store.seek(0)
    mem_stored_db = pd.read_csv(store)
    
#     db = pd.read_sql_query('SELECT date, forecast, temp_max, issue, extended_text FROM "bom-weather";',engine)
#     db = pd.read_sql('bom-weather', engine)  # Don't need whole db
    return mem_stored_db


# Define Times (easier to just make a string format time here.)
today = dt.date.today()
todaystr = today.strftime("%Y-%m-%d")
yesterday = dt.date.today() - pd.DateOffset(days=1)
yesterdaystr = yesterday.strftime("%Y-%m-%d")
tomorrow = dt.date.today() + pd.DateOffset(days=1)
tomorrowstr = tomorrow.strftime("%Y-%m-%d")
day_after_tomorrow = dt.date.today() + pd.DateOffset(days=2)
day_after_tomorrowstr = day_after_tomorrow.strftime("%Y-%m-%d")

# Load Data
db = get_database_connection()  # pull DB data.
db.index = pd.to_datetime(db['date'])  # Set DB Index

#################################
# DataFrame
################################

# Build DataFrame from db
today0 = db[db['forecast'] == 0]
today1 = db[db['forecast'] == 1]
today2 = db[db['forecast'] == 2]
today3 = db[db['forecast'] == 3]
today4 = db[db['forecast'] == 4]
today5 = db[db['forecast'] == 5]
today6 = db[db['forecast'] == 6]

dates_index = list(set(db['issue']))  # Set Index
dates_index.sort()  # Sort Index

# Dataframe for Today + Forecast
tf = pd.DataFrame(None)
tf['today+0'] = today0['temp_max'].reset_index(drop=True)
tf['today+1'] = today1['temp_max'].reset_index(drop=True)
tf['today+2'] = today2['temp_max'].reset_index(drop=True)
tf['today+3'] = today3['temp_max'].reset_index(drop=True)
tf['today+4'] = today4['temp_max'].reset_index(drop=True)
tf['today+5'] = today5['temp_max'].reset_index(drop=True)
tf['today+6'] = today6['temp_max'].reset_index(drop=True)

tf.index = dates_index

#################################
# Heatmap
################################


# Heatmap Function
def heat_map(data, title):

    fig, ax = plt.subplots(figsize=(10, 10))
    ax = sns.heatmap(data, annot=True, center=True, cmap='coolwarm', cbar_kws={'label': 'Degrees Celsius'})
    ax.set_title(title, loc='center', fontsize=18)
    ax.set_xticklabels(ax.xaxis.get_ticklabels(), fontsize=14, rotation=30)
    ax.set_yticklabels(ax.yaxis.get_ticklabels(), fontsize=14, rotation=0)
    ax.figure.axes[-1].yaxis.label.set_size(14)
    ax.figure.axes[0].yaxis.label.set_size(14)
    ax.figure.axes[0].xaxis.label.set_size(14)
    return st.pyplot(fig);


#################################
# Accuracy
################################

# Create Accuracy Table
tf.index = pd.to_datetime(tf.index)  # make index a datetime.

# Accuracy Mechanism: Compare forecast to actual Temp.
fac = pd.DataFrame()
counter = list(range(len(tf)))
columns = list(tf.columns)

for i in counter:
    # 7 day forecast inc today, so len can't exceed 7
    if i < 7:
        window = i 
        j = i
    else: 
        window = 6
        j = 6
    
    # Start date at most recent row
    actual_date = tf.index[-1]  # start with the last day
    window_date = actual_date - pd.DateOffset(days=window)  # Number of days in the past can't be more than those forecast
    row_0 = tf.index[0]  # We want to end when window date is equal to row_0.
    
    tf_list = []  # temporary holder of weeks values.
    while window_date >= row_0:
        true_temp = int(tf.loc[actual_date][0])  # True temperature recorded on day
        predicted_temp = int(tf.loc[window_date][window])  # data predicted on value of window
        difference = true_temp - predicted_temp
        # loop 
        actual_date -= pd.DateOffset(days=1)  # take off 1 day.
        window_date -= pd.DateOffset(days=1)  # take off 1 day.
        # append
        tf_list.append(difference)    
    # Add list to df as series    
    fac[columns[j]] = pd.Series(tf_list[::-1])  # Add list backwards.
        
fac.index = dates_index
tf.index = dates_index

#################################
# RMSE
################################

# Assign (Root) Mean Squared Error
rmse_today1 = [np.sqrt(mean_squared_error(fac['today+0'][:len(fac['today+1'].dropna())], fac['today+1'].dropna()))]
rmse_today2 = [np.sqrt(mean_squared_error(fac['today+0'][:len(fac['today+2'].dropna())], fac['today+2'].dropna()))]
rmse_today3 = [np.sqrt(mean_squared_error(fac['today+0'][:len(fac['today+3'].dropna())], fac['today+3'].dropna()))]
rmse_today4 = [np.sqrt(mean_squared_error(fac['today+0'][:len(fac['today+4'].dropna())], fac['today+4'].dropna()))]
rmse_today5 = [np.sqrt(mean_squared_error(fac['today+0'][:len(fac['today+5'].dropna())], fac['today+5'].dropna()))]
rmse_today6 = [np.sqrt(mean_squared_error(fac['today+0'][:len(fac['today+6'].dropna())], fac['today+6'].dropna()))]

# Assign error vals to a df
accuracy = pd.DataFrame()
accuracy['1 Day Forecast'] = rmse_today1
accuracy['2 Day Forecast'] = rmse_today2
accuracy['3 Day Forecast'] = rmse_today3
accuracy['4 Day Forecast'] = rmse_today4
accuracy['5 Day Forecast'] = rmse_today5
accuracy['6 Day Forecast'] = rmse_today6

accuracy.index = ["Average Daily Forecast Error"]

#################################
# Persistence
################################

# Persistence Mechanism subtract each max temp from the one before.
pmodel = pd.Series([today - yesterday for today, yesterday in zip(tf['today+0'], tf['today+0'][1:])], index=tf.index[:len(tf.index)-1])

# Assign pmodel vals to series.
persistence = pd.DataFrame()
persistence['Persistence Accuracy'] = pmodel.values
for i in range(1, 7):
    persistence[str(i)+' Day Forecast'] = pd.Series(fac['today+'+str(i)].values)
persistence.index = dates_index[:len(dates_index)-1]

# Assign RMSE value for pmodel
persistence_rmse = np.sqrt(mean_squared_error(pmodel, fac['today+0'][:len(fac)-1]))

#################################
# Accuracy
################################

# Create Accuracy Table
tf.index = pd.to_datetime(tf.index)  # make index a datetime.

# Accuracy Mechanism: Compare forecast to actual Temp.
fac = pd.DataFrame()
counter = list(range(len(tf)))
columns = list(tf.columns)

for i in counter:
    # 7 day forecast inc today, so len can't exceed 7
    if i < 7:
        window = i
        j = i
    else:
        window = 6
        j = 6

    # Start date at most recent row
    actual_date = tf.index[-1]  # start with the last day
    window_date = actual_date - pd.DateOffset(
        days=window)  # Number of days in the past can't be more than those forecast
    row_0 = tf.index[0]  # We want to end when window date is equal to row_0.

    tf_list = []  # temporary holder of weeks values.
    while window_date >= row_0:
        true_temp = int(tf.loc[actual_date][0])  # True temperature recorded on day
        predicted_temp = int(tf.loc[window_date][window])  # data predicted on value of window
        difference = true_temp - predicted_temp
        # loop
        actual_date -= pd.DateOffset(days=1)  # take off 1 day.
        window_date -= pd.DateOffset(days=1)  # take off 1 day.
        # append
        tf_list.append(difference)
        # Add list to df as series
    fac[columns[j]] = pd.Series(tf_list[::-1])  # Add list backwards.

fac.index = dates_index
tf.index = dates_index

#################################
# VS RMSE
################################

persistence_vs = pd.DataFrame()
persistence_vs['1 Day Error'] = accuracy['1 Day Forecast'] - persistence_rmse
persistence_vs['2 Day Error'] = accuracy['2 Day Forecast'] - persistence_rmse
persistence_vs['3 Day Error'] = accuracy['3 Day Forecast'] - persistence_rmse
persistence_vs['4 Day Error'] = accuracy['4 Day Forecast'] - persistence_rmse
persistence_vs['5 Day Error'] = accuracy['5 Day Forecast'] - persistence_rmse
persistence_vs['6 Day Error'] = accuracy['6 Day Forecast'] - persistence_rmse

persistence_vs.index = ["BOM Error vs Persistence Error"]
#################################
#################################
# Display
################################
#################################

# App Begins
st.write("""
# Melbourne Forecast Accuracy

### Evaluating the accuracy of the Bureau of Meteorology 6 day forecast.
The following information is an examination of the Bureau of Meteorology's 6-day forecast.

It's hard to know if a forecast is good because it depends on how *'good'* is measured.
Is accurate to within 1º good? How about within 5º?   

This project is evaluating how accurate forecasts are, depending on how many days away the forecast is.
So instead of comparing to the historical temperatures, this will just look at how much the forecast changes as the date gets closer.   

Firstly, it looks at the error (Root Mean Squared Error or RMSE) of how correct/incorrect forecasts are by day (eg: how similar is the 3-day forecast compared to the same day forecast).    
Secondly, it evaluates at how accurate the forecast is against a naive forecasting approach, in this case the persistence model which is simply "The weather tomorrow will be the same as today" ie: the temperature will persist. 
This is a good way to evaluate model accuracy as this form of forecast naturally varies with changing weather, which makes it comparable to the difficulties typically faced in weather forecasting.
""")

st.write("""
#### Summary of Data
""")
# Summary
st.text(f"Today\'s date is: {today}")
st.text(f"New forecasts:	{len(db)}, Starting on: {db['issue'][0]}, Ending on: {db['issue'][len(db)-1][:10]}")
todays_forecast = f"#### Today's forecast: \n >*{db['extended_text'][-1]}*"
st.markdown(todays_forecast)

# Display Previous Data Heatmap Description
st.write("""
#### 1.1: Heatmap of previous Max-Temp forecasts.
Reading this chart, each value shifts one space to the left for each descending row as the 6-day forecast becomes day 5, 4, 3 .. etc. Today + 6 on the first row becomes Today+5 on the second row, Today+4 on the third row. 
As this project only uses forecast data, (no past recorded temperatures), Today + 0 is still a forecast. Working with historical data will be added in future versions, but it is for the most part, Today+0 is very accurate and serves the purposes of this project.
# """)

# Previous Data Heatmap
heat_map(tf, "7 Day Forecasts From BOM (Descending to the left)")

# Variation Heatmap Description
st.write("""
#### 1.2: Heatmap of Forecast Accuracy   
This chart shows how accurate the forecasts were against the actual temperature. There is no need to read down and to the left, the cells show how accurate the forecast was, once the date of the forecast has reached Today+0. As the days in the bottom right corner have not occurred yet, (this coming week) there is no way to evaluate the accuracy.
""")

# Variation Heatmap
heat_map(fac, "Forecast Variation (0 = 100% Accurate)")

# RMSE Values
st.write("""
#### 1.3: RMSE Accuracy of predictions
This table shows how many degrees the forecasts is likely to fall between.
so for a value of 2, the forecasts is likely to be within 2ºC higher or lower of that which they forecast.
# """)
st.dataframe(accuracy)


# Chart accuracy
st.write("""
#### 1.4: Line Chart of Forecast Accuracy
As the forecast moves further into the future, the average forecast error increases.
""")
st.line_chart(accuracy.T)

# PART 2
st.write("""
## PART 2: Persistence
Evaluating against Weather(t+i) = Weather(t).
This compares the accuracy of the forecast against the naive model of "Tomorrow's max-temp will be the same as today". This comparison shows how much the weather changes according to the day before it. As cool and warm fronts come through, the temperature changes significantly. This is where the persistence model is a weak predictor.
""")

st.write("""
#### 2.1: Persistence Accuracy +/- ºC above and below forecast
""")

persistence_info = f"#### Persistence RMSE: \n **{persistence_rmse}** \n >This is the current mean error of the persistence model."
st.subheader("Persistence Mean Error")
st.markdown(persistence_info)

st.write("""
#### 2.2: Persistence Variation by Day 
Displayed as a bar chart
""")
# Persistence DataFrame
st.bar_chart(pmodel)

# Variation Heatmap Description
st.write("""
#### 2.3: Heatmap of Persistence Accuracy   
Here you can compare how accurate the persistence model was vs the BOM forecast for any given day.
As the days get further away, the accuracy of the persistence and BOM forecast becomes more even.
""")
# Display a Heatmap of the Persistence Accuracy
heat_map(persistence, "Persistence (far left) vs Forecast")

# Persistence vs
st.write("""
#### 2.4: RMSE Accuracy of Persistence predictions
The error for persistence should be constantly changing depending on the swing in the weather,
however 
# """)
st.dataframe(persistence_vs)


# Chart accuracy
st.write("""
#### 2.5: BOM VS Persistence
This chart shows (Persistence RMSE - BOM RMSE), in other words, how much more accurate is the BOM than Persistence.
As the forecast error increases with each day further into the future that is predicted, the difference in error between the models becomes smaller.
Here you can see see that for 1 day into the future, the BOM is over +/-3º more accurate than a persistence model, but by the 6th day, it's less than 1º more accurate.
""")
st.bar_chart(persistence_vs.T)

st.write(""" 
It appears that the persistence model may be a good benchmark for forecasts greater than 6 days away.
It also hints at why the BOM doesn't typically offer longer forecasts like a 10 or 14 day forecast.
To summarise, it looks like the Bureau is doing a good job of predicting something notoriously difficult to forecast. 
""")
        
st.write("""
#### DATA Sources 
- Data Comes From: ftp://ftp.bom.gov.au/anon/gen/fwo/
- Melbourne Forecast File: ftp://ftp.bom.gov.au/anon/gen/fwo/IDV10450.xml

The url for the BOM API is:
https://api.weather.bom.gov.au/v1/locations/r1r143/forecasts/daily   
Be Aware that the update is adjusted every 10 mins.
""")

st.write(""" 
#### Please watch this space for future development.
# """)