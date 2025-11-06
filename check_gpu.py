"""
Script de vérification GPU pour StreamHighlightAI
Vérifie que le GPU NVIDIA est bien détecté et configuré
"""

import sys
import subprocess

def check_nvidia_gpu():
    """Vérifie la présence d'un GPU NVIDIA avec nvidia-smi"""
    print("🔍 Vérification du GPU NVIDIA...")
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            gpu_info = result.stdout.strip()
            print(f"✅ GPU détecté: {gpu_info}")
            return True
        else:
            print("❌ nvidia-smi a retourné une erreur")
            print(f"   Erreur: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ nvidia-smi non trouvé - Drivers NVIDIA non installés?")
        print("   Installez les drivers depuis: https://www.nvidia.com/Download/index.aspx")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def check_pytorch_cuda():
    """Vérifie que PyTorch détecte CUDA"""
    print("\n🔍 Vérification de PyTorch CUDA...")
    try:
        import torch
        cuda_available = torch.cuda.is_available()

        if cuda_available:
            print(f"✅ PyTorch CUDA disponible!")
            print(f"   Version CUDA: {torch.version.cuda}")
            print(f"   Nombre de GPUs: {torch.cuda.device_count()}")
            print(f"   GPU principal: {torch.cuda.get_device_name(0)}")
            return True
        else:
            print("❌ PyTorch CUDA NON disponible")
            print("   PyTorch est installé mais ne détecte pas CUDA")
            print("\n💡 Solution:")
            print("   pip uninstall torch torchvision torchaudio")
            print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            return False
    except ImportError:
        print("❌ PyTorch non installé")
        print("   Installez avec: pip install -r requirements.txt")
        return False

def check_ffmpeg_nvenc():
    """Vérifie que FFmpeg supporte h264_nvenc"""
    print("\n🔍 Vérification de FFmpeg NVENC...")
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if 'h264_nvenc' in result.stdout:
            print("✅ FFmpeg supporte h264_nvenc (encodage GPU NVIDIA)")
            return True
        else:
            print("⚠️  FFmpeg ne supporte PAS h264_nvenc")
            print("   FFmpeg va utiliser le CPU pour encoder (plus lent)")
            print("\n💡 Solution:")
            print("   Téléchargez FFmpeg avec support GPU depuis:")
            print("   https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg non trouvé")
        print("   Installez FFmpeg (voir WINDOWS.md)")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def check_config():
    """Vérifie la configuration GPU dans config.yaml"""
    print("\n🔍 Vérification de config.yaml...")
    try:
        import yaml
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        use_gpu = config.get('performance', {}).get('use_gpu', False)

        if use_gpu:
            print("✅ GPU activé dans config.yaml")
            return True
        else:
            print("⚠️  GPU DÉSACTIVÉ dans config.yaml")
            print("   Pour activer: changez 'use_gpu: false' -> 'use_gpu: true'")
            return False
    except FileNotFoundError:
        print("⚠️  config.yaml non trouvé")
        return False
    except ImportError:
        print("⚠️  PyYAML non installé")
        print("   Installez avec: pip install pyyaml")
        return False
    except Exception as e:
        print(f"⚠️  Erreur lors de la lecture: {e}")
        return False

def main():
    print("=" * 60)
    print("🎮 StreamHighlightAI - Vérification GPU")
    print("=" * 60)

    checks = []

    # Vérifications
    checks.append(("GPU NVIDIA", check_nvidia_gpu()))
    checks.append(("PyTorch CUDA", check_pytorch_cuda()))
    checks.append(("FFmpeg NVENC", check_ffmpeg_nvenc()))
    checks.append(("Configuration", check_config()))

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)

    all_ok = all(result for _, result in checks)

    for name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {name}")

    print("\n" + "=" * 60)

    if all_ok:
        print("🎉 TOUT EST BON! Le GPU sera utilisé pour:")
        print("   - Whisper (transcription audio)")
        print("   - Encodage vidéo (h264_nvenc)")
        print("\n⚡ Temps estimé pour 15min de highlights:")
        print("   - Avec GPU: ~5-10 minutes")
        print("   - Sans GPU: ~20-30 minutes")
        print("\n🚀 Vous pouvez lancer:")
        print("   python main.py -i votre_video.mp4")
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS")
        print("\nLe programme fonctionnera mais utilisera le CPU (plus lent)")
        print("Suivez les solutions indiquées ci-dessus pour activer le GPU")

    print("=" * 60)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
