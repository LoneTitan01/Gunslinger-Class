# Gunslinger custom icon artwork

All checkboxes below mean **final artwork still needed**, not missing wiring.
The mod already contains registered icon names, a populated placeholder atlas,
380x380 tooltip exports, 144x144 controller exports, and 48x48 resource exports.
These use temporary firearm images derived from the permitted Immersive Firearms
assets. Replace them with your artwork; do not rename the files or stat references.
UI appearance still needs an in-game check on keyboard/mouse and controller.

## ComfyUI generation workflow

Import [Gunslinger_Icons_FLUX.json](artwork/comfyui/Gunslinger_Icons_FLUX.json)
by dragging it onto the ComfyUI canvas. The matching
[icon_prompts.json](artwork/comfyui/icon_prompts.json) contains subjects for all
50 ability icons and six resource icons. This is a reusable **one-icon-at-a-time**
workflow, not an automatic batch runner. It uses built-in local nodes only; no
custom-node pack, paid API, or external image-generation service is required.

### Generate through the API with Python

[generate_icons.py](artwork/comfyui/generate_icons.py) automates the workflow
above using Python's standard library (no pip dependencies). Start ComfyUI and
install BiRefNet as described below, then run from the repository root:

```powershell
# Verify live node/model availability without queueing or writing images.
python artwork\comfyui\generate_icons.py --dry-run

# Generate one icon first and review the result.
python artwork\comfyui\generate_icons.py --icons GSL_MercilessShot

# Generate the six resource glyphs.
python artwork\comfyui\generate_icons.py --group resources

# List keys without contacting ComfyUI.
python artwork\comfyui\generate_icons.py --list

# Generate every icon into a separate candidate directory.
python artwork\comfyui\generate_icons.py --output artwork\comfyui\generated\set2 --seed 12345
```

Default API: `http://127.0.0.1:8188`; use `--url` for a different local port.
Only loopback HTTP endpoints are accepted and proxies/redirects are disabled,
so prompts are not sent to an external service.

The script reads your current catalog edits, converts the UI workflow into an
API prompt, updates the prompt and all five filenames, validates node/model
availability, and queues **one icon at a time**. It polls `/history/<prompt_id>`
and downloads each output through `/view`. Generated PNGs use exact names such
as `generated\tooltip\GSL_MercilessShot.png` without ComfyUI's counter suffix.
The server also retains its normal counter-suffixed copies.

All five sizes are downloaded, including the 1024px master. Ability icons use
380/144/64px outputs; resources use 48px. PNG headers are checked for the required
dimensions and RGBA colour type before saving. Each icon has a metadata JSON
containing its complete prompt, reproducible derived seed, API graph, prompt ID,
and completion state. Changing the selected subset/order does not change a key's
seed. No generated files overwrite mod-source DDS assets.

The default candidate folder is `artwork\comfyui\generated`, ignored by Git.
Existing selected outputs cause an error **before anything is queued**.
Use `--overwrite` deliberately to replace them, or choose another `--output`.
After a partial run, select only the unfinished icons with `--icons`; there is
no automatic resume/requeue. `--timeout` defaults to 1800 seconds per icon,
including time behind other jobs. Errors/timeouts stop the batch and preserve
the queued prompt ID in metadata. A timeout or Ctrl+C does not interrupt other
users' ComfyUI jobs or clear its shared queue; inspect the queued job before retrying.

DDS conversion, atlas placement and resource-state variants remain the finishing
steps documented below.

### Install the additional background-removal model

The installation checked for this workflow is
`C:\Users\natha\ComfyUI-Installs\ComfyUI\ComfyUI` (the inner `ComfyUI` directory).
FLUX.1-dev, CLIP-L, the FP8 T5 encoder, and the VAE are already present.
The background-removal model is not installed yet.

1. Open the [Comfy-Org BiRefNet model repository](https://huggingface.co/Comfy-Org/BiRefNet/tree/main).
2. Open the repository's `background_removal` folder and download
   **`birefnet.safetensors`**, the ComfyUI-repackaged model. Do not
   substitute an arbitrary `.pth`, ONNX file, or unrelated BiRefNet variant.
   Direct download: <https://huggingface.co/Comfy-Org/BiRefNet/resolve/main/background_removal/birefnet.safetensors>.
3. Save it as:
   `C:\Users\natha\ComfyUI-Installs\ComfyUI\ComfyUI\models\background_removal\birefnet.safetensors`.
   Create the `background_removal` directory if necessary. Avoid a doubled
   filename extension or saving the download's HTML page instead of the model.
4. Restart ComfyUI through its normal launcher so the model dropdown refreshes.
5. In **Load Background Removal Model**, select `birefnet.safetensors`.

The model publisher explicitly documents this folder/name. The installed
ComfyUI includes `LoadBackgroundRemovalModel`, `RemoveBackground`,
`InvertMask` and `JoinImageWithAlpha`; no background-removal plugin is needed.
Check the model's license and FLUX.1-dev's usage terms before distributing or
commercially using generated artwork.

### Generate each icon

1. Import the workflow. Confirm these loader selections:
   - UNET: `flux1-dev.safetensors`, weight dtype `fp8_e4m3fn`.
   - Dual CLIP: `clip_l.safetensors` and
     `t5xxl_fp8_e4m3fn_scaled.safetensors`, type `flux`.
   - VAE: `ae.safetensors`.
   - Background removal: `birefnet.safetensors`.
2. Pick an exact key from the prompt catalog, such as `GSL_PrimaryReload`.
   Concatenate `style_prefix`, that key's subject, and `style_suffix`, then paste
   into **POSITIVE**. For a resource key, use `resource_style_suffix` instead.
   Keep the common style wording stable across the set.
3. Change the basename in **all five Save Image nodes** to that exact key,
   keeping their folder prefixes. For example:
   `Gunslinger/masters/GSL_PrimaryReload`,
   `Gunslinger/tooltip/GSL_PrimaryReload`,
   `Gunslinger/controller/GSL_PrimaryReload`,
   `Gunslinger/hotbar/GSL_PrimaryReload`,
   `Gunslinger/resource/GSL_PrimaryReload`.
   The `/` characters here are ComfyUI filename-prefix syntax, not Windows
   filesystem paths. For grit, use the key `GunslingerGrit`, not `GSL_Grit`.
4. Queue once. Starting settings: 1024x1024, batch size 1, 24 steps, Euler,
   Simple scheduler, sampler CFG **1**, FLUX Guidance **3.5**, denoise 1.
   The fixed seed makes retries reproducible. Change the seed to obtain a new
   candidate; reuse a selected seed while refining its prompt. A shared seed
   and prompt style encourage consistency but do not guarantee it.
5. Inspect the transparent master and small versions. Reject extra barrels,
   modern firearms, illegible detail, clipped silhouettes, weak contrast, or
   silhouettes that resemble another action. Revise the subject or seed.
   Resource glyphs should be simpler than spell icons.
6. The workflow saves RGBA PNGs under:
   `C:\Users\natha\ComfyUI-Installs\ComfyUI\ComfyUI\output\Gunslinger\`
   in `masters`, `tooltip`, `controller`, `hotbar`, and `resource` subfolders.
   A launcher output-directory override changes this root; Save Image follows
   ComfyUI's configured output directory. ComfyUI appends counters such as
   `_00001_` to filenames. Choose a candidate and strip that suffix when exporting
   to the exact mod basename.

Pipeline: FLUX generation -> VAE decode -> BiRefNet foreground mask ->
**InvertMask** -> Join Image With Alpha -> master PNG and Lanczos-resized PNGs.
Do not remove InvertMask: BiRefNet supplies foreground coverage, while the join
node uses the opposite Comfy mask convention. Without it the subject becomes
transparent instead of its background.

The workflow generates 380x380 tooltip, 144x144 controller, 64x64 atlas-tile and
48x48 resource versions from the same master. Only use the outputs appropriate
to the selected key: ability keys use the first three, resource keys use 48x48.
The extra size outputs are harmless working files, not mod assets.

### Finish and export

- Background removal is actual segmentation, not a promise made by the text
  prompt. Inspect alpha on both light and dark checkerboards. Thin muzzle smoke
  or magical glows may be removed; repair the mask/alpha in an image editor
  before creating final exports. Avoid white/dark halos after resizing.
- Convert approved tooltip/controller PNGs locally to alpha-capable BC3/DXT5
  DDS using a DDS-capable image editor or texture converter. Preserve dimensions
  and save to the exact destinations below. ComfyUI's Save Image writes PNG,
  **not DDS**, and LSLib does not perform this image conversion.
- Paste each approved 64x64 tile into its listed atlas cell, then export the
  entire 2048x2048 atlas as DDS. Do not place each tile as an independent
  hotbar DDS and expect it to replace atlas registration.
- For resources, create available/Highlight/Used/Missing variants from the
  approved 48x48 glyph and export to every resource destination below.
  This workflow generates the base glyph, **not all 16 state/surface copies**.
- Generated files remain working artwork outside the game source until you
  explicitly replace placeholders. Queueing the workflow does not overwrite
  mod assets or rebuild PAKs.

The graph and model selections were checked against the running local
ComfyUI node schemas. A full generation including segmentation still requires
installing the additional model; final art quality and in-game appearance are
not yet verified.

## 1. Export each spell, ability, passive and status icon

For every `GSL_*` name in the checklist, produce these three versions:

| Surface | Repository-relative destination | File type and dimensions |
|---|---|---|
| Tooltip / large feature preview | `GunslingerClass\Public\Game\GUI\Assets\Tooltips\Icons\<IconName>.DDS` | DDS, 380x380, transparent background |
| Controller / radial menu | `GunslingerClass\Public\Game\GUI\Assets\ControllerUIIcons\skills_png\<IconName>.DDS` | DDS, 144x144, transparent background |
| Hotbar / character-creation selection slot | `GunslingerClass\Public\GunslingerClass\Assets\Textures\Icons\Icons_GunslingerAbilities.dds` | DDS atlas, 2048x2048; each icon occupies one 64x64 cell |

Use alpha-capable DDS compression (BC3/DXT5 matches the supplied ability exports).
The cached wiki also supports PNG for the separate tooltip/controller files,
but this scaffold consistently uses `.DDS`. Replace the existing DDS rather than
leaving a second PNG with the same basename. Preserve the atlas's lowercase
`.dds` filename and all other filename casing.

Example: Merciless Shot's two separate images are
`GunslingerClass\Public\Game\GUI\Assets\Tooltips\Icons\GSL_MercilessShot.DDS`
and
`GunslingerClass\Public\Game\GUI\Assets\ControllerUIIcons\skills_png\GSL_MercilessShot.DDS`.
Its 64x64 hotbar artwork belongs at pixels x=0..63, y=0..63 in the atlas.

### Where the references are already wired

- **S** = [GunslingerSpells.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerSpells.txt).
- **P** = [GunslingerPassives.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerPassives.txt).
- **T** = [GunslingerStatuses.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerStatuses.txt).
- Grit spend tiers, repair/Tinkerer hand choices, and the range-modified secondary shot in [GunslingerGritSpells.txt](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerGritSpells.txt), their [statuses](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerGritStatuses.txt), and [Desperado interrupts](GunslingerClass/Public/GunslingerClass/Stats/Generated/Data/GunslingerInterrupts.txt) explicitly reuse the corresponding existing icon keys. They do not require extra atlas cells or new images.
- Each consumer has `data "Icon" "<IconName>"`. This is a symbolic key, **not a file path**.
- Every key is registered in [Icons_GunslingerAbilities.lsx](GunslingerClass/Public/GunslingerClass/GUI/Icons_GunslingerAbilities.lsx).
- The atlas is registered in the [UI TextureBank](GunslingerClass/Public/GunslingerClass/Content/UI/%5BPAK%5D_UI/_merged.lsx).
- Related actions, unlock passives and buffs share artwork. Hidden mechanics also
  have references, but do not need an extra image beyond their shared key.
- The three internal spell parents (`Projectile_GSL_FirearmAttack`,
  `Shout_GSL_ClassAction`, `Shout_GSL_Reload`) are not player-facing actions and
  do not need separate art.

### Artwork checklist and atlas slots

Coordinates are **zero-based column,row**, measured from the atlas's top-left.
The top-left pixel is `(column * 64, row * 64)`.
For every row below, replace both `<IconName>.DDS` exports and its atlas cell.

#### Grit abilities, subclass actions and associated statuses

| Done | IconName / export basename | Cell | Consumers already referencing this icon |
|---|---|---|---|
| [ ] | `GSL_MercilessShot` | 0,0 | S `Shout_GSL_MercilessShot`; P `GSL_MercilessShotUnlock`; T `GSL_MERCILESS_SHOT` |
| [ ] | `GSL_LineEmUp` | 1,0 | S `Zone_GSL_LineEmUp`; P `GSL_LineEmUpUnlock` |
| [ ] | `GSL_RapidShot` | 2,0 | S `Shout_GSL_RapidShot`; P `GSL_RapidShotUnlock`; T `GSL_RAPID_SHOT` |
| [ ] | `GSL_BiteTheBullet` | 3,0 | S `Shout_GSL_BiteTheBullet`; P `GSL_BiteTheBulletUnlock`; T `GSL_BITE_THE_BULLET` |
| [ ] | `GSL_ShotInTheDark` | 4,0 | S `Shout_GSL_ShotInTheDark`; P `GSL_ShotInTheDarkUnlock`; T `GSL_SHOT_IN_THE_DARK` |
| [ ] | `GSL_RapidRepair` | 5,0 | S `Shout_GSL_RapidRepair`; P `GSL_RapidRepairUnlock` |
| [ ] | `GSL_Tinkerer` | 6,0 | S `Shout_GSL_Tinkerer`; P `GSL_TinkererUnlock`; T `GSL_TINKERED` |
| [ ] | `GSL_FanningFire` | 7,0 | S `Shout_GSL_FanningFire`; P `GSL_FanningFireUnlock`; T `GSL_FANNING_FIRE` |
| [ ] | `GSL_DoubleLoad` | 8,0 | S `Shout_GSL_DoubleLoad`; P `GSL_Desperado_DoubleLoadUnlock`; T `GSL_DOUBLE_LOAD` |
| [ ] | `GSL_CloseCall` | 9,0 | S `Target_GSL_CloseCall`; P `GSL_Desperado_CloseCallUnlock`; T `GSL_CLOSE_CALL` |
| [ ] | `GSL_LastWord` | 10,0 | S `Shout_GSL_LastWord`; P `GSL_Desperado_LastWordUnlock`; T `GSL_LASTWORD_CD` |
| [ ] | `GSL_StableShot` | 11,0 | S `Shout_GSL_StableShot`; P `GSL_Marksman_StableShot`; T `GSL_STABLE_SHOT` |
| [ ] | `GSL_Headshot` | 12,0 | S `Shout_GSL_Headshot`; P `GSL_Marksman_Headshot`; T `GSL_HEADSHOT` |
| [ ] | `GSL_InfusedRounds` | 13,0 | S `Projectile_GSL_InfusedRounds`; P `GSL_ArcaneGunsman_InfusedRoundsUnlock` |
| [ ] | `GSL_InfusedRounds_2` | 14,0 | S `Projectile_GSL_InfusedRounds_2`; P `GSL_ArcaneGunsman_ImprovedInfusedRounds` |
| [ ] | `GSL_ArcaneReload` | 15,0 | S `Shout_GSL_ArcaneReload`; P `GSL_ArcaneGunsman_ArcaneReload` |
| [ ] | `GSL_InfusedRounds_3` | 16,0 | S `Projectile_GSL_InfusedRounds_3`; P `GSL_ArcaneGunsman_MasteredInfusedRounds` |
| [ ] | `GSL_InfusedRounds_Unstable` | 17,0 | S `Projectile_GSL_InfusedRounds_Unstable`; P `GSL_ArcaneGunsman_UnstableInfusedRoundsUnlock` |
| [ ] | `GSL_UnstableBackfire` | 18,0 | S `Zone_GSL_UnstableBackfire`; T `GSL_UNSTABLE_ROUNDS_SELFDAMAGE` (internal warning/effect) |

#### Shooting and reloading

These keys are deliberately separate from firearm **inventory** icons.
All three primary firearms share Primary Reload artwork; Secondary and Full
Reload have separate artwork. This changes icons only, not action costs.

| Done | IconName / export basename | Cell | Consumers already referencing this icon |
|---|---|---|---|
| [ ] | `GSL_ShootFlintlock` | 19,0 | S `GSL_MainHand_Flintlock_attack`; P `GSL_Flintlock_MainHand` |
| [ ] | `GSL_ShootSecondaryFlintlock` | 20,0 | S `GSL_OffHand_Flintlock_attack`; P `GSL_Flintlock_OffHand` |
| [ ] | `GSL_ShootBlunderbuss` | 21,0 | S `GSL_MainHand_Blunderbuss_attack`; P `GSL_Blunderbuss_MainHand` |
| [ ] | `GSL_ShootMusket` | 22,0 | S `GSL_MainHand_Musket_attack`; P `GSL_Musket_MainHand` |
| [ ] | `GSL_Scattershot` | 17,1 | S `Zone_GSL_Scattershot` (Blunderbuss 10-ft cone, Dex save); unlocked by P `GSL_Blunderbuss_MainHand`. ComfyUI candidate generated at `artwork\comfyui\generated\{tooltip,controller,hotbar}\GSL_Scattershot.png`; current DDS exports and atlas cell are placeholders copied from `GSL_ShootBlunderbuss` |
| [ ] | `GSL_PrimaryReload` | 23,0 | S `Shout_GSL_Reload_Flintlock`, `Shout_GSL_Reload_Blunderbuss`, `Shout_GSL_Reload_Musket` |
| [ ] | `GSL_SecondaryReload` | 24,0 | S `Shout_GSL_Reload_OffhandFlintlock` |
| [ ] | `GSL_FullReload` | 25,0 | S `Shout_GSL_Reload_DualFlintlock` |

#### Craft menu and its five choices

| Done | IconName / export basename | Cell | Consumers already referencing this icon |
|---|---|---|---|
| [ ] | `GSL_Craft` | 26,0 | S `Shout_GSL_Craft` (linked action container) |
| [ ] | `GSL_CraftFlintlock` | 27,0 | S `Shout_GSL_CraftFlintlock` |
| [ ] | `GSL_CraftBlunderbuss` | 28,0 | S `Shout_GSL_CraftBlunderbuss` |
| [ ] | `GSL_CraftMusket` | 29,0 | S `Shout_GSL_CraftMusket` |
| [ ] | `GSL_CraftAssemblyKit` | 30,0 | S `Shout_GSL_CraftAssemblyKit` |
| [ ] | `GSL_CraftDisassemblyKit` | 31,0 | S `Shout_GSL_CraftDisassemblyKit` |

#### Feats, passive features and warnings

Feat components share a single icon per feat, including their hidden components.

| Done | IconName / export basename | Cell | Consumers already referencing this icon |
|---|---|---|---|
| [ ] | `GSL_Gunner` | 0,1 | P `GSL_Feat_Gunner_Proficiency`, `GSL_Feat_Gunner_Dexterity` |
| [ ] | `GSL_QuickReload` | 1,1 | P `GSL_Feat_QuickReload_Marker`, `GSL_Feat_QuickReload_Dexterity` |
| [ ] | `GSL_GritAdept` | 2,1 | P `GSL_Feat_GritAdept_MaxGrit` |
| [ ] | `GSL_CloseQuartersGunner` | 3,1 | P `GSL_Feat_CloseQuartersGunner_Push`, `GSL_Feat_CloseQuartersGunner_Dexterity` |
| [ ] | `GSL_LongarmSpecialist` | 4,1 | P `GSL_Feat_LongarmSpecialist_Range`, `GSL_Feat_LongarmSpecialist_Dexterity` |
| [ ] | `GSL_CalledShot` | 5,1 | P `GSL_Feat_CalledShot_Rider`, `GSL_Feat_CalledShot_Dexterity`; T `GSL_CALLEDSHOT_MARKED` |
| [ ] | `GSL_SpellshotAdept` | 6,1 | P `GSL_Feat_SpellshotAdept_Magical`, `GSL_Feat_SpellshotAdept_Rider`, `GSL_Feat_SpellshotAdept_RiderDamage`, `GSL_Feat_SpellshotAdept_Intelligence`; T `GSL_SPELLSHOT_CHARGED` |
| [ ] | `GSL_DesperadosLuck` | 7,1 | P `GSL_Desperado_DesperadosLuckUnlock` |
| [ ] | `GSL_SecondAttack` | 8,1 | P `GSL_Desperado_SecondAttack` |
| [ ] | `GSL_LockOn` | 9,1 | P `GSL_Marksman_LockOn` |
| [ ] | `GSL_LongShot` | 10,1 | P `GSL_Marksman_LongShot` |
| [ ] | `GSL_PinpointAccuracy` | 11,1 | P `GSL_Marksman_PinpointAccuracy` |
| [ ] | `GSL_SmartShooting` | 12,1 | P `GSL_ArcaneGunsman_SmartShooting` |
| [ ] | `GSL_SpellstrikeShooter` | 13,1 | P `GSL_ArcaneGunsman_SpellstrikeShooter` |
| [ ] | `GSL_GritRecovery` | 14,1 | P `GSL_GritRecovery` (hidden resource recovery mechanic) |
| [ ] | `GSL_BrokenFirearm` | 15,1 | T `GSL_DOUBLE_LOAD_BROKEN`; P `GSL_DoubleLoad_Misfire` |
| [ ] | `GSL_Misfire` | 16,1 | T `GSL_MISFIRE`; P `GSL_Firearm_Misfire_Passive` |

## 2. Create grit, ammunition and crafting-resource artwork

Resource icons follow a **different pipeline**. The filename matches `Name` in
[ActionResourceDefinitions.lsx](GunslingerClass/Public/GunslingerClass/ActionResourceDefinitions/ActionResourceDefinitions.lsx).
Do not add a made-up `Icon` attribute there, and do not put these images in the
spell atlas. Resource names are already used by the relevant `UseCosts`,
`TooltipUseCosts`, `ActionResource` and `RestoreResource` fields.

| Done | Exact resource filename | UI meaning / principal consumers |
|---|---|---|
| [ ] | `GunslingerGrit.DDS` | Grit; base/subclass grit abilities, Grit Adept and grit recovery |
| [ ] | `GunslingerFlintlockAmmo.DDS` | Primary flintlock ammunition; primary shooting/reload and Full Reload |
| [ ] | `GunslingerOffhandFlintlockAmmo.DDS` | Secondary flintlock ammunition; secondary shooting/reload and Full Reload |
| [ ] | `GunslingerBlunderbussAmmo.DDS` | Blunderbuss ammunition; shooting and Primary Reload |
| [ ] | `GunslingerMusketAmmo.DDS` | Musket ammunition; shooting and Primary Reload |
| [ ] | `GunslingerCraftCharges.DDS` | Gunsmithing Charge; Craft and its five choices |

Produce **48x48 alpha-capable DDS** images in all paths below, matching the cached
5e reference mod's resource layout and dimensions. Existing placeholder files
are provided in every location. `AssetsLowRes` resource files are also 48x48
in that reference; they are not the 144x144 controller skill exports.

Prefix every path below with `GunslingerClass\Mods\GunslingerClass\GUI\`.
Replace `<ResourceName>` with each of the six basenames above:

| Surface | Available | Highlight | Used | Missing |
|---|---|---|---|---|
| Shared | `Assets\Shared\Resources\<ResourceName>.DDS` | `Assets\Shared\Resources\Highlight\<ResourceName>.DDS` | `Assets\Shared\Resources\Used\<ResourceName>.DDS` | `Assets\Shared\Resources\Missing\<ResourceName>.DDS` |
| Resource panel | `Assets\ActionResources_c\Icons\Resources\<ResourceName>.DDS` | `Assets\ActionResources_c\Icons\Resources\Highlight\<ResourceName>.DDS` | `Assets\ActionResources_c\Icons\Resources\Used\<ResourceName>.DDS` | `Assets\ActionResources_c\Icons\Resources\Missing\<ResourceName>.DDS` |
| Shared low-res | `AssetsLowRes\Shared\Resources\<ResourceName>.DDS` | `AssetsLowRes\Shared\Resources\Highlight\<ResourceName>.DDS` | `AssetsLowRes\Shared\Resources\Used\<ResourceName>.DDS` | `AssetsLowRes\Shared\Resources\Missing\<ResourceName>.DDS` |
| Resource panel low-res | `AssetsLowRes\ActionResources_c\Icons\Resources\<ResourceName>.DDS` | `AssetsLowRes\ActionResources_c\Icons\Resources\Highlight\<ResourceName>.DDS` | `AssetsLowRes\ActionResources_c\Icons\Resources\Used\<ResourceName>.DDS` | `AssetsLowRes\ActionResources_c\Icons\Resources\Missing\<ResourceName>.DDS` |

Example full path for available grit:
`GunslingerClass\Mods\GunslingerClass\GUI\Assets\Shared\Resources\GunslingerGrit.DDS`.

- [ ] Give available resources their normal colour.
- [ ] Make Highlight brighter and clearly distinguishable.
- [ ] Make Used visibly spent/dim.
- [ ] Make Missing visibly unavailable; distinguish it from available and used.
- [ ] Check grit and both flintlock ammo pools remain recognizable at 48x48.

There are 16 exports per resource (four surfaces/quality combinations times four
states), for 96 resource DDS files. These are name-based GUI assets; no extra
TextureBank or atlas registration is needed for this reference layout.

## 3. Preserve atlas registration and package the artwork

- [ ] Paint the 50 cells above in the existing 2048x2048 ability atlas. Keep the
  remaining cells blank. Do not overwrite the separate firearm inventory atlas.
- [ ] Keep `MapKey` names and UV coordinates in
  [Icons_GunslingerAbilities.lsx](GunslingerClass/Public/GunslingerClass/GUI/Icons_GunslingerAbilities.lsx).
  Current UVs are `U1=column/32`, `U2=(column+1)/32`,
  `V1=row/32`, `V2=(row+1)/32`. Keep transparent padding inside cells to avoid
  sampling neighboring artwork.
- [ ] Preserve atlas UUID `832eff43-b1dc-49b7-b021-1fc625c94ea4` in both the GUI
  map and [UI TextureBank](GunslingerClass/Public/GunslingerClass/Content/UI/%5BPAK%5D_UI/_merged.lsx).
  The GUI path is `Assets/Textures/Icons/Icons_GunslingerAbilities.dds`;
  the TextureBank source is
  `Public/GunslingerClass/Assets/Textures/Icons/Icons_GunslingerAbilities.dds`.
  Only update registration if you intentionally change the layout or atlas path.
- [ ] Run `python -m unittest discover -s tests -v` and `python validate_xml.py`.
  [test_icon_data.py](tests/test_icon_data.py) checks stat references, checklist
  slots, DDS dimensions, UV positions, atlas registration and all resource states.
  It does not judge artistic quality or prove that the game renders the icons.
- [ ] Run [stage_packages.py](stage_packages.py) with
  `--divine "C:\path\to\Divine.exe"` to convert Content banks/root templates to
  LSF, localization XML to LOCA, and pack both PAKs. DDS assets are staged as-is;
  LSLib does **not** resize images or convert PNG artwork into DDS.
- [ ] Install the rebuilt main PAK and inspect hotbar icons, Craft's submenu,
  character-creation/level-up grit selections, passive tooltips, active statuses,
  controller radials, and available/used/missing resources.
- [ ] Confirm Primary Reload, Secondary Reload and Full Reload are visually
  distinct; test dual flintlocks as well as each two-handed firearm.

## 4. Separate / optional artwork work

- Existing firearm inventory icons (`GSL_Flintlock`, `GSL_Musket`,
  `GSL_Blunderbuss`) remain in
  [Icons_GunslingerFirearms.lsx](GunslingerClass/Public/GunslingerClass/GUI/Icons_GunslingerFirearms.lsx),
  `Tooltips\ItemIcons` and `ControllerUIIcons\items_png`. They already use imported
  firearm artwork and are **not** replaced by shooting-action art.
- Assembly/Disassembly Kit inventory items still use vanilla kit artwork.
  Their **Craft actions** are covered above; custom inventory art is optional
  and would use the item-icon pipeline, not the skill-icon folders.
- Class/subclass emblems (Gunslinger, Marksman, Desperado, Arcane Gunsman) have a
  separate class-icon pipeline. They are not part of this spell/passive atlas
  and this change does not wire new class emblems.
- Vanilla spells and optional 5e spells retain their supplying mod/game icons.
  Do not duplicate those assets in the compatibility PAK.
- Adding final art does not implement currently approximate mechanics. See
  [README.md](README.md#implementation-notes--known-limitations) for gameplay limitations.

Workflow source: cached [Icon Creation guide](examples/Docs/wiki-cache/Icons/Icon-Creation.md).
Resource paths/dimensions were checked against the locally cached 5e reference
`RitualSpellResource` GUI assets; resource rendering still requires in-game verification.
