import tkinter as tk
import time
import urllib.request
import json
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import locale

locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')


class Application(tk.Tk):
    def __init__(self):

        tk.Tk.__init__(self)
        # logging.info("Application initialization")
        with open('config.json') as data_file:
            config = json.load(data_file)

        self.dsn_api_key = config['dsn_api_key']
        self.wu_api_key = config['wu_api_key']

        self.weather_data = WeatherData(self.dsn_api_key, self.wu_api_key)
        #
        # self.master = tk.Tk()
        # self.master_frame = tk.Frame(self.master, bg="black")
        # self.master_frame.pack(fill="both", expand=1)
        #
        self.top_frame = tk.Frame(self, bg="black")
        self.top_frame.pack(side="top", fill="both")
        self.bottom_frame = tk.Frame(self, bg="black")
        self.bottom_frame.pack(side="bottom", fill="both", expand=1)

        self.current_weather_frame = CurrentWeatherFrame(self.top_frame)
        self.current_weather_frame.pack(side="left", anchor="nw", fill="both")

        self.dttm_frame = DttmFrame(self.top_frame)
        self.dttm_frame.pack(side="right", anchor="ne", fill="both")
        #
        self.astro_frame = AstroFrame(self.top_frame)
        self.astro_frame.frame.pack(side="top", anchor="n", fill="both")
        #
        self.forecast_frame = ForecastFrame(self.bottom_frame)
        self.forecast_frame.pack(side="left", anchor="sw")
        #
        # self.calendar = Calendar(self.bottom_frame)
        # self.calendar.frame.pack(side="right", anchor="se")
        self.refresh_data()

    def refresh_data(self):
        # logging.warning("Application refresh")
        self.weather_data.get_data()
        self.current_weather_frame.refresh(getattr(self.weather_data, 'data_curr_temp'))
        self.forecast_frame.redraw(self.weather_data.data)
        self.astro_frame.refresh(self.weather_data.data['daily_sunrise'][0], self.weather_data.data['daily_sunset'][0])
        self.after(30*60*1000, self.refresh_data)


class WeatherData:
    def __init__(self, dsn_api_key, wu_api_key):

        self.dsn_api_key = dsn_api_key
        self.wu_api_key = wu_api_key

        self.data = {}

        self.data_curr_temp = float()

        self.data['hr_dttm'] = list()
        self.data['hr_temp'] = list()
        self.data['hr_cloud'] = list()
        self.data['hr_precip_int'] = list()
        self.data['hr_precip_prob'] = list()
        self.data['hr_precip_type'] = list()

        self.data['daily_sunrise'] = list()
        self.data['daily_sunset'] = list()

        self.data['hist_temp_min'] = float()
        self.data['hist_temp_max'] = float()

    def get_data(self):
        url = "https://api.darksky.net/forecast/{}/52.200521,20.963080?lang=pl&units=si".format(self.dsn_api_key)
        html = urllib.request.urlopen(url).read()
        forecast = json.loads(html.decode('utf-8'))

        # current
        self.data_curr_temp = forecast['currently']['temperature']

        # forecast
        n = len(forecast['hourly']['data'])
        for i in range(n):
            self.data['hr_dttm'].append(datetime.fromtimestamp(forecast['hourly']['data'][i]['time']))
            self.data['hr_temp'].append(forecast['hourly']['data'][i]['temperature'])
            self.data['hr_cloud'].append(forecast['hourly']['data'][i]['cloudCover'])
            self.data['hr_precip_int'].append(forecast['hourly']['data'][i]['precipIntensity'])
            self.data['hr_precip_prob'].append(forecast['hourly']['data'][i]['precipProbability'])
            try:
                self.data['hr_precip_type'].append(forecast['hourly']['data'][i]['precipType'])
            except:
                self.data['hr_precip_type'].append('')

        # sun
        n = len(forecast['daily']['data'])
        for i in range(n):
            self.data['daily_sunrise'].append(datetime.fromtimestamp(forecast['daily']['data'][i]['sunriseTime']))
            self.data['daily_sunset'].append(datetime.fromtimestamp(forecast['daily']['data'][i]['sunsetTime']))

        # historical
        date = datetime.now()
        min_dt = (date - timedelta(days=15)).strftime("%m%d")
        max_dt = (date + timedelta(days=15)).strftime("%m%d")
        url = "http://api.wunderground.com/api/{0}/planner_{1}{2}/q/PL/Warsaw.json".format(self.wu_api_key, min_dt, max_dt)
        html = urllib.request.urlopen(url).read()
        history = json.loads(html.decode('utf-8'))['trip']
        self.data['hist_temp_min'] = (float(history['temp_low']['avg']['C']) + float(history['temp_low']['min']['C'])) / 2
        self.data['hist_temp_max'] = (float(history['temp_high']['avg']['C']) + float(history['temp_high']['max']['C'])) / 2


class DttmFrame(tk.Frame):
    def __init__(self, master):
        # logging.debug("Frame Dttm initialization")
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


class CurrentWeatherFrame(tk.Frame):
    def __init__(self, master):
        # logging.debug("Frame Weather initialization")
        tk.Frame.__init__(self, master, bg='black')
        self.temp = tk.StringVar()
        self.weather = tk.Label(self, textvariable=self.temp, font=('Helvetica', 100), bg="black", fg="white")
        self.weather.pack(anchor="nw", ipadx=20, ipady=10)

    def refresh(self, temp):
        # logging.debug("Frame Weather refresh")
        temp = round(temp/0.5)*0.5  # round to nearest 0.5
        self.temp.set(str(temp)+u'\N{DEGREE SIGN}'+'C')


class AstroFrame:
    def __init__(self, master):
        # logging.debug("Frame Astro initialization")
        self.frame = tk.Frame(master, bg= "black")
        self.sunrise = tk.StringVar()
        self.sunset = tk.StringVar()
        self.sunrise_label = tk.Label(self.frame, textvariable=self.sunrise, bg="black", fg="white")
        self.sunset_label = tk.Label(self.frame, textvariable=self.sunset, bg="black", fg="white")
        self.sunrise_label.pack(side="top", anchor="n", ipady=0)
        self.sunset_label.pack(side="top", anchor="n")

    def refresh(self, sunrise, sunset):
        sunrise = sunrise.strftime('%H:%M')
        sunset = sunset.strftime('%H:%M')
        self.sunrise.set("Wschod: "+sunrise)
        self.sunset.set("Zachod: "+sunset)


class ForecastFrame(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, bg="black")
        #self.forecast_label = tk.Label(self, bg="black")
        #self.forecast_label.pack(side="bottom")

    def redraw(self, data):
        dttm_min = min(data['hr_dttm'])
        dttm_max = max(data['hr_dttm'])
        dttm_width = timedelta(hours=1)

        temp_min = min(data['hr_temp'])
        temp_max = max(data['hr_temp'])
        temp_base = temp_min - 2

        scale_factor = (temp_max - temp_min) / 8

        norm_temp = Normalize(vmin=data['hist_temp_min'], vmax=data['hist_temp_max'], clip=True)
        mapper_temp = cm.ScalarMappable(norm=norm_temp, cmap=cm.viridis)  # coolwarm

        plt.style.use('dark_background')

        fig, ax = plt.subplots(1, figsize=(12, 4), dpi=100)

        for s1, s2 in zip(data['daily_sunrise'], data['daily_sunset']):
            rect_daylight = patches.Rectangle((s1, temp_base),
                                              (s2 - s1),
                                              # (s2-s1).total_seconds()/(60*60*24),
                                              temp_max + 4 - temp_base,
                                              edgecolor='none', facecolor='yellow', alpha=0.1)
            ax.add_patch(rect_daylight)

            rect_daylight_ext = patches.Rectangle((s1 - timedelta(hours=0.5), temp_base),
                                                  (s2 - s1 + timedelta(hours=1)),
                                                  temp_max + 4 - temp_base,
                                                  edgecolor='none', facecolor='yellow', alpha=0.1)
            ax.add_patch(rect_daylight_ext)

        for x, t, c, p, pp, pt in zip(data['hr_dttm'], data['hr_temp'], data['hr_cloud'],
                                      data['hr_precip_int'], data['hr_precip_prob'], data['hr_precip_type']):

            if t <= data['hist_temp_min']:
                tcol = data['hist_temp_min']
            elif t >= data['hist_temp_max']:
                tcol = data['hist_temp_max']
            else:
                tcol = t

            rect_temp = patches.Rectangle((x, temp_base), dttm_width, t - temp_base, edgecolor='none',
                                          facecolor=mapper_temp.to_rgba(tcol))
            ax.add_patch(rect_temp)

            if t < (temp_max + temp_min) / 2:
                cl = 'white'
            else:
                cl = 'black'

            ax.text(x + timedelta(hours=0.5), t - 0.1, str(round(t)), horizontalalignment='center',
                    verticalalignment='top', color=cl)
            c = c * scale_factor
            rect_cloud = patches.Rectangle((x, temp_max + 3 - c), dttm_width, c * 2, edgecolor='none', facecolor='w')
            ax.add_patch(rect_cloud)

            pp = pp ** 0.2
            if pt == "rain":
                col = "aqua"
            elif pt == "snow":
                col = "snow"
            else:
                col = "red"

            rect_precip = patches.Rectangle((x, temp_base), dttm_width, p * scale_factor * 10, edgecolor='none',
                                            facecolor=col, alpha=pp)
            ax.add_patch(rect_precip)

        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%d-%m-%Y %A'))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
        ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
        ax.grid(axis='x', linestyle='--')

        ax.set_xlim([dttm_min - timedelta(hours=0), dttm_max + timedelta(hours=1)])
        ax.set_ylim([temp_min - 2, temp_max + 4])

        ax.get_yaxis().set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)

        canvas = FigureCanvasTkAgg(fig, master=self)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1)


class CalendarFrame:
    def __init__(self, master):
        # logging.debug("Frame Calendar initialization")
        self.frame = tk.Frame(master, bg="black")
        self.calendar = tk.Label(self.frame, text="CALENDAR", bg="black", fg="white")
        self.calendar.pack(side="bottom", anchor="se")


app = Application()
app.mainloop()
