import numpy as np
import pandas as pd

def ahp_consensus(review_df: pd.DataFrame, score_column="review_score"):
    """
    review_df columns:
      reviewer, identity_hash, review_score

    review_score scale (recommendation):
      1 = strongly approve
      5 = neutral
      9 = strongly block

    Returns:
      dict: { identity_hash: ahp_score_0_to_100 }
    """
    if review_df.empty:
        return {}

    items = review_df["identity_hash"].unique()
    pivoted = review_df.pivot(index="reviewer", columns="identity_hash", values=score_column)

    ahp_matrix = np.zeros((len(items), len(items)))
    ahp_sum = np.zeros(len(items))

    # Pairwise comparisons (same structure as professor)
    for i in range(len(pivoted)):
        for j in range(len(items)):
            for k in range(j - 1, -1, -1):
                try:
                    vj = float(pivoted.iloc[i].iloc[j])
                    vk = float(pivoted.iloc[i].iloc[k])
                    if vj > vk:
                        ahp_matrix[k, j] += 1.0
                        ahp_sum[j] += 1.0
                    elif vj < vk:
                        ahp_matrix[j, k] += 1.0
                        ahp_sum[k] += 1.0
                    else:
                        ahp_matrix[j, k] += 0.5
                        ahp_matrix[k, j] += 0.5
                        ahp_sum[j] += 0.5
                        ahp_sum[k] += 0.5
                except:
                    pass

    # Normalize rows
    for i in range(len(items)):
        if ahp_sum[i] != 0:
            ahp_matrix[i, :] = ahp_matrix[i, :] / ahp_sum[i]

    # Aggregate column sums = final ranking signal
    ahp_final = np.sum(ahp_matrix, axis=0)

    # Normalize to 0..100
    if ahp_final.max() > 0:
        ahp_final = 100.0 * ahp_final / ahp_final.max()

    return dict(zip(items, ahp_final))