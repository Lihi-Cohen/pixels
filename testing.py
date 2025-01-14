import os
import csv

def validate_frame_counts(csv_file):
    print(f"Validating file: {csv_file}")
    csv_file_path = os.path.abspath(csv_file)
    print(f"Resolved path: {csv_file_path}")
    
    if not os.path.exists(csv_file_path):
        print(f"CSV file not found: {csv_file_path}")
        return

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            audio_path, frame_path, frame_count = row
            audio_path = os.path.abspath(audio_path)
            frame_path = os.path.abspath(frame_path)
            frame_count = int(frame_count)

            print(f"Checking audio path: {audio_path}")
            print(f"Checking frame path: {frame_path}")

            if not os.path.exists(audio_path):
                print(f"Missing audio file: {audio_path}")
            if not os.path.exists(frame_path):
                print(f"Missing frame directory: {frame_path}")
            else:
                # Count the number of .jpg files in the frame directory
                actual_frame_count = len([file for file in os.listdir(frame_path) if file.endswith('.jpg')])
                if actual_frame_count != frame_count:
                    print(f"Frame count mismatch in {frame_path}. Expected: {frame_count}, Found: {actual_frame_count}")
                else:
                    print("GOOD")

# Replace these with your actual CSV file paths
validate_frame_counts('data/train.csv')
validate_frame_counts('data/val.csv')
