import heapq
from sklearn.metrics import (adjusted_rand_score,
                             homogeneity_completeness_v_measure)


def recall_at_k(heap, k, value):
    """
    Checks if a value is in the top k elements of a heap.

    Args:
        heap (list): Binary heap.
        value: Value to check.
        k (int): Number of top elements to consider.

    Returns:
        bool: True if value is in the top k elements, False otherwise.
    """
    top_k_elements = heapq.nsmallest(k, heap)
    return value in [elem[2] for elem in top_k_elements]


def get_value_position(heap, value):
    """
    Returns the position (index) of a value in a binary heap.

    Args:
        heap (list): Binary heap.
        value: Value to find the position of.

    Returns:
        int: Position (index) of the value in the heap.
        Returns -1 if the value is not found.
    """
    try:
        position = next(idx for idx, element in enumerate(heap)
                        if element[2] == value)
    except StopIteration:
        position = -1
    return position + 1


def heap_to_ordered_list(heap):
    """
    Converts a binary heap into an ordered list.

    Args:
        heap (list): Binary heap.

    Returns:
        list: Ordered list representing the heap elements.
    """
    ordered_list = []
    while heap:
        ordered_list.append(heapq.heappop(heap))
    return ordered_list


def gpt_cluster_metrics(true_labels, found_labels):
    # Calculate the Adjusted Rand Index
    ari = adjusted_rand_score(true_labels, found_labels)
    ari_range = (-1, 1)
    ari_ideal = 1

    # Calculate the Normalized Mutual Information
    nmi = normalized_mutual_info_score(true_labels, found_labels)
    nmi_range = (0, 1)
    nmi_ideal = 1

    # Calculate the Fowlkes-Mallows Index
    fmi = fowlkes_mallows_score(true_labels, found_labels)
    fmi_range = (0, 1)
    fmi_ideal = 1

    # Calculate homogeneity, completeness, and V-measure
    homogeneity, completeness, v_measure = homogeneity_completeness_v_measure(true_labels, found_labels)
    hcv_range = (0, 1)
    hcv_ideal = 1

    # Print the results
    print(f"Adjusted Rand Index: {ari:.4f} [range: {ari_range}, ideal: {ari_ideal}]")
    print(f"Normalized Mutual Information: {nmi:.4f} [range: {nmi_range}, ideal: {nmi_ideal}]")
    print(f"Fowlkes-Mallows Index: {fmi:.4f} [range: {fmi_range}, ideal: {fmi_ideal}]")
    print(f"Homogeneity: {homogeneity:.4f} [range: {hcv_range}, ideal: {hcv_ideal}]")
    print(f"Completeness: {completeness:.4f} [range: {hcv_range}, ideal: {hcv_ideal}]")
    print(f"V-measure: {v_measure:.4f} [range: {hcv_range}, ideal: {hcv_ideal}]")
