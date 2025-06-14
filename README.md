﻿# fastreplay-MEG-bids
BIDS dataset for the MEG replication of Wittkuhn et al 2021

If you have the raw data, you can run the following command to convert them to BIDS. Beforehand you might need to edit paths in the Makefile and in convert_to_bids.py.

It is assumed that the raw data is in `../highspeed-MEG-raw/*`

```bash
make anat

make defacing

python code/fix_files.py

python code/convert_to_bids.py
```


References
----------
Appelhoff, S., Sanderson, M., Brooks, T., Vliet, M., Quentin, R., Holdgraf, C., Chaumon, M., Mikulan, E., Tavabi, K., Höchenberger, R., Welke, D., Brunner, C., Rockhill, A., Larson, E., Gramfort, A. and Jas, M. (2019). MNE-BIDS: Organizing electrophysiological data into the BIDS format and facilitating their analysis. Journal of Open Source Software 4: (1896).https://doi.org/10.21105/joss.01896

Niso, G., Gorgolewski, K. J., Bock, E., Brooks, T. L., Flandin, G., Gramfort, A., Henson, R. N., Jas, M., Litvak, V., Moreau, J., Oostenveld, R., Schoffelen, J., Tadel, F., Wexler, J., Baillet, S. (2018). MEG-BIDS, the brain imaging data structure extended to magnetoencephalography. Scientific Data, 5, 180110.https://doi.org/10.1038/sdata.2018.110

