import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants

import numpy as np #use numpy for buffers

import matplotlib.pyplot as plt
import matplotlib.animation as animation

#enumerate devices
results = SoapySDR.Device.enumerate()
for result in results: print(result)

#create device instance
#args can be user defined or from the enumeration result
sdr = SoapySDR.Device(dict(driver="sdrplay"))

#query device info
print("List device's antennas: ",sdr.listAntennas(SOAPY_SDR_RX, 0))
print("List device's gains: ",sdr.listGains(SOAPY_SDR_RX, 0))
print("List device's samplerates: ",sdr.listSampleRates(SOAPY_SDR_RX, 0))
print("List device's frequencies: ",sdr.listFrequencies(SOAPY_SDR_RX, 0))
freqs = sdr.getFrequencyRange(SOAPY_SDR_RX, 0)
for freqRange in freqs: print(freqRange)

#apply settings

a = input("Set the center frequency between ",min(sdr.listFrequencies(SOAPY_SDR_RX, 0))," and "max(sdr.listFrequencies(SOAPY_SDR_RX, 0)), ":")

if a == "":
   # Action to be taken when Enter is pressed
   sdr.setFrequency(SOAPY_SDR_RX, 0, 90e6)
else:
   sdr.setFrequency(SOAPY_SDR_RX, 0, a)


a = input("Set the gain between ",min(sdr.listGains(SOAPY_SDR_RX, 0))," and ", max(sdr.listGains(SOAPY_SDR_RX, 0))," or press enter for automatic:")

if a == "":
   # Action to be taken when Enter is pressed
   sdr.setGainMode(SOAPY_SDR_RX, 0, True)
else:
   sdr.setGainMode(SOAPY_SDR_RX, 0, False)  # Enable AGC
   sdr.setGain(SOAPY_SDR_RX, 0, float(a))

a = input("Set the samplerate (double-bandwidth) between ",min(sdr.listSampleRates(SOAPY_SDR_RX, 0))," and "max(sdr.listSampleRates(SOAPY_SDR_RX, 0)), ":")

if a == "":
   # Action to be taken when Enter is pressed
   sdr.setFrequency(SOAPY_SDR_RX, 0, 10e6)
else:
   sdr.setFrequency(SOAPY_SDR_RX, 0, a)

#setup a stream (complex floats)
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CS16)

fig, (ax1, ax2) = plt.subplots(1,2, figsize = (8, 6))

buff = np.array([0]*1024, np.complex64)

def animate(i):
    ax1.clear()
    ax2.clear()
    sdr.activateStream(rxStream)
    samples = sdr.readStream(rxStream, [buff], len(buff))
    sdr.deactivateStream(rxStream) 
    # use matplotlib to estimate and plot the PSD
    ax1.psd(buff, NFFT=1024, Fs=sdr.getSampleRate(SOAPY_SDR_RX, 0)/1e6, Fc=sdr.getFrequency(SOAPY_SDR_RX, 0)/1e6)
    ax1.set_xlabel("Frequencie / MHz")
    ax1.set_ylabel("PSD")
    
    ax2.scatter(np.linspace(0,1024/a, 1024),np.abs(buff))
    ax2.set_xlabel("Time / s")
    ax2.set_ylabel("Radio Signal")
   
    print(samples)
    print(buff)


try:
    ani = animation.FuncAnimation(fig, animate, interval=3000)
    plt.show()
except KeyboardInterrupt:
    pass
finally:
    #shutdown the stream
    sdr.closeStream(rxStream)#stop streaming