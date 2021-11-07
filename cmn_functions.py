from pathlib import Path
import json
from collections import defaultdict


def jsonKeys2int(x):
    if isinstance(x, dict):
        newdict = {}
        for k, v in x.items():
            if k.isnumeric():
                newdict[int(k)] = v
            else:
                newdict[k] = v
        return newdict
    return x


def swap_dict_keys_values(cur_dict):
    return dict([(value, key) for key, value in cur_dict.items()])


def tree():  # Weird self expanding dictionary. Will have to study how it actually works at some point.
    def the_tree():
        return defaultdict(the_tree)

    return the_tree()


def create_folder(cur_dir, new_folder):  # Creates a folder if it does not exist.
    '''
    :param cur_dir: Path object
    :param new_folder: String
    '''

    my_path = cur_dir / new_folder
    my_path.mkdir(exist_ok=True)
    return my_path


def export_json(target_path, filename, data):  # Writes a json to a certain directory
    '''
    :param target_path: Path object
    :param filename: String
    :param data: Dictionary
    '''

    jsonFile = json.dumps(data, ensure_ascii=False, indent=2)
    jsonPath = target_path / (filename + r'.json')
    jsonPath.write_text(jsonFile)
    print("Json file written to " + str(jsonPath))


def import_json(target_path, name):  # Goes through a directory, then loads json info into a dict
    '''
    :param target_path: Path Object
    :param name: String
    '''
    import_file = target_path / (name + r'.json')
    with import_file.open() as input_file:
        json_array = json.loads(input_file.read())
        return (json_array)
