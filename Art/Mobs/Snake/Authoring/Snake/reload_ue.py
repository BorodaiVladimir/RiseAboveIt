from pathlib import Path
p=Path(__file__).with_name('verify_ue.py')
exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),{'__file__':str(p),'RELOAD_ONLY':True})
