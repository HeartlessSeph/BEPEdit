# -*- coding: utf-8 -*-
import sys
from cmn_functions import *
import argparse
from binary_reader import BinaryReader
from GameTypes.BEP_Properties import change_bep_version
from GameTypes.BEP_Properties import convert_bep_to_json
from GameTypes.BEP_Properties import convert_json_to_bep


def check_game_choice(game_dict, message):
    '''

    :param game_dict: Dict Object
    :param message: String
    '''
    print(message)
    for key, value in game_dict.items():
        print(str(key) + ": " + value)
    print("")
    game_num = int(input('Input a number: '))
    x = 0
    while x == 0:
        if game_num in game_dict:
            print("")
            return game_num
        else:
            print("Given number is not in listed range")
            game_num = int(input('Input a number: '))


if len(sys.argv) <= 1:
    print('Drag and drop a bep file or a folder containing bep files to run this program.')
    input("Press ENTER to exit... ")
    sys.exit()

# Arguments & File Variables
parser = argparse.ArgumentParser(description=".BEP extraction tool")
parser.add_argument("file", help=".bep file or folder containing bep files")
parser.add_argument("-verchange", "--verchange", help="Converts bep from one game to another.", action="store_true")
args = parser.parse_args()
kfile = Path(args.file)
file_bool = kfile.is_file()
file_extension = kfile.suffix
file_name = kfile.stem

# Global Dictionaries
bep_dictionary = tree()  # Stores bep data
game_dictionary = jsonKeys2int(import_json(Path(""), "Game Dictionary"))

# Actual Code
cur_game = check_game_choice(game_dictionary, "Select the number of the game you are importing from")
bep_game = game_dictionary[int(cur_game)]

if args.verchange:
    ver_change_to = check_game_choice(game_dictionary, "Choose the game you would like to change the version to:")
    bep_game_2 = game_dictionary[int(ver_change_to)]

if file_bool:  # Single File
    if file_extension == '.bep':
        with kfile.open(mode='rb') as input_file:
            f = BinaryReader(input_file.read())
        if args.verchange:
            json_property_path = Path("GameTypes/" + bep_game)
            json_property_path_2 = Path("GameTypes/" + bep_game_2)
            bep_prop_dict = jsonKeys2int(import_json(json_property_path, "Property_Types"))
            bep_prop_dict_2 = jsonKeys2int(import_json(json_property_path_2, "Property_Types"))
            change_bep_version(f, file_name, bep_prop_dict, bep_prop_dict_2, bep_game, bep_game_2)
        else:
            json_property_path = Path("GameTypes/" + bep_game)
            bep_prop_dict = jsonKeys2int(import_json(json_property_path, "Property_Types"))
            convert_bep_to_json(f, bep_dictionary, file_name, bep_game, bep_prop_dict)
            export_json(Path.cwd(), file_name, bep_dictionary)
    if file_extension == '.json':
        json_property_path = Path("GameTypes/" + bep_game)
        bep_prop_dict = jsonKeys2int(import_json(json_property_path, "Property_Types"))
        bep_json = import_json(Path(""), file_name)
        convert_json_to_bep(bep_json, bep_prop_dict, bep_game)


else:
    for bep in kfile.iterdir():
        current_bep = bep
        with current_bep.open(mode='rb') as input_file:
            f = BinaryReader(input_file.read())
        bep_name = current_bep.stem
        print("Current bep: " + bep_name + ".bep")
        if args.verchange:
            json_property_path = Path("GameTypes/" + bep_game)
            json_property_path_2 = Path("GameTypes/" + bep_game_2)
            bep_prop_dict = jsonKeys2int(import_json(json_property_path, "Property_Types"))
            bep_prop_dict_2 = jsonKeys2int(import_json(json_property_path_2, "Property_Types"))
            if current_bep.is_file() and current_bep.suffix == ".bep":
                change_bep_version(f, bep_name, bep_prop_dict, bep_prop_dict_2, bep_game, bep_game_2, kfile)
            elif current_bep.is_file() and current_bep.suffix == ".json":
                print("Can't perform version change on json file.")
        else:
            if current_bep.is_file() and current_bep.suffix == ".bep":
                json_property_path = Path("GameTypes/" + bep_game)
                bep_prop_dict = jsonKeys2int(import_json(json_property_path, "Property_Types"))
                convert_bep_to_json(f, bep_dictionary, bep_name, bep_game, bep_prop_dict)
    if args.verchange:
        pass
    else:
        export_json(Path.cwd(), file_name, bep_dictionary)
