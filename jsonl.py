import json,os

class Episode:
    def __init__(self, episode_index, tasks, length):
        self.episode_index = episode_index
        self.tasks = tasks
        self.length = length

class EpisodesJsonl:
    def __init__(self, filename=""):
        self.data = []

        if filename != "":
            self.data = self.Load_Jsonl(filename)

    def Load_Jsonl(self, filename):
        data = []
        with open(filename, 'r') as f:
            for line in f:
                data.append(json.loads(line, object_hook=self.episode_object_hook))
        return data
    
    def episode_object_hook(self, dict):
        if 'episode_index' in dict and 'tasks' in dict and 'length' in dict:
            return Episode(dict['episode_index'], dict['tasks'], dict['length'])
        else:
            raise Exception("Failed to load episodes.")

    def Add(self, episode):
        resort = False
        if len(self.data) > 0 and episode.episode_index < self.data[-1].episode_index:
            resort = True

        self.data.append(episode)

        if resort == True:
            self.data.sort(key=lambda x: x.episode_index)

    def Delete(self, filename, episode_index):
        self.data = [item for item in self.data if item.episode_index != episode_index]   

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
    def __init__(self, filename=""):
        self.data = []

        if filename != "":
            self.data = self.Load_Jsonl(filename)
    
    def Load_Jsonl(self, filename):
        data = []
        with open(filename, 'r') as f:
            for line in f:
                data.append(json.loads(line, object_hook=self.task_object_hook))
        return data
    
    def task_object_hook(self, dict):
        if 'task_index' in dict and 'task' in dict:
            return Task(dict['task_index'], dict['task'])
        else:
            raise Exception("Failed to load tasks.")
    
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
    # Load existing episodes.jsonl
    episodes = EpisodesJsonl('episodes.jsonl')  
    for episode in episodes.data:
        print(f"Loaded: {episode.episode_index} and {episode.tasks} and {episode.length}")

    # Create a new episodes.jsonl
    episodes = EpisodesJsonl()

    # Add episodes
    episodes.Add(Episode(0, ['task1'], 100))
    episodes.Add(Episode(1, ['task2'], 200))
    episodes.Add(Episode(2, ['task3'], 300))
    for episode in episodes.data:
        print(f"{episode.episode_index} and {episode.tasks} and {episode.length}")

    # Detelet episode with episode_index
    episodes.Delete(1)
    for episode in episodes.data:
        print(f"{episode.episode_index} and {episode.tasks} and {episode.length}")

    # Re-add episode
    episodes.Add(Episode(1, ['task2'], 200))
    for episode in episodes.data:
        print(f"{episode.episode_index} and {episode.tasks} and {episode.length}")

    # Save episodes.jsonl in the end of the recording process.
    episodes.Save('test_episodes.jsonl')

    # Example on tasks.jsonl
    tasks = TasksJsonl()
    tasks.Add(Task(0, 'Move to target position'))
    tasks.Save('test_tasks.jsonl')

