import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from python_model.utils.logger import get_logger
from python_model.utils.utils import utils


logger = get_logger(__name__)


class DSP:
    def __init__(self,sample_rate,state = 0):
        self.sampleRate = sample_rate
        self.state = state

        #CONSTANTS
        self.BARKERCODE = 'BARKER'
        self.LINEARFM   = 'LFM'

        self.BARKER_CODES = {'13':np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1]),
                             '11':np.array([1,1,1,-1,-1,-1,1,-1,-1,1,-1]),
                              '7':np.array([1,1,1,-1,-1,1,-1]),
                              '5':np.array([1,1,1,-1,1]),
                              '4':np.array([1,1,-1,1]),
                              '3':np.array([1,1,-1]),
                              '2':np.array([1,-1]),
                            }


""" 

TODO: Clean up: Create a function to do some basics.
Bit manipulation - Util
Plot waveform/correlation plot
Phase Shift (Input waveform would be great) -Util?
MatchFilter w/ waveform input
MatchFilter Normalization for better detection 
Plot FFT - Util
Message Packing
buildHeader 
decodeHeader


matchFilter(signal,waveform)

normalizeFilter(signal,waveform)

pipeline
RX signal
↓
derotate (remove carrier)
↓
baseband IQ samples
↓
integrate over symbol
↓
one complex symbol
↓
angle / decision
↓
bits

"""

class tx(DSP):
    def __init__(self,code_len,amplitude,chips_per_symbol,carrier_frequency,sample_rate):
        super().__init__(sample_rate,0)
        try:
            self.barker_code = self.BARKER_CODES[code_len] # Barker code length
            self.code_len = len(self.barker_code) # Code length is always the length of the code
            self.chips_per_symbol = chips_per_symbol #Oversampling factor. How many time we want to sample each chip
            self.carrier_frequency = carrier_frequency #Carrier Frequency for signal
            self.num_of_chips = self.code_len # How many chips we have (It should match length of barker code) 
            self.amplitude = amplitude
            self.bit_rate = self.sampleRate/self.chips_per_symbol
        except KeyError as e:
            logger.error(f"Code length Error: {e}\nAvailable Code lengths are {list(self.BARKER_CODES.keys())}")
        except Exception as e:
            logger.error(f"Input parameters could not be set.{e}")

        #Header specification 
        self.msg_field_length = 8
        self.version_field_length = 4
        self.pack_ID_field_length = 8
        self.flag_field_length = 2


        self.baseband_chips = np.repeat(self.barker_code,self.chips_per_symbol) #Creating our 1s and 0s 
        self.time_axis = np.arange(0,self.code_len*self.chips_per_symbol)/self.sampleRate #Creating our time axis for ploting signal
        #We can appearently match filter at baseband. No need to keep wavefrom as passband
        self.waveform = self.amplitude * self.baseband_chips * np.exp((2*np.pi*self.carrier_frequency*self.time_axis)*1j) #Creating our wave by combing carrier, baseband chips, amplitude

    def bin_to_baseband(self,msg):
        # bin_msg = utils.text_to_bits(msg)
        raw_msg = utils.to_bits(msg) #convert to binary values
        raw_msg = utils.replace_value(raw_msg,0,-1) #replace 0 with -1 so we can multiply 
        raw_msg = np.repeat(raw_msg,self.chips_per_symbol)
        return raw_msg

    def generate_header(self, version, length, flags, packetID):
        #Head should contain the following items
        # Version: For different RX decode types
        # Length: How long the message should be
        # Flags: Mainly for start and stop bits
        # packet ID: in case messages are not recieved in the correct order

        # Binary Size:
        # Version: 2 bit string.
        # Length: We may need to add class variable? for no 8 bits
        # Flags: 2 bit string.
        # packet ID: 2^num_packets for now 64. Add to class variable 
        version_bits = utils.int_to_bits(version,self.version_field_length)
        length_bits = utils.int_to_bits(length,self.msg_field_length)
        flags_bits = utils.int_to_bits(flags,self.flag_field_length)
        packetID_bits = utils.int_to_bits(packetID,self.pack_ID_field_length)

        header = version_bits + length_bits + flags_bits + packetID_bits
        logger.info(f"Header:{header}")
        logger.info(f"Version:{version_bits}\nLength:{length_bits}")
        logger.info(f"Flags:{flags_bits}\npacketID:{packetID_bits}")


        raw_header = utils.replace_value(header,0,-1)
        logger.info(raw_header)
        raw_header = np.repeat(raw_header,self.chips_per_symbol)
        time = np.arange(0,len(raw_header))/self.sampleRate
        tmp_carrier = self.amplitude * np.exp((2*np.pi*self.carrier_frequency*time)*1j)
        msg = tmp_carrier*raw_header
        header = msg
        return (header,raw_header)

    def bpsk_modulation(self,bits,plot=False):
        #We will need to ensure bits are in the correct format
        tmp_bits = bits
        bits = utils.to_bits(bits)
        bits = utils.replace_value(bits,0,-1)

        #We will use the over sampling factor for the waveform
        msgBits = np.repeat(bits,self.chips_per_symbol)
        #Create time axis
        t=np.arange(0,len(msgBits))/self.sampleRate
        baseband_signal = np.exp((2*np.pi*self.carrier_frequency*t)*1j)
        signal = baseband_signal*msgBits

        if plot:
            fig,ax = plt.subplots(nrows=2,ncols=1,figsize=(10,6))
            
            ax[1].plot(t,np.real(signal))
            ax[0].plot(t,msgBits)

            ax[0].set_title(f"Msg Signal at baseband")
            ax[0].set_xlabel('Time (s)')
            ax[0].set_ylabel('Amplitude')
            ax[0].grid(True)

            ax[1].set_title(f"Msg Signal at {self.carrier_frequency} Hz")
            ax[1].set_xlabel('Time (s)')
            ax[1].set_ylabel('Amplitude')
            ax[1].grid(True)
            plt.tight_layout()
            plt.show()

        logger.debug(f"We are encoding binary word {tmp_bits} with carrier waveform")

    def packetize(self,payload_bits,header_bits):
        baseband_payload_bits = self.bin_to_baseband(payload_bits)
        baseband_header_bits = header_bits
        time = np.arange(0,len(self.baseband_chips)+len(baseband_header_bits)+len(baseband_payload_bits))/self.sampleRate
        baseband_msg = np.append(self.baseband_chips,baseband_header_bits)
        baseband_msg = np.append(baseband_msg,baseband_payload_bits)
        passband_msg = baseband_msg * np.exp((2*np.pi*self.carrier_frequency*time)*1j) #DUC to passband
        return (passband_msg,baseband_msg,time)

class rx(DSP):
    def __init__(self):
        pass

    def decodeHeader(self,header):

        t = np.arange(0,len(header))/self.sampleRate
        header = header * np.exp(-1j*(2*np.pi*self.carrier_frequency*t))
        idx = 0
        version = self.decode_field(header[idx:idx + 2*self.chips_per_symbol])
        idx += 2*self.chips_per_symbol

        length = self.decode_field(header[idx:idx + 8*self.chips_per_symbol])
        idx += 8*self.chips_per_symbol

        flags = self.decode_field(header[idx:idx + 2*self.chips_per_symbol])
        idx += 2*self.chips_per_symbol

        packetId = self.decode_field(header[idx:idx + 6*self.chips_per_symbol])

        print(version, length, flags, packetId)

    def decode_field(self,field_bits):
        bits = []
        for i in range(0, len(field_bits), self.chips_per_symbol):
            chunk = field_bits[i:i+self.chips_per_symbol]
            symbol = np.sum(chunk)
            bits.append(1 if np.real(symbol) > 0 else 0)
        return bits

class BarkerWaveforms(DSP):
    def __init__(self,code_len,amplitude,chips_per_symbol,carrier_frequency,sample_rate):
        super().__init__(sample_rate,0)
        try:
            self.barker_code = self.BARKER_CODES[code_len] # Barker code length
            self.code_len = len(self.barker_code) # Code length is always the length of the code
            self.chips_per_symbol = chips_per_symbol #Oversampling factor. How many time we want to sample each chip
            self.carrier_frequency = carrier_frequency #Carrier Frequency for signal
            self.num_of_chips = self.code_len # How many chips we have (It should match length of barker code) 
            self.amplitude = amplitude
        except KeyError as e:
            logger.error(f"Code length Error: {e}\nAvailable Code lengths are {list(self.BARKER_CODES.keys())}")
        except Exception as e:
            logger.error(f"Input parameters could not be set.{e}")

        self.baseband_chips = np.repeat(self.barker_code,self.chips_per_symbol)
        self.time_axis = np.arange(0,self.code_len*self.chips_per_symbol)/self.sampleRate
        self.waveform = self.amplitude * self.baseband_chips * np.exp((2*np.pi*self.carrier_frequency*self.time_axis)*1j)
        self.waveformFilter = self.amplitude * self.baseband_chips * np.exp((2*np.pi*self.carrier_frequency*self.time_axis)*1j)

        self.PACKET_SIZE = 8 #Bits

        #Some parameters for the bpsk BarkerWaveforms
        self.PRI = 1000
        self.DUTY_CYCLE = 0.5
        self.PREZEROS = 100 #SAMPLES
        self.POSTZEROS = 100 #SAMPLES
        self.PULSEWIDTH = len(self.time_axis)+self.PREZEROS+self.POSTZEROS
        self.WINDOW_LEN = round(self.PULSEWIDTH/self.DUTY_CYCLE)
        self.detection_threshold = 0.75


        #Item for simulation
        self.sim_tx_signal = None
        self.sim_tx_signal_time = None
        self.sim_rx_signal = None
        self.sim_rx_signal_time = None

    def shiftPhase(self,phase_offset=0):
        self.waveform = self.waveformFilter * np.exp(1j * phase_offset)

    def plotWaveform(self):
        plt.figure(figsize=(10,6))
        plt.subplot(2,1,1,)
        plt.plot(self.time_axis,self.baseband_chips,'.-',label='Baseband 13-Length Baker Code')
        plt.title('Barker-13 Baseband Sequnce (Rectangular Pulse)')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude (+1 or -1)')
        plt.grid(True)
        plt.axis([0,self.time_axis[-1],-1.5,1.5])


        # Plot the modulated waveform
        plt.subplot(2, 1, 2)
        plt.plot(self.time_axis, np.real(self.waveform), label='Modulated Barker-13 Waveform')
        plt.title(f'Phase Modulated Barker-13 Waveform ({self.carrier_frequency/1e3:.1f} kHz carrier)')
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.tight_layout() # Adjust subplot params so that the subplot(s) fits in to the figure area.
        plt.show()

    def plotFrequencySpecturm(self):
        fft_vals = np.fft.fft(self.waveform)
        fft_len = len(fft_vals)
        fft_vals = abs(fft_vals/fft_len) #Scale down due to signal increase with each samples.
        #Create the x_axis, actual frequency values.
        k = np.arange(fft_len)
        freq = k*self.sampleRate/fft_len
        plt.figure(figsize=(12,6))
        plt.subplot(121)
        plt.plot(freq,fft_vals)
        plt.show()

    def matchFilter(self,signal,plot=False):
        data = np.correlate(signal,self.waveformFilter,mode='full')
        #normalize data
        norm_data = data/np.sum(np.abs(self.waveform)**2)
        time_axis = np.arange(len(norm_data))/self.sampleRate
        if plot:
            plt.figure()
            plt.plot(time_axis,np.real(norm_data))
            plt.show()
        return (data,norm_data,time_axis)

    def simulateSignal(self,sig_size=1000,delay=0,plot=False):
        #We will assume sig_size and delay will be samples not time for now
        signal = np.random.normal(0,1,sig_size)+ 1j*np.random.normal(0,1,sig_size)
        logger.debug(f"Length\nWaveform:{len(self.waveform)}\nSignal:{len(signal[delay:delay+len(self.waveform)])}\nPlot:{plot}")
        signal[delay:delay+len(self.waveform)] = self.waveform + signal[delay:delay+len(self.waveform)]
        time_signal = np.arange(sig_size)/self.sampleRate

        (match_sig,match_norm,match_time)=self.matchFilter(signal=signal)
        peak_index = np.argmax(np.abs(match_sig))
        peak_time = match_time[peak_index]
        peak_amp = match_sig[peak_index]
        peak_phase = np.angle(match_sig[peak_index])
        print(f"Peak is found at {peak_time} with an amplitude of {peak_amp} with phase {peak_phase}")

        if plot:
            plt.figure(figsize=(10,6))
            plt.subplot(4,1,1,)
            plt.plot(self.time_axis,self.baseband_chips,'.-',label='Baseband 13-Length Baker Code')
            plt.title('Barker-13 Baseband Sequnce (Rectangular Pulse)')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude (+1 or -1)')
            plt.grid(True)
            plt.axis([0,self.time_axis[-1],-1.5,1.5])


            # Plot the modulated waveform
            plt.subplot(4, 1, 2)
            plt.plot(self.time_axis, np.real(self.waveform), label='Modulated Barker-13 Waveform')
            plt.title(f'Phase Modulated Barker-13 Waveform ({self.carrier_frequency/1e3:.1f} kHz carrier)')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.tight_layout() # Adjust subplot params so that the subplot(s) fits in to the figure area.


            plt.subplot(4,1,3)
            plt.title('Simulated Signal with Random Noise')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(time_signal,np.real(signal))

            plt.subplot(4,1,4)
            plt.title('Match Filter of Simulated Signal with Random Noise')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(match_time,np.abs(match_sig))

            plt.show()
        return (time_signal,signal)

    def packetMsg(self,msg,plot=False):

        num_of_packets = int(len(msg)/self.PACKET_SIZE)

        #For now we will work on sending one packet.abs
        signal_len = self.WINDOW_LEN * self.PACKET_SIZE
        signal = np.random.normal(0,1,signal_len)+1j*np.random.normal(0,1,signal_len)
        time_signal = np.arange(len(signal))/self.sampleRate

        for nSt,bit in enumerate(msg):
            if bit == "1":
                phase = np.pi
            else:
                phase = 0
            self.shiftPhase(phase)
            start_loc = self.WINDOW_LEN*nSt + self.PREZEROS
            end_loc = start_loc + len(self.waveform)
            signal[start_loc:end_loc] = self.waveform

        (match_sig,match_norm,match_time)=self.matchFilter(signal=signal)

        mag = np.abs(match_norm)
        peaks, props = find_peaks(
                                    mag,
                                    height=self.detection_threshold,
                                    distance=len(self.waveform) // 2
                                )
                                
        for idx,peak in enumerate(peaks):
            peak_time = match_time[peak]
            peak_amp = match_sig[peak]
            peak_phase = np.angle(match_sig[peak])
            logger.info(f"Peak {idx+1} is found at {peak_time:.6f} seconds with an amplitude of {peak_amp:.2f} and phase {peak_phase:.2f} radians")

        if plot:
            plt.figure(figsize=(10,6))
            plt.subplot(2,1,1)
            plt.title('Simulated Signal with Random Noise')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(time_signal,np.real(signal))

            plt.subplot(2,1,2)
            plt.title('Match Filter of Simulated Signal with Random Noise')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(match_time,np.abs(match_norm))
            plt.show()
            
    def sendMsg(self,textMsg,plot=False):
        #Convert text to binary
        binaryMsg = ''.join(format(ord(char), '08b') for char in textMsg)
        logger.info(f"Message: {textMsg}")
        logger.info(f"Binary Message: {binaryMsg}")
        num_of_packets = int(len(binaryMsg)/self.PACKET_SIZE)
        # We need to handle message size. If the message size is not a multiple of the packet size, we can pad it with zeros.
        if len(binaryMsg) % self.PACKET_SIZE != 0:
            padding_size = self.PACKET_SIZE - (len(binaryMsg) % self.PACKET_SIZE)
            binaryMsg += '0' * padding_size
            logger.info(f"Binary Message after padding: {binaryMsg}")

        logger.info(f"Number of packets to send: {num_of_packets}")
        logger.info(f"Packet size: {self.PACKET_SIZE} bits")
        logger.info(f"Total bits to send: {len(binaryMsg)} bits")
        logger.info(f"Total symbols to send: {len(binaryMsg) // self.PACKET_SIZE} symbols")


        num_of_packets = int(len(binaryMsg)/self.PACKET_SIZE)

        #For now we will work on sending one packet.
        signal_len = self.WINDOW_LEN * self.PACKET_SIZE*num_of_packets
        signal = np.random.normal(0,1,signal_len)+1j*np.random.normal(0,1,signal_len)
        time_signal = np.arange(len(signal))/self.sampleRate

        for nSt,bit in enumerate(binaryMsg):
            if bit == "1":
                phase = np.pi
            else:
                phase = 0
            self.shiftPhase(phase)
            start_loc = self.WINDOW_LEN*nSt + self.PREZEROS
            end_loc = start_loc + len(self.waveform)
            signal[start_loc:end_loc] = self.waveform

        (match_sig,match_norm,match_time)=self.matchFilter(signal=signal)

        mag = np.abs(match_norm)
        peaks, props = find_peaks(
                                    mag,
                                    height=self.detection_threshold,
                                    distance=len(self.waveform) // 2
                                )
                                
        for idx,peak in enumerate(peaks):
            peak_time = match_time[peak]
            peak_amp = match_sig[peak]
            peak_phase = np.angle(match_sig[peak])
            logger.info(f"Peak {idx+1} is found at {peak_time:.6f} seconds with an amplitude of {peak_amp:.2f} and phase {peak_phase:.2f} radians")

        #TODO: Need to create a function that we can pass data into and it will plot.
        if plot:
            plt.figure(figsize=(10,6))
            plt.subplot(2,1,1)
            plt.title('Simulated Signal with Random Noise')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(time_signal,np.real(signal))

            plt.subplot(2,1,2)
            plt.title('Match Filter of Simulated Signal with Random Noise')
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(match_time,np.abs(match_norm))
            plt.show()
            
    def simTxRx(self,textMsg,plot=False):
        #TODO: We want to create function that create the whole message so we can use it in a more complex simulation.
        raw_msg = self.to_bits(textMsg) #convert to binary values
        raw_msg = self.replace_value(raw_msg,0,-1) #replace 0 with -1 so we can multiply 
        raw_msg = np.repeat(raw_msg,self.chips_per_symbol)

        raw_header = self.buildHeader(1,len(textMsg),1,0)
        raw_header = self.replace_value(raw_header,0,-1)
        raw_header = np.repeat(raw_header,self.chips_per_symbol)
        time = np.arange(0,len(raw_msg))/self.sampleRate
        tmp_carrier = self.amplitude * np.exp((2*np.pi*self.carrier_frequency*time)*1j)
        msg = tmp_carrier*raw_msg


        time = np.arange(0,len(raw_header))/self.sampleRate
        tmp_carrier = self.amplitude * np.exp((2*np.pi*self.carrier_frequency*time)*1j)
        header = tmp_carrier*raw_header

        txSignal = np.append(self.waveform, header)
        txSignal = np.append(txSignal,msg)
        time = np.arange(0,len(txSignal))/self.sampleRate

        sig_size = len(time)*5
        delay = int(np.random.normal(0,1,1))
        signal = np.random.normal(0,1,sig_size)+ 1j*np.random.normal(0,1,sig_size)
        signal[delay:delay+len(txSignal)] = txSignal + signal[delay:delay+len(txSignal)]
        time_signal = np.arange(sig_size)/self.sampleRate

        (match_sig,match_norm,match_time)=self.matchFilter(signal=signal)
        peak_index = np.argmax(np.abs(match_norm))
        peak_time = match_time[peak_index]
        peak_amp = match_sig[peak_index]
        peak_phase = np.angle(match_sig[peak_index])
        print(f"Peak is found at {peak_time} with an amplitude of {np.real(peak_amp)} with phase {peak_phase}")

        #Need to grab the data from the waveform
        # We will use peak_index and it will be our starting point
        headerAndMsg = signal[peak_index+len(self.waveform):len(txSignal)]

        #We will assume 20 chips per symbol
        #We will need to decode the header first

    def buildHeader(self, version, length, flags, packetID):
        #Head should contain the following items
        # Version: For different RX decode types
        # Length: How long the message should be
        # Flags: Mainly for start and stop bits
        # packet ID: in case messages are not recieved in the correct order

        # Binary Size:
        # Version: 2 bit string.
        # Length: We may need to add class variable? for no 8 bits
        # Flags: 2 bit string.
        # packet ID: 2^num_packets for now 64. Add to class variable 
        version_bits = self.int_to_bits(version,2)
        length_bits = self.int_to_bits(length,8)
        flags_bits = self.int_to_bits(flags,2)
        packetID_bits = self.int_to_bits(packetID,6)

        header = version_bits + length_bits + flags_bits + packetID_bits
        print(f"Header:{header}")
        print(f"Version:{version_bits}\nLength:{length_bits}")
        print(f"Flags:{flags_bits}\npacketID:{packetID_bits}")


        raw_header = self.replace_value(header,0,-1)
        print(raw_header)
        raw_header = np.repeat(raw_header,self.chips_per_symbol)
        time = np.arange(0,len(raw_header))/self.sampleRate
        tmp_carrier = self.amplitude * np.exp((2*np.pi*self.carrier_frequency*time)*1j)
        msg = tmp_carrier*raw_header
        header = msg
        return header

    def decodeHeader(self,header):

        t = np.arange(0,len(header))/self.sampleRate
        header = header * np.exp(-1j*(2*np.pi*self.carrier_frequency*t))
        idx = 0
        version = self.decode_field(header[idx:idx + 2*self.chips_per_symbol])
        idx += 2*self.chips_per_symbol

        length = self.decode_field(header[idx:idx + 8*self.chips_per_symbol])
        idx += 8*self.chips_per_symbol

        flags = self.decode_field(header[idx:idx + 2*self.chips_per_symbol])
        idx += 2*self.chips_per_symbol

        packetId = self.decode_field(header[idx:idx + 6*self.chips_per_symbol])

        print(version, length, flags, packetId)

    def decode_field(self,field_bits):
        bits = []
        for i in range(0, len(field_bits), self.chips_per_symbol):
            chunk = field_bits[i:i+self.chips_per_symbol]
            symbol = np.sum(chunk)
            bits.append(1 if np.real(symbol) > 0 else 0)
        return bits

    def int_to_bits(self,value, width):
        return [int(b) for b in format(value, f'0{width}b')]

    def encodeBits(self,bits,plot=False):
        #We will need to ensure bits are in the correct format
        tmp_bits = bits
        bits = self.to_bits(bits)
        bits = self.replace_value(bits,0,-1)

        #We will use the over sampling factor for the waveform
        msgBits = np.repeat(bits,self.chips_per_symbol)
        #Create time axis
        t=np.arange(0,len(msgBits))/self.sampleRate
        baseband_signal = np.exp((2*np.pi*self.carrier_frequency*t)*1j)
        signal = baseband_signal*msgBits
        if plot:
            plt.figure(figsize=(10,6))
            plt.title(f"Msg Signal at {self.carrier_frequency} Hz")
            plt.xlabel('Time (s)')
            plt.ylabel('Amplitude')
            plt.grid(True)
            plt.plot(t,np.real(signal))
            plt.show()

        logger.debug(f"We are encoding binary word {tmp_bits} with carrier waveform")

    def to_bits(self,data):
        """
        Convert int, binary string, or bit string into a list of bits [0,1]
        """
        # Case 1: integer
        if isinstance(data, int):
            return [int(b) for b in bin(data)[2:]]

        # Case 2: string
        if isinstance(data, str):
            data = data.strip()

            # Handle "0b101"
            if data.startswith("0b"):
                data = data[2:]

            # Validate it's binary
            if not all(c in "01" for c in data):
                raise ValueError("String must contain only 0 or 1")

            return [int(b) for b in data]

        # Case 3: already list of bits
        if isinstance(data, list):
            if not all(b in [0, 1] for b in data):
                raise ValueError("List must contain only 0 or 1")
            return data

        raise TypeError("Unsupported data type")  

    def replace_value(self, arr, old, new):
        return [new if x == old else x for x in arr]