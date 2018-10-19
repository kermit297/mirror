import Tkinter as tk
import time
import urllib2
import json
import numpy as np
import pandas as pd
from subprocess import call
from datetime import datetime, timedelta
from PIL import ImageTk, Image


class Application:
    def __init__(self):

        with open('config.json') as data_file:
            config = json.load(data_file)

        self.dsn_api_key = config['dsn_api_key']
        self.wu_api_key = config['wu_api_key']

        self.master = tk.Tk()
        self.master_f = tk.Frame(self.master, bg="black")
        self.master_f.pack()
        #for i in range(2):
        #    self.master.grid_rowconfigure(i, weight=1)
        for j in range(3):
            self.master_f.grid_columnconfigure(j, weight=1)

        self.weather = Weather(self.master_f)
        # self.weather.frame.grid(row=0, column=0, sticky="NW")
        self.weather.frame.pack(side="top", anchor="nw")

        self.astro = Astro(self.master_f)
        # self.astro.frame.grid(row=0, column=1, sticky="N")
        self.astro.frame.pack(side="top", anchor="n")

        self.dttm = Dttm(self.master_f)
        # self.dttm.frame.grid(row=0, column=2, sticky="NE")
        self.dttm.frame.pack(side="top", anchor="ne")

        self.forecast = Forecast(self.master_f, self.wu_api_key, self.dsn_api_key)
        # self.forecast.frame.grid(row=1, column=0, sticky="SW", columnspan=2)
        self.forecast.frame.pack(side="bottom", anchor="sw")

        self.calendar = Calendar(self.master_f)
        # self.calendar.frame.grid(row=1, column=2, sticky="SE")
        self.calendar.frame.pack(side="bottom", anchor="se")


class Dttm:
    def __init__(self, master):
        self.frame = tk.Frame(master, bg="black")
        self.time = tk.StringVar()
        self.time_label = tk.Label(self.frame, textvariable=self.time, font=('Helvetica', 30), bg="black", fg="white")
        self.time_label.grid(row=0, column=0, sticky="E")
        self.date = tk.StringVar()
        self.date_label = tk.Label(self.frame, textvariable=self.date, bg="black", fg="white")
        self.date_label.grid(row=1, column=0, sticky="E")
        self.update()

    def update(self):
        self.time.set(time.strftime("%H:%M"))
        self.date.set(time.strftime("%Y-%m-%d"))
        self.frame.after(1000, self.update)


class Weather:
    def __init__(self, master):
        self.frame = tk.Frame(master, bg= "black")
        self.weather = tk.Label(self.frame, text="18 stopni C", bg="black", fg="white")
        self.weather.pack()


class Astro:
    def __init__(self, master):
        self.frame = tk.Frame(master, bg= "black")
        self.sun_rise = tk.Label(self.frame, text="wschod: 06:21", bg="black", fg="white")
        self.sun_set = tk.Label(self.frame, text="zachod: 17:55", bg="black", fg="white")
        self.sun_rise.pack()
        self.sun_set.pack()


class Forecast:
    def __init__(self, master, wu_api_key, dsn_api_key):
        self.wu_api_key = wu_api_key
        self.dsn_api_key = dsn_api_key
        self.frame = tk.Frame(master, bg= "black")
        self.forecast_label = tk.Label(self.frame, bg="black", fg="white")
        self.update()

    def update(self):
        self.get_historical(self.wu_api_key)
        self.get_forecast(self.dsn_api_key)
        self.plot_forecast_in_r()
        self.refresh_plot_label()
        self.frame.after(1000*60*30, self.update)

    def get_historical(self, wu_api_key):
        print("[getting historical data]")
        date = datetime.now()
        min_dt = (date - timedelta(days=15)).strftime("%m%d")
        max_dt = (date + timedelta(days=15)).strftime("%m%d")
        url = "http://api.wunderground.com/api/{0}/planner_{1}{2}/q/PL/Warsaw.json".format(wu_api_key, min_dt, max_dt)
        history = json.load(urllib2.urlopen(url))['trip']
        self.hist_temp_min = (int(history['temp_low']['avg']['C'])+int(history['temp_low']['min']['C']))/2
        self.hist_temp_max = (int(history['temp_high']['avg']['C'])+int(history['temp_high']['max']['C']))/2

        d_hist = pd.DataFrame({'temp_min': [self.hist_temp_min], 'temp_max': [self.hist_temp_max]})
        d_hist.to_feather('d_hist.feather')
        print("[DONE]")

    def get_forecast(self, dsn_api_key):
        print("[getting forecast data]")
        #url = "http://api.wunderground.com/api/{0}/hourly10day/lang:PL/q/PL/Warsaw.json".format(api_key)
        #hourly_forecast = json.load(urllib2.urlopen(url))['hourly_forecast']

        url = "https://api.darksky.net/forecast/{0}/52.200521,20.963080?lang=pl&units=si".format(dsn_api_key)
        forecast = json.load(urllib2.urlopen(url))

        hr_forecast = forecast['hourly']['data']

        n = len(hr_forecast)

        self.dttm = np.zeros(n)
        self.temp = np.zeros(n)
        self.humidity = np.zeros(n)
        self.cloudCov = np.zeros(n)
        self.precipProb = np.zeros(n)
        self.precipInt = np.zeros(n)
        #self.precipType = np.empty(n, dtype = np.object)

        for i in range(n):
            self.dttm[i] = hr_forecast[i]['time']
            self.temp[i] = hr_forecast[i]['temperature']
            self.humidity[i] = hr_forecast[i]['humidity']
            self.cloudCov[i] = hr_forecast[i]['cloudCover']
            self.precipProb[i] = hr_forecast[i]['precipProbability']
            self.precipInt[i] = hr_forecast[i]['precipIntensity']
            #self.precipType = hr_forecast[i]['precipType']

        d_forecast = forecast['daily']['data']
        n = len(d_forecast)

        self.d_dttm = np.zeros(n)
        self.d_sunrise = np.zeros(n)
        self.d_sunset = np.zeros(n)
        for i in range(n):
            self.d_dttm[i] = d_forecast[i]['time']
            self.d_sunrise[i] = d_forecast[i]['sunriseTime']
            self.d_sunset[i] = d_forecast[i]['sunsetTime']

        d = pd.DataFrame(
            {'dttm': self.dttm, 'temp': self.temp, 'humidity': self.humidity, 'cloud_cov': self.cloudCov,
             'precipInt': self.precipInt, 'precipProb': self.precipProb})
        d.to_feather('d.feather')

        d_d = pd.DataFrame({'dttm': self.d_dttm, 'sunrise': self.d_sunrise, 'sunset': self.d_sunset})
        d_d.to_feather('d_daily.feather')

        print("[DONE]")

    def plot_forecast_in_r(self):
        print("[plotting]")
        call(["Rscript", "plot.R"])
        print("[plotting DONE]")

    def refresh_plot_label(self):
        img = ImageTk.PhotoImage(Image.open("p.png"))
        self.forecast_label = tk.Label(self.frame, image=img)
        self.forecast_label.image = img
        self.forecast_label.grid(row=0, column=0, sticky="NSEW")




class Calendar:
    def __init__(self, master):
        self.frame = tk.Frame(master, bg="black")
        self.calendar = tk.Label(self.frame, text="CALENDAR", bg="black", fg="white")
        self.calendar.pack()


app = Application()
app.master.mainloop()
