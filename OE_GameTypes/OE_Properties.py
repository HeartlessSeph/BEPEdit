from binary_reader import BinaryReader
import sys

sys.path.append("..")
from cmn_functions import *


def get_string_from_pointer(my_file, pointer_val=0):
    h = my_file.pos()
    if pointer_val != 0:
        pointer_check = pointer_val
    else:
        pointer_check = my_file.read_uint32()
    my_file.seek(pointer_check)
    string = my_file.read_str()
    my_file.seek(h)
    return string


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


def convert_property_bin_to_beps(f, move_list, mep_folder):
    """
    :param f: BinaryStream
    :param move_list: Dictionary
    :param mep_folder: Path Object
    """
    f.seek(0)
    f.set_endian(True)  # Big Endian for Property.bin file
    magic = f.read_str(4)
    if magic != 'CAPR':
        raise Exception('Incorrect Magic.')
    move_data_dictionary = {}
    HitboxDictionaryY0 = {2080: "Right Foot/Knee", 1152: "Left Foot/Knee", 10: "Left Hand", 266: "Left Hand", 20: "Right Hand", 84: "Right Hand", 17536: "Left Foot/Knee", 10240: "Right Foot/Knee",
                          6: "Both Hands", 2: "Left Hand", 3232: "Both Legs", 4180: "Left Elbow", 4362: "Left Elbow", 596: "Right Elbow", 4608: "Head",
                          10272: "Right Foot/Knee"}
    HitboxDictionaryK2 = {262144: "Weapon", 138956: "Chest", 5126: "Center", 136394: "Left Shoulder", 133830: "Right Shoulder", 5128: "Left Elbow", 2564: "Right Elbow", 81952: "Left Foot/Knee",
                          40796: "Right Foot/Knee", 4104: "Left Hand", 2052: "Right Hand", 1538: "Head", 7692: "Both Hands"}

    f.seek(8, 1)  # Skip endian stuff
    file_size = f.read_uint32()
    f.seek(file_size)
    f.seek(-40, 1)  # Go to move table start
    Num_Moves = f.read_uint32()
    Move_Name_Table_Pointer = f.read_uint32()
    Move_Data_Table_Pointer = f.read_uint32()
    f.seek(Move_Name_Table_Pointer)
    Cur_Move_Name = f.pos()
    f.seek(Move_Data_Table_Pointer)
    Cur_Move_Data = f.pos()

    x = 0
    while x < Num_Moves:
        f.seek(Cur_Move_Name)
        name = get_string_from_pointer(f)
        f.seek(4, 1)
        Cur_Move_Name = f.pos()
        f.seek(Cur_Move_Data)
        data_pointer = f.read_uint32()
        move_data_dictionary[name] = data_pointer
        Cur_Move_Data = f.pos()
        x += 1

    for move in list(move_list.keys()):
        writer = BinaryReader()
        move_data_list = []
        writer.write_bytes(b'\x5f\x50\x45\x42\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00')  # Header
        if move in move_data_dictionary:
            f.seek(move_data_dictionary[move])
            f.seek(8, 1)
            move_data_size = f.read_uint32()
            f.seek(move_data_size, 1)
            property_table_start = f.pos()
            f.seek(2, 1)
            num_properties = f.read_uint16()
            a = 0
            if num_properties == 0:
                print(move + " has no properties that can be converted. A blank bep file has been created.")
            while a < num_properties:
                start_frame = f.read_uint16()
                end_frame = f.read_uint16()
                modifier = f.read_int8()
                struct_num = f.read_uint8()
                f.seek(1, 1)
                PropertyType = f.read_uint8()
                f.seek(4, 1)
                pointer_offset = f.read_uint32()
                cur_pos = f.pos()

                if PropertyType == 5:  # Hitbox
                    f.seek(property_table_start + pointer_offset)
                    write_zero_bytes(writer, 64)
                    writer.write_bytes(b'\x0C\x00\x4D\x00\x30\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
                    writer.write_bytes(b'\x4D\x00\x00\x00')
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 12)
                    writer.write_bytes(b'\x02\x00\x00\x00\x00\x00\x00\x00')  # Always 2
                    Hitbox1 = f.read_uint16()
                    Hitbox2 = f.read_uint16()
                    MoveEffect = f.read_uint16()
                    KnockbackForce = f.read_uint8()
                    HitLocation = f.read_uint8()
                    Flags = f.read_uint16()
                    damage = f.read_uint8() * 10
                    heat = f.read_uint8()
                    MoveEffectNum = f.read_uint8()
                    MEBitfield = bitfield(MoveEffectNum)
                    GuardBreak = bool(MEBitfield[2])

                    writer.write_uint32(damage)  # Damage
                    writer.write_uint32(KnockbackForce)  # KnockbackForce
                    if Hitbox1 in HitboxDictionaryY0:
                        tempdict = swap_dict_keys_values(HitboxDictionaryK2)
                        if HitboxDictionaryY0[Hitbox1] in tempdict:
                            writer.write_uint32(tempdict[HitboxDictionaryY0[Hitbox1]])
                        else:
                            print("OE Hitbox in " + str(move) + "(" + str(Hitbox1) + ") has no DE equivalent " + str(move) + ": " + str(Hitbox1))
                            write_zero_bytes(writer, 4)
                    else:
                        print("Unknown Hitbox Value in " + str(move) + ": " + str(Hitbox1))
                        write_zero_bytes(writer, 4)  # Write rest of data
                    if GuardBreak:
                        f.write_uint32(32)  # Writes Movetype as Regular Hit with Guardbreak
                    else:
                        f.write_uint32(1)  # Writes Movetype as Regular Hit
                    f.seek(cur_pos)

                elif PropertyType == 10:  # Self Contained Hitbox
                    damage = structnum * 10
                    write_zero_bytes(writer, 64)
                    writer.write_bytes(b'\x0C\x00\x61\x00\x30\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
                    writer.write_bytes(b'\x61\x00\x00\x00')
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 8)
                    writer.write_bytes(b'\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00')  # Always 2
                    writer.write_uint32(damage)
                    write_zero_bytes(writer, 12)
                    f.seek(cur_pos)

                elif PropertyType == 4:  # Control Lock
                    write_zero_bytes(writer, 64)
                    writer.write_bytes(b'\x0C\x00\x4B\x00\x24\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
                    writer.write_bytes(b'\x4B\x00\x00\x00')
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 12)
                    writer.write_bytes(b'\x02\x00\x00\x00\x00\x00\x00\x00')  # Always 2
                    writer.write_uint32(struct_num)

                elif PropertyType == 3:  # Follow Up
                    write_zero_bytes(writer, 64)
                    writer.write_bytes(b'\x0C\x00\x4A\x00\x24\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
                    writer.write_bytes(b'\x4A\x00\x00\x00')
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 12)
                    writer.write_bytes(b'\x02\x00\x00\x00\x00\x00\x00\x00')  # Always 2
                    writer.write_uint32(struct_num)

                elif PropertyType == 2:  # Audio
                    f.seek(property_table_start + pointer_offset)
                    AudioContainer = f.read_uint16
                    AudioID = f.read_uint16

                    write_zero_bytes(writer, 64)  # Write padding
                    writer.write_bytes(b'\x0C\x00\x1A\x00\x40\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')  # Writes prop header
                    writer.write_bytes(b'\x1A\x00\x00\x00')  # Property Type/Controller Type
                    writer.write_float(start_frame)
                    writer.write_float(end_frame + 99)
                    write_zero_bytes(writer, 12)
                    writer.write_bytes(b'\x02\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00')

                    writer.write_bytes(b'\x01\x80\x24\x00')
                    writer.write_bytes(b'\x10\x00\x00\x00\x00\x00\x80\x40\x00\x00\x80\x3F\x00\x00\x20\x42\x0A\xD7\x23\x3C')
                    write_zero_bytes(writer, 4)

                    f.seek(cur_pos)

                elif PropertyType == 18:  # Camera Shake
                    write_zero_bytes(writer, 64)
                    writer.write_bytes(b'\x0C\x00\x58\x00\x30\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')
                    writer.write_bytes(b'\x58\x00\x00\x00')
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 8)
                    writer.write_bytes(b'\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00')  # Always 2
                    writer.write_float(0.2)
                    writer.write_float(1)
                    writer.write_uint32(0)

                elif PropertyType == 26:  # Hyperarmor
                    write_zero_bytes(writer, 64)  # Write padding
                    writer.write_bytes(b'\x0C\x00\x19\x00\x24\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')  # Writes prop header
                    writer.write_bytes(b'\x19\x00\x00\x00')  # Property Type/Controller Type
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 12)
                    writer.write_bytes(b'\x02\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00')

                elif PropertyType == 29:  # Heat Gain/Loss
                    write_zero_bytes(writer, 64)  # Write padding
                    writer.write_bytes(b'\x0C\x00\x9D\x00\x24\x00\x00\x00\xFF\xFF\xFF\xFF\x00\x00\x00\x00')  # Writes prop header
                    writer.write_bytes(b'\x9D\x00\x00\x00')  # Property Type/Controller Type
                    writer.write_float(start_frame)
                    writer.write_float(end_frame)
                    write_zero_bytes(writer, 8)
                    writer.write_bytes(b'\x01\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00')
                    writer.write_int32(modifier)
                a = a + 1
            write_zero_bytes(writer, 80)
            bep_name = move + ".bep"
            new_file_dir = Path("Converted (Property to BEP)")
            new_file_path = Path(new_file_dir / bep_name)
            new_file_dir.mkdir(exist_ok=True)
            with open(new_file_path, 'wb') as new_file:
                new_file.write(writer.buffer())
