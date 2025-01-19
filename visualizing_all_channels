def evaluate(netWrapper, loader, history, epoch, args):
    print('Evaluating at {} epochs...'.format(epoch))
    torch.set_grad_enabled(False)

    # remove previous viz results
    makedirs(args.vis, remove=True)

    # switch to eval mode
    netWrapper.eval()


    channel_samples = {}
    # Create directory for clustering visualizations
    clustering_dir = os.path.join(args.vis, 'clustering')
    makedirs(clustering_dir, remove=True)

    # Process all samples
    for i, batch_data in enumerate(loader):
        # forward pass
        pred_masks, feat_frames, feat_sound = netWrapper.forward(batch_data, args)
        frames = batch_data['frames'][0]
        
        B = pred_masks.shape[0]
        num_channels = feat_frames.shape[1]  # Number of channels
        
        # Initialize channel directories
        for c in range(num_channels):
            channel_dir = os.path.join(args.vis, f'channel_{c}')
            makedirs(channel_dir)
            if c not in channel_samples:
                channel_samples[c] = []
        
        # Process each sample
        for b in range(B):
            frame = frames[b, :, 1].cpu().numpy()
            visual_features = feat_frames[b].detach().cpu().numpy()
            audio_features = feat_sound[b].detach().cpu().numpy()
            
            # 1. Create clustering visualization
            pixel_spectrograms_flat = pred_masks[b].reshape(-1, pred_masks.shape[-1] * pred_masks.shape[-2]).detach().cpu().numpy()
            clustering_path = os.path.join(clustering_dir, f'clustering_batch{i}_sample{b}.png')
            
            try:
                visualize_sound_clustering(
                    pixel_spectrograms_flat,
                    frame,
                    clustering_path
                )
                print(f"Created clustering visualization for batch {i}, sample {b}")
            except Exception as e:
                print(f"Error processing clustering visualization: {str(e)}")
                continue
            
            # 2. Store sample information for each channel
            for c in range(num_channels):
                sample_info = {
                    'frame': frame,
                    'visual_features': visual_features[c:c+1],
                    'audio_features': audio_features[c:c+1],
                    'batch': i,
                    'sample': b
                }
                channel_samples[c].append(sample_info)

    # Create channel-wise visualizations
    for channel_idx in sorted(channel_samples.keys()):
        channel_dir = os.path.join(args.vis, f'channel_{channel_idx}')
        print(f"\nProcessing Channel {channel_idx}")
        
        # Process all samples for this channel
        for sample_idx, sample in enumerate(channel_samples[channel_idx]):
            output_path = os.path.join(
                channel_dir, 
                f'sample_{sample["batch"]}_{sample["sample"]}.png'
            )
            
            try:
                visualize_activations(
                    sample['frame'],
                    sample['visual_features'],
                    sample['audio_features'],
                    output_path,
                    channel_idx=channel_idx
                )
                print(f"Created visualization for channel {channel_idx}, sample {sample_idx+1}")
            except Exception as e:
                print(f"Error processing channel {channel_idx}, sample {sample_idx+1}: {str(e)}")
                continue

    print('\nEvaluation visualization completed!')
