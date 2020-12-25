from typing import List
import csv
from torch.utils.data import Dataset
from pathlib import Path
import numpy as np
from constants.enum_keys import PG

class LabelLoader(Dataset):

    def __init__(self, data_path, is_train):
        paths = dict()
        paths["train", "root"] = data_path / "train"
        paths["pred", "root"] = data_path / "pred"

        self.is_train = is_train

        if is_train:
            root: Path = paths["train", "root"]
        else:
            root: Path = paths["pred", "root"]

        video_paths: List = list(root.glob('./*.mp4'))

        csv_paths: List = [p.with_suffix('.csv') for p in video_paths]
        csv_contents: List = [self.__load_csv_label(p) for p in csv_paths]

        self.video_csv = list(zip(video_paths, csv_contents))

    def __len__(self):
        return len(self.video_csv)

    def __getitem__(self, index):
        v_path, label = self.video_csv[index]
        # Randomly clip the video because original video is too large to train.
        # start_ind = np.random.randint(0, len(video_loader) - self.num_frames)
        # truncated_video = video_loader.get(start_ind)
        # truncated_label = label[start_ind: start_ind+self.num_frames]
        return {PG.VIDEO_PATH: v_path, PG.GESTURE_LABEL: label}

    @staticmethod
    def __load_csv_label(csv_path):
        """
        Load csv labels. Each number indicates a gesture in a frame.
        example content: 0,0,0,2,2,2,2,2,0,0,0,0,0
        """
        with open(csv_path, newline='') as csv_file:
            reader = csv.reader(csv_file)
            row0 = list(reader)[0]

        return row0