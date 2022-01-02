"""Keil2Makefile
    file: Keil2Makefile.py
    author: qrpucp (qrpucp@qq.com)
    brief: a automatic script to change a Keil project to makefile project
    date: 2021-12-31
    usage: move Keil2Makefile-master to root directory of Keil project,
        then enter Keil2Makefile-master and run Keil2Makefile.py.
        read README to find more.
    workflow:
        1. detect Keil project
        2. read Keil project config and Config.yml
        3. generate makefile according to Keil config and user config
        4. backup old stm32 startup file, generate new stm32 startup 
            file and link script
"""

import re
import os
import shutil

def find_file(start_path, extension_name):
    """recursive search file by extension_name

    Args:
        start_path (string): search begin path
        extension_name (string): file's extension_name

    Returns:
        string: None or file path
    """
    for relpath, dirs, file_list in os.walk(start_path):
        for file in file_list:
            if file.endswith(extension_name):
                full_path = os.path.join(start_path, relpath, file)
                return file, os.path.normpath(os.path.abspath(full_path))
    return 'None', 'None'

def get_xml_config(config_file_path, xml_tag):
    """get config from xml file

    Args:
        config_file_path (string or string list): xml config file
        xml_tag (string): xml tag

    Returns:
        string: config get from the file
    """
    list = []
    with open(config_file_path, encoding = 'utf8') as file_handle:
        filelines = file_handle.readlines()
    for line in filelines:
        if xml_tag in line:
            info = re.findall('<' + xml_tag + '>'+ '(.*?)' + '</' + xml_tag + '>', line)
            if(type(info) == type([])):
                info = ''.join(info)
            if(len(info) != 0 and info[0] != ''):
                list.append(info)
    file_handle.close()
    return list

# get config from yaml config
def get_yaml_config(config_file_path, yaml_tag):
    """get config from yaml config

    Args:
        config_file_path (string): yaml config file
        yaml_tag (string): yaml tag

    Returns:
        string: config get from the file
    """
    with open(config_file_path, encoding = 'utf8') as file_handle:
        filelines = file_handle.readlines()
        filelines[len(filelines) - 1] = filelines[len(filelines) - 1] + '\n'
    for line in filelines:
        if yaml_tag in line:
            info = ''.join(re.findall(yaml_tag + '.*:' + '(.*?)' + '\n', line))
            info = str.replace(info, ' ', '')
    file_handle.close()
    return info

def path_process(path_list, parent_path):
    """change relative path to absolute path, and change \\ to /

    Args:
        path_list (string or string list): paths need to be changed
        parent_path (string): parent path

    Returns:
        string or string list: changed path
    """
    string_list_type = type(['',''])
    string_type = type('')
    processed_path_list = []
    if(type(path_list) == string_list_type):
        for path in path_list:
            processed_path = str.replace(path, '\\', '/')
            processed_path = str.replace(processed_path, '..', parent_path)
            processed_path_list.append(processed_path)
        return processed_path_list
    elif(type(path_list) == string_type):
        processed_path = str.replace(path_list, '\\', '/')
        processed_path = str.replace(processed_path, '..', parent_path)
        return processed_path

def path_absolute2relative(path_list, parent_path):
    """change absolute path to relative path

    Args:
        path_list (string list): paths need to be changed
        parent_path (string): parent path

    Returns:
        string list: changed path
    """
    string_list_type = type(['',''])
    string_type = type('')
    processed_path_list = []
    if(type(path_list) == string_list_type):
        for path in path_list:
            processed_path = str.replace(path, parent_path + '/', '')
            processed_path_list.append(processed_path)
        return processed_path_list
    elif(type(path_list) == string_type):
        processed_path = str.replace(path_list, parent_path + '/', '')
        return processed_path

def get_parent_path(path, split_symbol):
    """get parent path

    Args:
        path (string): raw path
        split_symbol (string): path separator

    Returns:
        string: the parent path
    """
    reversed_path = ''
    times = 0
    for ch in reversed(path):
        if(times >= 2):
            reversed_path = reversed_path + ch
        else:
            if(ch == split_symbol):
                times = times + 1
    return reversed_path[::-1]

def get_dir_path(path, split_symbol):
    """remove file name from path

    Args:
        path (string): raw path
        split_symbol (string): path separator

    Returns:
        string: path without file name
    """
    reversed_path = ''
    times = 0
    for ch in reversed(path):
        if(times >= 1):
            reversed_path = reversed_path + ch
        else:
            if(ch == split_symbol):
                times = times + 1
    return reversed_path[::-1]

def delete_head_file(file_list):
    """delete C head file from file list

    Args:
        file_list (string list): the list
    """
    index_list = []
    for index, path in enumerate(file_list):
        if '.h' in path:
            index_list.append(index)
    for i in range(0, len(index_list)):
        del file_list[index_list[i] - i]

def split_list(list, split_symbol):
    """split list with string

    Args:
        list (list): the list need to be splited
        split_symbol (string): the symbol used for split

    Returns:
        list: splited list
    """
    return list[0].split(split_symbol)

def write_file_with_lines(file_name, lines):
    """write file with lines list

    Args:
        file_name (string): the file to be generated
        lines (string list): file content
    """
    with open(file_name, 'r+', encoding = 'utf8') as file_handle:
        for line in lines:
            file_handle.write(line) 
        file_handle.close()

if __name__ == '__main__':

    # recursive search keil project
    root_path = path_process(os.path.abspath(os.path.join(os.getcwd(), "../..")), '')
    keil_peoject_name, keil_project_path = find_file(root_path, '.uvprojx')
    if(keil_peoject_name == 'None'):
        print("can't find keil project, please check *.uvprojx position")
        exit()
    else:
        print('find keil project ' + keil_peoject_name)

    keil_project_parent_path = path_process(get_parent_path(keil_project_path, '\\'), '')

    # get user config from yaml file
    yaml_file_path = os.path.abspath(os.path.join(os.getcwd(), "..")) + '\Config\Config.yml'
    optimization = get_yaml_config(yaml_file_path, 'optimization')
    generate_mode = get_yaml_config(yaml_file_path, 'generate_mode')
    debug_build = get_yaml_config(yaml_file_path, 'debug_build')
    auto_add_file = get_yaml_config(yaml_file_path, 'auto_add_file')
    build_dir = get_yaml_config(yaml_file_path, 'build_dir')
    modify_asm = get_yaml_config(yaml_file_path, 'modify_asm')

    # get generate mode
    new_makefile_path = root_path + '/Makefile'
    if(os.path.isfile(new_makefile_path)):
        with open(new_makefile_path, encoding = 'utf8') as makefile_handle:
            makefile_first_line = makefile_handle.readline()
        if 'Keil2Makefile' in makefile_first_line and generate_mode != 'force_regenerate':
            generate_mode = 'update'
        else:
            try:
                # if there is a makefile not generated by Keil2Makefile or generate mode is 'force_regenerate'
                generate_mode = 'create'
                os.remove(new_makefile_path)
            except:
                print("can't delete original makefile file, please check permissions.")
        makefile_handle.close()
    else:
        generate_mode = 'create'
    
    print('generate mode: ' + generate_mode)
    
    # generate makefile file
    if generate_mode == 'force_regenerate' or generate_mode == 'create':
        try:
            shutil.copy(os.getcwd() + '/RawMakefile', root_path)
            os.rename(root_path + '/RawMakefile', root_path + '/Makefile')
            print('create makefile successfully')
        except:
            print("can't create file, please check R/W permissions.")

    with open(new_makefile_path, 'r+', encoding = 'utf8') as makefile_handle:
        makefile_lines = makefile_handle.readlines()
    
    # update parameters
    status = 0
    for index, line in enumerate(makefile_lines):
        if status == 0 and 'DEBUG' in line:
            status = status + 1
            del makefile_lines[index]
            makefile_lines.insert(index, 'DEBUG = ' + debug_build + '\n')
        if status == 1 and 'OPT' in line:
            status = status + 1
            del makefile_lines[index]
            makefile_lines.insert(index, 'OPT = ' + optimization + '\n')
        if status == 2 and 'BUILD_DIR' in line:
            status = status + 1
            del makefile_lines[index]
            makefile_lines.insert(index, 'BUILD_DIR = ' + build_dir + '\n')
        if status == 3:
            break
    if status != 3:
        print('makefile modified accidentally, try force_regenerate')
    write_file_with_lines(new_makefile_path, makefile_lines)

    # update mode
    if generate_mode == 'update':
        print("successfully update parameters, program exit.")
        exit()

    # create or force_regenerate mode
    # get keil project config
    device = get_xml_config(keil_project_path, 'Device')
    defines = get_xml_config(keil_project_path, 'Define')
    misc_controls = get_xml_config(keil_project_path, 'MiscControls')
    include_path = get_xml_config(keil_project_path, 'IncludePath')
    source_path = get_xml_config(keil_project_path, 'FilePath')
    target_name = get_xml_config(keil_project_path, 'TargetName')
    pocessed_include_path = path_process(include_path, keil_project_parent_path)
    processed_source_path = path_process(source_path, keil_project_parent_path)
    relative_include_path = path_absolute2relative(pocessed_include_path, root_path)
    relative_source_path = path_absolute2relative(processed_source_path, root_path)
    delete_head_file(relative_source_path)
    defines = split_list(defines, ',')
    misc_controls = split_list(misc_controls, ' ')
    relative_include_path = split_list(relative_include_path, ';')
    # backspace make command wrong
    target_name = str.replace(target_name[0], ' ', '_')
    # to do: add C99 mode through <uC99>

    # create link script
    if not os.path.isfile(root_path + '\\' + device[0] + '_FLASH.ld') or generate_mode == 'force_regenerate':
        new_link_script_src_path_1 = os.path.abspath(os.path.join(os.getcwd(), "..")) + '\LinkScript\\' + device[0] + '_FLASH.ld'
        new_link_script_src_path_2 = os.path.abspath(os.path.join(os.getcwd(), "..")) + '\LinkScript\\' + device[0] + 'Tx_FLASH.ld'
        try:
            shutil.copy(new_link_script_src_path_1, root_path)
            link_script_type = 'link_script_type1'
            print('generate link script')
        except:
            try:
                shutil.copy(new_link_script_src_path_2, root_path)
                link_script_type = 'link_script_type2'
                print('generate link script')
            except:
                print('failed to generate link script')

    # get config from misc_controls
    cpp_mode = 0
    for misc_control in misc_controls:
        if 'cpp' in misc_control:
            # if add --cpp in Keil, all file compiled by g++
            cpp_mode = 1

    # add c_defines in makefile and get config from defines
    use_dsp_flag = 0
    for index, line in enumerate(makefile_lines):
        if 'C_DEFS' in line:
            status = status + 1
            for define_index, define in enumerate(defines):
                if 'ARM_MATH_CM4' in define:
                    # use DSP library
                    use_dsp_flag = 1;
                    pass
                elif '__CC_ARM' in define:
                    # __CC_ARM represent ARM RealView, need to be removed
                    continue
                index = index + 1
                makefile_lines.insert(index, '-D' + define + ' \\\n')
            break

    # modify makefie file
    status = 0
    for index, line in enumerate(makefile_lines):
        if status == 0 and 'TARGET' in line:
            status = status + 1
            del makefile_lines[index]
            makefile_lines.insert(index, 'TARGET = ' + target_name + '\n')
        if status == 1 and 'CPP_SOURCES' in line:
            status = status + 1
            for source_path_index, source_path in enumerate(relative_source_path):
                if '.cpp' in source_path:
                    index = index + 1
                    makefile_lines.insert(index, source_path + ' \\\n')
        if status == 2 and 'C_SOURCES' in line:
            status = status + 1
            for source_path_index, source_path in enumerate(relative_source_path):
                if '.c' in source_path and '.cpp' not in source_path:
                    index = index + 1
                    makefile_lines.insert(index, source_path + ' \\\n')
            if use_dsp_flag == 1:
                index = index + 1
                makefile_lines.insert(index, '$(wildcard Keil2Makefile/Library/DSP/Source/*/*.c) \\\n')
        if status == 3 and 'ASM_SOURCES' in line:
            status = status + 1
            if modify_asm == '0':
                # not modify asm file
                continue
            for source_path_index, source_path in enumerate(relative_source_path):
                if '.asm' in source_path or '.s' in source_path:
                    index = index + 1
                    # backup original stm32 startup file
                    if 'startup' in source_path:
                        startup_file_path = root_path + '/' + source_path
                        try:
                            os.rename(startup_file_path, startup_file_path + '.backup')
                            print('backup stm32 startup file')
                        except:
                            # print("can't rename file, please check stm32 startup file.")
                            pass
                        # copy new startup file
                        new_startup_file_src_path = os.path.abspath(os.path.join(os.getcwd(), "..")) + \
                                                        '\StartupFile\startup_' + str.lower(device[0])[0:9] + 'xx.s'
                        new_startup_file_dst_path = str.replace(get_dir_path(startup_file_path, '/'), '/', '\\')
                        if not os.path.exists(new_startup_file_dst_path):
                            os.makedirs(new_startup_file_dst_path)
                        try:
                            shutil.copy(new_startup_file_src_path, new_startup_file_dst_path)
                            print('generate new stm32 startup file')
                        except:
                            print('failed to generate stm32 startup file')
                        new_startup_file_dst_path = str.replace(new_startup_file_dst_path, '\\', '/')
                        makefile_lines.insert(index, path_absolute2relative(new_startup_file_dst_path, root_path) 
                                                    + '/startup_' + str.lower(device[0])[0:9] + 'xx.s' + ' \\\n')
                    elif '.asm' in source_path:
                        print('you need to deal with ' + source_path + ' manually')
                        # change the extension name from .asm to .s
                        makefile_lines.insert(index, source_path[0 : len(source_path) - 3] + 's \\\n')
                    else:
                        makefile_lines.insert(index, source_path + ' \\\n')
        # two cc need to be modify
        if (status == 4 or status == 5) and 'CC = ' in line:
            status = status + 1
            # if add --cpp in Keil, all file compiled by g++
            if cpp_mode == 1:
                makefile_lines[index] = str.replace(line, 'gcc', 'g++')
        if status == 6 and 'C_INCLUDES' in line:
            status = status + 1
            for include_path_index, include_path in enumerate(relative_include_path):
                index = index + 1
                makefile_lines.insert(index, '-I' + include_path + ' \\\n')
            if use_dsp_flag == 1:
                index = index + 1
                makefile_lines.insert(index, '-IKeil2Makefile/Library/DSP/Include \\\n')
        if status == 7 and 'LDSCRIPT' in line:
            status = status + 1
            del makefile_lines[index]
            if link_script_type == 'link_script_type1':
                makefile_lines.insert(index, 'LDSCRIPT = ' + device[0] + '_FLASH.ld\n')
            elif link_script_type == 'link_script_type2':
                makefile_lines.insert(index, 'LDSCRIPT = ' + device[0] + 'Tx_FLASH.ld\n')
        if status == 8:
            break

    write_file_with_lines(new_makefile_path, makefile_lines)