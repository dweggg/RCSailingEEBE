import pandas as pd
import ast
import numpy as np

# File path to your CSV file
csv_file = 'data.csv'

# Read CSV file
df = pd.read_csv(csv_file)

# List of channels that have tuple values
channels = ['DIR', 'BAT', 'EX1', 'EX2']

# Parse tuple values in each channel into two separate columns:
# one for a sample value and one for the local timestamp.
for ch in channels:
    df[[f'{ch}_value', f'{ch}_local_time']] = df[ch].apply(lambda s: pd.Series(ast.literal_eval(s)))

# ---- Global Metrics ----
global_times = df['t'].values
global_intervals = np.diff(global_times)
global_avg_interval = np.mean(global_intervals) if len(global_intervals) > 0 else np.nan
global_data_rate = 1 / global_avg_interval if global_avg_interval > 0 else np.nan
global_jitter = np.std(global_intervals) if len(global_intervals) > 0 else np.nan

print("Global Time Metrics:")
print(f"  Average Global Sampling Interval: {global_avg_interval:.6f} sec")
print(f"  Global Data Rate: {global_data_rate:.2f} Hz")
print(f"  Global Jitter (std of intervals): {global_jitter:.6f} sec\n")

# ---- Channel Metrics ----
results = {}
for ch in channels:
    # Extract local times for this channel
    local_times = df[f'{ch}_local_time'].values
    local_intervals = np.diff(local_times)
    
    # Compute local metrics
    local_avg_interval = np.mean(local_intervals) if len(local_intervals) > 0 else np.nan
    local_data_rate = 1 / local_avg_interval if local_avg_interval > 0 else np.nan
    local_jitter = np.std(local_intervals) if len(local_intervals) > 0 else np.nan
    
    # Compute offsets between global time and local time
    offsets = df['t'] - df[f'{ch}_local_time']
    avg_offset = np.mean(offsets)
    offset_jitter = np.std(offsets)
    
    # Compare sample intervals: difference between global interval and local interval
    # Note: This is computed for the interval between consecutive samples.
    interval_diffs = global_intervals - local_intervals
    avg_interval_diff = np.mean(interval_diffs) if len(interval_diffs) > 0 else np.nan
    interval_diff_jitter = np.std(interval_diffs) if len(interval_diffs) > 0 else np.nan

    results[ch] = {
        'local_avg_interval': local_avg_interval,
        'local_data_rate_Hz': local_data_rate,
        'local_jitter': local_jitter,
        'avg_offset': avg_offset,
        'offset_jitter': offset_jitter,
        'avg_interval_diff': avg_interval_diff,
        'interval_diff_jitter': interval_diff_jitter,
    }

# Print channel metrics
for ch, metrics in results.items():
    print(f"Channel: {ch}")
    print(f"  Local Average Sampling Interval: {metrics['local_avg_interval']:.6f} sec")
    print(f"  Local Data Rate: {metrics['local_data_rate_Hz']:.2f} Hz")
    print(f"  Local Jitter (std of local intervals): {metrics['local_jitter']:.6f} sec")
    print(f"  Average Global-to-Local Offset: {metrics['avg_offset']:.6f} sec")
    print(f"  Offset Jitter (std of offsets): {metrics['offset_jitter']:.6f} sec")
    print(f"  Average Difference (global interval - local interval): {metrics['avg_interval_diff']:.6f} sec")
    print(f"  Interval Difference Jitter: {metrics['interval_diff_jitter']:.6f} sec\n")
