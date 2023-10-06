# Install filebench locally
```bash
./install_filebench.sh
```

# Usage

```bash
sudo nohup ./run_filebench.sh nvme_device zns_device workload &
```
Workload can be:
* varmail
* fileserver
* webserver
Results are stored in the results dir in format workload-timestamp.out for data and workload-timestamp.err for errors.
