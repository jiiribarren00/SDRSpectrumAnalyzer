import SoapySDR
from SoapySDR import *
import numpy as np
import pandas as pd
import static_frame as sf
from time import sleep
from tqdm import tqdm
import pyfftw

DefaultDtypes = {
   "ExperimentName":"str", "Channel":"uint8",
   "SpecTime":"float64", "SavingFrequency":"uint16",
   "Gain":"uint8", "SampleRate": "float64", "SpecTime": "float64",
   "MaxFreq": "float64", "MinFreq": "float64",
   "Spectrum Period": "float64", "Repetitions":"uint16",
   "SegParts":"uint8"
   
}
Conditions = pd.read_csv("ExperimentConditions.csv", header=1, dtype=DefaultDtypes)


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

GlobalInitTime = np.datetime64("now")

for i in Conditions.index.values:

   iCond = Conditions.iloc[i]
   
   # Set sample rate
   sdr.setSampleRate(SOAPY_SDR_RX, int(iCond["Channel"]), float(iCond["SampleRate"]))

   # Set gain
   if iCond["Gain"] == "Auto":
      sdr.setGainMode(SOAPY_SDR_RX, int(iCond["Channel"]), True)
   else:
      sdr.setGainMode(SOAPY_SDR_RX, int(iCond["Channel"]), False)
      sdr.setGain(SOAPY_SDR_RX, int(iCond["Channel"]), int(iCond["Gain"]))

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
   
   InitTime = np.datetime64("now")
   dTimes = np.array([], dtype="timedelta64[s]")

   j = 0
   
   while pd.to_timedelta(iCond["SpecTime"]) > (np.datetime64("now")-InitTime):
      
      spec_power =[ [] for i in range(iCond["Repetitions"])]
      
      spec_start_time = np.datetime64("now")
            
      for j in tqdm(range(iCond["Repetitions"]), desc= "Adquiring "+str(j+1)+"th spectrum"):

         for f in spec_central_freq:
            
            sdr.setFrequency(SOAPY_SDR_RX, int(iCond["Channel"]), f)

            CheckInf = True

            while(CheckInf):
               # Read samples

               sdr.activateStream(rx_stream)
               results = sdr.readStream(rx_stream, [rx_buff], int(iCond["SampleNum"]))
               sdr.deactivateStream(rx_stream)

               rx_buff2 = rx_buff*window
               
               fft_object = pyfftw.builders.fft(rx_buff2)
               
               # Calculamos la potencia de la señal de radio a cada frecuencia y las reordenamos
               seg_power = np.abs(fft_object())**2 / (iCond["SampleNum"]*iCond["SampleRate"])

               if np.all(seg_power):
                  # Pasamos la potencia a dB
                  seg_power = 10.0*np.log10(seg_power)

                  CheckInf=np.isinf(seg_power).any()
               else:
                  CheckInf = True
               

               if(not(CheckInf)):

                  seg_power = np.fft.fftshift(seg_power)

                  if iCond["SegParts"] != 1 and iCond["SegParts"] != 2:
                     # Descartamos la primer y última seg_parts-esima parte de seg_power
                     seg_power = seg_power[seg_power.size // iCond["SegParts"] : - seg_power.size // iCond["SegParts"] ]

                  # Agregamos las potencias de esta medida al espectro
                  spec_power[j] = np.concatenate((spec_power[j], seg_power))

      dTimes = np.append(dTimes, np.datetime64("now")-spec_start_time)

      PSDs.loc[spec_start_time+dTimes[-1]/2] = np.mean(spec_power, axis=1)
      
      if j % iCond["Saving Frequency"] == 0:
         SF = sf.Frame.from_pandas(PSDs)
         SF.to_npz("/"+np.datetime_as_string(GlobalInitTime, timezone='UTC')+
                   "/"+str(iCond["ExperimentName"]))
         del SF
         
         np.save(dTimes, "/"+np.datetime_as_string(GlobalInitTime, timezone='UTC')+
                         "/"+str(iCond["ExperimentName"]))
         
      if np.timedelta64("now") - spec_start_time < iCond["Spectrum Period"]:
         # Si el tiempo que se tardo en tomar el último espectro es menor a spec_period,
         # esperamos ese tiempo
         sleep(iCond["Spectrum Period"] - (np.datetime64("now") - spec_start_time).seconds)

      j += 1

sdr.closeStream(rx_stream)

print("Experinment ", filename, " ended")
print("Execution time = ", time.time() - TIME[0])
print(f"{i} spectra were obtained")


   
      

