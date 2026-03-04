import json,os

class Episode:
    def __init__(self, episode_index, tasks, length):
        self.episode_index = episode_index
        self.tasks = tasks
        self.length = length

class EpisodesJsonl:
    def __init__(self):
        self.data = []

    def Add(self, episode):
        self.data.append(episode)

    def Save(self, filename):
        # 若檔案不存在則建立新檔案
        dir_path = os.path.dirname(filename)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        # Append new episodes to the file instead of overwriting
        with open(filename, "a") as f:
            for item in self.data:
                json_line = json.dumps(item.__dict__)
                f.write(json_line + "\n")
        self.data = []  # Clear after saving to avoid duplicate appends

class Task:
    def __init__(self, task_index, task):
        self.task_index = task_index
        self.task = task

class TasksJsonl:
    def __init__(self):
        self.data = []
    
    def Add(self, task):
        self.data.append(task)

    def Save(self, filename): 
        # 若檔案不存在則建立新檔案
        dir_path = os.path.dirname(filename)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)       
        with open(filename, "w") as f:
            for item in self.data:
                json_line = json.dumps(item.__dict__)
                f.write(json_line + "\n")

if __name__ == '__main__':
    episodes = EpisodesJsonl()  
    episodes.Add(Episode(2, ['grasp oil bottle'], 567))
    episodes.Save('test_episodes.jsonl')

    tasks = TasksJsonl()
    tasks.Add(Task(0, 'Move to target position'))
    tasks.Save('test_tasks.jsonl')

