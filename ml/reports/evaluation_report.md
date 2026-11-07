# GTZAN Test Set Model Evaluation Report

## 1. Summary of Performance

- **Checkpoint Evaluated:** `/home/sandbox/music_genre_classify/artifacts/models/genre_cnn.pt`
- **Held-Out Test Samples:** 101
- **Overall Test Accuracy:** **49.50%**
- **Macro Precision:** 49.01%
- **Macro Recall:** 49.73%
- **Macro F1-Score:** **47.69%**

## 2. Per-Genre Performance

| Genre | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **Blues** | 42.9% | 30.0% | 35.3% | 10 |
| **Classical** | 81.8% | 90.0% | 85.7% | 10 |
| **Country** | 46.2% | 60.0% | 52.2% | 10 |
| **Disco** | 25.0% | 10.0% | 14.3% | 10 |
| **Hip-Hop** | 50.0% | 27.3% | 35.3% | 11 |
| **Jazz** | 50.0% | 40.0% | 44.4% | 10 |
| **Metal** | 64.3% | 90.0% | 75.0% | 10 |
| **Pop** | 30.0% | 60.0% | 40.0% | 10 |
| **Reggae** | 55.6% | 50.0% | 52.6% | 10 |
| **Rock** | 44.4% | 40.0% | 42.1% | 10 |

## 3. Top Confused Genre Pairs

| True Genre | Misclassified As | Track Count | Misclassification Rate |
| :--- | :--- | :---: | :---: |
| disco | pop | 5 | 50.0% |
| hiphop | pop | 4 | 36.4% |
| country | jazz | 3 | 30.0% |
| blues | metal | 2 | 20.0% |
| blues | reggae | 2 | 20.0% |
| blues | rock | 2 | 20.0% |
| disco | hiphop | 2 | 20.0% |
| hiphop | reggae | 2 | 18.2% |
| jazz | blues | 2 | 20.0% |
| jazz | country | 2 | 20.0% |

## 4. Visual Diagnostics

- Confusion Matrix: `ml/reports/confusion_matrix.png`
- Training Curves: `ml/reports/training_curves.png`

```
              precision    recall  f1-score   support

       Blues     0.4286    0.3000    0.3529        10
   Classical     0.8182    0.9000    0.8571        10
     Country     0.4615    0.6000    0.5217        10
       Disco     0.2500    0.1000    0.1429        10
     Hip-Hop     0.5000    0.2727    0.3529        11
        Jazz     0.5000    0.4000    0.4444        10
       Metal     0.6429    0.9000    0.7500        10
         Pop     0.3000    0.6000    0.4000        10
      Reggae     0.5556    0.5000    0.5263        10
        Rock     0.4444    0.4000    0.4211        10

    accuracy                         0.4950       101
   macro avg     0.4901    0.4973    0.4769       101
weighted avg     0.4902    0.4950    0.4757       101

```