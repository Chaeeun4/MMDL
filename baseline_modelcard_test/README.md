# MMMU test baseline

This runner uses the recorded `baseline_modelcard_v1` recipe with the pinned
Qwen snapshot and MMMU test split. Launch it from the existing `eval` environment.

```bash
cd /shared_dir/MMDL/baseline_modelcard_test
python -u supervise_test.py
```

For automatic resume, configure the container platform to run this command
at every start after `/shared_dir` is mounted. The start command must activate
the same evaluation environment. For example, with Conda on the startup PATH:

```bash
conda run --no-capture-output -n eval python -u /shared_dir/MMDL/baseline_modelcard_test/supervise_test.py
```

Use the platform secret or environment configuration to set
`DISCORD_WEBHOOK_URL`. The supervisor sends start, resume, interruption,
failure and completion messages. If the process is killed without a signal
handler or the container loses power, it reports the previous interruption
when it starts again. A terminal failure can be retried by launching the same
command. Completed runs are skipped on subsequent starts.

The default `runs/baseline_modelcard_v1_mmmu_test_98e6` folder is inside this
directory. If the repository is outside persistent storage, set `RUN_DIR`
to an absolute path on the mounted volume. Keep the same run directory for
restarts. `run.log` contains runner output, `per_subject/` holds checkpoints,
and `metrics.json` contains the final score.
