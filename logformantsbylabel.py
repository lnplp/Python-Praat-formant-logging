#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# logformantsbylabel.py version 1.2
# By Chris Norton, 2014–9.

# Looks for sound files and associated textgrids (with matching names) in a
# given directory, then uses the textgrids to locates intervals by a given label
# in each sound file. On an interval-by-interval, file-by-file basis, passes the
# locations to a Praat script (logformantsbylabel.praat) which displays formant
# information. This Python script then picks up this information from Praat and
# asks user if this should be logged, or if the formant measuring parameters
# need to be changed and the analysis performed again. Values are logged in a
# tab-separated text file.

# Obviously these scripts requires Praat (www.fon.hum.uva.nl/praat/) to be
# installed. They also require the interface program sendpraat
# (www.fon.hum.uva.nl/praat/sendpraat.html), which is used to send commands from
# Python to Praat.

# For information about settings and options, see the documentation in
# logformantsbylabel_man.txt.

import argparse
import os
import sys
import re
import subprocess
import time

if sys.version_info.major < 3:
    sys.exit('This program requires Python 3 or newer.')

settings_file = 'settings.cfg'

# These parameters will be used if the script is run with the -i or
# --ignore_settings_file flag is set. Otherwise, parameters will be pulled from
# the above settings file (or a user-specified settings file when the script is
# run with -s or --settings_file).
default_params = {}
default_params['bandwidth_cost'] = {'male': '1', 'female': '1'}
default_params['data_directory'] = 'Data'
default_params['f1_reference'] = {'male': '5000', 'female': '5500'}
default_params['f2_reference'] = {'male': '1485', 'female': '1650'}
default_params['f3_reference'] = {'male': '2475', 'female': '2750'}
default_params['f4_reference'] = {'male': '3465', 'female': '3850'}
default_params['f5_reference'] = {'male': '4455', 'female': '4950'}
default_params['frequency_cost'] = {'male': '1', 'female': '1'}
default_params['interval_label'] = 'V'
default_params['output_file_name'] = 'formant_tenths.txt'
default_params['play_sound'] = 'True'
default_params['praat_script_path'] = 'getformantsbylabel.praat'
default_params['sendpraat_path'] = 'sendpraat'
default_params['sound_extension'] = '.wav'
default_params['spectrogram_window_length'] = '0.005'
default_params['temporary_file_name'] = 'praat_output.tmp'
default_params['textgrid_extension'] = '.TextGrid'
default_params['textgrid_tier'] = '1'
default_params['transition_cost'] = {'male': '1', 'female': '1'}

# Summarise what has been logged and/or skipped.
def final_report(intervals_logged_count, files_logged_count,
    intervals_skipped_count, files_skipped_count):

    report_text = []

    if intervals_logged_count > 0:
        report_text.append(
            '{0} intervals in {1} files logged.'.
            format(intervals_logged_count, files_logged_count)
            )
    else:
        report_text.append('No intervals logged.')

    if intervals_skipped_count > 0:
        report_text.append(
            '{0} intervals in {1} files skipped.\n'.
            format(intervals_skipped_count, files_skipped_count)
        )

    return '\n'.join(report_text)

# Dictionary of files in a given directory for a given extension.
def get_files_by_ext(directory, extension):
    files = []
    if not os.path.isdir(directory):
        sys.exit("Error: directory {0} not found.".format(directory))

    for f in os.listdir(directory):
        if f.endswith(extension):
            files.append({'name': os.path.splitext(f)[0]})
    return files

# Return user input, validated by regexp.
def get_user_input(prompt, validation_rule='', validation_error=''):

    user_input = ''
    input_valid = False

    while input_valid == False:
        try:
            user_input = input(prompt)
        except KeyboardInterrupt:
            sys.exit('\nScript terminated by keystroke.')

        # If there’s a validation regexp, check it.
        if len(validation_rule) > 0:
            if re.match(validation_rule, user_input):
                input_valid = True
            else:
                input_valid = False
                print('Invalid input. ' + validation_error)
        else:
            input_valid = True

    return user_input

# Some of the parameters have different defaults for either male or female sex.
# Set current parameters to sex provided.
def set_params_by_sex(sex, use_settings_file, params):

    new_params = {}

    # The defaults taken from the settings file should have values for the
    # different sexes in format "male_f1_reference: 5000" &
    # "female_f1_reference: 5500".
    if use_settings_file:
        for formant in range(1,6):
            param_name = 'f{0}_reference'.format(formant)
            new_params[param_name] = params[sex + '_' + param_name]
        new_params['frequency_cost'] = params[sex + '_frequency_cost']
        new_params['bandwidth_cost'] = params[sex + '_bandwidth_cost']
        new_params['transition_cost'] = params[sex + '_transition_cost']

    # Default hard-coded settings store values for the sexes in dictionaries:
    # "default_params['f1_reference'] = {'male': '5000', 'female': '5500'}"
    else:
        for formant in range(1,6):
            param_name = 'f{0}_reference'.format(formant)
            new_params[param_name] = params[param_name][sex]
        new_params['frequency_cost'] = params['frequency_cost'][sex]
        new_params['bandwidth_cost'] = params['bandwidth_cost'][sex]
        new_params['transition_cost'] = params['transition_cost'][sex]

    return new_params

def main():

    global settings_file

    # Handle arguments passed from command line.
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--settings_file', action='store',
        default=False, help='path to settings file')
    parser.add_argument('-i', '--ignore_settings_file', action='store_true',
        default=False, help='ignore settings file; use hard-coded settings')
    parser.add_argument('-v', '--version', action='version',
        version='logformantsbylabel.py 1.1')
    results = parser.parse_args()
    use_settings_file = not results.ignore_settings_file
    # If user has specified a different settings file, use that.
    if results.settings_file:
        settings_file = results.settings_file

    print('logformantsbylabel.py\n(Chris Norton, 2014)\n')

    # Grab parameters either from settings file, or from defaults set above.
    if use_settings_file:
        print('Using settings from {0}\n'.format(settings_file))
        try:
            lines = [line.strip() for line in open(settings_file)]
        except EnvironmentError:
            sys.exit('Error: Settings file {0} not found.'.format(settings_file))
        params = {}
        for line in lines:
            if len(line) == 0 or line[0] == '#':
                continue
            parts = line.split(':', 1)
            key = parts[0].strip()
            value = parts[1].strip()
            params[key] = value
    else:
        print('Using default settings from python script.\n')
        params = default_params

    # Set variables which user can't change during script.
    data_directory = params['data_directory']
    interval_label = params['interval_label']
    output_file_name = params['output_file_name']
    praat_script_path = params['praat_script_path']
    sendpraat_path = params['sendpraat_path']
    sound_extension = params['sound_extension']
    spectrogram_window_length = params['spectrogram_window_length']
    temporary_file_name = params['temporary_file_name']
    textgrid_extension = params['textgrid_extension']
    textgrid_tier = params['textgrid_tier']
    # Praat uses 1 or 0 for True/False
    if params['play_sound'].lower() == 'true':
        play_sound = '1'
    else:
        play_sound = '0'

    # Get sound and textgrid files.
    sounds = get_files_by_ext(data_directory, sound_extension)
    textgrids = get_files_by_ext(data_directory, textgrid_extension)

    files_previously_logged = ''

    # Check if there's already an output file from this script in the current
    # directory.
    output_path = os.path.join(data_directory, output_file_name)
    try:
        lines = [
            line.strip() for line
            in open(output_path)
        ]
    # No output file, create one.
    except EnvironmentError:
        files_in_list_logged = False

        header_line = ['Sound file', 'Interval position']
        # Make formant tenth headers in format f1_10%, f2_10%, f3_10% etc.
        for percentage in range (0, 11):
            for formant_no in range(1, 4):
                header_line.append(
                    'f{0}_{1}%'.format(formant_no, percentage * 10)
                    )
        header_line += [
            'interval_label', 'spectrogram_window_length', 'textgrid_tier',
            'f1_reference', 'f2_reference', 'f3_reference', 'f4_reference',
            'f5_reference', 'frequency_cost', 'bandwidth_cost',
            'transition_cost', 'time_stamp'
            ]

        with open(output_path, 'a') as fout:
            fout.write('\t'.join(header_line) + '\n')

    # Output file exists; check which files have already been processed
    # (N.B. checks whole files, not individual intervals within the files).
    else:
        print(
            'Existing log file {0} found in {1}\n'.format(output_file_name,
            data_directory)
            )
        files = [line.split('\t')[0] for line in lines]
        files_previously_logged = set(files)
        sounds_set = set([sound['name'] for sound in sounds])
        files_in_list_logged = files_previously_logged.intersection(sounds_set)

    # List sound files found
    if len(sounds) > 0:
        print("{0} sound files found in {1}:".format(
            len(sounds), data_directory
            ))
        for no, sound in enumerate(sounds):
            log_text = ''
            if sound['name'] in files_previously_logged:
                log_text = ' (previously logged)'
            print("{0}. {1}{2}\t{3}".format(no + 1, sound['name'],
                sound_extension, log_text))
        print()

        # Ask user if they want to reprocess the logged files.
        if files_in_list_logged:
            print('Some of the sound files found have been logged previously.')
            user_input = get_user_input(
                'Process previously logged files again (y) or ignore them ' +
                '(enter): ', '^[yn]$|^$'
                )
            if user_input == 'y':
                print(
                    'Including previously logged files. New measurements' +
                    ' will be appended to the output file.\n'
                    )
            # Remove previously logged files from list.
            else:
                print('Ignoring previously logged files.\n')
                sounds = [sound for sound in sounds if sound['name'] not in files_previously_logged]
                if len(sounds) == 0:
                    sys.exit('No unlogged files to process.')

    else:
        sys.exit('Error: No sound files found in {0}.'.format(data_directory))

    # If there aren't enough textgrids for the sounds, check which ones are
    # missing.
    if len(textgrids) < len(sounds) :
       without_textgrids = [
           sound['name'] + sound_extension for sound in sounds
           if sound not in textgrids
           ]
       sys.exit("Error: No textgrid for file(s) {0} ".
           format(', '.join(without_textgrids))
       )

    # Read in textgrid files and store where the intervals to measure appear in
    # each of them.
    for sound_key, sound in enumerate(sounds):
        filepath = os.path.join(
            data_directory, (sound['name'] + textgrid_extension)
            )
        lines = [line.strip() for line in open(filepath)]
        file_content = '\n'.join(lines)
        interval_positions = []

        # Split file by the string 'intervals [', which should result in junk in
        # the first [0] slot, leaving the proper list to start at [1], which is
        # handy because, unlike Python, Praat counts from 1.
        intervals = file_content.split('intervals [')
        for interval_key, interval_content in enumerate(intervals):
            if 'text = "' + interval_label + '"' in interval_content:
                interval_positions.append(interval_key)
        sounds[sound_key]['interval_positions'] = interval_positions

    # Make a current copy of the default parameters, selecting values according
    # to sex.
    sex = get_user_input('Enter speaker sex (m/f) [default m]: ', '^[mf]$|^$',
        'Enter either m or f only.')
    sex_names = {'m':'male', 'f':'female'}
    if sex == '':
        sex = 'm'
    measuring_params = set_params_by_sex(sex_names[sex], use_settings_file,
        params)

    # The files_logged/skipped sets hold names of files which contain an
    # interval that has been logged or skipped; the presence of a filename in
    # either does not imply that *all* its intervals were either logged or
    # skipped.
    intervals_logged_count = 0
    intervals_skipped_count = 0
    files_logged = set()
    files_skipped = set()

    for sound_key, sound in enumerate(sounds):

        for interval_no, interval_position in enumerate(sound['interval_positions']):

            user_accepted = False

            sound_file_name = sound['name'] +  sound_extension
            textgrid_file_name = sound['name'] + textgrid_extension

            # Keep processing this interval until the user accepts or skips it.
            while not user_accepted:

                print('\nFilename:     ' + sound_file_name)
                print('Sound no.:    {0}/{1}'.format(sound_key + 1, len(sounds)))
                print('Interval no.: {0}/{1}'.format(
                    interval_no + 1,
                    len(sound['interval_positions'])
                    ))

                # Prepare command-line arguments for sendpraat program to pass
                # to Praat.
                praat_arguments = [
                    os.path.join(data_directory, sound_file_name),
                    os.path.join(data_directory, textgrid_file_name),
                    str(interval_position),
                    textgrid_tier,
                    spectrogram_window_length,
                    play_sound,
                    measuring_params['f1_reference'],
                    measuring_params['f2_reference'],
                    measuring_params['f3_reference'],
                    measuring_params['f4_reference'],
                    measuring_params['f5_reference'],
                    measuring_params['frequency_cost'],
                    measuring_params['bandwidth_cost'],
                    measuring_params['transition_cost'],
                    temporary_file_name
                    ]
                praat_arguments = ' '.join(praat_arguments)
                # sendpraat needs to go through shell, and to give full path of
                # script for execution.

                if not os.path.exists(sendpraat_path):
                    sys.exit(
                        "Error: sendpraat cannot be found at {0}.".
                        format(sendpraat_path)
                    )

                if not os.path.exists(praat_script_path):
                    sys.exit(
                        "Error: Praat script cannot be found at {0}.".
                        format(praat_script_path)
                    )

                path_parts = os.path.abspath(__file__).split(os.sep)
                script_path = os.sep.join(path_parts[:-1])
                subprocess_return = subprocess.call(
                    '{0} praat "execute {1} {2}"'.format(
                        sendpraat_path,
                        os.path.join(script_path, praat_script_path),
                        praat_arguments
                        ),
                        shell=True
                    )

                if subprocess_return != 0:
                    sys.exit('Error: could not run Praat script properly.')

                user_input = get_user_input(
                    'Log formants (enter), skip interval (s), ' +
                    'change settings (c) or quit (q): ', '^[cqs]$|^$'
                    )

                # Don't log this interval; move onto the next.
                if user_input == 's':
                    intervals_skipped_count +=1
                    files_skipped.update([sound_file_name])
                    break

                # Change a setting.
                elif user_input == 'c':

                    # Keep going until user types <enter> alone.
                    while user_input != '':
                        print('\nSex: ' + sex_names[sex])

                        # Show enumerated list of settings.
                        param_count = str(len(measuring_params))
                        param_refs = ['']
                        i = 0
                        for key in sorted(measuring_params.keys()):
                            i += 1
                            param_refs.append(key)
                            print('{0}. {1:<16} {2}'.format(i, key,
                                measuring_params[key]))
                        prompt = (
                            'Change setting (1-{0}), '.format(param_count) +
                            'reload defaults by sex (m/f) or accept settings '
                            + '(enter): '
                            )
                        validation = '^[1-{0}]$|^[mf]$|$'.format(param_count)
                        user_input = get_user_input(prompt, validation)

                        # User has chosen to reload defaults according to sex.
                        if re.match('^[m|f]$', user_input):
                            measuring_params = set_params_by_sex(
                                sex_names[user_input], use_settings_file, params
                                )
                            print("Defaults for {0} reloaded.\n".format(
                                sex_names[user_input]
                                ),)
                            if use_settings_file:
                                print('from {0}'.format(settings_file))
                            sex = user_input

                        # User has chosen a particular setting to change.
                        elif re.match('^[1-{0}]$'.format(param_count), user_input):
                            param_key = int(user_input)
                            setting_name = param_refs[param_key]
                            setting_value = measuring_params[param_refs[param_key]]
                            prompt = (
                                "Type new value for {0}, ".format(setting_name) +
                                "or (enter) for previous value '{1}': ".
                                format(setting_name, setting_value)
                                )
                            user_input = get_user_input(
                                prompt, '^[0-{0}]+$|^$'.format(param_count),
                                'Type a number or press <enter>.'
                                )
                            if user_input == '':
                                user_input = setting_value
                            measuring_params[param_refs[param_key]] = user_input

                        # User has accepted changes to settings.
                        else:
                            print('Settings accepted.')

                # Quit
                elif user_input =='q':
                    print(final_report(
                        intervals_logged_count, len(files_logged),
                        intervals_skipped_count,
                        len(files_skipped)
                        ))
                    sys.exit('Script terminated by user.')

                # Current measurements OK; log the formants.
                else:
                    # Get measurements from Praat temp file
                    try:
                        lines_from_praat = [
                            line.strip() for line
                            in open(temporary_file_name)
                            ]
                    except EnvironmentError:
                        sys.exit('Error: Praat output file {0} not found.'.
                            format(temporary_file_name))

                    # Add a line with these measurements to the
                    # output file.
                    try:
                        with open(output_path, 'a') as fout:
                            write_line = (
                                lines_from_praat[0],
                                interval_label,
                                spectrogram_window_length,
                                textgrid_tier,
                                measuring_params['f1_reference'],
                                measuring_params['f2_reference'],
                                measuring_params['f3_reference'],
                                measuring_params['f4_reference'],
                                measuring_params['f5_reference'],
                                measuring_params['frequency_cost'],
                                measuring_params['bandwidth_cost'],
                                measuring_params['transition_cost'],
                                time.strftime('%Y/%m/%d %H:%M:%S')
                                )
                            fout.write('\t'.join(write_line) + '\n')
                    except EnvironmentError:
                        sys.exit('Error: Could not write to output file {0}.'.
                            format(output_path))
                    else:
                        files_logged.update([sound_file_name])
                        user_accepted = True
                        print('Formants logged.')
                        intervals_logged_count +=1

    # Output report.
    report_text = final_report(intervals_logged_count, len(files_logged),
        intervals_skipped_count, len(files_skipped))
    print('\n' + report_text)

    # Remove temporary file
    if os.path.isfile(temporary_file_name):
        os.remove(temporary_file_name)

if __name__ == '__main__':
    main()
