# This is the entire directory with 4KiB block size in fio

We had to increase to 8KiB blocks size as we were not able to reach peak bandwidth of the device (1.2GiB, while we
reached ~600MiB only). This is because we can only issue 1 I/O to a zone and 14 in parallel maximum (max active zones)
which still does not reach the peak.
