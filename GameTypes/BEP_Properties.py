from binary_reader import BinaryReader
import sys

sys.path.append("..")
from cmn_functions import *


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


def convert_bep_to_json(bepfile, bep_dict, bep_name, base_game, base_game_dict):
    """
    :param base_game_dict: Dictionary
    :param base_game: String
    :param bepfile: BinaryStream Buffer
    :param bep_dict: tree()
    :param bep_name: String
    """
    bepfile.seek(0)
    bepfile.set_endian(False)
    if bepfile.read_str(4) != '_PEB':
        raise Exception('Incorrect Magic.')
    file_header = bepfile.read_bytes(12)  # Not really needed
    x = 0
    y = 0
    while x == 0:
        property_guid = convert_hex_to_hexstring(bepfile.read_bytes(32))
        bone_checksum = convert_hex_to_hexstring(bepfile.read_bytes(2))
        bone_name = bepfile.read_str(30)
        property_section = bepfile.read_uint16()
        property_type = bepfile.read_uint16()
        property_size = bepfile.read_uint32()
        prop_header_unk1 = bepfile.read_int32()
        prop_header_unk2 = bepfile.read_uint32()
        if property_section == 12:
            bepfile.seek(4, 1)  # Skip Property Controller
            property_size_temp = 32
            if property_type in base_game_dict:
                property_type_text = base_game_dict[property_type]
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property GUID"] = property_guid
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Bone Checksum"] = bone_checksum
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Bone Name"] = bone_name
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Section"] = property_section
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Type"] = property_type
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Size (Reference Only)"] = property_size
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk1"] = prop_header_unk1
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk2"] = prop_header_unk2
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Start Frame"] = bepfile.read_float()
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["End Frame"] = bepfile.read_float()
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk3"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk4"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk5"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk6"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Header Unk7"] = bepfile.read_uint32()
                print(property_type_text)
                prop_json_orig_path = Path("GameTypes/" + base_game + "/Properties")
                prop_json_orig = import_json(prop_json_orig_path, property_type_text)

                if prop_json_orig["Structure Type"] == "Generic":
                    z = 0
                    while z < (property_size / 4) - 8:
                        bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Property Unk " + str(z)] = bepfile.read_uint32()
                        z = z + 1

                elif prop_json_orig["Structure Type"] == "Custom":
                    for sub_property in list(prop_json_orig["Property"].keys()):  # Places all properties from the original to the new dictionary type
                        data_type = prop_json_orig["Property"][sub_property]["DataType"]

                        if data_type == "uint8":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint8()
                            property_size_temp += 1
                        elif data_type == "int8":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int8()
                            property_size_temp += 1
                        elif data_type == "uint16":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint16()
                            property_size_temp += 2
                        elif data_type == "int16":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int16()
                            property_size_temp += 2
                        elif data_type == "half_float":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_half_float()
                            property_size_temp += 2
                        elif data_type == "uint32":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint32()
                            property_size_temp += 4
                        elif data_type == "int32":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int32()
                            property_size_temp += 4
                        elif data_type == "float":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_float()
                            property_size_temp += 4
                        elif data_type == "uint64":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_uint64()
                            property_size_temp += 8
                        elif data_type == "int64":
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_int64()
                            property_size_temp += 8
                        elif "bytes" in data_type:
                            end_char = len(data_type) - 1
                            num_bytes = int(data_type[6: end_char])
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_bytes(num_bytes)
                            property_size_temp += num_bytes
                        elif "string" in data_type:
                            end_char = len(data_type) - 1
                            num_chars = int(data_type[6: end_char])
                            prop_json_orig["Property"][sub_property]["Value"] = bepfile.read_str(num_chars)
                            property_size_temp += num_chars
                        elif data_type == "nibble_1":
                            hex_byte = bepfile.read_uint8()
                            bepfile.seek(-1, 1)
                            prop_json_orig["Property"][sub_property]["Value"] = convert_byte_to_nibble(hex_byte, 1)
                        elif data_type == "nibble_2":
                            hex_byte = bepfile.read_uint8()
                            prop_json_orig["Property"][sub_property]["Value"] = convert_byte_to_nibble(hex_byte, 2)
                            property_size_temp += 1

                        elif data_type == "End Structure":
                            num_bytes = property_size - property_size_temp
                            if num_bytes == 0:
                                pass
                            else:
                                z = 0
                                while z < num_bytes / 4:
                                    bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"]["Undefined Unk " + str(z)] = bepfile.read_uint32()
                                    z = z + 1

                        if prop_json_orig["Property"][sub_property]["Enumeration"] != "None" and data_type != "End Structure":
                            old_enumeration_name = prop_json_orig["Property"][sub_property]["Enumeration"]
                            enum_json_orig_path = Path("GameTypes/" + base_game + "/Properties/Enumerations")
                            enum_json_orig = jsonKeys2int(import_json(enum_json_orig_path, old_enumeration_name))
                            if prop_json_orig["Property"][sub_property]["Value"] in enum_json_orig:
                                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"][sub_property] = enum_json_orig[prop_json_orig["Property"][sub_property]["Value"]]
                            else:
                                bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"][sub_property] = prop_json_orig["Property"][sub_property]["Value"]
                        elif data_type != "End Structure":
                            bep_dict[bep_name]["Property " + str(y) + " (" + property_type_text + ")"][sub_property] = prop_json_orig["Property"][sub_property]["Value"]
            else:
                bep_dict[bep_name]["Property " + str(y)]["Property GUID"] = property_guid
                bep_dict[bep_name]["Property " + str(y)]["Bone Checksum"] = bone_checksum
                bep_dict[bep_name]["Property " + str(y)]["Bone Name"] = bone_name
                bep_dict[bep_name]["Property " + str(y)]["Property Section"] = property_section
                bep_dict[bep_name]["Property " + str(y)]["Property Type"] = property_type
                bep_dict[bep_name]["Property " + str(y)]["Property Size (Reference Only)"] = property_size
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk1"] = prop_header_unk1
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk2"] = prop_header_unk2
                bep_dict[bep_name]["Property " + str(y)]["Start Frame"] = bepfile.read_float()
                bep_dict[bep_name]["Property " + str(y)]["End Frame"] = bepfile.read_float()
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk3"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk4"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk5"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk6"] = bepfile.read_uint32()
                bep_dict[bep_name]["Property " + str(y)]["Property Header Unk7"] = bepfile.read_uint32()
                z = 0
                while z < (property_size / 4) - 8:
                    bep_dict[bep_name]["Property " + str(y)]["Property Unk " + str(z)] = bepfile.read_uint32()
                    z = z + 1
        else:
            bep_dict[bep_name]["Property " + str(y)]["Property GUID"] = property_guid
            bep_dict[bep_name]["Property " + str(y)]["Bone Checksum"] = bone_checksum
            bep_dict[bep_name]["Property " + str(y)]["Bone Name"] = bone_name
            bep_dict[bep_name]["Property " + str(y)]["Property Section"] = property_section
            bep_dict[bep_name]["Property " + str(y)]["Property Type"] = property_type
            bep_dict[bep_name]["Property " + str(y)]["Property Size (Reference Only)"] = property_size
            bep_dict[bep_name]["Property " + str(y)]["Property Header Unk1"] = prop_header_unk1
            bep_dict[bep_name]["Property " + str(y)]["Property Header Unk2"] = prop_header_unk2
            z = 0
            while z < (property_size / 4):
                bep_dict[bep_name]["Property " + str(y)]["Property Unk " + str(z)] = bepfile.read_uint32()
                z = z + 1
        if bepfile.size() == bepfile.pos() + 80: x = 1
        y = y + 1


def convert_json_to_bep(bep_json, base_game_dict, base_game, bep_path=Path("")):
    """
    :param base_game_dict: Dictionary
    :param base_game: String
    :param bepfile: BinaryStream Buffer
    :param bep_dict: tree()
    :param bep_name: String
    :param bep_path: Path Object
    """

    for bep_name in list(bep_json.keys()):
        writer = BinaryReader()
        writer.write_uint64(9701773407)
        writer.write_uint64(2)
        for bep_property in list(bep_json[bep_name].keys()):
            property_guid = convert_hexstring_to_hex(bep_json[bep_name][bep_property]["Property GUID"])
            bone_checksum = convert_hexstring_to_hex(bep_json[bep_name][bep_property]["Bone Checksum"])
            bone_name = bep_json[bep_name][bep_property]["Bone Name"]
            property_section = bep_json[bep_name][bep_property]["Property Section"]
            property_type = bep_json[bep_name][bep_property]["Property Type"]
            property_header_unk1 = bep_json[bep_name][bep_property]["Property Header Unk1"]
            property_header_unk2 = bep_json[bep_name][bep_property]["Property Header Unk2"]
            writer.write_bytes(property_guid)
            writer.write_bytes(bone_checksum)
            if len(bone_name) < 30:
                num_chars = 30 - len(bone_name)
                writer.write_str(bone_name)
                x = 0
                while x < num_chars:
                    writer.write_uint8(0)
                    x += 1
            elif len(bone_name > 30):
                writer.write_str(bone_name[:30])
            else:
                writer.write_str(bone_name)
            writer.write_uint16(property_section)
            writer.write_uint16(property_type)
            property_size_pos = writer.pos()
            writer.write_uint32(0)  # Skip property size for now
            writer.write_int32(property_header_unk1)
            writer.write_uint32(property_header_unk2)

            if property_section == 12:
                start_frame = bep_json[bep_name][bep_property]["Start Frame"]
                end_frame = bep_json[bep_name][bep_property]["End Frame"]
                property_header_unk3 = bep_json[bep_name][bep_property]["Property Header Unk3"]
                property_header_unk4 = bep_json[bep_name][bep_property]["Property Header Unk4"]
                property_header_unk5 = bep_json[bep_name][bep_property]["Property Header Unk5"]
                property_header_unk6 = bep_json[bep_name][bep_property]["Property Header Unk6"]
                property_header_unk7 = bep_json[bep_name][bep_property]["Property Header Unk7"]
                writer.write_uint32(property_type)
                writer.write_float(start_frame)
                writer.write_float(end_frame)
                writer.write_uint32(property_header_unk3)
                writer.write_uint32(property_header_unk4)
                writer.write_uint32(property_header_unk5)
                writer.write_uint32(property_header_unk6)
                writer.write_uint32(property_header_unk7)
                property_size = 32

                if property_type in base_game_dict:
                    property_type_text = base_game_dict[property_type]
                    prop_json_orig_path = Path("GameTypes/" + base_game + "/Properties")
                    prop_json_orig = import_json(prop_json_orig_path, property_type_text)

                    if prop_json_orig["Structure Type"] == "Generic":
                        temp_dict = remove_keys_from_dict(bep_json[bep_name][bep_property], 15)
                        for sub_property in list(temp_dict.keys()):
                            writer.write_uint32(temp_dict[sub_property])
                            property_size += 4

                    elif prop_json_orig["Structure Type"] == "Custom":
                        for index, sub_property in enumerate(list(prop_json_orig["Property"].keys())):  # Places all properties from the original to the new dictionary type
                            data_type = prop_json_orig["Property"][sub_property]["DataType"]
                            if sub_property in bep_json[bep_name][bep_property]:
                                sub_prop_val = bep_json[bep_name][bep_property][sub_property]
                            else: sub_prop_val = 0

                            if prop_json_orig["Property"][sub_property]["Enumeration"] != "None" and data_type != "End Structure":
                                old_enumeration_name = prop_json_orig["Property"][sub_property]["Enumeration"]
                                enum_json_orig_path = Path("GameTypes/" + base_game + "/Properties/Enumerations")
                                enum_json_orig = swap_dict_keys_values(jsonKeys2int(import_json(enum_json_orig_path, old_enumeration_name)))
                                if sub_prop_val in enum_json_orig:
                                    sub_prop_val = enum_json_orig[sub_prop_val]

                            if data_type == "uint8":
                                writer.write_uint8(sub_prop_val)
                                property_size += 1
                            elif data_type == "int8":
                                writer.write_int8(sub_prop_val)
                                property_size += 1
                            elif data_type == "uint16":
                                writer.write_uint16(sub_prop_val)
                                property_size += 2
                            elif data_type == "int16":
                                writer.write_int16(sub_prop_val)
                                property_size += 2
                            elif data_type == "half_float":
                                writer.write_half_float(sub_prop_val)
                                property_size += 2
                            elif data_type == "uint32":
                                writer.write_uint32(sub_prop_val)
                                property_size += 4
                            elif data_type == "int32":
                                writer.write_int32(sub_prop_val)
                                property_size += 4
                            elif data_type == "float":
                                writer.write_float(sub_prop_val)
                                property_size += 4
                            elif data_type == "uint64":
                                writer.write_uint64(sub_prop_val)
                                property_size += 8
                            elif data_type == "int64":
                                writer.write_int64(sub_prop_val)
                                property_size += 8
                            elif "bytes" in data_type:
                                end_char = len(data_type) - 1
                                num_bytes = int(data_type[6: end_char])
                                if num_bytes < len(sub_prop_val):
                                    cur_byte_nums = 0
                                    sub_prop_val = sub_prop_val[:num_bytes]
                                else:
                                    cur_byte_nums = num_bytes - len(sub_prop_val)
                                writer.write_bytes(sub_prop_val)
                                x = 0
                                while x < cur_byte_nums:
                                    writer.write_uint8(0)
                                property_size += num_bytes
                            elif "string" in data_type:
                                end_char = len(data_type) - 1
                                num_chars = int(data_type[6: end_char])
                                if num_chars < len(sub_prop_val):
                                    cur_char_nums = 0
                                    sub_prop_val = sub_prop_val[:num_chars]
                                else:
                                    cur_char_nums = num_chars - len(sub_prop_val)
                                writer.write_str(sub_prop_val)
                                x = 0
                                while x < cur_char_nums:
                                    writer.write_uint8(0)
                                property_size += num_chars
                            elif data_type == "nibble_1":
                                next_sub_prop = get_nth_key(prop_json_orig["Property"], index + 1)
                                next_data_type = prop_json_orig["Property"][next_sub_prop]["DataType"]
                                next_data_value = bep_json[bep_name][bep_property][next_sub_prop]
                                if next_data_type != "nibble_2":
                                    raise Exception("Not a nibble pair? Please correctly format nibble pair.")
                                else:
                                    if prop_json_orig["Property"][next_sub_prop]["Enumeration"] != "None":
                                        new_enumeration_name = prop_json_orig["Property"][next_sub_prop]["Enumeration"]
                                        enum_json_new_path = Path("GameTypes/" + base_game + "/Properties/Enumerations")
                                        enum_json_new = swap_dict_keys_values(jsonKeys2int(import_json(enum_json_new_path, new_enumeration_name)))
                                        if next_data_value in enum_json_new:
                                            next_data_value = enum_json_new[sub_prop_val]
                                    nibble_pair = convert_nibbles_to_byte(sub_prop_val, next_data_value)
                                    writer.write_uint8(nibble_pair)
                                property_size += 1
                            elif data_type == "nibble_2":
                                pass

                            elif data_type == "End Structure":
                                prev_sub_prop = get_nth_key(prop_json_orig["Property"], index - 1)
                                last_key_in_index = get_dict_key_index(bep_json[bep_name][bep_property], prev_sub_prop)
                                temp_dict = remove_keys_from_dict(bep_json[bep_name][bep_property], last_key_in_index)
                                print(temp_dict)
                                print(sub_property)
                                for temp_sub_property in list(temp_dict.keys()):
                                    writer.write_uint32(temp_dict[temp_sub_property])
                                    property_size += 4

                else:
                    temp_dict = remove_keys_from_dict(bep_json[bep_name][bep_property], 15)
                    for sub_property in list(temp_dict.keys()):
                        writer.write_uint32(temp_dict[sub_property])
                        property_size += 4

            else:
                property_size = 0
                temp_dict = remove_keys_from_dict(bep_json[bep_name][bep_property], 8)
                for sub_property in list(temp_dict.keys()):
                    writer.write_uint32(temp_dict[sub_property])
                    property_size += 4
            cur_prop_pos = writer.pos()
            writer.seek(property_size_pos)
            writer.write_uint32(property_size)
            writer.seek(cur_prop_pos)
        bep_file_name = bep_name + ".bep"
        new_file_path = Path(bep_path / "Converted (Json to BEP)" / bep_file_name)
        new_file_dir = Path(bep_path / "Converted (Json to BEP)")
        new_file_dir.mkdir(exist_ok=True)
        x = 0
        while x < 80:
            writer.write_uint8(0)
            x += 1
        with open(new_file_path, 'wb') as f:
            f.write(writer.buffer())


def change_bep_version(bepfile, bep_name, bep_game_base_dict, bep_game_conv_dict, bep_game_base, bep_game_conv, bep_path=Path("")):
    writer = BinaryReader()
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
