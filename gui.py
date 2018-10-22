import Tkinter as tk
import time
import urllib2
import json
import numpy as np
import pandas as pd
from subprocess import call
from datetime import datetime, timedelta
from PIL import ImageTk, Image
import locale

from PIL.ImageTk import PhotoImage

locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')


class Application(tk.Tk):
    def __init__(self):

        tk.Tk.__init__(self)

        with open('config.json') as data_file:
            config = json.load(data_file)

        self.dsn_api_key = config['dsn_api_key']
        self.wu_api_key = config['wu_api_key']

        self.weather_data_hist = WeatherDataHist(self.wu_api_key)
        self.weather_data_forecast = WeatherDataForecast(self.dsn_api_key)
        #
        # self.master = tk.Tk()
        # self.master_frame = tk.Frame(self.master, bg="black")
        # self.master_frame.pack(fill="both", expand=1)
        #
        self.top_frame = tk.Frame(self, bg="black")
        self.top_frame.pack(side="top", fill="both")
        self.bottom_frame = tk.Frame(self, bg="black")
        self.bottom_frame.pack(side="bottom", fill="both", expand=1)

        self.weather = Weather(self.top_frame)
        self.weather.pack(side="left", anchor="nw", fill="both")

        self.dttm = Dttm(self.top_frame)
        self.dttm.pack(side="right", anchor="ne", fill="both")
        #
        # self.astro = Astro(self.top_frame)
        # self.astro.frame.pack(side="top", anchor="n", fill="both")
        #
        self.forecast = Forecast(self.bottom_frame)
        self.forecast.pack(side="left", anchor="sw")
        #
        # self.calendar = Calendar(self.bottom_frame)
        # self.calendar.frame.pack(side="right", anchor="se")
        self.refresh_data()

    def refresh_data(self):
        self.weather_data_forecast.get_data()
        self.weather_data_forecast.save_data()
        self.weather_data_hist.get_data()
        self.weather_data_hist.save_data()
        self.weather.refresh(getattr(self.weather_data_forecast, 'curr_temp'))
        self.forecast.refresh()


class WeatherDataHist:
    def __init__(self, wu_api_key):
        self.wu_api_key = wu_api_key
        self.data = {}
        self.hist_temp_min = int()
        self.hist_temp_max = int()

    def get_data(self):
        date = datetime.now()
        min_dt = (date - timedelta(days=15)).strftime("%m%d")
        max_dt = (date + timedelta(days=15)).strftime("%m%d")
        url = "http://api.wunderground.com/api/{0}/planner_{1}{2}/q/PL/Warsaw.json".format(self.wu_api_key, min_dt, max_dt)
        self.data = history = json.load(urllib2.urlopen(url))['trip']
        self.hist_temp_min = (int(history['temp_low']['avg']['C'])+int(history['temp_low']['min']['C']))/2
        self.hist_temp_max = (int(history['temp_high']['avg']['C'])+int(history['temp_high']['max']['C']))/2

    def save_data(self):
        d_hist = pd.DataFrame({'temp_min': [self.hist_temp_min], 'temp_max': [self.hist_temp_max]})
        d_hist.to_feather('d_hist.feather')


class WeatherDataForecast:
    def __init__(self, dsn_api_key):
        # dictionaries of names in the self object and in api data
        self.hr_vars = {'hr_dttm': 'time', 'hr_temp': 'temperature', 'hr_humidity': 'humidity',
                        'hr_cloudCov': 'cloudCover', 'hr_precipProb': 'precipProbability',
                        'hr_precipInt': 'precipIntensity'}
        self.d_vars = {'d_dttm': 'time', 'd_sunrise': 'sunriseTime', 'd_sunset': 'sunsetTime'}
        self.curr_vars = {'curr_temp': 'temperature', 'curr_summary': 'summary'}
        self.dsn_api_key = dsn_api_key

    def get_data(self):

        url = "https://api.darksky.net/forecast/{0}/52.200521,20.963080?lang=pl&units=si".format(self.dsn_api_key)
        forecast = json.load(urllib2.urlopen(url))

        hr_forecast = forecast['hourly']['data']
        n = len(hr_forecast)
        for v_app, v_net in self.hr_vars.items():
            tmp = np.zeros(n)
            for i in range(n):
                tmp[i] = hr_forecast[i][v_net]
            setattr(self, v_app, tmp)

        d_forecast = forecast['daily']['data']
        n = len(d_forecast)
        for v_app, v_net in self.d_vars.items():
            tmp = np.zeros(n)
            for i in range(n):
                tmp[i] = d_forecast[i][v_net]
            setattr(self, v_app, tmp)

        d_current = forecast['currently']
        for v_app, v_net in self.curr_vars.items():
            setattr(self, v_app, d_current[v_net])

    def save_data(self):
        d_hr = {}  # an empty dictionary, will be converted to data frame
        for hr_var, _ in self.hr_vars.items():  # get variable names from dictionary
            d_hr[hr_var] = getattr(self, hr_var)  # add list to new dictionary
        d_hr = pd.DataFrame(d_hr)  # convert dictionary to pd
        d_hr.to_feather('d_hr.feather')  # save feather file

        d_d = {}
        for d_var, _ in self.d_vars.items():
            d_d[d_var] = getattr(self, d_var)
        d_d = pd.DataFrame(d_d)
        d_d.to_feather('d_d.feather')


class Dttm(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg = 'black')
        #self.frame = tk.Frame(master, bg="black")

        self.time = tk.StringVar()
        self.time_label = tk.Label(self, textvariable=self.time, font=('Helvetica', 100), bg="black", fg="white")
        self.time_label.pack(side="top", anchor="e")

        # self.week_day = tk.StringVar()
        # self.week_day_label = tk.Label(self.frame, textvariable=self.week_day, font=('Helvetica', 50), bg="black", fg="white")
        # self.week_day_label.pack(side="top", anchor="e")

        self.date = tk.StringVar()
        self.date_label = tk.Label(self, textvariable=self.date, font=('Helvetica', 50), bg="black", fg="white")
        self.date_label.pack(side="top", anchor="e")
        self.refresh()

    def refresh(self):
        self.time.set(time.strftime("%H:%M"))
        # self.week_day.set(time.strftime("%A"))
        self.date.set(time.strftime("%A, %d. %b"))
        self.after(1000, self.refresh)


class Weather(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg='black')
        self.temp = tk.StringVar()
        self.weather = tk.Label(self, textvariable=self.temp, font=('Helvetica', 50), bg="black", fg="white")
        self.weather.pack(anchor="nw")

    def refresh(self, temp):
        self.temp.set(temp)


class Astro:
    def __init__(self, master):
        self.frame = tk.Frame(master, bg= "black")
        self.sun_rise = tk.Label(self.frame, text="wschod: 06:21", bg="black", fg="white")
        self.sun_set = tk.Label(self.frame, text="zachod: 17:55", bg="black", fg="white")
        self.sun_rise.pack(side="top", anchor="n")
        self.sun_set.pack(side="top", anchor="n")


class Forecast(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="black")
        self.forecast_label = tk.Label(self, bg="black", fg="black")
        self.forecast_label.pack(side="bottom")

    def refresh(self):
        call(["Rscript", "plot.R"])
        img = ImageTk.PhotoImage(Image.open("p.png"))
        self.forecast_label.image = img
        # TODO: doesn't work
        # self.forecast_label.pack(side="bottom")
        # self.after(1000*10, self.refresh())


class Calendar:
    def __init__(self, master):
        self.frame = tk.Frame(master, bg="black")
        self.calendar = tk.Label(self.frame, text="CALENDAR", bg="black", fg="white")
        self.calendar.pack(side="bottom", anchor="se")


app = Application()
app.mainloop()
