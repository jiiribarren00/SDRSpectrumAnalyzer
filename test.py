import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants

import numpy as np #use numpy for buffers

import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.animation as animation

#enumerate devices
results = SoapySDR.Device.enumerate()
for result in results: print(result)

#create device instance
#args can be user defined or from the enumeration result
sdr = SoapySDR.Device(dict(driver="rtlsdr"))

#query device info
print("\nList device's antennas: ",sdr.listAntennas(SOAPY_SDR_RX, 0))
print("List device's gains range: ",sdr.getGainRange(SOAPY_SDR_RX, 0))
print("List device's gains range: ",sdr.getGain(SOAPY_SDR_RX, 0))
print("List device's gains range: ",sdr.listGains(SOAPY_SDR_RX, 0))
print("List device's samplerates: ",sdr.listSampleRates(SOAPY_SDR_RX, 0))
print("List device's frequency range: ",sdr.getFrequencyRange(SOAPY_SDR_RX, 0))

#apply settings

a = input("\n Set the center frequency from range "+str(sdr.getFrequencyRange(SOAPY_SDR_RX, 0))+":")

if a == "":
   # Action to be taken when Enter is pressed
   sdr.setFrequency(SOAPY_SDR_RX, 0, 90e6)
else:
   sdr.setFrequency(SOAPY_SDR_RX, 0, float(a))


a = input("\n Set the gain from range "+str(sdr.getGainRange(SOAPY_SDR_RX, 0))+" or press enter for automatic:")

if a == "":
   # Action to be taken when Enter is pressed
   sdr.setGainMode(SOAPY_SDR_RX, 0, True)
   print("Device's AutoGain: ",sdr.getGainMode(SOAPY_SDR_RX, 0))
else:
   sdr.setGainMode(SOAPY_SDR_RX, 0, False)  # Enable AGC
   sdr.setGain(SOAPY_SDR_RX, 0, float(a))
   



a = input("\n Set the samplerate (double-bandwidth) between "+str(min(sdr.listSampleRates(SOAPY_SDR_RX, 0)))+" and "+str(max(sdr.listSampleRates(SOAPY_SDR_RX, 0)))+":")

if a == "":
   # Action to be taken when Enter is pressed
   sdr.setSampleRate(SOAPY_SDR_RX, 0, 10e6)
else:
   sdr.setSampleRate(SOAPY_SDR_RX, 0, float(a))
   
del a

#setup a stream (complex floats)
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)

fig, (ax0, ax1, ax2) = plt.subplots(3, 1,figsize=(9,6))

buff = np.array([0]*1024, np.complex64)


def animate(i):
    ax0.clear()
    ax1.clear()
    ax2.clear()
    
    sdr.activateStream(rxStream)
    samples = sdr.readStream(rxStream, [buff], len(buff))
    sdr.deactivateStream(rxStream)
    
    # use matplotlib to estimate and plot the PSD
    ax0.psd(buff, NFFT=len(buff), Fs=sdr.getSampleRate(SOAPY_SDR_RX, 0), Fc=sdr.getFrequency(SOAPY_SDR_RX, 0)) #, window = mlab.window_none(buff))
    
    hann = np.hanning(len(buff))
    buff2 = buff*hann
    mes_power = np.abs(np.fft.fft(buff2))**2 / (len(buff2)*sdr.getSampleRate(SOAPY_SDR_RX, 0)/2)
    mes_power = 10.0*np.log10(mes_power)
    mes_power = np.fft.fftshift(mes_power)
    mes_freq = np.fft.fftfreq(n=mes_power.size, d=2/sdr.getSampleRate(SOAPY_SDR_RX, 0))    
    mes_freq = np.fft.fftshift(mes_freq)+sdr.getFrequency(SOAPY_SDR_RX, 0)
    
    ax1.plot(mes_freq/1e6, mes_power)
    ax1.set_xlabel("Frequencie / MHz")
    ax1.set_ylabel("PSD")
    
    ax2.scatter(np.linspace(0, len(buff)/sdr.getSampleRate(SOAPY_SDR_RX, 0), len(buff))*1000,np.abs(buff))
    ax2.set_xlabel("Time / ms")
    ax2.set_ylabel("Radio Signal")
    fig.suptitle(str(samples)+", Gain"+str(sdr.getGain(SOAPY_SDR_RX, 0)))
    #print(buff)


try:
    ani = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)
    plt.show()
except KeyboardInterrupt:
    pass
finally:
    
    #shutdown the stream
    sdr.closeStream(rxStream)#stop streaming