from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import matplotlib.dates as mdates
import time
import locale
import urllib.request
import json
from datetime import timedelta, datetime
import matplotlib.pyplot as plt

plt.style.use('dark_background')

locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')


class Application(QApplication):
    def __init__(self):
        QApplication.__init__(self, [])

        self.window = Window()
        p = self.window.palette()
        p.setColor(self.window.backgroundRole(), Qt.black)
        self.window.setPalette(p)
        self.window.show()


class Window(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        uic.loadUi("mirror.ui", self)

        plt_layout = QVBoxLayout()
        self.frame_bottom_1.setLayout(plt_layout)
        self.fig = Figure(figsize=(5, 3))
        self.canvas = FigureCanvas(self.fig)
        plt_layout.addWidget(self.canvas)
        self.ax = self.canvas.figure.subplots()

        with open('config.json') as data_file:
            config = json.load(data_file)

        self.dsn_api_key = config['dsn_api_key']
        self.wu_api_key = config['wu_api_key']

        self.weather_data = WeatherData(self.dsn_api_key, self.wu_api_key)
        self.update_data()

        self.timer_clock = QTimer()
        self.timer_clock.timeout.connect(self.update_dttm)
        self.timer_clock.start(1000)

        self.timer_plot = QTimer()
        self.timer_plot.timeout.connect(self.update_data)
        self.timer_plot.start(1000*60*30)

    def update_dttm(self):
        self.label_time.setText(time.strftime("%H:%M:%S"))
        self.label_time.setStyleSheet('QLabel { color: white }')
        self.label_date.setText(time.strftime("%A, %d. %b"))
        self.label_date.setStyleSheet('QLabel { color: white }')

        now = datetime.strptime(datetime.now().strftime('%Y%m%d %H:%M:%S'), '%Y%m%d %H:%M:%S')
        sunrise = self.weather_data.data['daily_sunrise'][0]
        sunset = self.weather_data.data['daily_sunset'][0]

        if now < sunrise:
            timeTo = datetime.strptime(str(sunrise - now), '%H:%M:%S').strftime('%H:%M')
            txtTo = "Wschód Słońca za: "
        elif now > sunrise and now <= sunset:
            timeTo = datetime.strptime(str(sunset - now), '%H:%M:%S').strftime('%H:%M')
            txtTo = "Zachód Słońca za: "
        elif now > sunset:
            timeTo = datetime.strptime(str(now-sunset), '%H:%M:%S').strftime('%H:%M')
            txtTo = "Czas po zachodzie Słońca: "

        self.label_time_to.setText(txtTo)
        self.label_time_to.setStyleSheet('QLabel { color: white }')
        self.label_time_to_value.setText(timeTo)
        self.label_time_to_value.setStyleSheet('QLabel { color: white }')

    def update_data(self):
        self.weather_data.get_data()
        self.plot_forecast()

        temp = round(self.weather_data.data_curr_temp / 0.5) * 0.5  # round to nearest 0.5
        self.label_temp.setText(str(temp) + u'\N{DEGREE SIGN}' + 'C')
        self.label_temp.setStyleSheet('QLabel { color: white }')

        self.label_summary.setText(self.weather_data.data_curr_summary)
        self.label_summary.setStyleSheet('QLabel { color: white }')

        sunrise = self.weather_data.data['daily_sunrise'][0]
        sunset = self.weather_data.data['daily_sunset'][0]
        self.label_sunrise.setText(sunrise.strftime('%H:%M') + " - " + sunrise.strftime('%H:%M'))
        self.label_sunrise.setStyleSheet('QLabel { color: white }')

        self.label_day_len.setText(datetime.strptime(str(sunset - sunrise), "%H:%M:%S").strftime('%H:%M'))
        self.label_day_len.setStyleSheet('QLabel { color: white }')

        self.label_humidity.setText(str(int(round(self.weather_data.data_curr_humidity, 2)*100)) + "%")
        self.label_humidity.setStyleSheet('QLabel { color: white }')
        self.label_cloud.setText(str(int(round(self.weather_data.data_curr_cloudCover, 2)*100)) + "%")
        self.label_cloud.setStyleSheet('QLabel { color: white }')
        self.label_precip.setText(str(int(round(self.weather_data.data_curr_precipProbability, 2)*100)) + "%")
        self.label_precip.setStyleSheet('QLabel { color: white }')

    def plot_forecast(self):
        data = self.weather_data.data
        self.ax.clear()

        dttm_min = min(data['hr_dttm'])
        dttm_max = max(data['hr_dttm'])
        dttm_width = timedelta(hours=1)

        temp_min = min(data['hr_temp'])
        temp_max = max(data['hr_temp'])
        temp_base = temp_min - 2

        scale_factor = (temp_max - temp_min) / 8

        norm_temp = Normalize(vmin=data['hist_temp_min'], vmax=data['hist_temp_max'], clip=True)
        mapper_temp = cm.ScalarMappable(norm=norm_temp, cmap=cm.viridis)  # coolwarm

        for s1, s2 in zip(data['daily_sunrise'], data['daily_sunset']):
            rect_daylight = patches.Rectangle((s1, temp_base),
                                              (s2 - s1),
                                              # (s2-s1).total_seconds()/(60*60*24),
                                              temp_max + 4 - temp_base,
                                              edgecolor='none', facecolor='yellow', alpha=0.6)
            self.ax.add_patch(rect_daylight)

            rect_daylight_ext = patches.Rectangle((s1 - timedelta(hours=0.5), temp_base),
                                                  (s2 - s1 + timedelta(hours=1)),
                                                  temp_max + 4 - temp_base,
                                                  edgecolor='none', facecolor='yellow', alpha=0.2)
            self.ax.add_patch(rect_daylight_ext)

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
            self.ax.add_patch(rect_temp)

            if t < (data['hist_temp_min'] + data['hist_temp_max']) / 2:
                cl = 'white'
            else:
                cl = 'black'

            self.ax.text(x + timedelta(hours=0.5), t - 0.1, str(round(t)),
                                            horizontalalignment='center',
                                            verticalalignment='top', color=cl)
            c = c * scale_factor
            rect_cloud = patches.Rectangle((x, temp_max + 3 - c), dttm_width, c * 2, edgecolor='none', facecolor='w')
            self.ax.add_patch(rect_cloud)

            pp = pp ** 0.2
            if pt == "rain":
                col = "aqua"
            elif pt == "snow":
                col = "snow"
            else:
                col = "red"

            rect_precip = patches.Rectangle((x, temp_base), dttm_width, p ** 0.5 * scale_factor * 5, edgecolor='none',
                                            facecolor=col, alpha=pp)
            self.ax.add_patch(rect_precip)

        self.ax.xaxis.set_major_locator(mdates.DayLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('\n%d-%m-%Y %A'))
        self.ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
        self.ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))
        self.ax.grid(axis='x', linestyle='--')

        self.ax.set_xlim([dttm_min - timedelta(hours=0), dttm_max + timedelta(hours=1)])
        self.ax.set_ylim([temp_min - 2, temp_max + 4])

        self.ax.get_yaxis().set_visible(False)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['bottom'].set_visible(False)
        self.ax.spines['left'].set_visible(False)

        self.fig.tight_layout()

        self.ax.figure.canvas.draw()


class WeatherData:
    def __init__(self, dsn_api_key, wu_api_key):

        self.dsn_api_key = dsn_api_key
        self.wu_api_key = wu_api_key
        self.clr_data()

    def clr_data(self):
        self.data = {}

        self.data_curr_temp = float()
        self.data_curr_summary = str()
        self.data_curr_humidity = float()
        self.data_curr_cloudCover = float()
        self.data_curr_precipProbability = float()

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

        self.clr_data()

        url = "https://api.darksky.net/forecast/{}/52.200521,20.963080?lang=pl&units=si".format(self.dsn_api_key)
        html = urllib.request.urlopen(url).read()
        forecast = json.loads(html.decode('utf-8'))

        # current
        self.data_curr_temp = forecast['currently']['temperature']
        self.data_curr_summary = forecast['currently']['summary']
        self.data_curr_humidity = forecast['currently']['humidity']
        self.data_curr_cloudCover = forecast['currently']['cloudCover']
        self.data_curr_precipProbability = forecast['currently']['precipProbability']

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
        # history = json.loads(html.decode('utf-8'))['trip']
        self.data['hist_temp_min'] = 3 #(float(history['temp_low']['avg']['C']) + float(history['temp_low']['min']['C'])) / 2
        self.data['hist_temp_max'] = 25 # (float(history['temp_high']['avg']['C']) + float(history['temp_high']['max']['C'])) / 2


app = Application()
app.exec_()
