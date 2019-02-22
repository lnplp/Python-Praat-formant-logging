# getformantsbylabel.praat version 1.0
# Adapted by Chris Norton, 2014 from scripts by Katherine Crosswhite, 
# Leendert Plug & Bert Remijsen.

# Accepts a set of arguments passed from the Python script
# logformantsbylabel.py. Calculates formant values for a sound file at quarterly
# intervals over a given section of a textgrid associated with the sound file. 
# Displays these values along with a spectrogram featuring formant tracks, and
# spectra. Saves the values to a temporary file which is picked up by the Python
# script and logged (or discarded, ready for this script to be run again with
# different parameters).


# Set up arguments to be passed in from Python script.
form Get formants by label
    # The main sound file
    word sound_file_name
    # A textgrid for this sound file
    word textgrid_file_name
    # The number of the interval in the textgrid that needs to be measured
    integer interval_position
    # The relevant tier of the textgrid
    integer textgrid_tier
    # The window length to generate the spectrogram
    positive spectrogram_window_length
    # Whether or not to play the sound
    integer play_sound
    # Reference points for the formants
    positive f1_reference
    positive f2_reference
    positive f3_reference
    positive f4_reference
    positive f5_reference
    positive frequency_cost
    positive bandwidth_cost
    positive transition_cost
    # The temporary file to be picked up by the Python script
    word temporary_file_name
endform

# Clear any previous objects from object list.
select all
nocheck Remove

# Load in the main files
Read from file... 'sound_file_name$'
Read from file... 'textgrid_file_name$'

# Set up object variables
select all
sound_file_name$ = selected$ ("Sound")
sound = selected("Sound")
textgrid = selected("TextGrid")

# Work out points at 10% intervals
select 'textgrid'
finishing_time = Get finishing time
start_point = Get starting point... 'textgrid_tier' 'interval_position'
end_point = Get end point... 'textgrid_tier' 'interval_position'
range = end_point - start_point
tenth = range / 10
mid_point = start_point + (range / 2)

# Track formants
select 'sound'
Resample... 16000 50
sound_16khz = selected("Sound")
To Formant (burg)... 0.01 5 5000 0.025 50
Track... 3 'f1_reference' 'f2_reference' 'f3_reference' 'f4_reference'
    ... 'f5_reference' 'frequency_cost' 'bandwidth_cost' 'transition_cost'
Rename... 'sound_file_name$'_aftertracking
formant_aftertracking = selected("Formant")

# Get the f1, f2, f3 measurements.
select 'formant_aftertracking'

for i from 1 to 10
   measurepoint = start_point + (i * tenth)
   f1 [i] = Get value at time... 1 'measurepoint' Hertz Linear
   f2 [i] = Get value at time... 2 'measurepoint' Hertz Linear
   f3 [i] = Get value at time... 3 'measurepoint' Hertz Linear
endfor

# Display table in Praat info window
clearinfo
print 'tab$'
for i from 1 to 10
    percent = i * 10
    print 'percent'% 'tab$'
endfor
print 'newline$'F1'tab$'
for i from 1 to 10
    output = f1 [i]
    print 'output:0'
    print 'tab$'
    # (Following bit of ridiculous code is to pad short strings with spaces)
    if (output < 1000)
        print  
        if (output < 100)
            print  
        endif
    endif
    print 'tab$'
endfor
print 'newline$'F2'tab$'
for i from 1 to 10
    output = f2 [i]
    print 'output:0' 'tab$'
endfor
print 'newline$'F3'tab$'
for i from 1 to 10
    output = f3 [i]
    print 'output:0' 'tab$'
endfor
print 'newline$'

# Set display size
display_from = 'start_point' - 0.15
if ('display_from' < 0)
    display_from = 0
endif
display_until = 'end_point' + 0.15
if ('display_until' > 'finishing_time')
    display_until = 'finishing_time'
endif

# Generate and draw spectrogram
select 'sound'
Erase all
Font size... 14
To Spectrogram... 'spectrogram_window_length' 4000 0.002 20 Gaussian
Viewport... 0 7 0 3.5
Paint... 'display_from' 'display_until' 0 4000 100 yes 50 6 0 no

# Draw formants on spectrogram
select 'formant_aftertracking'
Yellow
Speckle... 'display_from' 'display_until' 4000 30 no
Marks left every... 1 500 yes yes yes
Viewport... 0 7 0 4.5

# Draw textgrid
select 'textgrid'
Black
Draw... 'display_from' 'display_until' no yes yes
One mark bottom... 'mid_point' yes yes yes

# Generate and draw spectra
select 'sound_16khz'
spectrum_begin = mid_point - 0.015
spectrum_end = mid_point + 0.015
Extract part...  'spectrum_begin' 'spectrum_end' Hanning 1 no
To Spectrum (fft)
Viewport... 0 7 4.5 8
Draw... 0 3250 0 80 yes
To Ltas (1-to-1)
Viewport... 0 7 4.5 8
Draw... 0 3250 0 80 no bars
Marks bottom every... 1 500 yes yes no
Marks bottom every... 1 250 no no yes

# Generate spectral slice
select 'sound_16khz'
To LPC (autocorrelation)... 18 0.025 0.005 50
lpc = selected("LPC")
To Spectrum (slice)... 'mid_point' 20 0 50
Rename... LPC_'sound_file_name$'
spectrum_lpc = selected("Spectrum")

# Draw spectral slice
select 'spectrum_lpc'
Line width... 2
Draw... 0 3250 0 80 no
Line width... 1
Text top... no Spectrum [30 ms], Ltas(1-to-1) [30 ms], LPC(autocorrelation), all
    ... three overlaid

# Play the sound if flag is set
if (play_sound = 1)
    select 'sound'
    Extract part... 'display_from' 'display_until' Hanning 1 no
    Play
endif

# Save measurements in a temporary file for the Python script to pick up
filedelete 'temporary_file_name$'
fileappend "'temporary_file_name$'" 'sound_file_name$''tab$'
    ...'interval_position''tab$'
for i from 1 to 10
    output = f1 [i]
    fileappend "'temporary_file_name$'" 'output:0''tab$'
    output = f2 [i]
    fileappend "'temporary_file_name$'" 'output:0''tab$'
    output = f3 [i]
    fileappend "'temporary_file_name$'" 'output:0''tab$'
endfor

fileappend "'temporary_file_name$'" 'newline$'
