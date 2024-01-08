# La librería utiliza los drivers de Rtl-Sdr desde python
# La librería se puede descargar desde https://pypi.org/project/pyrtlsdr/
# Los drivers se instalan según las intrucciones de 
from rtlsdr import RtlSdr
import matplotlib.pyplot as plt
import numpy as np
import time


#-------------------------


# Maximo plazo por el que se registrarán espectros / s
exp_time = 5*60

# Máximo periodo entre la toma de distintos espectros / s
spec_period = 0*60
# Numero de veces que se repetirán las medidas para obtener un espectro
spec_repetitions = 100
# Mínima frecuencia registrada en un espectro / Hz
spec_min_freq = 140*1e6
# Máxima frecuencia registrada en un espectro / Hz
spec_max_freq = 150*1e6

# Frecuencia de muestreo de la señal de radio o medio bandwith / Hz
mes_samplerate = 2.4*1e6 #2.4*1e6
# Numero de muestras de señal de radio a tomar en una medida
mes_sample_num = 2048


#-------------------------


# Se crea un objeto tipo RtlSdr que iniciará el dispositivo
sdr = RtlSdr()
# Se establece la frecuencia de muestreo de la señal de radio
sdr.sample_rate = mes_samplerate
# PPM [Hay que averiguar bien qué valor darle]
sdr.freq_correction = 60
# [Debe ser un valor fijo a lo largo del experimento. Hay que averiguar bien qué valor darle]
sdr.gain = 30 # entre 0 y 49


#-------------------------


#Creamos el nombre del archivo en el que se guardarán los datos
filename = "Exp__"+time.strftime("%Y_%m_%d__%H_%M_%S")
# Creamos el archivo e incluimos la metadata del experimento en él
np.savez(filename, Metadata = [filename, exp_time, spec_period, spec_repetitions, 
		spec_min_freq, spec_max_freq, mes_samplerate, mes_sample_num])


#-------------------------


# Tiempo de inicio de las medidas
TIME = [time.time()]

# Iniciamos el contador de espectros
i = 0

while exp_time-(time.time()-TIME[0]) > 0:


	# Registramos el tiempo en el que se comienza a tomar el espectro actual
	spec_start_time = time.time()

	# Creamos una lista de listas vacías para guardar la potencia en cada repetición
	spec_power = [[] for k in range(spec_repetitions)]
	# Creamos una lista vacías para guardar las frecuencias del espectro
	spec_freq = []

	# Creamos un rango de frecuencias en el que se tomaran las medidas
	spec_freq_range = np.arange(spec_min_freq, spec_max_freq, mes_samplerate/2)
	for j in range(spec_repetitions):
		print(f"{i+1}th spectrum {j+1}th repetition - scanning.")
		for mes_center_freq in spec_freq_range:
			# Configuramos la frecuencia central de la medida    
			sdr.center_freq = mes_center_freq
			CheckInf = True
			while(CheckInf):   		
				# Tomamos mes_samples_num muestras de la señal de radio	
				mes_samples = sdr.read_samples(mes_sample_num)

				# Calculamos la potencia de la señal de radio a cada frecuencia y las reordenamos
				mes_power = np.abs(np.fft.fft(mes_samples))**2 / (mes_sample_num*mes_samplerate/2)
				# Pasamos la potencia a dB
				mes_power = 10.0*np.log10(mes_power)
				CheckInf=np.isinf(mes_power).any()
				if(not(CheckInf)):
					mes_power = np.fft.fftshift(mes_power)
					# Descartamos el primer y último cuarto de mes_power
					mes_power = mes_power[mes_power.size // 4: - mes_power.size // 4]
					# Agregamos las potencias de esta medida al espectro
					spec_power[j] = np.concatenate((spec_power[j], mes_power))

					if j == 0 and i == 0:
						# Genero un vector de frecuencias en el rango de frecuencias de la señal de radio
						mes_freq = np.fft.fftfreq(n=mes_power.size, d=2/mes_samplerate)
						mes_freq = np.fft.fftshift(mes_freq)+mes_center_freq
						# Descartamos el primer y último cuarto de mes_freq
						#mes_freq = mes_freq[mes_freq.size // 4: - mes_freq.size // 4]
						# Agregamos las frecuencias de esta medida a las anteriores del espectro
						spec_freq = np.concatenate((spec_freq, mes_freq))
   
			#print(f"{j+1}th repetition - scanning {mes_center_freq/1e6}MHz")


	#spec_power = np.nan_to_num(spec_power, copy = False, nan = 0, posinf=0, neginf=0)
	# Esto no debería estar pero no sé qué hacer. Hay valores -in y Nan por el log.

	# Hay algun tema con la ganancia que no sé como ajustarla para mejorar los valores de la PSD
	spec_power = np.mean(spec_power, axis=0 )           #-min(np.mean(spec_power, axis=0))


	# Cargamos el archivo .npz en un diccionario
	arrays = dict(np.load(filename+".npz", allow_pickle = True))

	if i == 0:
		# Si estoy calculando el primer espectro del experimento, agrego antes las frecuencias
		arrays["frequencies"] = spec_freq

	# Añadimos el último espectro generado al diccionario recien abierto
	arrays[time.strftime("%H-%M-%S")] = spec_power
	# Guardamos el diccionario en el archivo que generamos originalmente
	np.savez(filename, **arrays)
	# Eliminamos el diccionario para liberar memoria
	del arrays


	if time.time() - spec_start_time < spec_period:
		# Si el tiempo que se tardo en tomar el último espectro es menor a spec_period,
		# esperamos ese tiempo
		time.sleep(spec_period - (time.time() - spec_start_time))

	i += 1


# Cerramos el sdr
sdr.close()
sdr = None


print("FIN DEL EXPERIMENTO")
print("TIEMPO DE EJECUCIÓN = ", time.time() - TIME[0])
print(f"SE OBTUVIERON {i} ESPECTROS")
