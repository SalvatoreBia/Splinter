import os
import sys
import torchaudio
from pydub import AudioSegment
from demucs.apply import apply_model
from demucs.pretrained import get_model
from demucs.audio import AudioFile


def check_if_file_exists(path):
    return os.path.exists(path)

def generate_instrumental(folder_name):
    components = ['bass.wav', 'drums.wav', 'other.wav']
    combined = None
    for track in components:
        path = os.path.join(f'../tmp/htdemucs/{folder_name}', track)
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
        combined.export(f'../tmp/{folder_name_without_ext}_instrumental.wav', format='wav')
    else:
        raise ValueError('No audio files were combined.')


class Splitter:

    def __init__(self):
        self.components = ['bass.wav', 'drums.wav', 'other.wav']
        self.options = {
            'instrumental': False,
            'drum': False,
            'guitar': False,
            'bass': False,
            'vocal': False,
        }
        self.file_path = None
        self.output_dir = 'tmp'

    def set_file_path(self, path):
        if not check_if_file_exists(path):
            raise FileNotFoundError(f'File not found: {path}')
        self.file_path = path

    def parse_options(self, options):
        cmd = options[1:]
        for o in cmd:
            if o == 'i':
                self.options['instrumental'] = True
            elif o == 'd':
                self.options['drum'] = True
            elif o == 'g':
                self.options['guitar'] = True
            elif o == 'b':
                self.options['bass'] = True
            elif o == 'v':
                self.options['vocal'] = True
            else:
                raise ValueError(f'Invalid option: {o}')

    def run(self, options, input_file, output_dir):
        self.set_file_path(input_file)
        self.parse_options(options)
        self.output_dir = output_dir

        folder_name = os.path.splitext(os.path.basename(self.file_path))[0]
        print(f"\n[Splitter] Starting separation on: {self.file_path}")
        print(f"[Splitter] Options: {options}")
        print(f"[Splitter] Output dir: {self.output_dir}\n")

        print("[Splitter] Loading Demucs model (htdemucs)...")
        model = get_model(name='htdemucs')
        model.cpu()

        wav = AudioFile(self.file_path).read(
            streams=0,
            samplerate=model.samplerate,
            channels=model.audio_channels
        )

        ref = wav.mean(0) if model.audio_channels == 1 else wav

        print("[Splitter] Applying model... (this may download weights if not cached)")
        sources = apply_model(
            model,
            ref[None, ...],
            overlap=0.25,
            split=True,
            progress=True
        )
        sources = sources[0]

        demucs_output_path = f'../tmp/htdemucs/{folder_name}'
        os.makedirs(demucs_output_path, exist_ok=True)

        sample_rate = model.samplerate
        source_names = model.sources

        print(f"[Splitter] Saving stems to: {demucs_output_path}")
        for i, name in enumerate(source_names):
            audio_data = sources[i].cpu().float()
            out_path = os.path.join(demucs_output_path, f"{name}.wav")
            torchaudio.save(out_path, audio_data, sample_rate)

        if self.options['instrumental']:
            print("[Splitter] Generating instrumental track...")
            generate_instrumental(folder_name)

        os.makedirs(self.output_dir, exist_ok=True)

        instrumental_path = f'../tmp/{folder_name}_instrumental.wav'
        if self.options['instrumental'] and os.path.exists(instrumental_path):
            os.rename(instrumental_path, os.path.join(self.output_dir, f'{folder_name}-instrumental.wav'))

        drum_path = os.path.join(demucs_output_path, 'drums.wav')
        if self.options['drum'] and os.path.exists(drum_path):
            os.rename(drum_path, os.path.join(self.output_dir, f'{folder_name}-drum.wav'))


        guitar_path = os.path.join(demucs_output_path, 'other.wav')
        if self.options['guitar'] and os.path.exists(guitar_path):
            os.rename(guitar_path, os.path.join(self.output_dir, f'{folder_name}-guitar.wav'))

        bass_path = os.path.join(demucs_output_path, 'bass.wav')
        if self.options['bass'] and os.path.exists(bass_path):
            os.rename(bass_path, os.path.join(self.output_dir, f'{folder_name}-bass.wav'))

        vocal_path = os.path.join(demucs_output_path, 'vocals.wav')
        if self.options['vocal'] and os.path.exists(vocal_path):
            os.rename(vocal_path, os.path.join(self.output_dir, f'{folder_name}-vocal.wav'))

        if os.path.exists(demucs_output_path):
            for root, dirs, files in os.walk(demucs_output_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(demucs_output_path)

        print("[Splitter] Separation process completed!")


def main():
    if len(sys.argv) != 4:
        print("Usage: python splitter_subprocess.py <options> <input_file> <output_dir>")
        sys.exit(1)

    options = sys.argv[1]
    input_file = sys.argv[2]
    output_dir = sys.argv[3]

    splitter = Splitter()
    splitter.run(options, input_file, output_dir)

if __name__ == "__main__":
    main()
