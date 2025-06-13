#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  8 10:22:10 2025

In some of the files there are channels missing, which prevents them from
being preprocessed. In this script we will add the missing channels


@author: simon.kern
"""
import os
import shutil
import mne
import joblib
import numpy as np
import meg_utils


def reset_backups():
    """restore the backups, just in case"""
    import ospath  # this is a custom module
    files = ospath.list_files(f'{raw_files_folder}/data-MEG/', exts='bak', recursive=True)
    for bak_file in files:
        fif_file = bak_file[:-3] + 'fif'
        os.remove(fif_file)
        shutil.move(bak_file, fif_file)

def fix_file(raw):
    fif_file =raw._filenames[0]

    bak_file = fif_file[:-3] + 'bak'
    if not os.path.isfile(bak_file):
        print(f'creating backup of {fif_file}')
        shutil.copy(fif_file, bak_file)

    ch_types = {'BIO001': 'bio',
                'BIO002': 'bio',
                'BIO003': 'bio',
                'MEG2112': 'grad',
                'MEG2211': 'mag',}

    missing = set(ch_expected) - set(raw.ch_names)
    chs_add = []
    bads = raw.info['bads'].copy()

    for ch in missing:
        if ch.startswith('CHPI'):
            # this just means motion correction didn't run - possibly
            # this file is just fine as it is.
            continue
        elif ch in ch_types:
            info = mne.create_info(ch_names=[ch], sfreq=raw.info['sfreq'], ch_types=ch_types[ch])
            raw_new = mne.io.RawArray(data=np.zeros([1, len(raw)]), info=info,
                                      first_samp=raw.first_samp, verbose='WARNING')
            chs_add += [raw_new]

            # these channels can be interpolated, unlike the BIO channels
            if ch.startswith('MEG'):
                bads += [ch]
            print(f'  -Adding {ch}')


        else:
            raise Exception(f'{ch=} missing! don\'t know what to do')

    if chs_add:
        raw.load_data(verbose='WARNING')
        raw.add_channels(chs_add, force_update_info=True)
        if bads:
            raw.info['bads'] += bads
            raw.interpolate_bads()
        assert len(raw.ch_names) == len(ch_expected)
        raw.save(fif_file, overwrite=True)


raw_files_folder = '/data/fastreplay/Fast-Replay-MEG/'
ch_expected = joblib.load('chs_expected.pkl.zip')

subjects = sorted([x for x in os.listdir(f'{raw_files_folder}/data-MEG/') if x.startswith('mfr')])

for subj in subjects:

    subj_folder = f'{raw_files_folder}/data-MEG/{subj}/'
    files_subj = [x for x in os.listdir(subj_folder) if x.endswith('fif') and not ('-1.fif' in x)]

    for file in files_subj:
        raw = mne.io.read_raw(f'{raw_files_folder}/data-MEG/{subj}/{file}/', verbose='ERROR')
        if len(raw.ch_names)!=len(ch_expected):
            print(f'Fixing {subj} - {file}')
            fix_file(raw)
