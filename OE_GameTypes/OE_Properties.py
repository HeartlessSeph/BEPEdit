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


def convert_property_bin_to_beps(f, move_list, mep_folder, file_directory=Path("")):
    """
    :param f: BinaryStream
    :param move_list: Dictionary
    :param mep_folder: Path Object
    :param file_directory: Path Object
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
                        writer.write_uint32(32)  # Writes Movetype as Regular Hit with Guardbreak
                    else:
                        writer.write_uint32(1)  # Writes Movetype as Regular Hit
                    f.seek(cur_pos)

                elif PropertyType == 10:  # Self Contained Hitbox
                    damage = struct_num * 10
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
            new_file_dir_append = Path("Converted (Property to BEP)")
            new_file_dir = Path(file_directory / new_file_dir_append)
            new_file_path = Path(file_directory / new_file_dir / bep_name)
            new_file_dir.mkdir(exist_ok=True)
            with open(new_file_path, 'wb') as new_file:
                new_file.write(writer.buffer())
