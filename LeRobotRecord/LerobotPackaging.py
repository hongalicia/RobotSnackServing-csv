import os
import shutil
import tyro
from LeRobotRecord.JsonReader import *
from dataclasses import dataclass
import copy

@dataclass
class ArgsConfig:
    """Configuration for LeRobot Packaging."""

    folder_dir: str = "/home/j300/task_0"
    """Directory that contains a data folder, a videos folder, and a meta folder."""

    num_arms: int = 2
    """Number of arms."""

#####################################################################################
# main packaging function
#####################################################################################

def meta(config: ArgsConfig):
    if(config.folder_dir == ''):
        print("No input folder.")
        return
    
    # print(config.folder_dir)
    # print(config.num_arms)

    if os.path.isdir(config.folder_dir + "/data/chunk-000") == False:
        print("data folder does not exist.")
        return

    if os.path.isdir(config.folder_dir+ "/videos/chunk-000") == False:
        print("videos folder does not exist.")
        return
    
    num_data = 0
    for _, _, files in os.walk(config.folder_dir + "/data/chunk-000"):
        num_data = len(files)
        if num_data == 0:
            print("data parquet does not exist.")
            return
    print("num_data: ", num_data)

    num_videos_dir = 0
    num_videos = []
    video_dir_names = []
    for _, dirnames, files in os.walk(config.folder_dir + "/videos/chunk-000"):
        if num_videos_dir == 0:
            video_dir_names = dirnames
            num_videos_dir = len(dirnames)
            for i in range(num_videos_dir):
                for _, _, files in os.walk(config.folder_dir + "/videos/chunk-000/" + dirnames[i]):
                    num_videos_i = len(files)
                    if num_videos_i != num_data:
                        print("Number of videos mismatchArgsConfig with the data.")
                        return
                    num_videos.append(num_videos_i)
    print("num_videos_dir: ", num_videos_dir)
    print("num_videos:", num_videos)

    if os.path.isdir(config.folder_dir + "/meta") == False:
        print("meta folder does not exist.")
        return   

    metapath = config.folder_dir + "/meta"

    ModifyInfoJson(metapath, config.num_arms, num_data, num_videos, video_dir_names)
    ModifyModalityJson(metapath, config.num_arms, video_dir_names)

def ModifyInfoJson(dir, num_arms, num_data, num_videos, video_dir_names):
    episodes = Load_Jsonl(dir + '/episodes.jsonl')
    total_frames = 0
    for e in episodes:
        total_frames += e['length']

    info = InfoJson(num_arms)
    info.total_episodes = num_data
    info.total_frames = total_frames
    info.total_videos = sum(num_videos)
    info.dict['splits']['train'] = '0:' + str(num_data)
    info = RemoveInvalidImageKeyInInfoJson(info, video_dir_names)
    info.Save(dir + '/info.json')

def RemoveInvalidImageKeyInInfoJson(info, video_dir_names):
    keyword = 'observation.images.'
    new_info = copy.deepcopy(info)

    for key in info.dict['features'].keys():
        if keyword in key:
            if key not in video_dir_names:
                del new_info.dict['features'][key]
    
    return new_info
    
def ModifyModalityJson(dir, num_arms, video_dir_names):
    modality = ModalityJson(num_arms)
    new_modality = copy.deepcopy(modality)

    keyword = 'observation.images.'
    new_video_dir_names = []
    for video_dir in video_dir_names:
        new_video_dir_names.append(video_dir.replace(keyword, ""))    

    for key in modality.dict['video']:
        if key not in new_video_dir_names:
            del new_modality.dict['video'][key]
    
    new_modality.Save(dir + '/modality.json')

if __name__ == "__main__":
    # Parse arguments using tyro
    config = tyro.cli(ArgsConfig)
    config.num_arms = 2
    meta(config)    