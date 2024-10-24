#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 21 09:37:28 2024

@author: simon.kern
"""
import os
import mne
from pathlib import Path
from tqdm import tqdm
import mne_bids
import events_conversion
import shutil
from mne_bids import BIDSPath, write_raw_bids

raw_files_folder = '/zi/flstorage/group_klips/data/data/Fast-Replay-MEG/'

bids_root_path = os.path.abspath(os.path.dirname(vars().get('__file__', '')) + '/../')
# bids_root = BIDSPath(root=bids_root_path)


subjects = [x for x in os.listdir(f'{raw_files_folder}/data-MEG/') if x.startswith('mfr')]
print(f'{len(subjects)=} subjects found')


for subj in tqdm(sorted(subjects), desc='processing subjects'):
    subj_id = subj.split('_', 1)[-1]
    if int(subj_id)==23:  # this participant's data is missing
        continue
    assert len(subj_id)==2

    subj_folder = f'{raw_files_folder}/data-MEG/{subj}/'
    files_subj = [x for x in os.listdir(subj_folder) if x.endswith('fif')]

    ### 1) first convert the two resting states
    # bids_path = BIDSPath(subject=subj_id, root=bids_root)
    for rs in [1, 2]:
        fif_file = [x for x in files_subj if f'_rs{rs}_' in x]
        assert len(fif_file)==1
        raw = mne.io.read_raw_fif(f'{subj_folder}/{fif_file[0]}')
        events = mne.find_events(raw, min_duration=3/raw.info['sfreq'])
        event_id = {'resting state start': 1, 'resting state stop': 2}
        bids_task = BIDSPath(subject=subj_id,
                             datatype='meg',
                             task=f'rest{rs}',
                             root=bids_root_path)

        write_raw_bids(raw=raw,
                        bids_path=bids_task,
                        events=events,
                        event_id=event_id,
                        # empty_room=raw_er,
                        overwrite=True,
                        verbose=True
                        )

    ### 2) next convert the main data
    fif_file = [x for x in files_subj if f'_main_' in x and x.endswith('mc.fif')]
    assert len(fif_file)==1
    raw = mne.io.read_raw_fif(f'{subj_folder}/{fif_file[0]}')
    events = mne.find_events(raw, min_duration=3/raw.info['sfreq'])
    stimuli = ['Face', 'House', 'Cat', 'Shoe', 'Chair']
    event_id = ({'Break start': 91,
                'Break stop': 92,
                'Sequence Buffer start': 61,
                'Sequence Buffer stop': 62,
                'sequence sound error': 70,
                'sequencesound coin': 71,
                'localizer sound error': 30,
                'localizer sound coin': 31,
                'fixation pre 1': 81,
                'fixation pre 2': 82,
                } | {f'localizer {stim} onset':i for i, stim in enumerate(stimuli, 1)}
                  | {f'localizer {stim} distractor onset':i+100 for i, stim in enumerate(stimuli, 1)}
                  | {f'cue {stim}':i+10 for i, stim in enumerate(stimuli, 1)}
                  | {f'sequence {stim} onset':i+20 for i, stim in enumerate(stimuli, 1)}
                )

    bids_task_main= BIDSPath(subject=subj_id,
                             datatype='meg',
                             task=f'main',
                             root=bids_root_path)
    write_raw_bids(raw=raw,
                    bids_path=bids_task_main,
                    events=events,
                    event_id=event_id,
                    # empty_room=raw_er,
                    overwrite=True,
                    verbose=True
                   )

    ### 3) behavioural data
    # basically sourdedata is a fractal BIDS folder
    bids_task_source = BIDSPath(subject=subj_id,
                         datatype='beh',
                         task=f'main',
                         root=bids_root_path + '/sourcedata/')
    bids_task_source.mkdir()

    # filter CSV file
    subj_folder = f'{raw_files_folder}/data-logs/{subj.replace("_", "-")}/'
    files_subj = [x for x in os.listdir(subj_folder) if x.endswith('csv') ]
    files_subj = [x for x in files_subj if (('main_' in x) & x.startswith(f'{int(subj_id):02d}'))]
    files_subj = [f'{subj_folder}/{x}' for x in files_subj]
    assert len(files_subj)==1
    csv_file = files_subj[0]
    log_file = files_subj[0][:-3] + 'log'
    shutil.copy(log_file, str(bids_task_source.fpath) + '.log')

    bids_task_main.update(suffix='beh')
    df_subj = events_conversion.convert_psychopy_to_bids(csv_file)
    df_subj['subject'] = f'sub-{subj_id}'
    df_subj['session'] = 1

    df_subj.to_csv(str(bids_task_main.fpath) + '.tsv', sep='\t', index=False,
                   na_rep='NaN')


    ### 4) MRI data
    # I have previously run recon-all on the data
    # TODO implement this, currently we don't use the MRI data yet
