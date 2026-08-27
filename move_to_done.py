import os
import shutil

def move_to_done(task_path):
    done_path = os.path.join(os.path.dirname(task_path), 'done')
    if not os.path.exists(done_path):
        os.makedirs(done_path)
    shutil.move(task_path, done_path)
    print(f"Task moved to {done_path}")

if __name__ == '__main__':
    import sys
    task_path = sys.argv[1]
    move_to_done(task_path)
