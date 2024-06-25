import SoapySDR
from SoapySDR import *
import numpy as np
import pandas as pd
import static_frame as sf
from time import sleep
from tqdm import tqdm
import pyfftw

Conditions = pd.read_excel("ExperimentConditions.xlsx", index_col=0)

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

GlobalInit = np.datetime64("now")

for i in Conditions.index.values():

   iCond = Conditions.iloc[i]
   
   # Set sample rate
   sdr.setSampleRate(SOAPY_SDR_RX, iCond["Channel"], iCond["SampleRate"])

   # Set gain
   if iCond["Gain"] == "Auto":
      sdr.setGainMode(SOAPY_SDR_RX, iCond["Channel"], True)
   elif:
      sdr.setGainMode(SOAPY_SDR_RX, iCond["Channel"], False)
      sdr.setGain(SOAPY_SDR_RX, iCond["Channel"], iCond["Gain"])

   rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

   #-------------------------
   
   rx_buff = pyfftw.empty_aligned(iCond["SampleNum"], dtype='complex64')
   window = np.hanning(iCond["SampleNum"]) # soon to be replaced with np.kaiser(Conditions.iloc[i]["SampleNum"]), 14)
   
   spec_freq = []
   
   if iCond["SegParts"] == 1:
      
      spec_central_freq = np.arange(iCond["MinFreq"], iCond["MaxFreq"]+iCond["SampleRate"]/iCond["SampleNum"], iCond["SampleRate"])

      for f in spec_central_freq:
         seg_freq = np.fft.fftfreq(iCond["SampleNum"], 1/iCond["SampleRate"])
         seg_freq = np.fft.fftshift(seg_freq)+f
         spec_freq = np.concatenate((spec_freq, seg_freq))
      
   elif iCond["SegParts"] != 2 and iCond["SegParts"] != 1:
      
      spec_central_freq = np.arange(iCond["MinFreq"]-iCond["SampleRate"]/iCond["SegParts"], iCond["MaxFreq"]+iCond["SampleRate"]/iCond["SegParts"], iCond["SampleRate"]*(iCond["SegParts"]-2)/iCond["SegParts"])

      for f in spec_central_freq:
         seg_freq = np.fft.fftfreq(iCond["SampleNum"]*(iCond["SegParts"]-2)//iCond["SegParts"], iCond["SegParts"]/(iCond["SampleRate"]*(iCond["SegParts"]-2)))
         seg_freq = np.fft.fftshift(seg_freq)+f
         spec_freq = np.concatenate((spec_freq, seg_freq))
   del seg_freq
   
   PSDs = pd.DataFrame(columns = spec_freq)
   
   TIME = [np.datetime64("now")]

   j = 0

   while np.timedelta64(iCond["SpecTime"], "s") > (np.datetime64("now")-TIME[0]):
      
      spec_power = np.empty(iCond["Repetitions"], dtype=object)
      
      spec_start_time = np.datetime64("now")
            
      for j in tqdm(range(iCond["Repetitions"]), desc= "Adquiring "+str(j+1)"th spectrum"):

         for f in spec_central_freq:
            
            sdr.setFrequency(SOAPY_SDR_RX, iCond["Channel"], f)

            CheckInf = True

            while(CheckInf):
               # Read samples

               sdr.activateStream(rx_stream)
               results = sdr.readStream(rx_stream, [rx_buff], iCond["SampleNum"])             
               sdr.deactivateStream(rx_stream)

               rx_buff2 = rx_buff*window
               
               fft_object = pyfftw.builders.fft(rx_buff2)
               
               # Calculamos la potencia de la señal de radio a cada frecuencia y las reordenamos
               seg_power = np.abs(fft_object()b)**2 / (iCond["SampleNum"]*iCond["SampleRate"])

               # Pasamos la potencia a dB
               seg_power = 10.0*np.log10(seg_power)

               CheckInf=np.isinf(seg_power).any()

               if(not(CheckInf)):

                  seg_power = np.fft.fftshift(seg_power)

                  if iCond["SegParts"] != 1 and iCond["SegParts"] != 2:
                     # Descartamos la primer y última seg_parts-esima parte de seg_power
                     seg_power = seg_power[seg_power.size // iCond["SegParts"] : - seg_power.size // iCond["SegParts"] ]

                  # Agregamos las potencias de esta medida al espectro
                  spec_power[j] = np.concatenate((spec_power[j], seg_power))

      TIME = np.append(TIME, np.datetime64("now")-spec_start_time)

      PSDs.loc[spec_start_time+TIME[-1]/2] = np.mean(spec_power, axis=1)
      
      if j % iCond["Saving Frequency"] == 0:
         SF = sf.Frame.from_pandas(PSDs)
         SF.to_npz("/"+np.datetime_as_string(GlobalInit, timezone='UTC')+
                   "/"+str(iCond["ExperimentName"]))
         del SF
         
         np.save(TIME[-1:], "/"+np.datetime_as_string(GlobalInit, timezone='UTC')+
                            "/"+str(iCond["ExperimentName"]))
         
      if np.timedelta64("now") - spec_start_time < iCond["Spectrum Period"]:
         # Si el tiempo que se tardo en tomar el último espectro es menor a spec_period,
         # esperamos ese tiempo
         sleep(iCond["Spectrum Period"] - (np.timedelta64("now") - spec_start_time))

      j += 1

sdr.closeStream(rx_stream)

print("Experinment ", filename, " ended")
print("Execution time = ", time.time() - TIME[0])
print(f"{i} spectra were obtained")


   
      

