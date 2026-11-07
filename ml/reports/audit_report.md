# GTZAN Dataset Audit and Validation Report

## 1. Executive Summary

- **Dataset Path:** `ml/Data/genres_original`
- **Total Audio Files Found:** 1000
- **Valid, Decodeable Tracks:** **999**
- **Excluded / Corrupt Files:** **1**
- **Classes Discovered:** 10 / 10 expected genres
- **Audio Sample Rate:** 22050 Hz (999 tracks)
- **Audio Channels:** 1-channel (999 tracks)
- **Mean Track Duration:** 30.024s (range: 29.932s to 30.649s)

## 2. Per-Genre Class Balance

| Genre | Raw Files | Valid Files | Excluded | Balance Status |
| :--- | :---: | :---: | :---: | :--- |
| **blues** | 100 | 100 | 0 | ✅ Balanced (100) |
| **classical** | 100 | 100 | 0 | ✅ Balanced (100) |
| **country** | 100 | 100 | 0 | ✅ Balanced (100) |
| **disco** | 100 | 100 | 0 | ✅ Balanced (100) |
| **hiphop** | 100 | 100 | 0 | ✅ Balanced (100) |
| **jazz** | 100 | 99 | 1 | ⚠️ 99/100 |
| **metal** | 100 | 100 | 0 | ✅ Balanced (100) |
| **pop** | 100 | 100 | 0 | ✅ Balanced (100) |
| **reggae** | 100 | 100 | 0 | ✅ Balanced (100) |
| **rock** | 100 | 100 | 0 | ✅ Balanced (100) |

## 3. Corrupt or Unreadable Audio Files

| File Path | Genre | Reason | Details |
| :--- | :--- | :--- | :--- |
| `ml/Data/genres_original/jazz/jazz.00054.wav` | jazz | `CORRUPTED_OR_UNREADABLE` | Error opening '/home/vansh/code/music_genre_calssifier/ml/Data/genres_original/jazz/jazz.00054.wav': Format not recognised. |

## 4. Duplicate Analysis & Contamination Prevention

A total of **14 duplicate groups** were detected via exact MD5 checksum analysis:

- **Cross-Genre Duplicates (1 groups):** Exact identical audio waveforms assigned to conflicting genres in GTZAN.
- **Intra-Genre Duplicates (13 groups):** Identical audio clips repeated inside the same genre folder.

### 4.1 Cross-Genre Duplicates (Critical for Split Isolation)

- **Hash:** `00025a41bc991e8a8d5232e6660df86f` | **Genres:** rock, metal
  - `ml/Data/genres_original/metal/metal.00058.wav`
  - `ml/Data/genres_original/rock/rock.00016.wav`

### 4.2 Intra-Genre Duplicates

- **Genre:** `disco` | **Hash:** `991d302992ab7961726908f5d7a58963`
  - `ml/Data/genres_original/disco/disco.00098.wav`
  - `ml/Data/genres_original/disco/disco.00099.wav`
- **Genre:** `hiphop` | **Hash:** `86985cbc22cbf7f75e6054920676d2e6`
  - `ml/Data/genres_original/hiphop/hiphop.00039.wav`
  - `ml/Data/genres_original/hiphop/hiphop.00045.wav`
- **Genre:** `hiphop` | **Hash:** `9a42deaa9beb74a739c30c624830841f`
  - `ml/Data/genres_original/hiphop/hiphop.00076.wav`
  - `ml/Data/genres_original/hiphop/hiphop.00078.wav`
- **Genre:** `metal` | **Hash:** `108396866a0b7bd6120ce0f2c3647a33`
  - `ml/Data/genres_original/metal/metal.00034.wav`
  - `ml/Data/genres_original/metal/metal.00094.wav`
- **Genre:** `metal` | **Hash:** `d7de8afad648505c0d6554ab763bc8af`
  - `ml/Data/genres_original/metal/metal.00040.wav`
  - `ml/Data/genres_original/metal/metal.00061.wav`
- **Genre:** `metal` | **Hash:** `6e6c3b5f83e2bc1bcbbedc3c0aaec346`
  - `ml/Data/genres_original/metal/metal.00041.wav`
  - `ml/Data/genres_original/metal/metal.00062.wav`
- **Genre:** `metal` | **Hash:** `dc24521ee6a1d42158ba0ff8c31e1ed6`
  - `ml/Data/genres_original/metal/metal.00042.wav`
  - `ml/Data/genres_original/metal/metal.00063.wav`
- **Genre:** `metal` | **Hash:** `cba45f2118073a824b026587a281f72e`
  - `ml/Data/genres_original/metal/metal.00043.wav`
  - `ml/Data/genres_original/metal/metal.00064.wav`
- **Genre:** `metal` | **Hash:** `8ee4d1bc07a8ac9fb7c4b05eea5177ce`
  - `ml/Data/genres_original/metal/metal.00044.wav`
  - `ml/Data/genres_original/metal/metal.00065.wav`
- **Genre:** `metal` | **Hash:** `6fb04d43192a9b025402fe6aca3f7e2b`
  - `ml/Data/genres_original/metal/metal.00045.wav`
  - `ml/Data/genres_original/metal/metal.00066.wav`
- **Genre:** `pop` | **Hash:** `294ff2f83536ceded548ed8b8ab4df50`
  - `ml/Data/genres_original/pop/pop.00054.wav`
  - `ml/Data/genres_original/pop/pop.00060.wav`
- **Genre:** `pop` | **Hash:** `91b4735c6f9751f489cc5be78d86aa44`
  - `ml/Data/genres_original/pop/pop.00067.wav`
  - `ml/Data/genres_original/pop/pop.00071.wav`
- **Genre:** `reggae` | **Hash:** `a2afab9cf2b8d73dc54823599f558116`
  - `ml/Data/genres_original/reggae/reggae.00081.wav`
  - `ml/Data/genres_original/reggae/reggae.00082.wav`

## 5. Splitting and Training Recommendations

1. **Exclude Corrupted Files:** Completely exclude unreadable files (e.g. `jazz.00054.wav`) from training, validation, and testing.
2. **Recording-Level Isolation:** Ensure that identical or duplicate recordings (like the 14 duplicate hash pairs) are assigned to the **same split** (or deduplicated) so evaluation sets remain strictly unpolluted.
3. **Stratified Partitioning:** Partition valid tracks with an 80% / 10% / 10% stratified split (`seed=42`).
4. **Training-Only Normalization:** Compute global dataset mean and standard deviation strictly over the training split to avoid data leakage.

## 6. How to Reproduce This Audit

```bash
# Run the audit script from the repository root
.venv/bin/python3 ml/scripts/audit_dataset.py --data-dir ml/Data/genres_original
```