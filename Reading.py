import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
#import seaborn as sn


def closest_time(x, v):
   a = []
   i = 0
   for vi in v:
      vi = [float(y) for y in vi.split('-')]
      a = np.append(a, np.sum(np.multiply(vi, [1, 1 / 60, 1 / 3600])))
      while a[i] < a[i - 1]:
         a[i] = a[i] + 24
      i = i + 1
   x = np.sum(
       np.multiply([float(y) for y in x.split('-')], [1, 1 / 60, 1 / 3600]))
   a = np.abs(a - x)
   return np.argmin(a)


def closest(x, v):
   a = [np.abs(vi - x) for vi in v]
   return np.argmin(a)


print("\n_____________________________________________________________________________\n",
       "This file reads the data from the Exp file and can express it in several ways.\n"
)

Option = 7

while Option != 8:
   if Option == 7:
      path = str(input("\n Enter the Exp file's path: "))

      data = dict(np.load(path, allow_pickle=True))
      del path

      metadata = {}
      for i in range(len(data["Metadata"])):
         a = [
             "filename", "exp_time", "spec_period", "spec_repetitions",
             "spec_min_freq", "spec_max_freq", "mes_samplerate",
             "mes_sample_num"
         ]
         if a[i] == "filename":
            metadata[a[i]] = data["Metadata"][i]
         else:
            metadata[a[i]] = float(data["Metadata"][i])
         del a

      frequencies = data["frequencies"]

      del data["Metadata"], data["frequencies"]

      data = pd.DataFrame.from_dict(data, orient="index", columns=frequencies)

      print("\nThe Exp file named " + str(metadata["filename"]) +
            " was loaded correctly.")
      print("\nIt contains " + str(len(data)) + " spectrums from " +
            str(metadata["spec_min_freq"] / 1e6) + " MHz to " +
            str(metadata["spec_max_freq"] / 1e6) + " MHz.\n")
      print("\nThese are the timestamps of each one: \n", data.index.values)
   
   print("\nNow, choose the way you want show the data.\n" +
         "[1] Plot a single spectrum.\n" +
         "[2] Plot all spectrums in an animation.\n" +
         "[3] Plot waterfall (a.k.a. heatmap).\n" +
         "[4] Plot the integrated power density of a frequency range over time.\n" +
         "[5] Print a single spectrum in the terminal.\n" +
         "[6] Print metadata and frequencies in the terminal.\n" +
         "[7] Change the Exp file.\n" + "[8] Exit.\n")
   
   Option = int(input("Enter the number of the option you want to choose: "))
   
   
   if Option == 1:
      print("\nYou have chosen to plot a single spectrum.\n")
      print("Choose the spectrum you want to plot.\n")
      print(
          "Enter the timestamp with format 'hh-mm-ss' and the closest time will be displayed. Days are considered adding 24 h.\n"
      )
      selection = input("Enter the timestamp correctly formatted: ")
      selection = closest_time(selection, data.index.values)
      print("\nThe closest time is " + str(data.index.values[selection]))
      
      fig, ax = plt.subplots()
      ax.fill_between(frequencies / 1e6, data.iloc[selection,:].values)
      ax.text(0.5,
           0.1,
           data.index.values[selection],
           horizontalalignment='center',
           verticalalignment='center',
           transform=ax.transAxes)
      ax.set_ylabel(r'Relative Power / $\mathrm{dB/Hz}$')
      ax.set_xlabel(r'Frequency / $\mathrm{MHz}$')
      ax.set_title(metadata["filename"])
      plt.tight_layout()
      plt.show()

   if Option == 2:
      print("You have chosen to plot an animation of all the sprectums.\n")

      fig, ax = plt.subplots()

      def animate(i):
         
         ax.clear()
         ax.fill_between(frequencies / 1e6, data.iloc[i,:].values)
         ax.text(0.5,0.1,data.index.values[i], horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
         ax.set_ylim(data.values.min()*1.05, data.values.max()*0.9)
         ax.set_ylabel(r'Relative Power $\mathrm{dB/Hz}$')
         ax.set_xlabel(r'Frequency $\mathrm{MHz}$')
         ax.set_title(metadata["filename"])
         plt.tight_layout()
         

      if len(data) == 1:
         animate(0)
      else:
         anim = animation.FuncAnimation(fig,
                                           animate,
                                           frames=len(data),
                                           interval=np.max(
                                               [1e4 / len(data), 1000]))
      plt.show()
      
   if Option == 3:
      print("You have chosen to plot the waterfall of the spectrums.\n")

      fig, ax = plt.subplots()
      ax.pcolor(data.columns.values/1e6, data.index.values, data.values, cmap ='viridis')
      ax.set_xlabel(r'Frequency / $\mathrm{MHz}$')
      plt.setp(ax.get_xticklabels(), rotation=90, ha="right",
         rotation_mode="anchor")
      ax.set_ylabel('Time')
      plt.show()
      
      
   if Option == 4:
      print(
          "You have chosen to plot the integrated power density of a frequency range.\n"
      )
      print("Choose the frequency range you want to plot.\n")
      print(
          "Enter the bottom frequency of the integration range in MHz.\n"
      )
      f_min = float(input("Enter the bottom frequency: "))
      f_min = closest(f_min*1e6, frequencies)

      while frequencies[f_min]<metadata["spec_min_freq"]:
         print("The frequency you entered is lower than the minimum frequency of the spectrums, ",metadata["spec_min_freq"]/1e6," MHz. Please enter a higher frequency.\n")
         f_min = float(input("Enter the bottom frequency: "))
         f_min = closest(f_min*1e6, frequencies)
      
      print("Enter the top frequency of the integration range in MHz.\n")
      f_max = float(input("Enter the top frequency: "))
      f_max = closest(f_max*1e6, frequencies)

      while frequencies[f_max]>metadata["spec_max_freq"] and frequencies[f_min]<frequencies[f_max]:
         print("The top frecuency must be between the bottom frequency ", frequencies[f_min]/1e6," MHz and the maximum frequency of the spectrum", metadata["spec_max_freq"]/1e6, " MHz.\n")
         f_max = float(input("Enter the top frequency: "))
         f_max = closest(f_max*1e6, frequencies)

      Int = np.trapz(data.iloc[:,f_min:f_max], x=frequencies[f_min:f_max], axis=1)

      fig, ax = plt.subplots()
      ax.plot(data.index.values, Int, "rx")
      ax.set_ylabel(r'Integrated Relative Power / $\mathrm{dB}$')
      ax.set_xlabel(r'Timestamp')
      plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
         rotation_mode="anchor")
      ax.set_title(metadata["filename"])
      plt.tight_layout()
      plt.show()
      
   if Option == 5:
      print("You have chosen to print a single spectrum in the terminal.\n")
      print("Choose the spectrum you want to print.\n")
      print(
          "Enter the timestamp with format 'hh-mm-ss' and the closest time will be displayed. Days are considered adding 24 h.\n"
      )
      selection = input("Enter the timestamp correctly formatted: ")
      selection = closest_time(selection, data.index.values)
      print("\nThe closest time is " + str(data.index.values[selection]))
      print("\nThw corresponding sprectrum is:\n", data.iloc[selection,:])
   if Option == 6:
      print("You have chosen to print the metadata and frequencies in the terminal.\n")
      print(metadata)
      print(frequencies)
   if Option == 7:
      Option = 7

   if Option == 8:
      Option = 8
      print("Thanks for using SDRSpectrumAnalyzer!")
