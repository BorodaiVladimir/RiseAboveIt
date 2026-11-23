# Ставит «Канаву» в ОТКРЫТЫЙ уровень без переимпорта ассетов (они уже должны быть импортированы
# ue_import_rise_above_it.py). Порядок: File → New Level (Empty Level) → Execute Python Script → этот файл → сохранить уровень.
# Лежит рядом с ue_import_rise_above_it.py в корне UE_Import.
import os, runpy

os.environ["RAI_ARENA"] = "Ditch"
os.environ["RAI_SKIP_IMPORT"] = "1"
try:
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ue_import_rise_above_it.py"), run_name="__main__")
finally:
    os.environ.pop("RAI_ARENA", None)
    os.environ.pop("RAI_SKIP_IMPORT", None)
