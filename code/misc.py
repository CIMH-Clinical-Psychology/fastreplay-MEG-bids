#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  8 11:43:48 2025

@author: simon.kern
"""
import os
from functools import cache
import numpy as np
import mne
from joblib import load as _joblib_load

joblib_load = cache(_joblib_load)

def check_and_fix_channels(raw):
    """check for missing channels or empty channels or NaN channels"""
    report = {'filename': os.path.basename(raw._filenames[0]),
              'missing': []}
    template_info = mne.io.read_info('template-info.fif')

    ch_types = {'BIO001': 'bio',
                'BIO002': 'bio',
                'BIO003': 'bio',
                'MEG2112': 'grad',
                'MEG2211': 'mag',}

    # check for missing channels
    missing = set(template_info.ch_names) - set(raw.ch_names)
    chs_add = []
    bads = raw.info['bads'].copy()

    raw.load_data()
    empty_ch = np.zeros_like(raw.get_data(0))
    for ch in missing:
        report['missing'] += [ch]
        if ch.startswith('CHPI'):
            # this just means motion correction didn't run - possibly
            # this file is just fine as it is.
            continue
        elif ch in ch_types:
            info = mne.create_info(ch_names=[ch], sfreq=raw.info['sfreq'], ch_types=ch_types[ch])

            ch_idx = template_info.ch_names.index(ch)
            ch_t = template_info['chs'][ch_idx]
            for key in ('loc', 'coil_type', 'kind', 'unit', 'unit_mul', 'coord_frame'):
                info['chs'][0][key] = ch_t[key]

            raw_new = mne.io.RawArray(data=empty_ch, info=info,
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


    # next check if any data is nan
    data = raw.get_data()
    for ch, d in zip(raw.ch_names, data):
        if 'CHPI' in ch:
            continue
        assert not np.isnan(d).any(), f'some data is NaN for {ch=}!'
    return raw, report


if __name__=='__main__':
    import mne
    raw = mne.io.read_raw('/zi/flstorage/group_klips/data/data/Simon/highspeed/highspeed-MEG-raw/data-MEG/mfr_03/MFR03_main_trans[MFR03_main]_tsss_mc.fif', preload=True)
    check_and_fix_channels(raw)
