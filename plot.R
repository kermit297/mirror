library(tidyverse)
#library(grid)
#library(gridExtra)
library(lubridate)
library(hms)

#Sys.setlocale("LC_ALL", "pl_PL.UTF-8")
orig <- ymd_hms('1970-01-01 00:00:00')

dh <- read.csv('d_hist.csv')
n <- dh$temp_min[1]
m <- dh$temp_max[1]

df <- read.csv('d_hr.csv') %>%
    mutate(dttm = as.POSIXct(hr_dttm, origin = orig, tz = "Europe/Warsaw"),
           hr_precipLabel = ifelse(hr_precipInt > 0.5, round(hr_precipInt,1), NA),
           umbrella = ifelse(hr_precipInt > 0.5 & hr_precipProb > 0.2, 
                             intToUtf8(utf8ToInt("\xe2\x98\x82")), NA),
           hr_precipProb = ifelse(hr_precipProb==0&lag(hr_precipProb)==0&lead(hr_precipProb)==0,
                               NA, hr_precipProb),
           temp_col = hr_temp
           # temp_col = case_when(hr_temp < n ~ n,
           #                      hr_temp > m ~ m,
           #                      TRUE ~ hr_temp
           #                      )
           )

dd <- read.csv('d_d.csv') %>%
    mutate(dttm = as.POSIXct(d_dttm, origin = orig, tz = "Europe/Warsaw"),
           sunrise = as.POSIXct(d_sunrise, origin = orig, tz = "Europe/Warsaw"),
           sunset = as.POSIXct(d_sunset, origin = orig, tz = "Europe/Warsaw"),
           day = weekdays(sunrise, abbreviate = FALSE),
           d_len = as.character(as.hms(difftime(sunset,sunrise))),
           day_x = as.POSIXct(ifelse(sunrise > Sys.time(), sunrise, Sys.time()), 
                              origin = orig, tz = "Europe/Warsaw")
           )

y0 = min(df$hr_temp)
y1 = max(df$hr_temp)+5

ggplot(df, aes(xmin = dttm-minutes(30), xmax = dttm+minutes(30))) +
    # day-night
    geom_rect(data = dd, aes(xmin = sunrise, xmax = sunset, ymin = -Inf, ymax = Inf), 
              fill = 'yellow', alpha = 0.1) +
    # midnight dotted line
    geom_vline(xintercept = df$dttm[hour(df$dttm)==0], colour = 'white', linetype = 3) +
    # temperature
    geom_rect(aes(ymin = y0-5, ymax = hr_temp, fill = temp_col), show.legend = TRUE) +
    geom_text(aes(x = dttm, y = hr_temp, label = round(hr_temp,0)), vjust = 1.5, size = 1.7) +
    # cloud cover
    geom_rect(aes(ymin = y1-hr_cloudCov*3, ymax = y1+hr_cloudCov*3), fill = "white") +
    # geom_hline(data = NULL, yintercept = c(y1,y1+3), linetype = 2, colour = "white", alpha = 0.5) +
    # precip prob
    # geom_polygon(aes(x = dttm, y = y1+hr_precipProb*3), 
    #              fill = alpha("steelblue", 0.5), 
    #              colour = alpha("steelblue", 0.5) 
    #           ) + 
    # precip intensity
    geom_rect(aes(xmin = dttm-minutes(30), 
                  xmax = dttm+minutes(30),
                  ymax = y1, 
                  ymin = y1-hr_precipInt*5), 
              fill = alpha("steelblue", 0.8)
              ) +
    geom_text(aes(x = dttm, y = y1-hr_precipInt*5, label = hr_precipLabel), vjust = -0.5, size = 1.8) +
    # umbrella
    # geom_text(aes(x = dttm, y = y1-2, label = umbrella), colour = "white", size = 1.8) +
    # day label
    geom_label(data = dd, aes(x = day_x, y = y0-2.5, label = day), size = 2, colour = "black", alpha = 0.3, hjust = 0.3) +
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
    theme(plot.background = element_rect(fill = 'black', colour = NA), 
          panel.background = element_rect(fill = 'black', colour = NA),
          legend.background = element_rect(fill = 'black', colour = NA),
          legend.text = element_text(colour = 'white'),
          legend.title = element_blank(),
          #legend.position = c(1.2, .5),
          #legend.direction = 'horizontal',
          legend.box.spacing = unit(-0.1,'inches'),
          panel.grid = element_blank(),
          axis.text.y = element_blank(),
          #axis.ticks.x = element_blank(),
          axis.ticks.y = element_blank(),
          axis.text.x = element_text(size = 6),
          plot.margin = unit(c(0,-0.2,-0.7,-1.5), units = "lines"))

file.rename('p.png', paste0('p_',strftime(file.info('p.png')$mtime, '%Y_%m_%d_%H_%M_%S'),'.png'))
ggsave(filename = 'p.png', width = 6, height = 2, units = "in", dpi = 200)
