# La librería utiliza los drivers y librería de python de SoapySDR 
"""
Se construye a partir de clonaciones de los repositorios. Ejecutamos la siguiente guía:
   https://github.com/pothosware/SoapySDR/wiki/BuildGuide 
Luego clonamos los drivers específicos para SDRplay:
   https://github.com/pothosware/SoapySDRPlay3/wiki
Lo mismo para RTL-SDR:
   https://github.com/pothosware/SoapyRTLSDR/wiki 
Tambien hay que descargar e instalar los enlaces a python:
   https://github.com/pothosware/SoapySDR/wiki/PythonSupport 
"""
import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np
import time


#-------------------------


# Maximo plazo por el que se registrarán espectros / s
exp_time = 1*60
# Ganancia [0,66]dB
exp_gain = 40
# Space to leave annotations
annotations = ""

# Máximo periodo entre la toma de distintos espectros / s
spec_period = 0*60
# Numero de veces que se repetirán las medidas para obtener un espectro
spec_repetitions = 1
# Mínima frecuencia registrada en un espectro / Hz
spec_min_freq = 30*1e6
# Máxima frecuencia registrada en un espectro / Hz
spec_max_freq = 300*1e6

# Frecuencia de muestreo de la señal de radio o medio bandwith / Hz
seg_samplerate = 5e6 #2.4*1e6
# Numero de muestras de señal de radio a tomar en una medida
seg_sample_num = 2**12 #necesitamos 122KHz de res.
# Determine el numero de partes en las que se divide el segmento, se descartarán la primera y la última parte
seg_parts = 8

#-------------------------

Devices = SoapySDR.Device.enumerate()

if len(Devices) == 0:
    print("No devices found")
    exit()
elif len(Devices) == 1:
   sdr = SoapySDR.Device(dict(driver=Devices[0]["driver"]))
elif len(Devices) > 1:
   print("Multiple devices found. Select the device to record")
   for i in range(len(Devices)):
      print(str(i) + " - " + str(Devices[i]["driver"]))
   selection = int(input("Enter the number of the device you want to record: "))
   sdr = SoapySDR.Device(dict(driver=Devices[selection]["driver"])) #Hay que chequear si esto funciona. No creo que lo necesitemos

# Set sample rate
sdr.setSampleRate(SOAPY_SDR_RX, 0, seg_samplerate)

# Set gain
sdr.setGainMode(SOAPY_SDR_RX, 0, False)  # Enable AGC
sdr.setGain(SOAPY_SDR_RX, 0, exp_gain)   # Set gain value

rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

rx_buff = np.array([0]*seg_sample_num, np.complex64)
hann = np.hanning(len(rx_buff))

#-------------------------


#Creamos el nombre del archivo en el que se guardarán los datos
filename = "Exp__"+time.strftime("%Y_%m_%d__%H_%M_%S")

# Creamos el archivo e incluimos la metadata del experimento en él
np.savez(filename, Metadata = [filename, exp_time, exp_gain, spec_period, spec_repetitions, 
      spec_min_freq, spec_max_freq, seg_samplerate, seg_sample_num, seg_parts, annotations])


#-------------------------



# Iniciamos el contador de espectros
i = 0


# Tiempo de inicio de las medidas
TIME = []
TIME = np.append(TIME, time.time())

while exp_time-(time.time()-TIME[0]) > 0:


   # Registramos el tiempo en el que se comienza a tomar el espectro actual
   spec_start_time = time.time()

   spec_name = time.strftime("%H-%M-%S")

   # Creamos una lista de listas vacías para guardar la potencia en cada repetición
   spec_power = [[] for k in range(spec_repetitions)]
   # Creamos una lista vacías para guardar las frecuencias del espectro
   spec_freq = []

   # Creamos un rango de frecuencias en el que se tomaran las medidas
   if seg_parts == 1:
      spec_freq_range = np.arange(spec_min_freq, spec_max_freq, seg_samplerate)
   elif seg_parts != 2 and seg_parts != 1:
      spec_freq_range = np.arange(spec_min_freq+seg_samplerate/seg_parts, spec_max_freq, seg_samplerate/(seg_parts-2))

   for j in range(spec_repetitions):
      
      print(f"{i+1}th spectrum {j+1}th repetition - scanning.")
      
      for seg_center_freq in spec_freq_range:
      
         # Tune to center frequency
         sdr.setFrequency(SOAPY_SDR_RX, 0, seg_center_freq)

         CheckInf = True
         
         while(CheckInf):
            # Read samples
            
            sdr.activateStream(rx_stream)
            results = sdr.readStream(rx_stream, [rx_buff], seg_sample_num)             
            sdr.deactivateStream(rx_stream)

            rx_buff2 = rx_buff*hann
            # Calculamos la potencia de la señal de radio a cada frecuencia y las reordenamos
            if seg_parts == 1:
               seg_power = np.abs(np.fft.fft(rx_buff2))**2 / (seg_sample_num*seg_samplerate)
            elif seg_parts != 1 and seg_parts != 2:
               seg_power = np.abs(np.fft.fft(rx_buff2))**2 / (seg_sample_num*seg_samplerate/(seg_parts-2))

            # Pasamos la potencia a dB
            seg_power = 10.0*np.log10(seg_power)
   
            CheckInf=np.isinf(seg_power).any()
   
            if(not(CheckInf)):
               
               seg_power = np.fft.fftshift(seg_power)

               if seg_parts != 1 and seg_parts != 2:
                  # Descartamos la primer y última seg_parts-esima parte de seg_power
                  seg_power = seg_power[seg_power.size // seg_parts: - seg_power.size // seg_parts]
               
               # Agregamos las potencias de esta medida al espectro
               spec_power[j] = np.concatenate((spec_power[j], seg_power))

               if j == 0 and i == 0:
                  # Genero un vector de frecuencias en el rango de frecuencias de la señal de radio
                  if seg_parts == 1:
                     seg_freq = np.fft.fftfreq(n=seg_power.size, d=1/seg_samplerate)
                  elif seg_parts != 1 and seg_parts != 2:
                     seg_freq = np.fft.fftfreq(n=seg_power.size, d=(seg_parts-2)/seg_samplerate)
                  seg_freq = np.fft.fftshift(seg_freq)+seg_center_freq
                  # Agregamos las frecuencias de esta medida a las anteriores del espectro
                  spec_freq = np.concatenate((spec_freq, seg_freq))

   TIME = np.append(TIME, time.time()-spec_start_time)

   # Hay algun tema con la ganancia que no sé como ajustarla para mejorar los valores de la PSD
   spec_power = np.mean(spec_power, axis=0)     


   # Cargamos el archivo .npz en un diccionario
   arrays = dict(np.load(filename+".npz", allow_pickle = True))

   if i == 0:
      # Si estoy calculando el primer espectro del experimento, agrego antes las frecuencias
      arrays["frequencies"] = spec_freq

   # Añadimos el último espectro generado al diccionario recien abierto
   arrays[spec_name] = spec_power
   # Guardamos el diccionario en el archivo que generamos originalmente
   np.savez(filename, **arrays)
   # Eliminamos el diccionario para liberar memoria
   del arrays

   if time.time() - spec_start_time < spec_period:
      # Si el tiempo que se tardo en tomar el último espectro es menor a spec_period,
      # esperamos ese tiempo
      time.sleep(spec_period - (time.time() - spec_start_time))

   i += 1

sdr.closeStream(rx_stream)

arrays = dict(np.load(filename+".npz", allow_pickle = True))
arrays["times"] = TIME
np.savez(filename, **arrays)

print("Experinment ", filename, " ended")
print("Execution time = ", time.time() - TIME[0])
print(f"{i} spectra were obtained")
