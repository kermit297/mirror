library(feather)
library(tidyverse)
library(grid)
library(gridExtra)
library(lubridate)
library(hms)

Sys.setlocale("LC_ALL", "pl_PL.UTF-8")
orig <- ymd_hms('1970-01-01 00:00:00')

dh <- read_feather('d_hist.feather')
n <- dh$temp_min[1]
m <- dh$temp_max[1]

df <- read_feather('d.feather') %>%
    mutate(dttm = as.POSIXct(dttm, origin = orig, tz = "Europe/Warsaw"),
           precipLabel = ifelse(precipInt > 0.5, round(precipInt,1), NA),
           umbrella = ifelse(precipInt > 0.5 & precipProb > 0.2, 
                             intToUtf8(utf8ToInt("\xe2\x98\x82")), NA),
           precipProb = ifelse(precipProb==0&lag(precipProb)==0&lead(precipProb)==0,
                               NA, precipProb),
           temp_col = case_when(temp < n ~ n,
                                temp > m ~ m,
                                TRUE ~ temp
                                )
           )

dd <- read_feather('d_daily.feather') %>%
    mutate(dttm = as.POSIXct(dttm, origin = orig, tz = "Europe/Warsaw"),
           sunrise = as.POSIXct(sunrise, origin = orig, tz = "Europe/Warsaw"),
           sunset = as.POSIXct(sunset, origin = orig, tz = "Europe/Warsaw"),
           day = weekdays(sunrise, abbreviate = FALSE),
           d_len = as.character(as.hms(difftime(sunset,sunrise))),
           day_x = as.POSIXct(ifelse(sunrise > Sys.time(), sunrise, Sys.time()), 
                              origin = orig, tz = "Europe/Warsaw")
           )

y0 = min(df$temp)
y1 = max(df$temp)+5

ggplot(df, aes(xmin = dttm-minutes(30), xmax = dttm+minutes(30))) +
    # day/night
    geom_rect(data = dd, aes(xmin = sunrise, xmax = sunset, ymin = -Inf, ymax = Inf), 
              fill = 'yellow', alpha = 0.1) +
    # midnight dotted line
    geom_vline(xintercept = df$dttm[hour(df$dttm)==0], colour = 'white', linetype = 3) +
    # temperature
    geom_rect(aes(ymin = y0-5, ymax = temp, fill = temp_col), show.legend = FALSE) +
    geom_text(aes(x = dttm, y = temp, label = round(temp,0)), vjust = 1.5, size = 1.8) +
    # cloud cover
    geom_rect(aes(ymin = y1-cloud_cov*3, ymax = y1+cloud_cov*3), fill = "white") +
    # geom_hline(data = NULL, yintercept = c(y1,y1+3), linetype = 2, colour = "white", alpha = 0.5) +
    # precip prob
    geom_line(aes(x = dttm, y = y1+precipProb*3), colour = "steelblue", size = 0.5, 
              linetype = 2) + 
    # precip intensity
    geom_rect(aes(xmin = dttm-minutes(30), 
                  xmax = dttm+minutes(30),
                  ymax = y1, 
                  ymin = y1-precipInt*1), 
              fill = "steelblue", alpha = 0.8) +
    geom_text(aes(x = dttm, y = y1-precipInt*1, label = precipLabel), vjust = -0.5, size = 1.8) +
    # umbrella
    # geom_text(aes(x = dttm, y = y1-2, label = umbrella), colour = "white", size = 1.8) +
    # day label
    geom_label(data = dd, aes(x = day_x, y = y1+3, label = day), size = 2, colour = "black", alpha = 0.3, hjust = 0.3) +
    # sunrise
    # geom_label(data = dd, aes(x = sunrise, y = y0-2.5, label = paste(intToUtf8(utf8ToInt("\xe2\x98\xbc")),intToUtf8(utf8ToInt("\xe2\x86\x91")),format(sunrise, "%H:%M:%S"))), fill = 'black', size = 2, colour = "yellow", alpha = 0.8) +
    # sunset
    # geom_label(data = dd, aes(x = sunset, y = y0-2.5, label = paste(intToUtf8(utf8ToInt("\xe2\x98\xbc")),intToUtf8(utf8ToInt("\xe2\x86\x93")),format(sunset, "%H:%M:%S"))), fill = 'black', size = 2, colour = "orange", alpha = 0.8) +
    # day length
    # geom_label(data = dd, aes(x = sunrise + (sunset - sunrise)/2, y = y0-1, 
    # label = paste(intToUtf8(utf8ToInt("\xe2\x86\x94")),d_len)), fill = 'black', size = 2, colour = "white", alpha = 0.8) +
    # theme
    coord_cartesian(ylim = c(y0-3, y1+3.5), xlim = c(min(df$dttm), max(df$dttm))) +
    scale_fill_distiller(palette = "Spectral", limits = c(n,m)) +
    scale_x_datetime(date_breaks = '3 hours', date_minor_breaks = '3 hours', 
                     date_labels = "%H:%M") +
    theme(plot.background = element_rect(fill = 'black', colour = 'black'), 
          panel.background = element_rect(fill = 'black', colour = 'black'), 
          panel.grid = element_blank(),
          axis.text.y = element_blank(),
          #axis.ticks.x = element_blank(),
          axis.ticks.y = element_blank(),
          axis.text.x = element_text(size = 7),
          plot.margin = unit(c(0,-0.5,-0.7,-1.5), units = "lines"))

ggsave(filename = 'p.png', width = 6, height = 2, units = "in", dpi = 200)
