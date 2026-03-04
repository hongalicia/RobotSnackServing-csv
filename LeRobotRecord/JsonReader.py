from dataclasses import dataclass
import json

@dataclass
class JsonReader:
    @staticmethod
    def from_dict(filename):
        file = open(filename, 'r')
        content = file.read()
        jsonstr = json.loads(content)
        return jsonstr
    
    def save(dict, filename):
        with open(filename, 'w') as outfile:
            json.dump(dict, outfile, indent=4)

class InfoJson:
    def __init__(self, num_arms):
        if num_arms == 1:
            self.dict = JsonReader.from_dict('LeRobotRecord/info_single.json')
        else:
            self.dict = JsonReader.from_dict('LeRobotRecord/info.json')
        self.total_episodes = self.dict['total_episodes']
        self.total_frames = self.dict['total_frames']
        self.total_tasks = self.dict['total_tasks']
        self.total_videos = self.dict['total_videos']

    def Save(self, filename):
        self.dict['total_episodes'] = self.total_episodes
        self.dict['total_frames'] = self.total_frames
        self.dict['total_tasks'] = self.total_tasks
        self.dict['total_videos'] = self.total_videos
        self.dict['splits']['train'] = '0:' + str(self.total_episodes)
        JsonReader.save(self.dict, filename)

class ModalityJson:
    def __init__(self, num_arms):
        if num_arms == 1:
            self.dict = JsonReader.from_dict('LeRobotRecord/modality_single.json')
        else:
            self.dict = JsonReader.from_dict('LeRobotRecord/modality.json')

    def Save(self, filename):
        JsonReader.save(self.dict, filename)

def Load_Jsonl(filename):
    data = []
    with open(filename, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

if __name__ == '__main__':
    info = InfoJson()
    info.total_episodes = 10
    info.Save('new_info.json')
