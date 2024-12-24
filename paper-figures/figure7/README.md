## Figure 7

![](./figures/bent_pipe_victoria_1_latency.csv.png)
![](./figures/bent_pipe_victoria_2_latency.csv.png)
![](./figures/bent_pipe_victoria_3_latency.csv.png)
![](./figures/bent_pipe_victoria_4_latency.csv.png)
![](./figures/bent_pipe_victoria_5_latency.csv.png)
![](./figures/oneweb_iowa_latency.csv.png)

To recreate Figure 7, first decompress the latency traces inside the [data](./data) subfolders with the following command.

```bash
tar -xf data/figure7.tar.zst --directory=data
```

Then, run `python3 figure7.py`.
