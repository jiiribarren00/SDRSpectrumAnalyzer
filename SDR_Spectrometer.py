from rtlsdr import RtlSdr
# La librería utiliza los drivers de Rtl-Sdr desde python
# La librería se puede descargar desde https://pypi.org/project/pyrtlsdr/
# Los drivers se instalan según las intrucciones de 
import matplotlib.pyplot as plt
import numpy as np
import time


#-------------------------


exp_time = 5*60
# Maximo plazo por el que se registrarán espectros / s

spec_period = 0*60
# Máximo periodo entre la toma de distintos espectros / s
spec_repetitions = 100
# Numero de veces que se repetirán las medidas para obtener un espectro
spec_min_freq = 140*1e6
# Mínima frecuencia registrada en un espectro / Hz
spec_max_freq = 150*1e6
# Máxima frecuencia registrada en un espectro / Hz

mes_samplerate = 3.2*1e6 #2.4*1e6
# Frecuencia de muestreo de la señal de radio o medio bandwith / Hz
mes_sample_num = 2048
# Numero de muestras de señal de radio a tomar en una medida


#-------------------------


sdr = RtlSdr()
# Se crea un objeto tipo RtlSdr que iniciará el dispositivo
sdr.sample_rate = mes_samplerate
# Se establece la frecuencia de muestreo de la señal de radio
sdr.freq_correction = 60
# PPM [Hay que averiguar bien qué valor darle]
sdr.gain = 30 # entre 0 y 49
# [Debe ser un valor fijo a lo largo del experimento. Hay que averiguar bien qué valor darle]


#-------------------------


filename = "Exp__"+time.strftime("%Y_%m_%d__%H_%M_%S")
#Creamos el nombre del archivo en el que se guardarán los datos
np.savez(filename, Metadata = [filename, exp_time, spec_period, spec_repetitions, 
		spec_min_freq, spec_max_freq, mes_samplerate, mes_sample_num])
# Creamos el archivo e incluimos la metadata del experimento en él


#-------------------------


TIME = [time.time()]
# Tiempo de inicio de las medidas

i = 0
# Iniciamos el contador de espectros

while exp_time-(time.time()-TIME[0]) > 0:


	spec_start_time = time.time()
	# Registramos el tiempo en el que se comienza a tomar el espectro actual

	spec_power = [[] for k in range(spec_repetitions)]
	# Creamos una lista de listas vacías para guardar la potencia en cada repetición
	spec_freq = []
	# Creamos una lista vacías para guardar las frecuencias del espectro

	spec_freq_range = np.arange(spec_min_freq, spec_max_freq, mes_samplerate/2)
	# Creamos un rango de frecuencias en el que se tomaran las medidas
	for j in range(spec_repetitions):
		print(f"{i+1}th spectrum {j+1}th repetition - scanning")
		for mes_center_freq in spec_freq_range:
			sdr.center_freq = mes_center_freq
			# Configuramos la frecuencia central de la medida    
			CheckInf = True
			while(CheckInf):   		
				mes_samples = sdr.read_samples(mes_sample_num)
				# Tomamos mes_samples_num muestras de la señal de radio	

				mes_power = np.abs(np.fft.fft(mes_samples))**2 / (mes_sample_num*mes_samplerate/2)
				# Calculamos la potencia de la señal de radio a cada frecuencia y las reordenamos
				mes_power = 10.0*np.log10(mes_power)
				CheckInf=np.isinf(mes_power).any()
				if(not(CheckInf)):
					# Pasamos la potencia a dB
					mes_power = np.fft.fftshift(mes_power)
					mes_power = mes_power[mes_power.size // 4: - mes_power.size // 4]
					# Descartamos el primer y último cuarto de mes_power
					spec_power[j] = np.concatenate((spec_power[j], mes_power))
					# Agregamos las potencias de esta medida al espectro

					if j == 0 and i == 0:
						mes_freq = np.fft.fftfreq(n=mes_power.size, d=2/mes_samplerate)
						mes_freq = np.fft.fftshift(mes_freq)+mes_center_freq
						# Genero un vector de frecuencias en el rango de frecuencias de la señal de radio
						#mes_freq = mes_freq[mes_freq.size // 4: - mes_freq.size // 4]
						# Descartamos el primer y último cuarto de mes_freq
						spec_freq = np.concatenate((spec_freq, mes_freq))
						# Agregamos las frecuencias de esta medida a las anteriores del espectro
   
			#print(f"{j+1}th repetition - scanning {mes_center_freq/1e6}MHz")


	#spec_power = np.nan_to_num(spec_power, copy = False, nan = 0, posinf=0, neginf=0)
	# Esto no debería estar pero no sé qué hacer. Hay valores -in y Nan por el log.
	spec_power = np.mean(spec_power, axis=0 )           #-min(np.mean(spec_power, axis=0))
	# Hay algun tema con la ganancia que no sé como ajustarla para mejorar los valores de la PSD


	arrays = dict(np.load(filename+".npz", allow_pickle = True))
	# Cargamos el archivo .npz en un diccionario

	if i == 0:
		arrays["frequencies"] = spec_freq
		# Si estoy calculando el primer espectro del experimento, agrego antes las frecuencias

	arrays[time.strftime("%H-%M-%S")] = spec_power
	# Añadimos el último espectro generado al diccionario recien abierto
	np.savez(filename, **arrays)
	# Guardamos el diccionario en el archivo que generamos originalmente
	del arrays
	# Eliminamos el diccionario para liberar memoria


	if time.time() - spec_start_time < spec_period:
		time.sleep(spec_period - (time.time() - spec_start_time))
		# Si el tiempo que se tardo en tomar el último espectro es menor a spec_period,
		# esperamos ese tiempo

	i += 1


sdr.close()
sdr = None
# Cerramos el sdr


print("FIN DEL EXPERIMENTO")
print("TIEMPO DE EJECUCIÓN = ", time.time() - TIME[0])
print(f"SE OBTUVIERON {i} ESPECTROS")
