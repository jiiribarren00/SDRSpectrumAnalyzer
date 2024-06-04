import SoapySDR
from SoapySDR import *
import numpy as np
import staticframe as sf
import datetime as dt
from tqdm import tqdm

Conditions = sf.Frame.from_xlsx("Conditions.xlsx", skip_header = 1)

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
   sdr = SoapySDR.Device(dict(driver=Devices[selection-1]["driver"])) #Hay que chequear si esto funciona. No creo que lo necesitemos

#-------------------------

for i in Conditions.index():

   ithCond = Conditions.iloc[i]
   
   # Set sample rate
   sdr.setSampleRate(SOAPY_SDR_RX, 0, ithCond["SampleRate"])

   # Set gain
   if ithCond["Gain"] == "Auto":
      sdr.setGainMode(SOAPY_SDR_RX, 0, True)
   elif:
      sdr.setGainMode(SOAPY_SDR_RX, 0, False)
      sdr.setGain(SOAPY_SDR_RX, 0, ithCond["Gain"])

   rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

   #-------------------------
   
   rx_buff = np.array([0]*ithCond["SampleNum"], np.complex64)
   window = np.hanning(ithCond["SampleNum"]) # soon to be replaced with np.kaiser(Conditions.iloc[i]["SampleNum"]), 14)
   spec_power = [[] for k in range(ithCond["Repetitions"])]
   spec_freq = []
   
   if ithCond["SegParts"] == 1:
      
      spec_central_freq = np.arange(ithCond["MinFreq"], ithCond["MaxFreq"]+ithCond["SampleRate"]/ithCond["SampleNum"], ithCond["SampleRate"])

      for f in spec_central_freq:
         seg_freq = np.fft.fftfreq(ithCond["SampleNum"], 1/ithCond["SampleRate"])
         seg_freq = np.fft.fftshift(seg_freq)+f
         spec_freq = np.concatenate((spec_freq, seg_freq))
      
   elif ithCond["SegParts"] != 2 and ithCond["SegParts"] != 1:
      
      spec_central_freq = np.arange(ithCond["MinFreq"]-ithCond["SampleRate"]/ithCond["SegParts"], ithCond["MaxFreq"]+ithCond["SampleRate"]/ithCond["SegParts"], ithCond["SampleRate"]*(ithCond["SegParts"]-2)/ithCond["SegParts"])

      for f in spec_central_freq:
         seg_freq = np.fft.fftfreq(ithCond["SampleNum"]*(ithCond["SegParts"]-2)//ithCond["SegParts"], ithCond["SegParts"]/(ithCond["SampleRate"]*(ithCond["SegParts"]-2)))
         seg_freq = np.fft.fftshift(seg_freq)+f
         spec_freq = np.concatenate((spec_freq, seg_freq))
   del seg_freq
   
   PSDs = sf.Frame.from_array([0]*len(spec_freq), columns = spec_freq)
   
   TIME = []
   TIME = np.append(TIME, np.datetime64("now"))

   j = 0

   while ithCond["Time"]-(np.datetime64("now")-TIME[0]) > 0:
      
      spec_start_time = np.datetime64("now")
      
      for j in tqdm(range(ithCond["Repetitions"])):

         for f in spec_central_freq:
            
            sdr.setFrequency(SOAPY_SDR_RX, 0, f)

            CheckInf = True

            while(CheckInf):
               # Read samples

               sdr.activateStream(rx_stream)
               results = sdr.readStream(rx_stream, [rx_buff], seg_sample_num)             
               sdr.deactivateStream(rx_stream)

               rx_buff2 = rx_buf*window
               # Calculamos la potencia de la señal de radio a cada frecuencia y las reordenamos
               seg_power = np.abs(np.fft.fft(rx_buff2))**2 / (seg_sample_num*seg_samplerate)

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

      TIME = np.append(TIME, np.datetime64("now")-spec_start_time)

      PSDs[spec_start_time] = np.mean(spec_power, axis=0)



   
      

