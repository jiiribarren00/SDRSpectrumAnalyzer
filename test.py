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
print(sdr.listAntennas(SOAPY_SDR_RX, 0))
print(sdr.listGains(SOAPY_SDR_RX, 0))
print(sdr.listSampleRates(SOAPY_SDR_RX, 0))
print(sdr.listFrequencies(SOAPY_SDR_RX, 0))
freqs = sdr.getFrequencyRange(SOAPY_SDR_RX, 0)
for freqRange in freqs: print(freqRange)

#apply settings
sdr.setSampleRate(SOAPY_SDR_RX, 0, 10e6)
sdr.setFrequency(SOAPY_SDR_RX, 0, 90e6)
sdr.setGainMode(SOAPY_SDR_RX, 0, False)  # Enable AGC
sdr.setGain(SOAPY_SDR_RX, 0, 0)

#setup a stream (complex floats)
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CS16)
 #start streaming



# configure device

fig = plt.figure()
graph_out = fig.add_subplot(1, 1, 1)



def animate(i):
    graph_out.clear()
    buff = np.array([0]*1024, np.complex64)
    sdr.activateStream(rxStream)
    samples = sdr.readStream(rxStream, [buff], len(buff))
    sdr.deactivateStream(rxStream) 
    # use matplotlib to estimate and plot the PSD
    graph_out.psd(buff, NFFT=1024, Fs=sdr.getSampleRate(SOAPY_SDR_RX, 0)/1e6, Fc=sdr.getFrequency(SOAPY_SDR_RX, 0)/1e6)
    #graph_out.scatter(np.arange(0,len(buff)),np.abs(buff))
    #graph_out.xlabel('Frequency (MHz)')
    #graph_out.ylabel('Relative power (dB)')
    print(samples)
    print(buff)


try:
    ani = animation.FuncAnimation(fig, animate, interval=5000)
    plt.show()
except KeyboardInterrupt:
    pass
finally:
    #shutdown the stream
    sdr.closeStream(rxStream)#stop streaming