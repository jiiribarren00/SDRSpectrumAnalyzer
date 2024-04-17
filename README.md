# SDR Spectrum Analyzer
*by Juan I. Iribarren and Matías J. Tueros*

## Description

A Python library for analyzing the VHF radio spectrum using low-cost SDR devices.

## Prerequisites

There exist some libraries needed to use SDRSpectrumAnalyzer.
Some of them are common and you may already have them installed in your system `numpy`, `matplotlib`, `pandas` and `seaborn`.

You may have not installed `rtl-sdr` library yet. In this case use `pip install pyrtlsdr` or visit [PyPI](https://pypi.org/project/pyrtlsdr/).
When using this library, you will need special drivers for your SDR - Oporative Systems usually installs some DVB drivers which are not suitable
for us -, those from [RTL-SDR](https://www.rtl-sdr.com). Follow these steps to install:
  
  1. Delete older drivers:

 	sudo apt purge ^librtlsdr

	sudo rm -rvf /usr/lib/librtlsdr* /usr/include/rtl-sdr* /usr/local/lib/librtlsdr* /usr/local/include/rtl-sdr* /usr/local/include/rtl_* /usr/local/bin/rtl_*
2. Clone the repository and install it. Pay atention to the 3rd line which should be slightly different from what the repository owners states.

		sudo apt-get install libusb-1.0-0-dev git cmake pkg-config
		
		git clone https://github.com/rtlsdrblog/rtl-sdr-blog
		
		cd rtl-sdr-blog/
		
		mkdir build
		
		cd build
		
		cmake ../ -DINSTALL_UDEV_RULES=ON
		
		make
		
		sudo make install
		
		sudo cp ../rtl-sdr.rules /etc/udev/rules.d/
		
		sudo ldconfig

 4. Connect your RTL-SDR (or compatible) device and change it's default drivers. After the following line you may need to restart your device.

		echo 'blacklist dvb_usb_rtl28xxu' | sudo tee --append /etc/modprobe.d/blacklist-dvb_usb_rtl28xxu.conf

	If you want to avoid the restart, use this line which avoids the restart but isn't permanent: `sudo rmmod dvb_usb_rtl28xxu`

 	4. Finally, test everthing is ok running a `rtl_test`.

## Usage

Currently two programs are ready to use `Reading.py` and `SDR_Spectrometer.py`. The latter creates a `.npz` file which contains metadata,
frequencies and a timelapsed psd for specified portion of VHF spectrum. The other file reads the `.npz` file and can display it in several ways:
	1. It cans plot a single spectrum of those contained in the .npz file
 	2. plot an animation of the spectrum over time
	3. plot a waterfall diagram of the psd in time
 	4. or plot a portion of the spectrum integrated over time.

## Roadmap

* In development

	- [ ] Rewriting the code from SoapySDR, this library allows user to get samples from devices other than Rtl-Sdr.

* In a close future

	- [ ] Study samples, gain, windowing functions and possible optimizations.
 	- [ ] Implementation of pyFFT library which is fastar than np.fft.
	- [ ] Implement automatic background removal.

* Goals

	- [ ] Struggle to sense the galatic noise.
	- [ ] Calibrate the sensitivity and frecuency.

## Contributing

The project is currently too young, hence we won't require any additional contributions.
If there are new ideas or recommendations, please contact Juan I. Iribarren at [juan.iribarren@fisica.unlp.edu.ar](mailto:juan.iribarren@fisica.unlp.edu.ar) .

## License

[License GNU General Public Lincense 3.0](https://www.gnu.org/licenses/gpl-3.0.html)


