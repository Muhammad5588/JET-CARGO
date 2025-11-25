import os
import shutil

def remove_pycache(root_dir='.'):
    """
    Berilgan direktoriya va uning barcha subdirektoriyalaridan 
    __pycache__ papkalarini o'chiradi.
    """
    deleted_count = 0
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if '__pycache__' in dirnames:
            pycache_path = os.path.join(dirpath, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"O'chirildi: {pycache_path}")
                deleted_count += 1
            except Exception as e:
                print(f"Xatolik: {pycache_path} - {e}")
    
    print(f"\nJami {deleted_count} ta __pycache__ papka o'chirildi.")

if __name__ == "__main__":
    remove_pycache()