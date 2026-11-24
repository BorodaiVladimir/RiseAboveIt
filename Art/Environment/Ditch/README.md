# Канава — серый блокаут второй локации

Черновик для проверки геймплея: форма оврага, укрытия, вода и точки спавна. Арта пока нет (тун, мох и детальный тростник будут позже).

**Карта в проекте:** `Content/RiseAboveIt/Maps/L_Arena_Ditch` (`/Game/RiseAboveIt/Maps/L_Arena_Ditch`). Её можно просто открыть.
**Меши:** `Content/RiseAboveIt/Arena_Ditch/SM_Ditch_*`. Материалы общие из `Content/RiseAboveIt/Materials` (`M_Palette`, `M_Palette_TwoSided`, `M_Water`, `M_Glow`), верстак — `Arena_Earth/SM_Safe_Workbench`.

## Что внутри

Масштаб ×35: игрок ростом с лягушку (~5 см), канава глубиной 35 см становится оврагом 12 м. Овраг ~150 м вдоль оси X, по дну течёт ручей.

1. **Старт и safe zone** (x ≈ −60 м): консервная банка на боку, внутри верстак и светодиод. `PlayerStart` смотрит вдоль канавы на трубу.
2. **Бой** (x ≈ −50…30 м): кочки, коряги и камни по обе стороны, три бочага глубиной ~2 м. Середина свободна для прохода.
3. **Арена босса** (x ≈ 44 м): ровный круг r 15 м перед бетонной трубой Ø 10.5 м. В трубу можно зайти на ~7 м, дальше решётка. Босс-мышь выходит из трубы.

| Ассет | Коллизия |
|---|---|
| `SM_Ditch_Ground` — дно, склоны ~60°, верх | Complex as Simple; склоны круче предела пола, на них не залезть |
| `SM_Ditch_Water` — ручей и бочаги | нет, ходят вброд |
| `SM_Ditch_Props` — кочки, коряги, камни | UCX (28) |
| `SM_Ditch_Reeds` — тростник и рогоз по верху | нет |
| `SM_Ditch_Pipe` — труба, оголовок, решётка | UCX (24) |
| `SM_Ditch_SafeZone` — банка | UCX (25) |
| `SM_Ditch_Boundary` — стена по верху склонов | UCX (62), Hidden in Game |

Акторы на карте (папка `Arena_Ditch` в Outliner): `PlayerStart`, `SafeZone_Workbench`, `SafeZone_Light`, `SafeZone_Trigger` (Trigger Box по банке), `Spawn_Ground_01..05` (ящерицы, змеи, жабы-танки у подножия склонов), `Spawn_Water_01..04` (лягушки и жабы на воде), `Spawn_Boss` (в устье трубы), `BossArena_Trigger` (30 × 30 × 8 м). Те же точки в `ArenaDitch_Layout.csv` (см, оси UE).

Свет в `Arena_Ditch/Lighting`: пасмурно, густой серо-зелёный туман у дна. Цифры подобраны на глаз, их стоит подкрутить в редакторе.

## Проверки

- `Reports/check_ditch.log` — проходимость по выгрузке, сетка 0.5 м. От старта можно дойти до верстака и до босса, на склоны и за решётку не попасть, из бочагов можно выйти, спавны стоят на полу или на воде и не внутри коллизии. Результат: PASS.
- `Reports/ue57_publication_check.txt` — UE 5.7: карта открыта с материалами и верстаком из main, 26 акторов, пропавших мешей и материалов нет.

## Пересборка

Исходники в `Authoring/` (Blender 5.x):

```
blender -b --factory-startup --python Authoring/Arena_Ditch/build_ditch.py    # FBX + CSV в Authoring/Arena_Ditch/Export
blender -b --factory-startup --python Authoring/Arena_Ditch/check_ditch.py    # проходимость, код выхода 1 при ошибке
```

Форма задаётся в `ditch_shape.py`. `verify_ditch.py` рендерит кадры в `Preview/`; ему нужен ещё `Arena_Earth/Export/SM_Safe_Workbench.fbx` из исходников Земли. Импорт в UE: `UE_Tools/ue_import_rise_above_it.py`, затем `UE_Tools/ue_place_ditch.py` в пустом уровне. Оба скрипта ждут рядом раскладку папок `UE_Import` (`Arena_Ditch/SM_Ditch_*.fbx`, CSV, палитра).
