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
from mne_bids import BIDSPath, write_raw_bids

raw_files_folder = '/zi/flstorage/group_klips/data/data/Fast-Replay-MEG/'

bids_root_path = os.path.abspath(os.path.dirname(vars().get('__file__', '')) + '/../')
# bids_root = BIDSPath(root=bids_root_path)


subjects = [x for x in os.listdir(f'{raw_files_folder}/data-MEG/') if x.startswith('mfr')]
print(f'{len(subjects)=} subjects found')


for subj in tqdm(subjects):
    subj_id = subj.split('_', 1)[-1]
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

    bids_task = BIDSPath(subject=subj_id,
                         datatype='meg',
                         task=f'main',
                         root=bids_root_path)
    write_raw_bids(raw=raw,
                    bids_path=bids_task,
                    events=events,
                    event_id=event_id,
                    # empty_room=raw_er,
                    overwrite=True,
                    verbose=True
                   )

    ### 3) behavioural data


    ### 4) MRI data
    # I have previously run recon-all on the data
