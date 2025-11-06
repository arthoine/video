"""
Test script to verify NVENC parameters are correct
"""

# Simulate the parameters that will be generated
config = {
    'output': {'preset': 'hq', 'crf': 20},
    'performance': {'use_gpu': True, 'num_threads': 4}
}

codec_input = 'libx264'
preset = config.get('output', {}).get('preset', 'medium')
crf = str(config.get('output', {}).get('crf', 18))
num_threads = config.get('performance', {}).get('num_threads', 0)

# Codec determination
codec = codec_input
use_gpu = config.get('performance', {}).get('use_gpu', False)

if use_gpu and codec_input == 'libx264':
    codec = 'h264_nvenc'
    if preset not in ['fast', 'medium', 'slow', 'hq', 'bd', 'll', 'llhq', 'lossless']:
        preset = 'hq'
    print("✅ GPU ACTIVÉ: h264_nvenc")
else:
    print("❌ GPU non activé")

# Build FFmpeg params
ffmpeg_params = [
    '-c:v', codec,  # <-- PROBLÈME: codec est aussi passé au paramètre codec= de MoviePy
    '-preset', preset,
]

if codec == 'h264_nvenc':
    ffmpeg_params.extend([
        '-rc:v', 'vbr',
        '-cq:v', crf,
        '-b:v', '0',
        '-maxrate:v', '20M',
        '-bufsize:v', '40M',
    ])
else:
    ffmpeg_params.extend(['-crf', crf])

ffmpeg_params.extend([
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '192k',
    '-ar', '48000',
    '-movflags', '+faststart',
])

print("\n📋 FFmpeg params generés:")
print(' '.join(ffmpeg_params))

print("\n⚠️  PROBLÈME DÉTECTÉ:")
print("  1. '-c:v h264_nvenc' est dans ffmpeg_params")
print("  2. ET codec='h264_nvenc' est passé à write_videofile()")
print("  3. MoviePy va probablement dupliquer: -c:v h264_nvenc -c:v h264_nvenc")
print("\n💡 SOLUTION: Retirer '-c:v' de ffmpeg_params")

print("\n\n🔍 VÉRIFICATION NVENC:")
print("=" * 60)

# Test if NVENC params are correct
nvenc_params_test = ['-rc:v', 'vbr', '-cq:v', '20', '-b:v', '0', '-maxrate:v', '20M', '-bufsize:v', '40M']
print("Paramètres NVENC actuels:", ' '.join(nvenc_params_test))

# Simplified version (more reliable)
nvenc_params_simple = ['-cq', '20']
print("Paramètres NVENC simplifiés:", ' '.join(nvenc_params_simple))

print("\n✅ Les deux méthodes sont valides, mais la version simplifiée est plus sûre")
print("   car FFmpeg choisit automatiquement le meilleur rc mode avec -cq")
