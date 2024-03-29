from pathlib import Path
import json
from ruamel.yaml import YAML
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


def get_dict_key_index(cur_dict, key):
    return list(cur_dict.keys()).index(key)


def remove_keys_from_dict(cur_dict, num_keys):
    if isinstance(cur_dict, dict):
        newdict = {}
        for k, v in cur_dict.items():
            if get_dict_key_index(cur_dict, k) > num_keys: newdict[k] = v
        return newdict
    return cur_dict


def tree():  # Weird self expanding dictionary. Will have to study how it actually works at some point.
    def the_tree():
        return defaultdict(the_tree)

    return the_tree()


def create_folder(cur_dir, new_folder):  # Creates a folder if it does not exist.
    """
    :param cur_dir: Path object
    :param new_folder: String
    """

    my_path = cur_dir / new_folder
    my_path.mkdir(exist_ok=True)
    return my_path


def export_json(target_path, filename, data):  # Writes a json to a certain directory
    """
    :param target_path: Path object
    :param filename: String
    :param data: Dictionary
    """

    jsonFile = json.dumps(data, ensure_ascii=False, indent=2)
    jsonPath = target_path / (filename + r'.json')
    jsonPath.write_text(jsonFile)
    print("Json file written to " + str(jsonPath))


def import_json(target_path, name):  # Goes through a directory, then loads json info into a dict
    """
    :param target_path: Path Object
    :param name: String
    """
    import_file = target_path / (name + r'.json')
    with import_file.open() as input_file:
        json_array = json.loads(input_file.read())
        return json_array


def export_yaml(target_path, filename, data):  # Writes a yaml to a certain directory
    """
    :param target_path: Path object
    :param filename: String
    :param data: Dictionary
    """
    new_data = json.loads(json.dumps(data))
    yaml = YAML(typ='safe', pure=True)
    yaml.sort_base_mapping_type_on_output = False
    yaml.indent(mapping=2, sequence=5, offset=4)
    yaml.default_flow_style = False
    yamlPath = target_path / (filename + r'.yaml')
    yaml.dump(new_data, yamlPath)
    print("Yaml file written to " + str(yamlPath))


def import_yaml(target_path, name):  # Goes through a directory, then loads yaml info into a dict
    """
    :param target_path: Path Object
    :param name: String
    """
    import_file = target_path / (name + r'.yaml')
    yaml = YAML(typ='safe')
    return yaml.load(import_file)


def convert_hex_to_hexstring(hex_value):
    byte_array = bytearray(hex_value)
    hexadecimal_string = str(byte_array.hex(' '))
    return hexadecimal_string


def convert_hexstring_to_hex(hex_string):
    return bytes.fromhex(hex_string)


def convert_byte_to_nibble(hex_value, nibble_part):
    byte_array = hex_value
    nibble_1 = (byte_array >> 4) & 0xf
    nibble_2 = byte_array & 0xf
    if nibble_part == 1:
        return nibble_1
    else:
        return nibble_2


def convert_nibbles_to_byte(nibble_1, nibble_2):
    return (nibble_1 << 4) | nibble_2


def get_nth_key(dictionary, n=0):  # Not my function, taken from online
    if n < 0:
        n += len(dictionary)
    for i, key in enumerate(dictionary.keys()):
        if i == n:
            return key
    raise IndexError("dictionary index out of range")


def get_pathobject_from_string(message, file_extension=""):
    print(message)
    print("")
    file_string = input('Type the file/folder name: ')
    file_string += file_extension
    print("")
    return Path(file_string)


def yes_or_no(question):  # Not my function, taken from https://gist.github.com/garrettdreyfus/8153571
    while "the answer is invalid":
        reply = str(input(question + ' (y/n): ')).lower().strip()
        if reply[:1] == 'y':
            return True
        if reply[:1] == 'n':
            return False


def write_zero_bytes(my_file, num_bytes):
    x = 0
    while x < num_bytes:
        my_file.write_uint8(0)
        x += 1


def bitfield(num):
    # bitfieldlist = [1 if x=='1' else 0 for x in "{:08b}".format(num)]
    bitfieldlist = [1 if num & (1 << (7 - n)) else 0 for n in range(8)]
    if len(bitfieldlist) < 8:
        append = 8 - len(bitfieldlist)
        x = 0
        while x < append:
            bitfieldlist.append(0)
            x = x + 1
    return bitfieldlist


def debugging_print(text):
    print(text)
