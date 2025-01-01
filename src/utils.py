import os
from pydub import AudioSegment
import shutil


def check_if_file_exists(path):
    return os.path.exists(path)

def generate_instrumental(folder_name):
    components = ['bass.mp3', 'drums.mp3', 'other.mp3']
    combined = None
    for track in components:
        path = os.path.join(f'tmp/htdemucs/{folder_name}', track)
        if os.path.exists(path):
            audio = AudioSegment.from_file(path)
            if combined is None:
                combined = audio
            else:
                combined = combined.overlay(audio)
        else:
            raise FileNotFoundError(f'File not found: {path}')

    if combined:
        folder_name_without_ext = os.path.splitext(folder_name)[0]
        combined.export(f'tmp/htdemucs/{folder_name_without_ext}_instrumental.mp3', format='mp3')
    else:
        raise ValueError('No audio files were combined.')
    

def parse_options(options_string, options_dict):
    cmd = options_string[1:]
    for o in cmd:
        if o == 'i':
            options_dict['instrumental'] = True
        elif o == 'd':
            options_dict['drum'] = True
        elif o == 'g':
            options_dict['guitar'] = True
        elif o == 'b':
            options_dict['bass'] = True
        elif o == 'v':
            options_dict['vocal'] = True
        else:
            raise ValueError(f'Invalid option: {o}')

def clear_tmp():
    tmp_dir = 'tmp'
    if os.path.exists(tmp_dir) and os.path.isdir(tmp_dir):
        for item in os.listdir(tmp_dir):
            item_path = os.path.join(tmp_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

def save(output_dir, options, folder_name):
    options_dict = {
        'instrumental': False,
        'drum': False,
        'guitar': False,
        'bass': False,
        'vocal': False,
    }
    parse_options(options, options_dict)

    if options_dict['instrumental']:
        generate_instrumental(folder_name)
        os.rename(f'tmp/htdemucs/{folder_name}_instrumental.mp3', f'{output_dir}/{folder_name}_instrumental.mp3')

    if options_dict['drum']:
        os.rename(f'tmp/htdemucs/{folder_name}/drums.mp3', f'{output_dir}/{folder_name}_drums.mp3')

    if options_dict['guitar']:
        os.rename(f'tmp/htdemucs/{folder_name}/other.mp3', f'{output_dir}/{folder_name}_guitar.mp3')

    if options_dict['bass']:
        os.rename(f'tmp/htdemucs/{folder_name}/bass.mp3', f'{output_dir}/{folder_name}_bass.mp3')
    
    if options_dict['vocal']:
        os.rename(f'tmp/htdemucs/{folder_name}/vocals.mp3', f'{output_dir}/{folder_name}_vocals.mp3')

    clear_tmp()