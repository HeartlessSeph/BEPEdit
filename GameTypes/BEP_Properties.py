from binary_reader import BinaryReader
import sys

sys.path.append("..")
from cmn_functions import *


def convert_hex_to_hexstring(hex_value):
    byte_array = bytearray(hex_value)
    hexadecimal_string = str(byte_array.hex(' '))
    return hexadecimal_string


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


def change_property_ver_from_json(bepfile, new_file, base_game_dict, conv_game_dict, base_game, conv_game, property_type, property_section, header):
    if property_type in base_game_dict:
        if base_game_dict[property_type] in swap_dict_keys_values(conv_game_dict):
            property_type_text = base_game_dict[property_type]
            new_property_type = swap_dict_keys_values(conv_game_dict)[property_type_text]
            print(property_type_text)
            prop_json_orig_path = Path("GameTypes/" + base_game + "/Properties")
            prop_json_new_path = Path("GameTypes/" + conv_game + "/Properties")
            prop_json_orig = import_json(prop_json_orig_path, property_type_text)
            prop_json_new = import_json(prop_json_new_path, property_type_text)

            if prop_json_orig["Structure Type"] == "Generic":
                new_file.write_bytes(header)
                new_file.write_uint16(property_section)
                new_file.write_uint16(new_property_type)

                property_size = bepfile.read_uint32()
                bep_unks = bepfile.read_bytes(8)

                new_file.write_uint32(property_size)
                new_file.write_bytes(bep_unks)
                new_file.write_uint32(new_property_type)  # Property Controller
                bepfile.seek(4, 1)  # Skip property controller
                z = 0
                while z < (property_size / 4) - 1:
                    new_file.write_uint32(bepfile.read_uint32())
                    z = z + 1
                print(bepfile.pos() + 32)

            elif prop_json_orig["Structure Type"] == "Custom" and prop_json_new["Structure Type"] == "Custom":
                new_file.write_bytes(header)
                new_file.write_uint16(property_section)
                new_file.write_uint16(new_property_type)
                property_size_location = new_file.pos()
                new_file.write_uint32(0)  # temp property size
                orig_prop_size = bepfile.read_uint32()  # Skip property size
                new_file.write_bytes(bepfile.read_bytes(8))
                bepfile.seek(4, 1)  # Skip property controller
                new_file.write_uint32(new_property_type)
                new_file.write_bytes(bepfile.read_bytes(28))  # Start Frame, End frame, etc

                property_size = 32

                for sub_property in list(prop_json_orig["Property"].keys()):  # Places all properties from the original to the new dictionary type
                    data_type = prop_json_orig["Property"][sub_property]["DataType"]

                    if data_type == "uint8":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint8()
                        property_size += 1
                    if data_type == "int8":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int8()
                        property_size += 1
                    if data_type == "uint16":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint16()
                        property_size += 2
                    if data_type == "int16":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int16()
                        property_size += 2
                    if data_type == "half_float":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_half_float()
                        property_size += 2
                    if data_type == "uint32":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint32()
                        property_size += 4
                    if data_type == "int32":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int32()
                        property_size += 4
                    if data_type == "float":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_float()
                        property_size += 4
                    if data_type == "uint64":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint64()
                        property_size += 8
                    if data_type == "int64":
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int64()
                        property_size += 8
                    if "bytes" in data_type:
                        end_char = len(data_type) - 1
                        num_bytes = int(data_type[6: end_char])
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_bytes(num_bytes)
                        property_size += num_bytes
                    if "string" in data_type:
                        end_char = len(data_type) - 1
                        num_chars = int(data_type[6: end_char])
                        prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_str(num_chars)
                        property_size += num_chars
                    if data_type == "nibble_1":
                        hex_byte = bepfile.read_uint8()
                        bepfile.seek(-1, 1)
                        prop_json_orig["Property"][sub_property]["Value"] = convert_byte_to_nibble(hex_byte, 1)
                    if data_type == "nibble_2":
                        hex_byte = bepfile.read_uint8()
                        prop_json_orig["Property"][sub_property]["Value"] = convert_byte_to_nibble(hex_byte, 2)
                        property_size += 1

                    if data_type == "End Structure":
                        num_bytes = orig_prop_size - property_size
                        if num_bytes == 0:
                            prop_json_orig["Property"][sub_property]["Value"] = 0
                        else:
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_bytes(num_bytes)
                            property_size += num_bytes

                    if sub_property in prop_json_new["Property"]:
                        if prop_json_orig["Property"][sub_property]["Enumeration"] != "None" and prop_json_new["Property"][sub_property]["Enumeration"] != "None":
                            old_enumeration_name = prop_json_orig["Property"][sub_property]["Enumeration"]
                            new_enumeration_name = prop_json_new["Property"][sub_property]["Enumeration"]
                            enum_json_orig_path = Path("GameTypes/" + base_game + "/Properties/Enumerations")
                            enum_json_new_path = Path("GameTypes/" + conv_game + "/Properties/Enumerations")
                            enum_json_orig = jsonKeys2int(import_json(enum_json_orig_path, old_enumeration_name))
                            enum_json_new = jsonKeys2int(import_json(enum_json_new_path, new_enumeration_name))
                            if prop_json_orig["Property"][sub_property]["Value"] in enum_json_orig:
                                value_enum_orig = enum_json_orig[prop_json_orig["Property"][sub_property]["Value"]]
                                if value_enum_orig in swap_dict_keys_values(enum_json_new):
                                    prop_json_new["Property"][sub_property]["Value"] = swap_dict_keys_values(enum_json_new)[value_enum_orig]
                        else:
                            prop_json_new["Property"][sub_property]["Value"] = prop_json_orig["Property"][sub_property]["Value"]

                property_size = 32

                for index, sub_property in enumerate(list(prop_json_new["Property"].keys())):
                    data_type = prop_json_new["Property"][sub_property]["DataType"]
                    if "Value" in prop_json_new["Property"][sub_property]:
                        current_value = prop_json_new["Property"][sub_property]["Value"]
                    else:
                        current_value = prop_json_new["Property"][sub_property]["Default"]
                    if data_type == "uint8":
                        new_file.write_uint8(current_value)
                        property_size += 1
                    if data_type == "int8":
                        new_file.write_int8(current_value)
                        property_size += 1
                    if data_type == "uint16":
                        new_file.write_uint16(current_value)
                        property_size += 2
                    if data_type == "int16":
                        new_file.write_int16(current_value)
                        property_size += 2
                    if data_type == "half_float":
                        new_file.write_half_float(current_value)
                        property_size += 2
                    if data_type == "uint32":
                        new_file.write_uint32(current_value)
                        property_size += 4
                    if data_type == "int32":
                        new_file.write_int32(current_value)
                        property_size += 4
                    if data_type == "float":
                        new_file.write_float(current_value)
                        property_size += 4
                    if data_type == "uint64":
                        new_file.write_uint64(current_value)
                        property_size += 8
                    if data_type == "int64":
                        new_file.write_int64(current_value)
                        property_size += 8
                    if "bytes" in data_type:
                        end_char = len(data_type) - 1
                        num_bytes = int(data_type[6: end_char])
                        if num_bytes > len(current_value):
                            len_diff = num_bytes - len(current_value)
                            new_file.write_bytes(current_value)
                            loop_num = 0
                            while loop_num < len_diff:
                                new_file.write_uint8(0)
                                loop_num += 1
                        else:
                            new_file.write_bytes(current_value)
                        property_size += num_bytes
                    if "string" in data_type:
                        end_char = len(data_type) - 1
                        num_chars = int(data_type[6: end_char])
                        if num_chars > len(current_value):
                            len_diff = num_chars - len(current_value)
                            new_file.write_str(current_value)
                            loop_num = 0
                            while loop_num < len_diff:
                                new_file.write_uint8(0)
                                loop_num += 1
                        else:
                            new_file.write_str(current_value)
                        property_size += num_chars
                    if data_type == "nibble_1":
                        next_sub_prop = get_nth_key(prop_json_new["Property"], index + 1)
                        next_data_type = prop_json_new["Property"][next_sub_prop]["DataType"]
                        if "Value" in prop_json_new["Property"][next_sub_prop]:
                            next_data_value = prop_json_new["Property"][next_sub_prop]["Value"]
                        else:
                            next_data_value = prop_json_new["Property"][next_sub_prop]["Default"]
                        if next_data_type != "nibble_2":
                            raise Exception("Not a nibble pair? Please correctly format nibble pair.")
                        else:
                            nibble_pair = convert_nibbles_to_byte(current_value, next_data_value)
                            new_file.write_uint8(nibble_pair)
                        property_size += 1
                    if data_type == "nibble_2":
                        pass
                cur_pos = new_file.pos()
                new_file.seek(property_size_location)
                new_file.write_uint32(property_size)
                new_file.seek(cur_pos)
                print(bepfile.pos() + 32)
        else:
            property_size = bepfile.read_uint32()
            bep_unks = bepfile.read_bytes(8)
            z = 0
            while z < (property_size / 4):
                useless = bepfile.read_uint32()
                z = z + 1
    else:
        property_size = bepfile.read_uint32()
        bep_unks = bepfile.read_bytes(8)
        if property_section == 17:
            new_file.write_bytes(header)
            new_file.write_uint16(property_section)
            new_file.write_uint16(property_type)
            new_file.write_uint32(property_size)
            new_file.write_bytes(bep_unks)
        z = 0
        while z < (property_size / 4):
            data = bepfile.read_uint32()
            if property_section == 17:
                new_file.write_uint32(data)
            z = z + 1


def change_bep_version(bepfile, bep_name, bep_game_base_dict, bep_game_conv_dict, bep_game_base, bep_game_conv, bep_path=Path("")):
    writer = BinaryReader()  # Create a new BinaryReader (bytearray buffer is initialized automatically)
    bepfile.seek(0)
    bepfile.set_endian(False)
    magic = bepfile.read_str(4)
    if magic != '_PEB':
        raise Exception('Incorrect Magic.')
    writer.write_str(magic)
    writer.write_bytes(bepfile.read_bytes(12))
    x = 0

    while x == 0:
        header_stuff = bepfile.read_bytes(64)  # header stuff

        property_section = bepfile.read_uint16()
        property_type = bepfile.read_uint16()

        change_property_ver_from_json(bepfile, writer, bep_game_base_dict, bep_game_conv_dict, bep_game_base, bep_game_conv, property_type, property_section,
                                      header_stuff)

        if bepfile.size() == bepfile.pos() + 80: x = 1
    x = 0
    while x < 80:
        writer.write_uint8(0)
        x = x + 1
    bep_name = bep_name + ".bep"
    new_file_path = Path(bep_path / "Converted" / bep_name)
    new_file_dir = Path(bep_path / "Converted")
    new_file_dir.mkdir(exist_ok=True)
    with open(new_file_path, 'wb') as f:
        f.write(writer.buffer())
