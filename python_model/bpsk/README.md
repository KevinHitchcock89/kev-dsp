# BPSK Basics
____________________________________

### References
[Geeks for Geeks: BPSK - Binary Phase Shift Keying](https://www.geeksforgeeks.org/electronics-engineering/bpsk-binary-phase-shift-keying/)


[EF Johnson Technologies: Digital Phase Modulation](https://www.efjohnson.com/resources/dyn/files/75832z342fce97/_fn/Digital_Phase_Modulation.pdf)


## Basic concept
Binary Phase-Shift Keying is a digital communication protocal that untilizes the phase of a waveform. The protocal is a simple digital modulation that shifts the carrier signal phase between 0 and 180 degrees. 

This is a robust communication protocal because it has a high immunity noise and is power effient. This allow it to be used in muiltple communication systems. 

### Complex Waveform
   
This equation will allow us to create a waveform that we can then use to encode binary values into.

## Creating our waveform
We want to start by deciding certain paramters.

- What waveform type: 13-Length Barker Code
- Oversampling factor (chips per symbol): ?
- Carrier Frequency: ?
- Amplitude: ?
- Sample Rate: ?

To create a barker code waveform you will need 3 items.
- Amplitude
- Baseband Chips (Your barker code)
- Carrier wave


## Creating Carrier Wave

#### time axis: 
 $${ [0,1,2,..., codeLen * chipsPerSymbol]}/sampleRate$$
#### carrier: $${ e^{2\pi*f*timeAxis*j }  }$$

## Creating Barker Codes
- Select which code we want to chose

| Code Length | Code |
| --------: | :-------- |
| 13 | 1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1 |
| 11 | 1,1,1,-1,-1,-1,1,-1,-1,1,-1 |
| 7 | 1,1,1,-1,-1,1,-1 |
| 5 | 1,1,1,-1,1 |
| 4 | 1,1,-1,1 |
| 3 | 1,1,-1 |
| 2 | 1,-1 |

- Create and Oversampled version of the code
    - Barker Code Length: 2
    - OverSampling Value: 5  
     ***exp:***
    $${ [1,1,1,1,1,-1,-1,-1,-1,-1] }$$

- Create the Waveform
  $${ waveform = Amplitude*BaseBandChips*Carrier }$$



## Simulating Transmitter
This will be a BPSK simulation To simulate the transmitter there will need a waveform generator. TThis waveform will be construct in the following way.  

                        [Barker Code]+[Header]+[Message]

  - Barker Code 
    - **Code:** 13-bit Barker Code for easy detection and alignment 
  - Header
    - **Length:** Packet length in bits 
    - **Version:** Encocde/Decode Version
    - **packetID:** Packet #
    - **Flags:** Start/Stop Flags

  - Message
    -  **Message:** Binary message


## Simulating Receiver
## Decoding Messages 



**Carrier Frequency:** 10e3  \
**Carrier Amplitude:** 1     \
    **Sampling Rate:** 200e6 \
            **Phase:** 0     \
         **Duration:** 1     \
             **Baud:** 9600  \
  **Symbol Duration:** 1/Baud     
      

<!-- $$ e^{i (2\pi 10e3 t + \phi ) } = cos(2\pi 10e3 t+\phi)+isin(2\pi 10e3 t + \phi) $$
 and
 t = {0,1,2,3,...,200e6} -->

 






<!-- ### Converting to Frequency domain
$$ f(k)= \frac{k*f_s}{N_{fft}} -->


### TODO ###
#### Clean Up ####
  - Init function
  
  - Create Params for Waveform  
    - Carrier Frequency  
    - Chips Per Symbol  
    - Sample Rate  
    - Amplitude  
    - Detection threshold for Match filter
  - Create Barker Waveform
    - Pick Code Length - Default 13-Bit Length Code
  - Create Params for Packets
    - Packet Size: Defualt to 64
    
















