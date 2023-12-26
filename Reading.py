from numpy import load
import matplotlib.pyplot as plt
import matplotlib.animation as animation

#data = load('/home/mjtueros/TrabajoTemporario/SDR/Exp__2023_12_26__13_19_54.npz', allow_pickle = True)
data = load('/home/mjtueros/TrabajoTemporario/SDR/Exp__2023_12_26__11_10_00.npz', allow_pickle = True)

filename, exp_time, spec_period, spec_repetitions, spec_min_freq, spec_max_freq, mes_samplerate, mes_sample_num = data["Metadata"]

print(data["Metadata"])
print(data["frequencies"])
print(data.files)
fig, ax = plt.subplots()

# Define the animation function
def animate(i):
	# Plot the data
	ax.clear()
	ax.fill_between(data["frequencies"]/1e6,data[data.files[i+2]])
	
	ax.text(0.5,0.1,data.files[i+2], horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
	#ax.set_xlim(99, 101)
	#ax.set_ylim(0, 80)
	ax.set_ylabel(r'Relative Power $\mathrm{dB}$')
	ax.set_xlabel(r'Frequency $\mathrm{MHz}$')
	ax.set_title(filename)

# Create the animation
if len(data.files) == 3:
    animate(0)
else:
    anim = animation.FuncAnimation(fig, animate, frames=len(data)-2, interval=1000)


# Show the animation
plt.show()
