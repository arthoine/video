"""
Test FFmpeg NVENC direct - Bypass MoviePy

Ce script teste si FFmpeg peut vraiment encoder avec h264_nvenc
en appelant FFmpeg directement (sans MoviePy)
"""

import subprocess
import sys
from pathlib import Path

def test_ffmpeg_nvenc():
    """Test si FFmpeg peut encoder avec h264_nvenc"""
    print("=" * 70)
    print("TEST: FFmpeg h264_nvenc DIRECT (sans MoviePy)")
    print("=" * 70)

    # Créer une vidéo de test de 5 secondes
    test_input = "test_input.mp4"
    test_output = "test_nvenc_output.mp4"

    print("\n1. Création vidéo de test avec testsrc...")
    cmd_create = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', 'testsrc=duration=5:size=1920x1080:rate=60',
        '-f', 'lavfi',
        '-i', 'sine=frequency=1000:duration=5',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-c:a', 'aac',
        '-y',
        test_input
    ]

    try:
        result = subprocess.run(cmd_create, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Vidéo de test créée")
        else:
            print(f"❌ Erreur création: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

    # Test encodage avec h264_nvenc
    print("\n2. Test encodage avec h264_nvenc...")
    cmd_nvenc = [
        'ffmpeg',
        '-i', test_input,
        '-c:v', 'h264_nvenc',
        '-preset', 'hq',
        '-cq', '20',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-y',
        test_output
    ]

    print("Commande:")
    print(f"  {' '.join(cmd_nvenc)}")

    try:
        result = subprocess.run(cmd_nvenc, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("\n✅ SUCCÈS! h264_nvenc fonctionne!")
            print(f"Fichier créé: {test_output}")

            # Vérifier le codec
            cmd_check = ['ffmpeg', '-i', test_output]
            check = subprocess.run(cmd_check, capture_output=True, text=True)
            if 'h264' in check.stderr.lower():
                print("✅ Codec vérifié: H.264")

            # Nettoyer
            try:
                Path(test_input).unlink()
                Path(test_output).unlink()
                print("\n✓ Fichiers de test nettoyés")
            except:
                pass

            return True
        else:
            print("\n❌ ÉCHEC! h264_nvenc ne fonctionne PAS")
            print(f"Erreur FFmpeg:\n{result.stderr}")

            # Suggestions
            print("\n💡 SOLUTIONS:")
            print("1. Téléchargez FFmpeg avec support GPU:")
            print("   https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z")
            print("\n2. Ou vérifiez vos drivers NVIDIA:")
            print("   nvidia-smi")

            return False

    except subprocess.TimeoutExpired:
        print("❌ Timeout - L'encodage prend trop de temps")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("\n🎮 Ce test vérifie si FFmpeg peut utiliser h264_nvenc")
    print("   (sans passer par MoviePy qui peut causer des problèmes)\n")

    success = test_ffmpeg_nvenc()

    print("\n" + "=" * 70)
    if success:
        print("✅ RÉSULTAT: FFmpeg h264_nvenc FONCTIONNE")
        print("\nLe problème vient de MoviePy qui ignore nos paramètres.")
        print("Solution: Utiliser FFmpeg directement au lieu de MoviePy.")
    else:
        print("❌ RÉSULTAT: FFmpeg h264_nvenc NE FONCTIONNE PAS")
        print("\nVotre FFmpeg n'a pas le support NVENC.")
        print("Téléchargez la version complète (voir solutions ci-dessus).")
    print("=" * 70)

    sys.exit(0 if success else 1)
