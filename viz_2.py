def visualize_sound_clustering(pixel_spectrograms, frame, output_path):
    """
    Visualize sound clustering by mapping log spectrograms to RGB using PCA.

    Args:
        pixel_spectrograms (np.ndarray): Array of shape (H*W, D) where D is the spectrogram dimension.
        frame (np.ndarray): Input video frame of shape (H, W, 3).
        output_path (str): Path to save the output image.

    Returns:
        None
    """
    # Perform PCA on the spectrograms
    pca = PCA(n_components=3)
    pca_result = pca.fit_transform(pixel_spectrograms)

    # Normalize PCA results to [0, 1]
    pca_normalized = (pca_result - np.min(pca_result)) / (np.max(pca_result) - np.min(pca_result))
    pca_normalized = pca_normalized.reshape(frame.shape[0], frame.shape[1], 3)

    # Blend frame with PCA visualization
    overlay = (pca_normalized * 255).astype(np.uint8)
    blended_frame = 0.5 * frame + 0.5 * overlay

    # Save the visualization
    Image.fromarray(blended_frame.astype(np.uint8)).save(output_path)
    print(f"Saved sound clustering visualization: {output_path}")
