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
   # Set sample rate
   sdr.setSampleRate(SOAPY_SDR_RX, 0, Conditions.iloc[i]["SampleRate"])

   # Set gain
   if Conditions.iloc[i]["Gain"] == "Auto":
      sdr.setGainMode(SOAPY_SDR_RX, 0, True)
   elif:
      sdr.setGainMode(SOAPY_SDR_RX, 0, False)
      sdr.setGain(SOAPY_SDR_RX, 0, Conditions.iloc[i]["Gain"])

   rx_stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

   #-------------------------
   
   rx_buff = np.array([0]*Conditions.iloc[i]["SampleNum"], np.complex64)
   window = np.hanning(len(Conditions.iloc[i]["SampleNum"])) # soon to be replaced with np.kaiser(Conditions.iloc[i]["SampleNum"]), 14)
   spec_power = [[] for k in range(Conditions.iloc[i]["Repetitions"])]
   spec_freq = []
   
   if seg_parts == 1:
      spec_freq_range = np.arange(spec_min_freq, spec_max_freq+seg_samplerate/seg_sample_num, seg_samplerate)
   elif seg_parts != 2 and seg_parts != 1:
      spec_freq_range = np.arange(spec_min_freq-seg_samplerate/seg_parts, spec_max_freq+seg_samplerate/seg_sample_num, seg_samplerate*(seg_parts-2)/seg_parts)

