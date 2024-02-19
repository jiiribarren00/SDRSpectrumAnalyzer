import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation

print("\n This file reads the data from the Exp file and can express it in several ways.")

Option = 0

"while Option != 8:"

path = str(input("Enter the Exp file's path: "))

data = dict(np.load(path, allow_pickle = True))
del path

metadata = { a : b from a, b in  zip([filename, exp_time, spec_period, spec_repetitions, 
                                      spec_min_freq, spec_max_freq, mes_samplerate, mes_sample_num], data["Metadata"])}
frequencies = data["Frequencies"]
data = data.pop("Metadata", "Frequencies")
data = pd.DataFrame(data, columns = frequencies)

print("The Exp file named "+str(metadata["filename"])+" was loaded correctly.\n")
print("It contains "+str(len(data))+" spectrums from "+str(spec_min_freq/1e6)+"MHz to "+str(spec_max_freq/1e6)+"MHz.\n")
print("These are the timestamps of each one: \n",data.files)
print("If you need more information about the experiment, you can check the metadata dict and frecuencies list.\n\n")

print("Now, choose the way you want to plot the data.\n"+
      "[1] Plot a single spectrum.\n"+
      "[2] Plot all spectrums in an animation.\n"+
      "[3] Plot waterfall (a.k.a. heatmap).\n"+
      "[4] Plot the integrated power density of a frequency range.\n"+
      "[5] Print a single spectrum in the terminal.\n"+
      "[6] Print all metadata in the terminal.\n"+
      "[7] Change the Exp file.\n"+
      "[8] Exit.\n")

Option = int(input("Enter the number of the option you want to choose: "))

if np.isin(Option, [1,2,3,4]):
    
    fig, ax = plt.subplots()

    if Option == 1:
      print("You have chosen to plot a single spectrum.\n")
      print("Choose the spectrum you want to plot.\n")
			print("Enter the timestamp with format 'hh:mm:ss' and the closest time will be displayed.\n")
      selection = int(input("Enter the timestamp correctly formatted: "))
      selection = np.sum(np.multiply(float(selection.split(":")),[1, 1/60, 1/3600]))
			selection = [lambda X: np.abs(np.sum(np.multiply(float(X.split(":")),[1, 1/60, 1/3600]))-selection) for X in np.array(data.index()))]
			selection = np.array(data.index())[np.argmin(selection)]
			  
      ax.plot(frequencies/1e6, data[selection])
    
	  if Option == 2:
			print("You have chosen to plot an animation of the sprectums.\n")
			
			def animate(i):
				# Plot the data
				ax.clear()
				ax.fill_between(data["frequencies"]/1e6,data[data.files[i+2]])

				#ax.text(0.5,0.1,data.files[i+2], horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
				#ax.set_xlim(99, 101)
				#ax.set_ylim(0, 80)
				#ax.set_ylabel(r'Relative Power $\mathrm{dB}$')
				#ax.set_xlabel(r'Frequency $\mathrm{MHz}$')
				#ax.set_title(filename)
				#plt.tight_layout()

				if len(data.files) == 1:
					animate(0)
				else:
					anim = animation.FuncAnimation(fig, animate, frames = len(data), interval = np.max([1e4/len(data), 1000]))


    
    ax.text(0.5,0.1,data.files[i+2], horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
    ax.set_ylabel(r'Relative Power / $\mathrm{dB}$')
    ax.set_xlabel(r'Frequency / $\mathrm{MHz}$')
    ax.set_title(filename)
    plt.tight_layout()
	  plt.show()

    
