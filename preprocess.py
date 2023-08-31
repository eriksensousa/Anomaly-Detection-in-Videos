import os
import time
from config import Config
import uuid
from PIL import Image
import matplotlib.pyplot as plt
import multiprocessing as mp
import pandas as pd
import numpy as np
print(mp.cpu_count())


working_directory = "."
processes = {}

class Config:
    IMAGE_SIZE = 256
    DATASET_PATH = os.path.join(working_directory, "files")
    EDIT_DATASET_PATH = os.path.join(working_directory, "regenerated_files")
    THREAD_COUNT = mp.cpu_count()


def tree(folder, max_items=10000000):
    print("Tree view of", folder)
    directory_count = 0
    for directory_path, directory_names, filenames in os.walk(folder):
        directory_level = directory_path.replace(folder, "")
        directory_level = directory_level.count(os.sep)
        indent = " " * 4
        print("{}{}/".format(indent * directory_level, os.path.basename(directory_path)))

        for i in range(len(filenames)):
            if i >= max_items:
                print("{}{}".format(indent * (directory_level + 1), "..."))
                break
            print("{}{}".format(indent * (directory_level + 1), filenames[i]))

        directory_count = directory_count + 1
        if directory_count >= max_items:
            print("{}{}/".format(indent * directory_level, "..."))
            break


def save_image(image_class, img_file_name, img):
    img_folder = os.path.join(Config.EDIT_DATASET_PATH, image_class)
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)
    img_file = os.path.join(img_folder, img_file_name)
    img.save(img_file)


def preprocess_image(data):
    for item in data.values.tolist():
        sub_directory_path = item[0]
        file_name = item[1]
        class_name = item[2]
        img_path = os.path.join(sub_directory_path, file_name)
        if str(img_path)[-3:] == "tif":
            try:
                img = Image.open(img_path)
                img = img.resize((Config.IMAGE_SIZE, Config.IMAGE_SIZE))
                new_file_name = str(uuid.uuid4()) + ".tif"
                save_image(class_name, new_file_name, img)
            except:
                print("Problem on file", img_path)


def preprocess_images():
    data = []
    for f in sorted(os.listdir(Config.DATASET_PATH)):
        directory_path = os.path.join(Config.DATASET_PATH, f)
        if os.path.isdir(directory_path):
            class_name = f
            for v in sorted(os.listdir(directory_path)):
                sub_directory_path = os.path.join(directory_path, v)
                for c in sorted(os.listdir(sub_directory_path)):
                    data.append([sub_directory_path, c, class_name])

    df = pd.DataFrame(data=data, columns=['directory_path', 'file_name', 'label'])
    sample_count = len(df)
    slider = int(sample_count / Config.THREAD_COUNT)

    sliders = []
    for i in range(Config.THREAD_COUNT):
        sliders.append(i * slider)
    sliders.append(sample_count)

    print("Sliders", sliders)

    df = df.iloc[np.random.permutation(len(df))]

    dfs = []
    for i in range(Config.THREAD_COUNT):
        dfs.append(df.iloc[sliders[i]:sliders[i + 1] - 1])

    for i in range(Config.THREAD_COUNT):
        print('registering process %d' % i)
        proc = mp.Process(target=preprocess_image, args=(dfs[i],))
        processes[i] = proc
        proc.start()

    while (True):
        finished_count = 0
        for id in processes.keys():
            if not processes[id].is_alive():
                finished_count = finished_count + 1

        if finished_count == Config.THREAD_COUNT:
            break
        else:
            time.sleep(5)


def get_stats():
    total_samples_count = 0
    for f in sorted(os.listdir(Config.EDIT_DATASET_PATH)):
        directory_path = os.path.join(Config.EDIT_DATASET_PATH, f)
        if os.path.isdir(directory_path):
            class_name = f
            sample_count = len(os.listdir(directory_path))
            print("Class Name:", class_name, ", Samples Count:", sample_count)
            total_samples_count = total_samples_count + sample_count
            plt.figure(figsize=(10, 10))
            plt.title("Some examples of class " + class_name)
            count = 0
            images = []
            for v in sorted(os.listdir(directory_path)):
                img_path = os.path.join(directory_path, v)
                img = Image.open(img_path)
                images.append(img)
                count = count + 1
                if count >= 25:
                    break
            for n in range(25):
                ax = plt.subplot(5, 5, n + 1)
                plt.imshow(images[n], cmap='gray')
                plt.axis('off')
            plt.show()
    print("Total Samples Count:", total_samples_count)


if __name__ == '__main__':
    start_time = time.time()
    tree(Config.DATASET_PATH, max_items=3)
    preprocess_images()
    tree(Config.EDIT_DATASET_PATH, max_items=3)
    get_stats()
    print("Execution time:", time.time() - start_time, "seconds.")
