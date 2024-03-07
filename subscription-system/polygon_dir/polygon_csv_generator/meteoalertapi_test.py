from meteoalertapi import Meteoalert

# Find you country and province on https://meteoalarm.org/ or https://feeds.meteoalarm.org/
meteo = Meteoalert('country', 'china')

# Get the weather alarm for your place
meteo = Meteoalert('country', 'china')
print(str(meteo.get_alert()))
