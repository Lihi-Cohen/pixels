import os
import glob
import argparse
import random
import fnmatch
import json

def find_recursive(root_dir, ext='.mp3'):
    files = []
    for root, dirnames, filenames in os.walk(root_dir):
        for filename in fnmatch.filter(filenames, '*' + ext):
            files.append(os.path.join(root, filename))
    return files

def load_json(json_path):
    with open(json_path, 'r') as f:
        return json.load(f)

def get_sampled_videos(videos, num_samples):
    sampled_videos = {}
    for category, video_list in videos.items():
        sampled_videos[category] = random.sample(video_list, min(num_samples, len(video_list)))
    return sampled_videos

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root_audio', default='./data/audio',
                        help="root for extracted audio files")
    parser.add_argument('--root_frame', default='./data/frames',
                        help="root for extracted video frames")
    parser.add_argument('--fps', default=8, type=int,
                        help="fps of video frames")
    parser.add_argument('--path_output', default='./data',
                        help="path to output index files")
    parser.add_argument('--trainset_ratio', default=0.8, type=float,
                        help="80% for training, 20% for validation")
    parser.add_argument('--json_file', default='./data/video_info.json',
                        help="Path to the JSON file containing video categories")
    parser.add_argument('--num_samples', default=2, type=int,
                        help="Number of samples to select from each category in the JSON file")
    args = parser.parse_args()

    print(f"Resolved root_audio: {os.path.abspath(args.root_audio)}")
    print(f"Resolved root_frame: {os.path.abspath(args.root_frame)}")

    # Load the .json file
    json_data = load_json(args.json_file)
    videos = json_data.get("videos", {})

    # Sample videos from each category
    sampled_videos = get_sampled_videos(videos, args.num_samples)

    # find all audio/frames pairs
    infos = []
    audio_files = find_recursive(args.root_audio, ext='.mp3')

    for category, video_list in sampled_videos.items():
        for video_id in video_list:
            # Construct paths based on video_id (you may need to adapt this)
            audio_path = os.path.join(args.root_audio, f"{video_id}.mp3")
            frame_path = os.path.join(args.root_frame, f"{video_id}.mp4")

            # Check if corresponding frames exist
            frame_files = glob.glob(frame_path + '/*.jpg')
            if len(frame_files) > args.fps * 20:
                infos.append(','.join([audio_path, frame_path, str(len(frame_files))]))

    print('{} audio/frames pairs found.'.format(len(infos)))

    # split train/val
    n_train = int(len(infos) * args.trainset_ratio)
    random.shuffle(infos)
    trainset = infos[0:n_train]
    valset = infos[n_train:]

    for name, subset in zip(['train', 'val'], [trainset, valset]):
        filename = '{}.csv'.format(os.path.join(args.path_output, name))
        with open(filename, 'w') as f:
            for item in subset:
                f.write(item + '\n')
        print('{} items saved to {}.'.format(len(subset), filename))

    print('Done!')
