import datetime
wanted_date = '2023-06-28'
date = datetime.datetime.strptime(wanted_date, '%Y-%m-%d')
week_num = date.isocalendar()[0]
 
print("Week number for",wanted_date,":",week_num)
