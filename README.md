# Python-Praat-formant-logging
This set of Python and Praat files allows for dynamic formant checking and logging. The way it all works is explained in the user manual. Attribution is there, as well as in the .py and .praat files. The whole set of files comes with no guarantees of doing  what you hope it will do.

In a nutshell, the Python (.py) script allows you to cycle through a directory with sound files and associated textgrids to perform formant analysis according to the code in the Praat (.praat) script -- as written it does this in 10% steps through a specified segment. Crucial settings are supplied at the outset by the user, in the .cfg file. The formant analysis for each sound file is visualised in the Praat picture window in the form of a spectrogram with overlaid formant tracks and a midpoint spectrum. If it looks as if the analysis is not tracking the formants accurately, the user can change the settings; the analysis will then be redone and visualised again. The user can edit the settings until the tracking looks accurate in the visualisation, and at that point can log the values and move on to the next file. The script outputs a .txt file with all the logged formant values.

For the whole thing to run, you need a Python installation, and you need to specify in the .cfg file where Praat and sendpraat resideon your system. The script appears not to run well from within a Python editor (at least not IDLE), while running reliably from the command line (cmd on a Windows PC).
