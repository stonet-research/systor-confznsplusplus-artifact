# zinc-configuration

Synthetic fio benchmarks to measure the impact of ZINC's epoch_interval and command_token parameters.
We do a grid search on both parameters and measure the impact of reset operations on write performance. Additionally, we measure the maximum latency of a reset request under various configurations. The benchmark also contains various baseline benchmarks to test ZINC's performance when there is no reset interference, and benchmarks to measure the max reset performance in isolation (are resets still delayed if there is no write-traffic?).

# zinc-cpu-usage

Synthetic benchmarks to compare zinc's CPU usage compared to mq-deadline.
All evaluations are with fio benchmarks, with experiments similar to the interference study.

# zinc-resset-epoch-cdf

Synthetic benchmark to measure the impact of the number of epoch holds on zinc (P95-latency).
The benchmark uses fio with a reset thread and a write thread. We configure ZINC always hold resets until it no longer can. In this configuration, we use pending_requests_threshold==0, write_ratio=5000000, reset_timer_interval=64. We use max_priority of 0--5 and attempt the experiment three times.
