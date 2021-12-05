# -*- coding: utf-8 -*-
import sys
import tkinter
from tkinter import filedialog
from cmn_functions import *
import argparse
from binary_reader import BinaryReader
from DE_GameTypes.BEP_Properties import change_bep_version
from DE_GameTypes.BEP_Properties import convert_bep_to_json
from DE_GameTypes.BEP_Properties import convert_json_to_bep
from OE_GameTypes.OE_Properties import convert_property_bin_to_beps


def check_game_choice(game_dict, message):
    """

    :param game_dict: Dict Object
    :param message: String
    """
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


tkinter.Tk().withdraw()  # prevents an empty tkinter window from appearing

# Arguments
parser = argparse.ArgumentParser(description=".BEP extraction tool")
parser.add_argument("--skipoption", help="Skips startup options", action="store_true")
parser_group = parser.add_mutually_exclusive_group()
ver_text = parser_group.add_argument("--verchange", help="Converts bep from one game to another. Required input file is *.bep or folder containing .bep files.", action="store_true")
conv_text = parser_group.add_argument("--OEbinconv", help="Converts list of OE Properties to bep files. Required input file is property.bin", action="store_true")
move_rec_text = parser_group.add_argument("--getmoves", help="Extracts a move_list.json file from an extracted Fighter_Commander moveset json. Required input file is *.json", action="store_true")
if len(sys.argv) <= 1:
    parser.print_help(sys.stderr)
    input("Press ENTER to exit... ")
    sys.exit()
parser.add_argument("file", help=".bep file or folder containing bep files")
args = parser.parse_args()

if not args.verchange and not args.OEbinconv and not args.getmoves:
    arg_check = check_game_choice({1: 'Extract/Repack (Default Usage): Extracts a bep or folder of beps to a json file. Repacks json to bep file(s).',
                                   2: 'Version Change (--verchange): ' + ver_text.help, 3: 'Property.bin Conversion (--OEbinconv): ' + conv_text.help,
                                  4: 'Extract Moves from command set (--getmoves): ' + move_rec_text.help}, "Pick an option for the type of action you would like to perform")
    if arg_check == 2: args.verchange = True
    if arg_check == 3: args.OEbinconv = True
    if arg_check == 4: args.getmoves = True

# File variables
kfile = Path(args.file)
file_bool = kfile.is_file()
if file_bool:
    file_directory = kfile.parents[0]
else:
    file_directory = kfile
file_extension = kfile.suffix
file_name = kfile.stem
script_folder = Path(sys.argv[0]).parents[0]

# Global Dictionaries
bep_dictionary = tree()  # Stores bep data
game_dictionary_DE = import_yaml(Path(script_folder), "Game Dictionary DE")

# Actual Code
if not args.getmoves and not args.OEbinconv:
    cur_engine = check_game_choice(game_dictionary_DE["Engines"], "Select the number of the engine you are importing from")
    bep_engine = game_dictionary_DE["Engines"][cur_engine]
    cur_game = check_game_choice(game_dictionary_DE["Engine Games"][bep_engine], "Select the number of the game you are importing from")
    bep_game = game_dictionary_DE["Engine Games"][bep_engine][cur_game]

if args.verchange:
    cur_engine_2 = check_game_choice(game_dictionary_DE["Engines"], "Choose the engine you would like to change the version to:")
    bep_engine_2 = game_dictionary_DE["Engines"][cur_engine_2]
    cur_game_2 = check_game_choice(game_dictionary_DE["Engine Games"][bep_engine_2], "Choose the game you would like to change the version to:")
    bep_game_2 = game_dictionary_DE["Engine Games"][bep_engine_2][cur_game_2]

if args.OEbinconv:
    # Use this when MEP converting is implemented: "Would you like to define custom move list json & mep folder? Defaults are move_list.json & MEP in the program directory."
    if not yes_or_no("Would you like to define a custom move list json? Defaults are move_list.json in the program directory."):
        move_list_path = "move_list"
        move_list_json = import_json(Path(script_folder), move_list_path)
        mep_folder = Path("MEP")
    else:
        move_list_path = filedialog.askopenfilename(title="Select the file containing list of moves")
        move_list_json = import_json(Path(""), str(Path(move_list_path).parents[0]) + "/" + str(Path(move_list_path).stem))
        mep_folder = Path("MEP")
        # mep_folder = filedialog.askdirectory(title="Select the folder containing MEP files")
        # mep_folder = Path(mep_folder)

if args.getmoves:
    jsonfile = import_json(file_directory, file_name)
    if "Old Engine Game" in jsonfile:
        commandsetname = list(jsonfile.keys())[2]
    else:
        commandsetname = list(jsonfile.keys())[2]
    x = 0
    MoveIDXDict = {}
    for move in list(jsonfile[commandsetname]["Move Table"].keys()):
        if "Animation Used" in jsonfile[commandsetname]["Move Table"][move]:
            Animname = jsonfile[commandsetname]["Move Table"][move]["Animation Used"]
            MoveIDXDict[Animname] = x
        elif "Animation Table" in jsonfile[commandsetname]["Move Table"][move]:
            for animtable in list(jsonfile[commandsetname]["Move Table"][move]["Animation Table"].keys()):
                Animname = jsonfile[commandsetname]["Move Table"][move]["Animation Table"][animtable]["Animation Used"]
                MoveIDXDict[Animname] = x
        x = x + 1
    MoveIDXDict.pop('Null', None)
    export_json(script_folder, "move_list", MoveIDXDict)
    sys.exit()

if file_bool:  # Single File
    if file_extension == '.bep':
        with kfile.open(mode='rb') as input_file:
            f = BinaryReader(input_file.read())
        if args.verchange:
            json_property_path = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine)
            json_property_path_2 = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine_2)
            bep_prop_dict = import_yaml(json_property_path, "Property_Types")
            bep_prop_dict_2 = import_yaml(json_property_path_2, "Property_Types")
            change_bep_version(f, file_name, bep_prop_dict, bep_prop_dict_2, bep_game, bep_engine, bep_game_2, bep_engine_2, file_directory)
        elif args.OEbinconv:
            raise Exception("Property.bin file has improper extension?")
        else:
            json_property_path = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine)
            bep_prop_dict = import_yaml(json_property_path, "Property_Types")
            convert_bep_to_json(f, bep_dictionary, file_name, bep_game, bep_engine, bep_prop_dict)
            export_yaml(file_directory, file_name, bep_dictionary)
    elif file_extension == '.yaml':
        if args.verchange:
            raise Exception("Can't perform version change on json file")
        elif args.OEbinconv:
            raise Exception("Property.bin file has improper extension?")
        json_property_path = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine)
        bep_prop_dict = import_yaml(json_property_path, "Property_Types")
        bep_json = import_yaml(Path(""), file_name)
        convert_json_to_bep(bep_json, bep_prop_dict, bep_game, bep_engine)
    elif file_extension == '.bin':
        with kfile.open(mode='rb') as input_file:
            f = BinaryReader(input_file.read())
        if args.verchange:
            raise Exception("Can't perform version change on bin file")
        elif args.OEbinconv:
            convert_property_bin_to_beps(f, jsonKeys2int(move_list_json), mep_folder, file_directory)


else:
    for bep in kfile.iterdir():
        current_bep = bep
        if not current_bep.is_file(): continue
        with current_bep.open(mode='rb') as input_file:
            f = BinaryReader(input_file.read())
        bep_name = current_bep.stem
        print("Current bep: " + bep_name + ".bep")
        if args.verchange:
            json_property_path = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine)
            json_property_path_2 = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine_2)
            bep_prop_dict = import_yaml(json_property_path, "Property_Types")
            bep_prop_dict_2 = import_yaml(json_property_path_2, "Property_Types")
            if current_bep.is_file() and current_bep.suffix == ".bep":
                change_bep_version(f, bep_name, bep_prop_dict, bep_prop_dict_2, bep_game, bep_engine, bep_game_2, bep_engine_2, kfile)
            elif current_bep.is_file() and current_bep.suffix == ".yaml":
                print("Can't perform version change on yaml file.")
        elif args.OEbinconv:
            raise Exception("Must input a property.bin file, not a folder.")
        else:
            if current_bep.is_file() and current_bep.suffix == ".bep":
                json_property_path = Path(str(script_folder) + "/DE_GameTypes/" + bep_engine)
                bep_prop_dict = import_yaml(json_property_path, "Property_Types")
                convert_bep_to_json(f, bep_dictionary, bep_name, bep_game, bep_engine, bep_prop_dict)
    if args.verchange:
        pass
    else:
        export_yaml(Path(""), file_name, bep_dictionary)
