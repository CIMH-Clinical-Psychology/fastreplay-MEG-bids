# This script converts psychopy log files into a single CSV.

# target format is similar to this https://gin.g-node.org/lnnrtwttkhn/highspeed-bids/src/master/sub-01/ses-01/func/sub-01_ses-01_task-highspeed_rec-prenorm_run-03_events.tsv
import pandas as pd
import os
import datetime
from tqdm import tqdm
import numpy as np
import json
from collections import defaultdict
# import psychopy  # you should be running python 3.8 or 3.10
# from psychopy.misc import fromFile
# assert psychopy.__version__.startswith('2024.2'), f'psychopy needs to be version 2024.2 to load the files but {psychopy.__version__=}'

def extract_datetime(file):
    """extract datetime from psychopy timestamped filenames"""
    date, time = file.split('_')[-2:]  # Only get the last two parts for date-time
    year, month, day = map(int, date.split('-'))
    hour, minute_second_micro = time.split('h')
    minute, second, *_ = minute_second_micro.split('.')
    return datetime.datetime(year, month, day, int(hour), int(minute), int(second))

def add_row(df, **new_row):
    """add a row to a dataframe, inplace with varying arguments.
    all keywords that don't exist will be be added as columns to the df

    Parameters
    ----------
    df : dataframe to add a row to
    onset : only required argument
    kwargs: keyword argument to add as columns

    Returns None
    """
    # make sure these are present
    assert 'onset' in new_row
    assert 'condition' in new_row
    new_row['onset'] -= t_offset
    if 'duration' in new_row:
        new_row['duration'] = round(new_row['duration'], 4)
    if np.isinf(t_offset):
        raise ValueError('offset has not been defined yet! {t_offset=}')
    # if column doesnt exist, create it
    for name in new_row:
        if name not in df.columns:
            df[name]= [np.nan]*len(df)
    df.loc[len(df)] = new_row
    return None  # it works in-place, so no return of df

def json_decode(cell):
    """convert strings to lists , e..g "[1,2]" => [1, 2]"""
    try:
        return json.loads(cell)
    except (TypeError, ValueError):
        # print(f'not json: {cell}')
        return cell  # Return the cell unchanged if it's not a JSON string



#%% actual code
output_dir = 'Z:/Fast-Replay-7T/output/'
psychopy_data = 'Z:/Fast-Replay-7T/data_cleaned' # directory where psychopy log files for the experiment are stored

intervals = np.array([32, 64, 128, 512])
stimuli = ['gesicht', 'haus', 'katze', 'schuh', 'stuhl']
behavior_dir = os.path.dirname(os.path.abspath(__file__)) + '/../inputs/behavior/'

os.makedirs(output_dir, exist_ok=True)
csv_files = [file for file in os.listdir(psychopy_data) if file.endswith('csv')]

subjects = sorted(set([file.split('_', 1)[0] for file in csv_files]))
print(f'found files for the following {subjects=}, will ignore 0')
subjects.remove('0')  # remove default participant

# split files for each subject
subject_files = {subj: [file for file in csv_files if file.startswith(f'{subj}_')] for subj in subjects}

# def convert_psychopy_to_bids():
# for subj, files in tqdm(subject_files.items(), total=len(subject_files), desc='participant'):
if True:
    rs_files = [file for file in files if 'RS' in file]
    main_files = [file for file in files if 'main' in file]

    # sanity check if we have the right number of files
    assert len(rs_files)==2, f'more {len(rs_files)=} found than expected for {subj=}, please clean up manually'
    assert len(main_files)==1, f'more {len(main_files)=} found than expected  {subj=}, please clean up manually'

    # sanity check that the files are in right chronological order
    rs_times = [extract_datetime(file) for file in rs_files]
    main_times = [extract_datetime(file) for file in main_files]
    assert rs_times[0] < main_times[0] < rs_times[1], 'timestamps are not in order!'
    main_file = main_files[0]
    # if subj=='2': basdf
    # load the log file (only there we have the image labels, what?!)
    with open(f'{psychopy_data}/{main_file}'[:-3] + 'log', 'r') as f:
        loglines = f.readlines()
        # build lookup dictionary
        # this is increasingly ugly, but it creates a nested dict of a nested dict
        log_dict = defaultdict(lambda: defaultdict(dict))
        for line in loglines:
            t, lvl, msg = [x.strip() for x in line.split('\t', 3)]
            if msg.startswith('Created'): continue  # ignore creation events
            if not ' = ' in msg: continue  # only record property assignments
            if not ': ' in msg: continue  # only record property assignments
            if lvl=='DATA': continue  # ignore keypresses
            cmp_name, msg = msg.split(': ', 1)
            prop, val = msg.split(' = ', 1)
            log_dict[float(t)][cmp_name][prop] = val

    # load the CSV file
    df_runs = pd.read_csv(f'{psychopy_data}/{main_file}')
    tqdm_loop = tqdm(total = len(df_runs))
    print(subj)
    df_runs = df_runs.sort_index(axis=1)
    # these are the indices of where a new run starts
    new_run_idx = list(np.where(~df_runs['scanner_1.started'].isna())[0]) + [len(df_runs)]
    runs = [df_runs.iloc[start:end, :] for start, end in zip(new_run_idx[:-1], new_run_idx[1:], strict=True) if (end-start)>1]
    assert len(runs)==6
    for r, df_run in enumerate(runs, 1):
        df_run_bids = pd.DataFrame(columns=['onset', 'duration', 'subject', 'session', 'run_session', 'condition', 'trial_type'])
        df_trs = pd.DataFrame()
        run_folder = f'{behavior_dir}/sub-{int(subj):02d}/func/'
        os.makedirs(run_folder, exist_ok=True)
        tsv_file_thisrun = f'{run_folder}/sub-{int(subj):02d}_ses-01-highspeed-7T_main_run-{r:02d}_events.tsv'
        # loop over all trials
        t_offset = np.inf

        for i, line in df_run.iterrows():
            line = line[~line.isna()]  # filter all NaN entries, makes it a bit easier to debug
            line = line.apply(json_decode)  # convert strings to python datatypes

            condition = 'other'  # default condition
            # parse which trial this currently is

            if 'wait_for_scanner.started' in line:  # trial that waits for the first scanner pulse
                condition = 'waiting'
                assert len(line['scanner_1.rt'])==1, f'expected exactly one t! but {line["scanner_1.keys"]=}'
                # record exact time of first trigger
                t_offset = line['scanner_1.rt'][0] + line['scanner_1.started']
                continue

            elif 'localizer.started' in line:  # this row is a localizer trial
                condition = 'localizer'

                # there are several events within this trial that we need to transfer
                # 1 fixation dot pre, only once before the entire block
                component = 'text_6'
                if f'{component}.started' in line:  # only present in first trial
                    add_row(df_run_bids,
                            onset=line[f'{component}.started'],
                            duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                            condition=condition,
                            trial_type= 'instruction',
                            stim_label='localizer_start')

                # 2 fixation dot pre, before every image
                component = 'localizer_fixation'
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'fixation',
                        stim_label='dot')

                # 3 image itself
                component = 'localizer_img'
                onset = line[f'{component}.started']
                orientation = log_dict[round(onset, 4)][component]['ori']
                stim_label = log_dict[round(onset, 4)][component]['image'].split('/')[-1][:-5]
                stim_index = stimuli.index(stim_label.lower())+1

                add_row(df_run_bids,
                        onset=onset,
                        duration=line[f'{component}.stopped'] - onset,
                        condition=condition,
                        trial_type= 'stimulus',
                        stim_label= stim_label,
                        orientation=orientation,
                        interval_time=line[f'localizer_isi.stopped'] - line[f'localizer_isi.started'],
                        response_time=line['key_resp_localizer.rt'] if 'key_resp_localizer.rt' in line else np.nan,
                        accuracy= ('key_resp_localizer.rt' in line)==(orientation=='180')
                        )
                        # accuracy=
                del onset, orientation, stim_label, stim_index  # for safety, not to accidentially reuse it later

                # 4 ISI
                component = 'localizer_isi'
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'blank',
                        stim_label='interval')

                # 5 feedback, if given
                component = 'loc_feedback'
                if f'{component}.started' in line:
                    onset = line[f'{component}.started']
                    add_row(df_run_bids,
                            onset=onset,
                            duration=line[f'{component}.stopped'] - onset,
                            condition=condition,
                            trial_type= 'feedback',
                            stim_label=log_dict[round(onset, 4)][component]['foreColor'])
                    del onset


            elif 'sequence.started' in line:
                condition = 'sequence'

                # 1 Cue of which item to look out for
                component = 'cue_text'
                onset = line[f'{component}.started']
                add_row(df_run_bids,
                        onset=onset,
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'cue',
                        stim_label=log_dict[round(onset, 4)][component]['text'])
                del onset

                # 2 empty blank for 1500 ms
                component = 'text'
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'blank',
                        stim_label='blank')

                # 3 fixation dot before sequence
                component = 'localizer_fixation'
                add_row(df_run_bids,
                        onset= line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] -  line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'fixation',
                        stim_label='dot')

                # 4 sequences of five images
                onset_seq1 = round(line['sequence_img_1.started'], 4)
                for seq in range(1, 6):

                    elapsed = (line[f'sequence_isi_{seq}.stopped'] - line[f'sequence_isi_{seq}.started'])*1000
                    interval = intervals[np.argmin(abs(intervals - elapsed))]

                    # 4.1 image
                    component = f'sequence_img_{seq}'
                    stim_label = log_dict[onset_seq1][component]['image'].split('/')[-1][:-5]
                    stim_index = stimuli.index(stim_label.lower())+1

                    add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'stimulus',
                        stim_index=stim_index,
                        stim_label=stim_label,
                        serial_position=seq,
                        interval_time=interval)
                    del stim_label, stim_index  # for safety, remove

                    # 4.2 ISI
                    component = f'sequence_isi_{seq}'
                    add_row(df_run_bids,
                            onset=line[f'{component}.started'],
                            duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                            condition=condition,
                            trial_type= 'interval',
                            stim_label= 'dot')

                component = f'buffer_fixation'
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'delay',
                        stim_label= 'dot')

                component = f'question'
                t_feedback = round(line['text_feedback__answer.started'], 4)
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'choice',
                        stim_label= 'choice',
                        response_time=line['question_key_resp.rt'] if 'question_key_resp.rt' in line else np.nan,
                        key_down=line['question_key_resp.keys'],
                        key_pressed=int('question_key_resp.rt' in line),
                        accuracy=int(log_dict[t_feedback]['text_feedback__answer']['foreColor']=="'green'")
                        )

                component = f'text_feedback__answer'
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'feedback',
                        stim_label= log_dict[t_feedback]['text_feedback__answer']['foreColor'].replace("'", ""),
                        )

            elif 'buffer_2.started' in line:
                condition = 'fixation'
                component = 'buffer_2'
                add_row(df_run_bids,
                        onset=line[f'{component}.started'],
                        duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                        condition=condition,
                        trial_type= 'pre-fixation',
                        stim_label= 'dot',
                        )

            elif f'scanner_4.duration' in line:
                continue  # ignore? No idea why this is there

            elif 'instruct_end.started' in line:
                component = 'text_5'
                add_row(df_run_bids,
                    onset=line[f'{component}.started'],
                    duration=line[f'{component}.stopped'] - line[f'{component}.started'],
                    condition=condition,
                    trial_type= 'instruction',
                    stim_label= 'end-of-experiment',
                    )
            else:
                print('this is unknown')
                stop
            df_run_bids['subject'] = f'subj-{int(subj):02d}'
            df_run_bids['session'] = 1
            df_run_bids['run_session'] = r
            df_run_bids['session'] = 1
            df_run_bids

            df_run_bids.to_csv(tsv_file_thisrun, sep='\t', index=False)
            tqdm_loop.update()
            # # next record TRs that were sent during this trial
            # for component, value in line.items():
            #     if component.startswith('scanner_'):
            #         scanner = component.rsplit('.', 1)[0]
            #         trs = [t + line[f'{scanner}.started'] for t in line[f'{scanner}.rt']]
            #         df_trs = pd.concat([df_trs,
            #                             pd.DataFrame({'time': trs,
            #                                           'condition': condition})])
            #         break
