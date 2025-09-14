import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
#import seaborn as sn


def _ensure_timedelta(val):
    """Convierte strings 'HH-MM-SS' o ya timedelta64/pd.Timedelta a np.timedelta64."""
    if isinstance(val, str):
        val = val.replace("-", ":")
        return pd.to_timedelta(val)
    elif isinstance(val, (np.timedelta64, pd.Timedelta)):
        return np.timedelta64(val)
    else:
        raise TypeError(f"Formato no soportado: {type(val)}")


def closest_time(x, v):
    """
    Devuelve el índice del valor en v cuya diferencia absoluta con x es mínima.
    Acepta strings 'HH-MM-SS' o timedelta64.
    """
    # Convertir x
    x = _ensure_timedelta(x)

    # Convertir v a np.array de timedelta64
    v = np.array([_ensure_timedelta(vi) for vi in v], dtype="timedelta64[ns]")

    diffs = np.abs(v - x)
    return int(np.argmin(diffs))


def closest(x, v):
   """
   Devuelve el índice del valor en v (array de float64) más cercano a x.
   """
   v = np.asarray(v, dtype=float)
   diffs = np.abs(v - float(x))
   return int(np.argmin(diffs))


print("\n_____________________________________________________________________________\n",
       "This file reads the data from the Exp file and can express it in several ways.\n"
)

Option = 8

while Option != 9:
   if Option == 8:
      path = str(input("\n Enter the Exp file's path: "))

      arrays = dict(np.load(path, allow_pickle=True))
      del path

      metadata = {}
      times = {}

      if len(arrays["Metadata"]) == 8: # This conditional nust be eliminated once no more old exp files are left
         
         a = [
            "filename", "exp_time", "spec_period", "spec_repetitions",
            "spec_min_freq", "spec_max_freq", "seg_samplerate",
            "seg_sample_num"
         ]

      elif len(arrays["Metadata"]) == 11:
         
         a = [
            "filename", "exp_time", "exp_gain", "spec_period", "spec_repetitions",
            "spec_min_freq", "spec_max_freq", "seg_samplerate",
            "seg_sample_num","seg_parts", "annotations"
         ]

         times["exp_init_timestamp"] = arrays["times"][0]
         for i in range(len(arrays)-3):
            times[list(arrays.keys())[i+2]] = arrays["times"][i+1]
      
      for i in range(len(arrays["Metadata"])):
         
         if a[i] == "filename" or a[i] == "annotations":
            metadata[a[i]] = str(arrays["Metadata"][i])
         else:
            metadata[a[i]] = float(arrays["Metadata"][i])
      
      frequencies = arrays["frequencies"]
      
      del arrays["times"], a, arrays["Metadata"], arrays["frequencies"]

      data = pd.DataFrame.from_dict(arrays, orient="index", columns=frequencies)
      
      data.columns = np.array(data.columns, dtype= float)
            
      # ------------------ Detectar y convertir índices 'HH-MM-SS' a datetime64 ------------------
      idx_as_str = data.index.astype(str)

      # comprobamos si *todos* los índices tienen el formato 'HH-MM-SS' (acepta opcionalmente .sss)
      is_hhmmss = idx_as_str.str.match(r'^\d{2}-\d{2}-\d{2}(?:\.\d+)?$').all()

      if is_hhmmss:
         # parsear fecha/hora desde metadata['filename']
         fname = metadata.get("filename", "")
         m = re.search(r"Exp__(\d{4})_(\d{2})_(\d{2})__(\d{2})_(\d{2})_(\d{2})", fname)
         if not m:
            raise ValueError(f"Formato inesperado en filename: {fname!r}")

         exp_start = pd.Timestamp(*map(int, m.groups()))
         day0 = exp_start.normalize()   # midnight del día del experimento

         # convertir 'HH-MM-SS' -> 'HH:MM:SS' y luego a Timedelta
         time_strings = idx_as_str.str.replace("-", ":")
         time_offsets = pd.to_timedelta(time_strings, errors="coerce")

         if time_offsets.isna().any():
            bad = list(data.index[time_offsets.isna()])[:10]
            raise ValueError(f"Algunos índices no pudieron convertirse a HH:MM:SS. Ejemplos: {bad}")

         # Timestamps asumiendo el mismo día
         base_ts = day0 + time_offsets

         # --- nueva y más robusta detección de 'wrap' (cruce de medianoche) ---
         # calculamos segundos desde medianoche (float)
         seconds = (time_offsets / pd.Timedelta(1, "s")).astype(float)

         # wrap[i] = True cuando seconds[i] < seconds[i-1] --> eso indica paso a siguiente día
         if len(seconds) > 1:
            wraps_bool = np.concatenate(([False], seconds[1:] < seconds[:-1]))
         else:
            wraps_bool = np.array([False])

         day_adds = np.cumsum(wraps_bool.astype(int))  # 0,0,...,1,1,...,2,...

         final_index = pd.DatetimeIndex(base_ts + pd.to_timedelta(day_adds, unit="D"))
         data.index = final_index
      # si no son HH-MM-SS no se toca el índice
      # ----------------------------------------------------------------------------------------


      print("\nThe Exp file named " + str(metadata["filename"]) +
            " was loaded correctly.")
      print("\nIt contains " + str(len(data)) + " spectrums from " +
            str(metadata["spec_min_freq"] / 1e6) + " MHz to " +
            str(metadata["spec_max_freq"] / 1e6) + " MHz.\n")
      print("\nThese are the timestamps of each one: \n", data.index)
      if len(metadata) == 11:
         print("\nConsider following anotations:",metadata["annotations"])
   
   print("\nNow, choose the way you want show the data.\n" +
         "[1] Plot a single spectrum.\n" +
         "[2] Plot all spectrums in an animation.\n" +
         "[3] Plot waterfall (a.k.a. heatmap).\n" +
         "[4] Plot the integrated power density of a frequency range over time.\n" +
         "[5] Export data to CSV.\n"
         "[6] Print a single spectrum in the terminal.\n" +
         "[7] Print metadata and frequencies in the terminal.\n" +
         "[8] Change the Exp file.\n" +
         "[9] Exit.\n")
   
   Option = int(input("Enter the number of the option you want to choose: "))
   
   
   if Option == 1:
      print("\nYou have chosen to plot a single spectrum.\n")

      fig, ax = plt.subplots()

      if len(data) == 1:
         ax.fill_between(frequencies / 1e6, data.iloc[0,:].values)
         ax.text(0.5,
           0.1,
           data.index.values[0],
           horizontalalignment='center',
           verticalalignment='center',
           transform=ax.transAxes)
         
      elif len(data) != 1:
         # Mostrar las fechas disponibles
         available_days = pd.to_datetime(data.index.normalize().unique())
         print("\nAvailable dates in this experiment:")
         for d in available_days:
            print(" -", d.date())

         # Elegir fecha
         day_choice = pd.to_datetime(input("\nEnter the date you want (YYYY-MM-DD): ")).normalize()

         # Filtrar datos de ese día
         mask = data.index.normalize() == day_choice
         day_data = data.loc[mask]

         # Elegir hora
         time_choice = input("Enter the time (HH:MM:SS or HH,MM,SS): ").replace(",", ":")
         td_choice = pd.to_timedelta(time_choice)

         # Buscar índice más cercano
         selection = closest_time(td_choice, day_data.index - day_choice)
         print("\nThe closest timestamp is:", day_data.index[selection])
         
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
      C = ax.pcolor(data.columns.values/1e6, data.index.values, data.values, cmap ='viridis')
      ax.set_xlabel(r'Frequency / $\mathrm{MHz}$')
      plt.setp(ax.get_xticklabels(), rotation=90, ha="right",
         rotation_mode="anchor")
      ax.set_ylabel('Time')
      fig.colorbar(C, ax=ax)
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

      Int = np.trapezoid(data.iloc[:,f_min:f_max], x=frequencies[f_min:f_max], axis=1)

      fig, ax = plt.subplots()
      ax.plot(data.index.values, Int, "r-")
      ax.set_ylabel(r'Integrated Relative Power / $\mathrm{dB}$')
      ax.set_xlabel(r'Timestamp')
      plt.setp(ax.get_xticklabels(), rotation=90, ha="right",
         rotation_mode="anchor")
      ax.locator_params(axis='x', nbins=len(data.index.values)//4)
   
      ax.set_title("Integrated power between "+str(round(frequencies[f_min]/1e6))+" MHz and "+str(round(frequencies[f_max]/1e6))+" MHz for "+str(metadata["filename"]))
      plt.tight_layout()
      plt.show()
      
   if Option == 5:
      
      print("You have chosen to export the DataFrame to CSV.\n")
         
      default_name = metadata["filename"] + ".csv"
      
      out_path = input(f"Enter output CSV file path (default: {default_name}): ")
      
      if out_path.strip() == "":
         out_path = default_name

      # Guardar con índice datetime64
      data.to_csv(out_path, index_label="Timestamp")
      print(f"\nData successfully exported to {out_path}\n")
      
   if Option == 6:
      print("You have chosen to print a single spectrum in the terminal.\n")
      print("Choose the spectrum you want to print.\n")
      print(
          "Enter the timestamp with format 'hh-mm-ss' and the closest time will be displayed. Days are considered adding 24 h.\n"
      )
      selection = input("Enter the timestamp correctly formatted: ")
      selection = closest_time(selection, data.index.values)
      print("\nThe closest time is " + str(data.index.values[selection]))
      print("\nThw corresponding sprectrum is:\n", data.iloc[selection,:])
      
   if Option == 7:
      print("You have chosen to print the metadata and frequencies in the terminal.\n")
      print(metadata)
      print(frequencies)
      print(times)
      
   if Option == 8:
      Option = 8

   if Option == 9:
      Option = 9
      print("Thanks for using SDRSpectrumAnalyzer!")
