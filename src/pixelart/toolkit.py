"""Unified pixel-asset workflow toolkit built on the deterministic pixelart core.

Provides explicit source-format routing (never forcing all assets into one flat
JSON grid), 3-tier verification (required / contract / advisory), local edit
boundaries, multi-state shared-grid and semantic patch-stack compilation with
local rollback, named atlas and layered component preservation, and deterministic
ZIP packing with isolated rebuild verification.
"""

from collections import deque
from copy import deepcopy
from io import BytesIO
import hashlib
import json
from math import isqrt
from pathlib import Path
from pathlib import PureWindowsPath
from struct import unpack_from
import tempfile
import unicodedata
import zipfile

from PIL import Image, ImageDraw

from .assembly import assemble, load_project, seam_sheet
from .compat import pixels, require_pillow
from .context import _box
from .core import MAX_PIXELS, MAX_SIDE, PixelArtError, color, dimensions, integer, make_preview
from .edit import _allowed_mask, recolor_image, replace_cell, verify_edit
from .ingest import image_to_spec
from .jsonio import read_json
from .metadata import layout_record, merge_layout, rgba_digest
from .output import encoded, publish
from .spec import render


TOOLKIT_VERSION = '1.0.0'
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)
SUPPORTED_MODES = (
    'auto',
    'grid',
    'png-native',
    'shared-grid-states',
    'state-set',
    'atlas',
    'assembly',
)


class ContractViolationError(PixelArtError):
    """Raised when a user-declared local contract fails (distinct from schema/IO errors)."""

    def __init__(self, message, report=None):
        super().__init__(message)
        self.report = report


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _state_name_key(name, mode):
    if not isinstance(name, str) or not name:
        raise PixelArtError(f'{mode}: state names must be non-empty filenames')

    normalized = unicodedata.normalize('NFKC', name)
    windows_path = PureWindowsPath(normalized)
    if (
        normalized in ('.', '..')
        or windows_path.is_absolute()
        or windows_path.drive
        or any(unicodedata.category(char) == 'Cc' for char in normalized)
        or any(char in '<>:"/\\|?*' for char in normalized)
        or normalized[-1] in ('.', ' ')
    ):
        raise PixelArtError(f'{mode}: invalid state filename {name!r}')

    device_name = normalized.split('.', 1)[0].rstrip(' .').casefold()
    reserved_names = {'con', 'prn', 'aux', 'nul', 'conin$', 'conout$', 'clock$'}
    reserved_names.update(f'{prefix}{number}' for prefix in ('com', 'lpt') for number in range(1, 10))
    if device_name in reserved_names:
        raise PixelArtError(f'{mode}: reserved Windows device name {name!r}')

    return normalized.casefold().rstrip(' .')


def _validate_state_names(states, mode):
    names = {}
    for state_name in states:
        key = _state_name_key(state_name, mode)
        previous = names.get(key)
        if previous is not None:
            raise PixelArtError(
                f'{mode}: state names {previous!r} and {state_name!r} resolve to the same filename'
            )
        names[key] = state_name


def _resolved_path(path):
    try:
        return Path(path).resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise PixelArtError(f'toolkit: could not resolve output path {path}: {exc}') from exc


def _path_key(path):
    text = str(_resolved_path(path)).replace('\\', '/')
    return tuple(
        unicodedata.normalize('NFKC', part).casefold().rstrip(' .')
        for part in text.split('/')
        if part
    )


def _path_keys_overlap(first, second):
    shared = min(len(first), len(second))
    return first[:shared] == second[:shared]


def _same_existing_path(first, second):
    try:
        return Path(first).samefile(second)
    except OSError:
        return False


def _publication_artifacts(out_dir, files, pack_zip, input_paths):
    out_root_key = _path_key(out_dir)
    delivery = [(Path(out_dir) / relative, data) for relative, data in files.items()]
    publication = list(delivery)
    if pack_zip is not None:
        publication.append((Path(pack_zip), _pack_zip_bytes(files)))

    resolved_targets = []
    for target, _ in publication:
        resolved = _resolved_path(target)
        key = _path_key(resolved)
        if len(resolved_targets) < len(delivery) and not (
            len(key) > len(out_root_key) and key[:len(out_root_key)] == out_root_key
        ):
            raise PixelArtError(
                f'toolkit: delivery output escapes --out-dir through path resolution: {target}'
            )

        for previous, previous_key in resolved_targets:
            if _path_keys_overlap(key, previous_key) or _same_existing_path(resolved, previous):
                raise PixelArtError(
                    f'toolkit: output path conflict between {previous} and {resolved}'
                )
        resolved_targets.append((resolved, key))

        for input_path in input_paths:
            input_resolved = _resolved_path(input_path)
            if key == _path_key(input_resolved) or _same_existing_path(resolved, input_resolved):
                raise PixelArtError(
                    f'toolkit: output path {resolved} aliases input path {input_resolved}'
                )

    return dict(publication)


def _check_preview_scale(size, scale):
    width, height = size
    maximum = min(
        MAX_SIDE // width, MAX_SIDE // height, isqrt(MAX_PIXELS // (width * height))
    )
    if scale > maximum:
        raise PixelArtError(
            f'toolkit: {scale}x preview exceeds image limits for {width}x{height}; '
            f'use --scale {maximum} or smaller'
        )


def _read_static_png(path):
    """Validate PNG header, <=8-bit depth, static single frame, and return RGBA copy."""
    path = Path(path)
    if not path.is_file():
        raise PixelArtError(f'toolkit: PNG file not found: {path}')
    with path.open('rb') as handle:
        header = handle.read(33)
        if (
            len(header) < 33
            or header[:8] != b'\x89PNG\r\n\x1a\n'
            or header[8:16] != b'\x00\x00\x00\x0dIHDR'
        ):
            raise PixelArtError(f'toolkit: expected a valid PNG input: {path}')
        if header[24] > 8:
            raise PixelArtError(
                f'toolkit: PNG bit depth above 8 ({header[24]}-bit) is not supported: {path}'
            )
        dimensions(unpack_from('>II', header, 16))
        handle.seek(0)
        with Image.open(handle, formats=('PNG',)) as opened:
            if getattr(opened, 'n_frames', 1) != 1:
                raise PixelArtError(
                    f'toolkit: animated or multiframe PNG is unsupported: {path}'
                )
            opened.load()
            return opened.copy()


def route_intent(query):
    """Map a natural-language pixel asset request to a concrete mode and command."""
    text = (query or '').strip()
    lower = text.lower()
    if not text:
        raise PixelArtError('route: provide a non-empty natural-language task description')

    has_png_edit = any(
        k in lower
        for k in (
            '已有png', '已有 png', '现有png', '现有 png', '局部修', '局部改', '局改',
            '改色', '掩码', '蒙版', 'mask', 'recolor', 'existing png', 'patch png',
        )
    )
    has_atlas = any(
        k in lower
        for k in ('图集', 'atlas', '单格', 'cell', 'spritesheet', 'sprite sheet', '格名')
    )
    has_layers = any(
        k in lower
        for k in ('图层', '组件', '分层', '拼接', 'layer', 'component', 'assemble', 'seam')
    )
    has_multistate = any(
        k in lower
        for k in (
            '双态', '双状态', '多态', '多状态', '状态', '亮暗', '点亮', '开合', '开关',
            '按下', 'hover', 'pressed', 'active', 'idle', 'state', 'variant',
        )
    )
    has_geom_change = any(
        k in lower
        for k in (
            '开合', '打开', '抬起', '位移', '变形', '改形', '轮廓变', '几何', '补丁',
            '回退', 'open', 'shift', 'geometry', 'alpha change', 'rollback', 'patch',
        )
    )

    if has_layers:
        return {
            'recommended_mode': 'assembly',
            'reason': '保留独立 PNG 图层与组件坐标，支持单组件替换、接缝检查与无损组包复建，避免过早扁平化。',
            'entrypoint': 'python <skill>/scripts/recipes/asset_toolkit.py deliver --mode assembly --source project.json --out-dir out --pack-zip out.zip',
            'fallback': 'python <skill>/scripts/pixel_art.py assemble --project project.json --out asset.png --seams seams.png',
            'warnings': ['若当前只有裸 PNG 而无 project.json 清单，需先提供分层 PNG 与 project.json；工具不会凭空猜测图层语义。'],
        }
    if has_atlas:
        return {
            'recommended_mode': 'atlas',
            'reason': '保留图集单元格命名与 layout.json 布局契约，支持单格替换与边界校验。',
            'entrypoint': 'python <skill>/scripts/recipes/asset_toolkit.py deliver --mode atlas --source atlas.json --out-dir out --pack-zip out.zip',
            'fallback': 'python <skill>/scripts/pixel_art.py replace-cell --spec atlas.json --cell <name> --replacement cell.json --out next.json --image-out next.png --metadata layout.json',
            'warnings': ['若输入为裸 PNG 图集，必须附带 --metadata layout.json（或内嵌布局块）；裸 PNG 本身不携带缺失的格名语义。'],
        }
    if has_multistate and has_geom_change:
        return {
            'recommended_mode': 'state-set',
            'reason': '几何或 alpha 会跨状态变化（如开合、位移、局部补丁与回退），应使用薄语义补丁栈（分区域 allow_alpha_delta），不可强行使用锁 alpha 的共享网格。',
            'entrypoint': 'python <skill>/scripts/recipes/asset_toolkit.py deliver --mode state-set --source states.json --out-dir out --pack-zip out.zip',
            'fallback': '编译产物 specs/<state>.json 为标准 JSON v1，可随时用 pixel_art.py render 独立重建。',
            'warnings': ['在 state-set 中仅对允许轮廓/透明度变化的区域声明 allow_alpha_delta，其余区域自动锁定 alpha。'],
        }
    if has_multistate:
        return {
            'recommended_mode': 'shared-grid-states',
            'reason': '同轮廓、固定 alpha 且以局部换色为主的双态/多态素材，共享语义网格可在渲染前拦截 alpha 错配并收敛跨态改色。',
            'entrypoint': 'python <skill>/scripts/recipes/asset_toolkit.py deliver --mode shared-grid-states --source shared.json --out-dir out --pack-zip out.zip',
            'fallback': '若后续需要改轮廓、加复杂纹理（对偶符号 >24）或分层位移，请切换至 --mode state-set 或独立双源 JSON v1。',
            'warnings': ['严格模式默认锁定跨态 alpha；一旦涉及几何变化请改用 state-set。'],
        }
    if has_png_edit:
        return {
            'recommended_mode': 'png-native',
            'reason': '以无损 8-bit PNG 作为像素真相，直接执行区域/蒙版限定补丁或换色并核对掩码外零变更，跳过 PNG->JSON->PNG 往返与 62 色膨胀悬崖。',
            'entrypoint': 'python <skill>/scripts/recipes/asset_toolkit.py deliver --mode png-native --source input.png --allow-region X Y W H --recolor map.json --out-dir out',
            'fallback': 'python <skill>/scripts/pixel_art.py recolor / verify',
            'warnings': ['裸 PNG 不保存图层或图集格名；若需保留命名结构请提供 sidecar layout.json 或使用 atlas/assembly 模式。'],
        }
    return {
        'recommended_mode': 'grid',
        'reason': '新建小尺寸像素素材（建议 ≤32×32）使用短行 JSON v1 字符网格或整数绘图指令，易读、易 diff、可逐像素确定性重建。',
        'entrypoint': 'python <skill>/scripts/recipes/asset_toolkit.py deliver --mode grid --source sprite.json --out-dir out --pack-zip out.zip',
        'fallback': 'python <skill>/scripts/pixel_art.py render --spec sprite.json --out asset.png --preview nearest.png',
        'warnings': ['网格透明像素需在 palette 中显式声明（如 ".": null）；完成后请人工查看 native.png (1x) 与 nearest.png。'],
    }


def detect_source_mode(source, metadata=None):
    """Detect source mode explicitly from file type and schema; refuse ambiguous guesses."""
    source = Path(source)
    if not source.exists():
        raise PixelArtError(f'toolkit: source not found: {source}')
    suffix = source.suffix.lower()
    if suffix == '.png':
        opened = _read_static_png(source)
        meta_val = read_json(metadata) if metadata is not None else None
        merged, _ = merge_layout(opened, metadata=meta_val)
        if 'atlas' in merged:
            return 'atlas'
        return 'png-native'
    if suffix == '.json':
        data = read_json(source)
        if not isinstance(data, dict):
            raise PixelArtError('toolkit: expected a JSON object as source specification')
        kind = data.get('kind')
        if kind == 'shared-grid-states':
            return 'shared-grid-states'
        if kind == 'state-set':
            return 'state-set'
        if kind == 'atlas':
            return 'atlas'
        if kind in ('grid', 'draw'):
            return 'grid'
        if 'parts' in data and 'size' in data:
            return 'assembly'
        raise PixelArtError(
            f'toolkit: cannot infer source mode for JSON kind={kind!r}; '
            'specify --mode explicitly or use a supported schema '
            '(grid, draw, atlas, shared-grid-states, state-set, assembly project)'
        )
    raise PixelArtError(
        f'toolkit: unsupported source extension {suffix!r}; expected .json or .png'
    )


def _connected_components_8(rgba_bytes, width, height):
    """Return sorted list of 8-connected opaque/non-zero-alpha component sizes."""
    visited = bytearray(width * height)
    sizes = []
    for y in range(height):
        row_off = y * width
        for x in range(width):
            idx = row_off + x
            if visited[idx] or rgba_bytes[idx * 4 + 3] == 0:
                continue
            q = deque([(x, y)])
            visited[idx] = 1
            count = 0
            while q:
                cx, cy = q.popleft()
                count += 1
                for dy in (-1, 0, 1):
                    ny = cy + dy
                    if ny < 0 or ny >= height:
                        continue
                    nrow = ny * width
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = cx + dx
                        if 0 <= nx < width:
                            nidx = nrow + nx
                            if not visited[nidx] and rgba_bytes[nidx * 4 + 3] > 0:
                                visited[nidx] = 1
                                q.append((nx, ny))
            sizes.append(count)
    sizes.sort(reverse=True)
    return sizes


def _edge_spikes(rgba_bytes, width, height):
    """Detect thin 1px edge spikes on the image perimeter (for optional contract checks)."""
    spikes = []
    if width < 4 or height < 4:
        return spikes

    def opaque(x, y):
        return rgba_bytes[(y * width + x) * 4 + 3] > 0

    edges = [
        ('top', [opaque(x, 0) for x in range(width)], width),
        ('bottom', [opaque(x, height - 1) for x in range(width)], width),
        ('left', [opaque(0, y) for y in range(height)], height),
        ('right', [opaque(width - 1, y) for y in range(height)], height),
    ]
    for name, flags, span in edges:
        count = sum(flags)
        if 0 < count <= max(2, span // 16):
            spikes.append({'edge': name, 'pixels': count, 'span': span})
    return spikes


def analyze_advisory(image):
    """Compute non-blocking visual heuristic diagnostics (never auto-fails valid art)."""
    rgba = image.convert('RGBA')
    width, height = rgba.size
    raw = rgba.tobytes()
    px = pixels(rgba)
    opaque = 0
    semi = 0
    colors = set()
    for r, g, b, a in px:
        if a > 0:
            opaque += 1
            colors.add((r, g, b, a))
            if a < 255:
                semi += 1

    # 4-connected isolated pixels
    isolated = 0
    for y in range(height):
        for x in range(width):
            if raw[(y * width + x) * 4 + 3] == 0:
                continue
            has_neighbor = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if raw[(ny * width + nx) * 4 + 3] > 0:
                        has_neighbor = True
                        break
            if not has_neighbor:
                isolated += 1

    # Exact-RGBA 2x2 same-color opaque dark blocks (avoids luma false positives)
    double_blocks = 0
    for y in range(height - 1):
        for x in range(width - 1):
            c00 = raw[(y * width + x) * 4 : (y * width + x) * 4 + 4]
            if c00[3] == 0:
                continue
            if (
                c00 == raw[(y * width + x + 1) * 4 : (y * width + x + 1) * 4 + 4]
                and c00 == raw[((y + 1) * width + x) * 4 : ((y + 1) * width + x) * 4 + 4]
                and c00 == raw[((y + 1) * width + x + 1) * 4 : ((y + 1) * width + x + 1) * 4 + 4]
            ):
                # Only count very dark outline-like blocks (max channel <= 48)
                if max(c00[0], c00[1], c00[2]) <= 48:
                    double_blocks += 1

    components = _connected_components_8(raw, width, height)
    spikes = _edge_spikes(raw, width, height)
    hints = []
    if isolated:
        hints.append(
            f'{isolated} isolated 4-connected pixel(s) detected; verify whether intentional sparks/specks.'
        )
    if double_blocks:
        hints.append(
            f'{double_blocks} exact-color dark 2x2 block(s) detected; check for unintentional double-thick outlines.'
        )
    if len(components) > 1:
        hints.append(
            f'{len(components)} 8-connected opaque components ({components[:6]}); multi-component art is valid when intentional.'
        )
    if spikes:
        hints.append(
            f'Perimeter thin edge contact(s) detected: {spikes}; inspect at 1x to ensure no stray edge pixel.'
        )
    return {
        'size': [width, height],
        'opaque_pixels': opaque,
        'semi_transparent_pixels': semi,
        'unique_visible_rgba_colors': len(colors),
        'isolated_pixels_4conn': isolated,
        'dark_exact_2x2_blocks': double_blocks,
        'components_8conn_count': len(components),
        'components_8conn_sizes': components[:16],
        'perimeter_edge_spikes': spikes,
        'hints': hints,
        'human_visual_check_required': True,
        'note': 'Advisory heuristics only; never blocks valid multi-component or stylized pixel art. Inspect 1x and nearest-neighbor previews on target background.',
    }


def check_declared_contract(image, contract):
    """Evaluate optional user-declared structural contract rules; returns (passed, failures, details)."""
    if not contract:
        return True, [], {'declared': False}
    if not isinstance(contract, dict):
        raise PixelArtError('contract: expected a JSON object')
    rgba = image.convert('RGBA')
    width, height = rgba.size
    raw = rgba.tobytes()
    failures = []
    details = {'declared': True}

    if 'size' in contract:
        expected = contract['size']
        if list(rgba.size) != list(expected):
            failures.append(f'size mismatch: expected {expected}, got {[width, height]}')
        details['size'] = [width, height]

    if contract.get('binary_alpha'):
        bad_alpha = sum(1 for i in range(3, len(raw), 4) if raw[i] not in (0, 255))
        details['non_binary_alpha_pixels'] = bad_alpha
        if bad_alpha:
            failures.append(f'binary_alpha violated: {bad_alpha} semi-transparent pixel(s)')

    if 'max_colors' in contract:
        max_colors = integer(contract['max_colors'], 'contract.max_colors', 1)
        vis = {raw[i : i + 4] for i in range(0, len(raw), 4) if raw[i + 3] > 0}
        details['visible_colors'] = len(vis)
        if len(vis) > max_colors:
            failures.append(f'max_colors violated: {len(vis)} > {max_colors}')

    if 'transparent_margin' in contract:
        margin = integer(contract['transparent_margin'], 'contract.transparent_margin', 0)
        if margin > 0:
            bbox = rgba.getchannel('A').getbbox()
            if bbox is not None:
                x0, y0, x1, y1 = bbox
                if x0 < margin or y0 < margin or (width - x1) < margin or (height - y1) < margin:
                    failures.append(
                        f'transparent_margin={margin} violated: opaque bbox {[x0, y0, x1 - x0, y1 - y0]}'
                    )
            details['transparent_margin'] = margin

    if 'max_components' in contract:
        max_comp = integer(contract['max_components'], 'contract.max_components', 1)
        comps = _connected_components_8(raw, width, height)
        details['components_8conn'] = len(comps)
        if len(comps) > max_comp:
            failures.append(
                f'max_components violated: {len(comps)} components ({comps[:6]}) > {max_comp}'
            )

    if contract.get('no_edge_spikes'):
        spikes = _edge_spikes(raw, width, height)
        details['edge_spikes'] = spikes
        if spikes:
            failures.append(f'no_edge_spikes violated: {spikes}')

    return len(failures) == 0, failures, details


def _alpha_diff_stats(before_img, after_img, allowed_regions=None):
    """Compare alpha channels between two same-size RGBA images, optionally with allowed regions."""
    a_img = before_img.convert('RGBA')
    b_img = after_img.convert('RGBA')
    if a_img.size != b_img.size:
        raise PixelArtError('alpha comparison: image dimensions must match')
    width, height = a_img.size
    a_alpha = a_img.getchannel('A').tobytes()
    b_alpha = b_img.getchannel('A').tobytes()
    allowed_bytes = None
    if allowed_regions is not None:
        if allowed_regions == 'all':
            allowed_bytes = bytes([255]) * (width * height)
        elif allowed_regions:
            allowed_bytes = _allowed_mask(
                (width, height), allowed_regions, None, 'alpha_contract'
            ).tobytes()
        else:
            allowed_bytes = bytes(width * height)

    total_diff = 0
    outside_diff = 0
    outside_samples = []
    for idx, (va, vb) in enumerate(zip(a_alpha, b_alpha)):
        if va != vb:
            total_diff += 1
            if allowed_bytes is not None and not allowed_bytes[idx]:
                outside_diff += 1
                if len(outside_samples) < 32:
                    outside_samples.append([idx % width, idx // width])
    return {
        'alpha_changed_pixels': total_diff,
        'alpha_changed_outside': outside_diff,
        'outside_samples': outside_samples,
    }


def _make_diff_image(before_img, after_img):
    """Build an RGBA highlight image showing unchanged pixels dimmed and changed pixels bright."""
    a = before_img.convert('RGBA')
    b = after_img.convert('RGBA')
    w, h = a.size
    raw_a = a.tobytes()
    raw_b = b.tobytes()
    out = bytearray(len(raw_b))
    for i in range(0, len(raw_b), 4):
        if raw_a[i : i + 4] != raw_b[i : i + 4]:
            # Magenta highlight for changed RGBA, yellow if alpha changed
            if raw_a[i + 3] != raw_b[i + 3]:
                out[i : i + 4] = bytes((255, 210, 60, 255))
            else:
                out[i : i + 4] = bytes((255, 70, 170, 255))
        else:
            out[i : i + 4] = bytes((raw_b[i] // 3, raw_b[i + 1] // 3, raw_b[i + 2] // 3, 255 if raw_b[i + 3] else 40))
    return Image.frombytes('RGBA', (w, h), bytes(out))


def _make_strip(labeled_images, scale, background):
    """Render a side-by-side nearest-neighbor comparison strip for multi-state assets."""
    if not labeled_images:
        raise PixelArtError('toolkit: cannot build comparison strip for empty state list')
    gap = 8
    header = 16 if scale >= 2 else 0
    cards = [make_preview(img, scale, background).convert('RGBA') for _, img in labeled_images]
    total_w = sum(c.width for c in cards) + gap * (len(cards) - 1) + 2 * gap
    max_h = max(c.height for c in cards)
    bg_rgba = color('172033') if background == 'checker' else color(background)
    strip = Image.new('RGBA', (total_w, max_h + header + 2 * gap), bg_rgba)
    draw = ImageDraw.Draw(strip)
    x = gap
    for (label, _), card in zip(labeled_images, cards):
        if header:
            draw.text((x, gap // 2), str(label)[:20], fill=(240, 244, 248, 255))
        strip.paste(card, (x, gap + header))
        x += card.width + gap
    return strip


def _apply_png_patch(base_image, patch_spec, *, regions=None, mask=None):
    """Apply explicit pixel/rect patches inside declared regions/mask with preflight checks."""
    if not isinstance(patch_spec, dict) or not isinstance(patch_spec.get('ops'), list):
        raise PixelArtError('patch: expected a JSON object with an "ops" list')
    rgba = base_image.convert('RGBA')
    width, height = rgba.size
    allowed = _allowed_mask((width, height), regions, mask, 'patch')
    perm = allowed.tobytes()
    raw = bytearray(rgba.tobytes())
    orig = bytes(raw)

    rejected = []
    noop_ops = 0
    applied_pixels = 0

    for idx, op in enumerate(patch_spec['ops']):
        if not isinstance(op, dict):
            raise PixelArtError(f'patch.ops[{idx}]: expected an operation object')
        kind = op.get('op', 'pixel')
        rgba_val = bytes(color(op.get('color')))
        coords = []
        if kind == 'pixel':
            x, y = op.get('x'), op.get('y')
            if type(x) is not int or type(y) is not int:
                raise PixelArtError(f'patch.ops[{idx}]: pixel requires integer x and y')
            coords = [(x, y)]
        elif kind == 'points':
            pts = op.get('points')
            if not isinstance(pts, list) or not pts:
                raise PixelArtError(f'patch.ops[{idx}]: points requires a non-empty list')
            for p in pts:
                if not isinstance(p, (list, tuple)) or len(p) != 2 or type(p[0]) is not int or type(p[1]) is not int:
                    raise PixelArtError(f'patch.ops[{idx}]: invalid point {p!r}')
                coords.append((p[0], p[1]))
        elif kind == 'rect':
            x, y, w, h = _box([op.get('x'), op.get('y'), op.get('w'), op.get('h')], (width, height), f'patch.ops[{idx}]')
            coords = [(cx, cy) for cy in range(y, y + h) for cx in range(x, x + w)]
        else:
            raise PixelArtError(f'patch.ops[{idx}]: unsupported op {kind!r}; use pixel, points or rect')

        op_changed = 0
        for cx, cy in coords:
            if not (0 <= cx < width and 0 <= cy < height):
                rejected.append({'op_index': idx, 'coord': [cx, cy], 'reason': 'out_of_bounds'})
                continue
            if not perm[cy * width + cx]:
                rejected.append({'op_index': idx, 'coord': [cx, cy], 'reason': 'outside_allowed_scope'})
                continue
            off = (cy * width + cx) * 4
            if raw[off : off + 4] != rgba_val:
                raw[off : off + 4] = rgba_val
                op_changed += 1
                applied_pixels += 1
        if op_changed == 0 and not rejected:
            noop_ops += 1

    if rejected:
        raise ContractViolationError(
            f'patch preflight rejected {len(rejected)} pixel write(s) outside allowed bounds/mask '
            f'(first: {rejected[0]})',
            report={'rejected': rejected[:32], 'rejected_count': len(rejected)},
        )

    candidate = Image.frombytes('RGBA', (width, height), bytes(raw))
    changed_total = sum(
        1 for i in range(0, len(raw), 4) if raw[i : i + 4] != orig[i : i + 4]
    )
    return candidate, {
        'applied_pixel_writes': applied_pixels,
        'changed_rgba_pixels': changed_total,
        'noop_ops': noop_ops,
        'rejected_count': 0,
    }


def compile_shared_grid_states(spec):
    """Validate and compile a shared-grid-states spec into standard JSON v1 grid specs."""
    if not isinstance(spec, dict) or spec.get('kind') != 'shared-grid-states':
        raise PixelArtError('shared-grid-states: expected kind="shared-grid-states"')
    rows = spec.get('rows')
    if not isinstance(rows, list) or not rows or not all(isinstance(r, str) and r for r in rows):
        raise PixelArtError('shared-grid-states: rows must be a non-empty list of equal-length strings')
    width = len(rows[0])
    if any(len(r) != width for r in rows):
        raise PixelArtError('shared-grid-states: all rows must have identical width')
    dimensions((width, len(rows)))

    base_palette = spec.get('base_palette', {})
    if not isinstance(base_palette, dict):
        raise PixelArtError('shared-grid-states: base_palette must be an object')
    states = spec.get('states')
    if not isinstance(states, dict) or not states:
        raise PixelArtError('shared-grid-states: states must be a non-empty object')
    _validate_state_names(states, 'shared-grid-states')
    allow_alpha_diff = bool(spec.get('allow_alpha_diff', False))

    used_symbols = sorted({ch for row in rows for ch in row})
    if len(used_symbols) > 88:
        raise PixelArtError(
            f'shared-grid-states: {len(used_symbols)} symbols exceeds safe ASCII grid limit (88); '
            'use --mode state-set or independent JSON v1 specs instead'
        )

    compiled = {}
    symbol_alphas = {}
    for state_name, overrides in states.items():
        if not isinstance(overrides, dict):
            raise PixelArtError(f'shared-grid-states: state {state_name!r} palette must be an object')
        merged_palette = {**base_palette, **overrides}
        missing = [sym for sym in used_symbols if sym not in merged_palette]
        if missing:
            raise PixelArtError(
                f'shared-grid-states: state {state_name!r} missing palette symbol(s): {missing}'
            )
        for sym in used_symbols:
            rgba = color(merged_palette[sym])
            alpha = rgba[3]
            if sym not in symbol_alphas:
                symbol_alphas[sym] = (state_name, alpha)
            elif not allow_alpha_diff and symbol_alphas[sym][1] != alpha:
                first_state, first_alpha = symbol_alphas[sym]
                raise ContractViolationError(
                    f'shared-grid-states preflight: symbol {sym!r} alpha changed '
                    f'({first_state}={first_alpha} -> {state_name}={alpha}); '
                    'for geometry/alpha changes use --mode state-set instead of relaxing shared-grid alpha lock',
                    report={
                        'symbol': sym,
                        'first_state': first_state,
                        'first_alpha': first_alpha,
                        'conflict_state': state_name,
                        'conflict_alpha': alpha,
                    },
                )
        compiled[state_name] = {
            'version': 1,
            'kind': 'grid',
            'size': [width, len(rows)],
            'palette': {sym: merged_palette[sym] for sym in used_symbols},
            'rows': list(rows),
        }

    warnings = []
    if len(used_symbols) > 24:
        warnings.append(
            f'shared-grid-states uses {len(used_symbols)} symbols (>24); consider --mode state-set for complex texture divergence.'
        )
    return compiled, {'used_symbols': len(used_symbols), 'allow_alpha_diff': allow_alpha_diff, 'warnings': warnings}


def compile_state_set(spec, *, disabled_patches=None):
    """Compile a thin semantic state-set IR to standard JSON v1 specs + rendered images.

    Order of operations per state (invariant):
    1. Apply enabled patches in declared order (supporting local rollback via enabled=false or --disable-patch).
    2. Apply region_recolor after patches so recolor covers patched geometry consistently.
    3. Verify per-region allow_alpha_delta against base image.
    """
    if not isinstance(spec, dict) or spec.get('kind') != 'state-set':
        raise PixelArtError('state-set: expected kind="state-set"')
    base_spec = spec.get('base')
    if not isinstance(base_spec, dict):
        raise PixelArtError('state-set: base must be a valid JSON v1 spec')
    base_img = render(base_spec).convert('RGBA')
    width, height = base_img.size

    regions_decl = spec.get('regions', {})
    if not isinstance(regions_decl, dict):
        raise PixelArtError('state-set: regions must be a mapping of name -> [x, y, w, h]')
    validated_regions = {}
    for rname, rect in regions_decl.items():
        validated_regions[rname] = list(_box(rect, (width, height), f'state-set.regions.{rname}'))

    states = spec.get('states')
    if not isinstance(states, dict) or not states:
        raise PixelArtError('state-set: states must be a non-empty object')
    _validate_state_names(states, 'state-set')

    disabled_set = set(disabled_patches or [])
    compiled_specs = {}
    rendered_images = {}
    state_reports = {}

    for state_name, state_cfg in states.items():
        if not isinstance(state_cfg, dict):
            raise PixelArtError(f'state-set: state {state_name!r} must be an object')
        img = base_img.copy()
        applied_patch_ids = []
        skipped_patch_ids = []

        # Step 1: Patches first
        for pidx, patch in enumerate(state_cfg.get('patches', [])):
            if not isinstance(patch, dict):
                raise PixelArtError(f'state-set.{state_name}.patches[{pidx}]: expected object')
            pid = str(patch.get('id', f'patch_{pidx}'))
            if patch.get('enabled', True) is False or pid in disabled_set:
                skipped_patch_ids.append(pid)
                continue
            rname = patch.get('region')
            if rname is not None:
                if rname not in validated_regions:
                    raise PixelArtError(
                        f'state-set.{state_name}.patches[{pidx}]: unknown region {rname!r}'
                    )
                scope = [validated_regions[rname]]
            else:
                scope = [[0, 0, width, height]]
            img, _ = _apply_png_patch(img, {'ops': patch.get('ops', [])}, regions=scope)
            applied_patch_ids.append(pid)

        # Recolor patched pixels along with the original pixels in each region.
        for ridx, rc in enumerate(state_cfg.get('region_recolor', [])):
            if not isinstance(rc, dict):
                raise PixelArtError(f'state-set.{state_name}.region_recolor[{ridx}]: expected object')
            rnames = rc.get('regions') or ([rc['region']] if 'region' in rc else None)
            if rnames is None:
                scope = [[0, 0, width, height]]
            else:
                scope = []
                for rn in rnames:
                    if rn not in validated_regions:
                        raise PixelArtError(
                            f'state-set.{state_name}.region_recolor[{ridx}]: unknown region {rn!r}'
                        )
                    scope.append(validated_regions[rn])
            mapping = rc.get('map')
            if not mapping:
                raise PixelArtError(f'state-set.{state_name}.region_recolor[{ridx}]: map is required')
            img, _ = recolor_image(img, mapping, regions=scope)

        # Step 3: Per-region alpha delta contract
        alpha_decl = state_cfg.get('allow_alpha_delta', [])
        if alpha_decl is True:
            alpha_scope = 'all'
        elif alpha_decl is False or alpha_decl is None:
            alpha_scope = []
        elif isinstance(alpha_decl, list):
            alpha_scope = []
            for rn in alpha_decl:
                if rn not in validated_regions:
                    raise PixelArtError(
                        f'state-set.{state_name}.allow_alpha_delta: unknown region {rn!r}'
                    )
                alpha_scope.append(validated_regions[rn])
        else:
            raise PixelArtError(
                f'state-set.{state_name}.allow_alpha_delta: expected list of region names or boolean'
            )

        alpha_stats = _alpha_diff_stats(base_img, img, allowed_regions=alpha_scope)
        if alpha_stats['alpha_changed_outside'] > 0:
            raise ContractViolationError(
                f'state-set contract failed for state {state_name!r}: '
                f'{alpha_stats["alpha_changed_outside"]} alpha change(s) outside declared allow_alpha_delta '
                f'regions {alpha_decl!r} (samples: {alpha_stats["outside_samples"][:5]})',
                report={'state': state_name, **alpha_stats},
            )

        # Compile to standard JSON v1 so user can always fall back to pixel_art.py render
        v1_spec = image_to_spec(img)
        if render(v1_spec).tobytes() != img.tobytes():
            raise PixelArtError(
                f'state-set: compiled JSON v1 for state {state_name!r} failed exact RGBA rebuild'
            )

        diff_count = sum(
            1
            for i in range(0, width * height * 4, 4)
            if base_img.tobytes()[i : i + 4] != img.tobytes()[i : i + 4]
        )
        compiled_specs[state_name] = v1_spec
        rendered_images[state_name] = img
        state_reports[state_name] = {
            'applied_patches': applied_patch_ids,
            'skipped_patches': skipped_patch_ids,
            'changed_rgba_from_base': diff_count,
            'alpha_changed_from_base': alpha_stats['alpha_changed_pixels'],
            'alpha_changed_outside_declared': alpha_stats['alpha_changed_outside'],
            'rgba_sha256': rgba_digest(img),
        }

    return compiled_specs, rendered_images, state_reports


def _pack_zip_bytes(file_map):
    """Build deterministic ZIP bytes and verify CRC immediately."""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for rel_name in sorted(file_map):
            info = zipfile.ZipInfo(rel_name, date_time=ZIP_TIMESTAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, file_map[rel_name], compress_type=zipfile.ZIP_DEFLATED)
    data = buffer.getvalue()
    with zipfile.ZipFile(BytesIO(data), 'r') as verify_arc:
        bad = verify_arc.testzip()
        if bad is not None:
            raise PixelArtError(f'toolkit: ZIP CRC verification failed on member {bad!r}')
    return data


def _rebuild_guide(mode, primary_cmd, *, primary_note=None):
    note = f'{primary_note}\n\n' if primary_note else ''
    return (
        f'# Rebuild Guide ({mode})\n\n'
        'This bundle contains the editable source(s), delivered RGBA PNG(s), '
        '1x and integer nearest-neighbor previews, and SHA-256 manifest.\n\n'
        '## Verify & Independently Rebuild with Toolkit\n\n'
        '```text\n'
        'python "<skill>/scripts/recipes/asset_toolkit.py" rebuild --input . --out-dir rebuilt-check\n'
        '```\n\n'
        '## Native Core Fallback (Zero Toolkit Lock-In)\n\n'
        f'{note}'
        f'```text\n{primary_cmd}\n```\n'
    ).encode('utf-8')


def deliver_asset(
    source,
    out_dir,
    *,
    mode='auto',
    metadata=None,
    baseline=None,
    allow_regions=None,
    mask=None,
    recolor_path=None,
    patch_path=None,
    allow_alpha_change=False,
    replace_cell_name=None,
    replacement_path=None,
    disabled_patches=None,
    contract_path=None,
    scale=4,
    background='checker',
    pack_zip=None,
    extra_files=None,
    force=False,
    portable=False,
):
    """Execute end-to-end delivery for any supported source mode with 3-tier verification."""
    require_pillow()
    source = Path(source)
    out_dir = Path(out_dir)
    integer(scale, 'scale', 1)
    if background != 'checker':
        color(background)
    if mode not in SUPPORTED_MODES:
        raise PixelArtError(f'toolkit: unsupported mode {mode!r}; choose from {SUPPORTED_MODES}')

    input_paths = [source]
    input_paths.extend(
        path
        for path in (
            baseline,
            metadata,
            mask,
            recolor_path,
            patch_path,
            replacement_path,
            contract_path,
            *(extra_files or []),
        )
        if path is not None
    )

    resolved_mode = detect_source_mode(source, metadata=metadata) if mode == 'auto' else mode
    contract = read_json(contract_path) if contract_path is not None else None

    files = {}
    required_checks = {'pillow_compatible': True, 'rgba_8bit': True, 'rebuild_verified': False}
    contract_checks = {'passed': True, 'failures': [], 'details': {}}
    advisory_report = {}
    manifest = {
        'toolkit_version': TOOLKIT_VERSION,
        'mode': resolved_mode,
        'source_name': source.name,
        'outputs': {},
    }

    if resolved_mode == 'grid':
        spec = read_json(source)
        if not isinstance(spec, dict) or spec.get('kind') not in ('grid', 'draw'):
            raise PixelArtError('grid mode: expected a JSON v1 grid or draw spec')
        image = render(spec).convert('RGBA')
        _check_preview_scale(image.size, scale)
        # Independent rebuild check
        rebuilt = render(json.loads(json.dumps(spec))).convert('RGBA')
        if rebuilt.tobytes() != image.tobytes():
            raise PixelArtError('grid mode: independent rebuild mismatch')
        required_checks['rebuild_verified'] = True
        passed, failures, cdet = check_declared_contract(image, contract)
        contract_checks = {'passed': passed, 'failures': failures, 'details': cdet}
        if not passed:
            raise ContractViolationError('; '.join(failures), report=contract_checks)
        advisory_report = analyze_advisory(image)
        files['asset.json'] = encoded(spec)
        files['asset.png'] = encoded(image)
        files['native.png'] = encoded(make_preview(image, 1, background))
        files['nearest.png'] = encoded(make_preview(image, scale, background))
        files['REBUILD.md'] = _rebuild_guide(
            'grid',
            'python "<skill>/scripts/pixel_art.py" render --spec asset.json --out rebuilt.png',
        )
        manifest['rgba_sha256'] = {'asset.png': rgba_digest(image)}

    elif resolved_mode == 'png-native':
        opened = _read_static_png(source)
        meta_val = read_json(metadata) if metadata is not None else None
        merged_layout, _ = merge_layout(opened, metadata=meta_val)
        if 'atlas' in merged_layout:
            raise PixelArtError(
                'png-native: named atlas metadata detected; use --mode atlas to preserve cell names'
            )
        src_rgba = opened.convert('RGBA')
        _check_preview_scale(src_rgba.size, scale)
        mask_img = _read_static_png(mask) if mask is not None else None

        edited = False
        edit_report = {}
        base_img = _read_static_png(baseline).convert('RGBA') if baseline is not None else src_rgba
        candidate = src_rgba

        if recolor_path is not None and patch_path is not None:
            raise PixelArtError('png-native: choose either --recolor or --patch per step, not both')
        if recolor_path is not None:
            mapping = read_json(recolor_path)
            candidate, edit_report = recolor_image(
                src_rgba, mapping, regions=allow_regions, mask=mask_img
            )
            edited = True
        elif patch_path is not None:
            patch_spec = read_json(patch_path)
            candidate, edit_report = _apply_png_patch(
                src_rgba, patch_spec, regions=allow_regions, mask=mask_img
            )
            edited = True
        elif baseline is not None:
            edited = True

        # Boundary & alpha contract check whenever edited or baseline provided
        contract_failures = []
        contract_details = {'edit_operation': edit_report or None}
        if edited:
            if allow_regions or mask_img is not None:
                vrep = verify_edit(candidate, base_img, regions=allow_regions, mask=mask_img)
                contract_details['boundary'] = vrep
                if not vrep['valid']:
                    contract_failures.append(
                        f'edit boundary violated: {vrep["changed_outside"]} RGBA pixel(s) changed outside '
                        f'allowed region/mask (bbox={vrep["outside_bbox"]}, samples={vrep["outside_samples"][:5]})'
                    )
            alpha_stats = _alpha_diff_stats(base_img, candidate)
            contract_details['alpha'] = alpha_stats
            if not allow_alpha_change and alpha_stats['alpha_changed_pixels'] > 0:
                contract_failures.append(
                    f'alpha lock violated: {alpha_stats["alpha_changed_pixels"]} pixel(s) changed alpha; '
                    'pass --allow-alpha-change if contour/transparency changes are intended'
                )

        c_ok, c_fail, c_det = check_declared_contract(candidate, contract)
        contract_failures.extend(c_fail)
        contract_details['declared_contract'] = c_det
        contract_checks = {
            'passed': len(contract_failures) == 0,
            'failures': contract_failures,
            'details': contract_details,
        }
        if not contract_checks['passed']:
            raise ContractViolationError('; '.join(contract_failures), report=contract_checks)

        # PNG-native round-trip check (encode -> decode RGBA exact match, no JSON grid forced!)
        png_bytes = encoded(candidate)
        with Image.open(BytesIO(png_bytes), formats=('PNG',)) as rt:
            if rt.convert('RGBA').tobytes() != candidate.tobytes():
                raise PixelArtError('png-native: PNG encode/decode RGBA mismatch')
        required_checks['rebuild_verified'] = True
        advisory_report = analyze_advisory(candidate)
        advisory_report['png_native_note'] = (
            'Bare PNG does not store atlas cell names or layers; keep sidecar layout.json or project.json if structural semantics are required.'
        )

        files['asset.png'] = png_bytes
        files['native.png'] = encoded(make_preview(candidate, 1, background))
        files['nearest.png'] = encoded(make_preview(candidate, scale, background))
        if edited:
            files['baseline.png'] = encoded(base_img)
            files['edit-diff.png'] = encoded(
                make_preview(_make_diff_image(base_img, candidate), scale, '172033')
            )
        if metadata is not None:
            files['sidecar-metadata.json'] = encoded(meta_val)
        verify_command = 'python "<skill>/scripts/recipes/asset_toolkit.py" verify --image asset.png'
        if edited:
            verify_command += ' --baseline baseline.png'
            if allow_alpha_change:
                verify_command += ' --allow-alpha-change'
            for region in allow_regions or []:
                verify_command += ' --allow-region ' + ' '.join(str(value) for value in region)
            if mask is not None:
                files['edit-mask.png'] = Path(mask).read_bytes()
                verify_command += ' --mask edit-mask.png'
            if allow_regions or mask is not None:
                verify_note = (
                    'This compares asset.png with baseline.png and checks that edits stay within '
                    'the declared region or the bundled edit mask.'
                )
            else:
                verify_note = (
                    'This compares asset.png with baseline.png and enforces the alpha-change '
                    'contract. No spatial edit boundary was declared.'
                )
        else:
            verify_note = 'This checks the delivered PNG. Pixel comparison requires a baseline.'
        if contract_path is not None:
            files['contract.json'] = json.dumps(contract, ensure_ascii=False, indent=2).encode('utf-8')
            verify_command += ' --contract contract.json'
            verify_note += ' This also checks the bundled structure contract.'
        files['REBUILD.md'] = _rebuild_guide(
            'png-native', verify_command, primary_note=verify_note
        )
        manifest['rgba_sha256'] = {'asset.png': rgba_digest(candidate)}
        manifest['edited'] = edited

    elif resolved_mode == 'shared-grid-states':
        raw_spec = read_json(source)
        compiled, info = compile_shared_grid_states(raw_spec)
        labeled = []
        state_hashes = {}
        state_advisories = {}
        contract_failures = []
        for sname, v1_spec in compiled.items():
            img = render(v1_spec).convert('RGBA')
            _check_preview_scale(img.size, scale)
            rebuilt = render(json.loads(json.dumps(v1_spec))).convert('RGBA')
            if rebuilt.tobytes() != img.tobytes():
                raise PixelArtError(f'shared-grid-states: state {sname!r} rebuild mismatch')
            c_ok, c_fail, _ = check_declared_contract(img, contract)
            if not c_ok:
                contract_failures.extend([f'{sname}: {msg}' for msg in c_fail])
            files[f'specs/{sname}.json'] = encoded(v1_spec)
            files[f'states/{sname}.png'] = encoded(img)
            state_hashes[f'states/{sname}.png'] = rgba_digest(img)
            state_advisories[sname] = analyze_advisory(img)
            labeled.append((sname, img))

        if contract_failures:
            raise ContractViolationError('; '.join(contract_failures), report={'failures': contract_failures})

        required_checks['rebuild_verified'] = True
        contract_checks = {'passed': True, 'failures': [], 'details': info}
        advisory_report = {'states': state_advisories, 'compiler_warnings': info['warnings']}
        files['source-shared.json'] = encoded(raw_spec)
        files['comparison-1x.png'] = encoded(_make_strip(labeled, 1, background))
        files['comparison-nearest.png'] = encoded(_make_strip(labeled, scale, background))
        files['REBUILD.md'] = _rebuild_guide(
            'shared-grid-states',
            'python "<skill>/scripts/pixel_art.py" render --spec specs/<state>.json --out rebuilt-<state>.png',
        )
        manifest['states'] = list(compiled.keys())
        manifest['rgba_sha256'] = state_hashes

    elif resolved_mode == 'state-set':
        raw_spec = read_json(source)
        compiled, rendered, sreports = compile_state_set(
            raw_spec, disabled_patches=disabled_patches
        )
        labeled = []
        state_hashes = {}
        state_advisories = {}
        contract_failures = []
        for sname, v1_spec in compiled.items():
            img = rendered[sname]
            _check_preview_scale(img.size, scale)
            rebuilt = render(json.loads(json.dumps(v1_spec))).convert('RGBA')
            if rebuilt.tobytes() != img.tobytes():
                raise PixelArtError(f'state-set: state {sname!r} rebuild mismatch')
            c_ok, c_fail, _ = check_declared_contract(img, contract)
            if not c_ok:
                contract_failures.extend([f'{sname}: {msg}' for msg in c_fail])
            files[f'specs/{sname}.json'] = encoded(v1_spec)
            files[f'states/{sname}.png'] = encoded(img)
            state_hashes[f'states/{sname}.png'] = rgba_digest(img)
            state_advisories[sname] = analyze_advisory(img)
            labeled.append((sname, img))

        if contract_failures:
            raise ContractViolationError('; '.join(contract_failures), report={'failures': contract_failures})

        required_checks['rebuild_verified'] = True
        contract_checks = {'passed': True, 'failures': [], 'details': sreports}
        advisory_report = {'states': state_advisories}
        files['source-states.json'] = encoded(raw_spec)
        files['comparison-1x.png'] = encoded(_make_strip(labeled, 1, background))
        files['comparison-nearest.png'] = encoded(_make_strip(labeled, scale, background))
        files['REBUILD.md'] = _rebuild_guide(
            'state-set',
            'python "<skill>/scripts/pixel_art.py" render --spec specs/<state>.json --out rebuilt-<state>.png',
        )
        manifest['states'] = list(compiled.keys())
        manifest['disabled_patches'] = sorted(disabled_patches or [])
        manifest['rgba_sha256'] = state_hashes

    elif resolved_mode == 'atlas':
        if source.suffix.lower() == '.png':
            opened = _read_static_png(source)
            meta_val = read_json(metadata) if metadata is not None else None
            merged_layout, _ = merge_layout(opened, metadata=meta_val)
            if 'atlas' not in merged_layout:
                raise PixelArtError(
                    'atlas mode: PNG lacks named atlas metadata; pass --metadata <layout.json> '
                    '(a bare PNG does not carry missing cell names)'
                )
            atlas_spec = image_to_spec(opened, metadata=meta_val)
        else:
            atlas_spec = read_json(source)
            if not isinstance(atlas_spec, dict) or atlas_spec.get('kind') != 'atlas':
                raise PixelArtError('atlas mode: expected a JSON v1 atlas spec or PNG + layout metadata')

        before_img = render(atlas_spec).convert('RGBA')
        final_spec = atlas_spec
        replace_report = None
        if replace_cell_name is not None:
            if replacement_path is None:
                raise PixelArtError('atlas mode: --replace-cell requires --replacement <spec.json>')
            rep_spec = read_json(replacement_path)
            final_spec = replace_cell(atlas_spec, replace_cell_name, rep_spec)
            after_img = render(final_spec).convert('RGBA')
            layout_after = layout_record(after_img)
            cell_entry = next(
                c for c in layout_after['atlas']['cells'] if c['name'] == replace_cell_name
            )
            if 'rect' in cell_entry:
                cell_rect = cell_entry['rect']
            elif 'x' in cell_entry:
                cell_rect = [cell_entry['x'], cell_entry['y'], cell_entry['w'], cell_entry['h']]
            else:
                cell_w, cell_h = layout_after['atlas']['cell_size']
                cell_rect = [cell_entry['at'][0], cell_entry['at'][1], cell_w, cell_h]
            vrep = verify_edit(after_img, before_img, regions=[cell_rect])
            if not vrep['valid']:
                raise ContractViolationError(
                    f'atlas replace-cell violated cell boundary: {vrep["changed_outside"]} outside pixel(s)',
                    report=vrep,
                )
            replace_report = {'cell': replace_cell_name, 'cell_rect': cell_rect, 'verify': vrep}
        else:
            after_img = before_img

        _check_preview_scale(after_img.size, scale)
        rebuilt = render(json.loads(json.dumps(final_spec))).convert('RGBA')
        if rebuilt.tobytes() != after_img.tobytes():
            raise PixelArtError('atlas mode: independent rebuild mismatch')
        layout_after = layout_record(after_img)
        cell_names = [c['name'] for c in layout_after['atlas']['cells']]
        c_ok, c_fail, c_det = check_declared_contract(after_img, contract)
        if not c_ok:
            raise ContractViolationError('; '.join(c_fail), report={'failures': c_fail, 'details': c_det})

        required_checks['rebuild_verified'] = True
        contract_checks = {
            'passed': True,
            'failures': [],
            'details': {'cell_names': cell_names, 'replace_cell': replace_report, 'declared_contract': c_det},
        }
        advisory_report = analyze_advisory(after_img)
        files['atlas.json'] = encoded(final_spec)
        files['asset.png'] = encoded(after_img)
        files['layout.json'] = encoded(layout_after)
        files['native.png'] = encoded(make_preview(after_img, 1, background))
        files['nearest.png'] = encoded(make_preview(after_img, scale, background))
        if replace_report is not None:
            files['edit-diff.png'] = encoded(
                make_preview(_make_diff_image(before_img, after_img), scale, '172033')
            )
        files['REBUILD.md'] = _rebuild_guide(
            'atlas',
            'python "<skill>/scripts/pixel_art.py" render --spec atlas.json --out rebuilt.png --metadata rebuilt-layout.json',
        )
        manifest['cell_names'] = cell_names
        manifest['rgba_sha256'] = {'asset.png': rgba_digest(after_img)}

    elif resolved_mode == 'assembly':
        project, sources, layer_paths = load_project(source)
        input_paths.extend(layer_paths)
        assembled, asm_report = assemble(project, sources)
        _check_preview_scale(assembled.size, scale)
        seams_img = seam_sheet(assembled, asm_report)

        # Build self-contained relocatable layers/ directory preserving layer names & files
        relocated_project = deepcopy(project)
        name_map = {}
        used_rel = set()
        for part in relocated_project['parts']:
            orig_rel = part['image']
            if orig_rel not in name_map:
                safe_name = Path(orig_rel).name
                while safe_name in used_rel:
                    safe_name = 'layer_' + safe_name
                used_rel.add(safe_name)
                name_map[orig_rel] = safe_name
                files[f'layers/{safe_name}'] = encoded(sources[orig_rel])
            part['image'] = name_map[orig_rel]
        files['layers/project.json'] = encoded(relocated_project)

        # Independent rebuild from relocated project & layer bytes
        rebuilt_sources = {
            safe: Image.open(BytesIO(files[f'layers/{safe}'])).convert('RGBA')
            for safe in name_map.values()
        }
        rebuilt_img, _ = assemble(relocated_project, rebuilt_sources)
        if rebuilt_img.tobytes() != assembled.tobytes():
            raise PixelArtError('assembly mode: independent relocated rebuild mismatch')

        c_ok, c_fail, c_det = check_declared_contract(assembled, contract)
        if not c_ok:
            raise ContractViolationError('; '.join(c_fail), report={'failures': c_fail, 'details': c_det})

        required_checks['rebuild_verified'] = True
        contract_checks = {
            'passed': True,
            'failures': [],
            'details': {
                'part_names': [p['name'] for p in relocated_project['parts']],
                'layer_files': sorted(name_map.values()),
                'seam_count': asm_report['seam_count'],
                'declared_contract': c_det,
            },
        }
        advisory_report = analyze_advisory(assembled)
        files['asset.png'] = encoded(assembled)
        files['assembly-report.json'] = encoded(asm_report)
        files['seams.png'] = encoded(seams_img)
        files['native.png'] = encoded(make_preview(assembled, 1, background))
        files['nearest.png'] = encoded(make_preview(assembled, scale, background))
        files['REBUILD.md'] = _rebuild_guide(
            'assembly',
            'python "<skill>/scripts/pixel_art.py" assemble --project layers/project.json --out rebuilt.png --seams rebuilt-seams.png',
        )
        manifest['part_names'] = [p['name'] for p in relocated_project['parts']]
        manifest['layer_files'] = sorted(name_map.values())
        manifest['rgba_sha256'] = {'asset.png': rgba_digest(assembled)}

    # Optional extra files (e.g., PLAN.md, brief, notes)
    for extra in extra_files or []:
        epath = Path(extra)
        if not epath.is_file():
            raise PixelArtError(f'toolkit: --extra-file not found: {epath}')
        dest_key = f'extras/{epath.name}'
        if dest_key in files:
            raise PixelArtError(f'toolkit: duplicate extra file name: {epath.name}')
        files[dest_key] = epath.read_bytes()

    report = {
        'version': 1,
        'toolkit_version': TOOLKIT_VERSION,
        'mode': resolved_mode,
        'tiers': {
            'required': required_checks,
            'contract': contract_checks,
            'advisory': advisory_report,
        },
    }
    files['report.json'] = encoded(report)

    # Finalize manifest with SHA-256 of every file (excluding manifest.json itself)
    manifest['files_sha256'] = {name: _sha256_bytes(data) for name, data in sorted(files.items())}
    files['manifest.json'] = encoded(manifest)

    zip_out = Path(pack_zip) if pack_zip is not None else None
    artifacts = _publication_artifacts(out_dir, files, zip_out, input_paths)

    publish(artifacts, force=force, portable=portable)
    return {
        'mode': resolved_mode,
        'out_dir': str(out_dir.resolve()),
        'files': sorted(files.keys()),
        'zip': str(zip_out.resolve()) if zip_out is not None else None,
        'tiers': report['tiers'],
    }


def rebuild_and_verify(bundle_input, out_dir, *, force=False, portable=False):
    """Unpack (if ZIP), verify CRC & SHA-256 manifest, and independently rebuild delivered PNG(s)."""
    require_pillow()
    bundle_input = Path(bundle_input)
    out_dir = Path(out_dir)
    if not bundle_input.exists():
        raise PixelArtError(f'rebuild: input not found: {bundle_input}')

    with tempfile.TemporaryDirectory(prefix='pixelart_rebuild_') as tmp:
        work_root = Path(tmp)
        crc_ok = None
        if bundle_input.is_file() and bundle_input.suffix.lower() == '.zip':
            with zipfile.ZipFile(bundle_input, 'r') as archive:
                bad = archive.testzip()
                if bad is not None:
                    raise PixelArtError(f'rebuild: ZIP CRC failure at {bad!r}')
                crc_ok = True
                for member in archive.namelist():
                    dest = (work_root / member).resolve()
                    if not dest.is_relative_to(work_root.resolve()):
                        raise PixelArtError(f'rebuild: unsafe archive member path {member!r}')
                archive.extractall(work_root)
            source_dir = work_root
        elif bundle_input.is_dir():
            source_dir = bundle_input
        else:
            raise PixelArtError(f'rebuild: expected a delivery directory or .zip bundle: {bundle_input}')

        manifest_path = source_dir / 'manifest.json'
        if not manifest_path.is_file():
            raise PixelArtError(f'rebuild: missing manifest.json in {bundle_input}')
        manifest = read_json(manifest_path)

        # Verify every listed file's SHA-256
        for rel, expected_hash in manifest.get('files_sha256', {}).items():
            fpath = (source_dir / rel).resolve()
            if not fpath.is_relative_to(source_dir.resolve()) or not fpath.is_file():
                raise PixelArtError(f'rebuild: missing manifest member {rel!r}')
            actual_hash = _sha256_bytes(fpath.read_bytes())
            if actual_hash != expected_hash:
                raise PixelArtError(f'rebuild: SHA-256 mismatch for {rel!r}')

        mode = manifest.get('mode')
        rebuilt_artifacts = {}
        verified_targets = []

        if mode == 'grid':
            rebuilt = render(read_json(source_dir / 'asset.json')).convert('RGBA')
            delivered = _read_static_png(source_dir / 'asset.png').convert('RGBA')
            if rebuilt.tobytes() != delivered.tobytes():
                raise PixelArtError('rebuild: grid asset.png mismatch')
            rebuilt_artifacts[out_dir / 'asset.png'] = encoded(rebuilt)
            verified_targets.append('asset.png')

        elif mode == 'png-native':
            delivered = _read_static_png(source_dir / 'asset.png').convert('RGBA')
            expected_rgba = manifest['rgba_sha256']['asset.png']
            if rgba_digest(delivered) != expected_rgba:
                raise PixelArtError('rebuild: png-native RGBA digest mismatch')
            rebuilt_artifacts[out_dir / 'asset.png'] = encoded(delivered)
            verified_targets.append('asset.png')

        elif mode in ('shared-grid-states', 'state-set'):
            for sname in manifest.get('states', []):
                rebuilt = render(read_json(source_dir / f'specs/{sname}.json')).convert('RGBA')
                delivered = _read_static_png(source_dir / f'states/{sname}.png').convert('RGBA')
                if rebuilt.tobytes() != delivered.tobytes():
                    raise PixelArtError(f'rebuild: state {sname!r} PNG mismatch')
                rebuilt_artifacts[out_dir / f'states/{sname}.png'] = encoded(rebuilt)
                verified_targets.append(f'states/{sname}.png')

        elif mode == 'atlas':
            rebuilt = render(read_json(source_dir / 'atlas.json')).convert('RGBA')
            delivered = _read_static_png(source_dir / 'asset.png').convert('RGBA')
            if rebuilt.tobytes() != delivered.tobytes():
                raise PixelArtError('rebuild: atlas asset.png mismatch')
            layout_data = read_json(source_dir / 'layout.json')
            rebuilt_layout = layout_record(rebuilt)
            if [c['name'] for c in rebuilt_layout['atlas']['cells']] != manifest.get('cell_names'):
                raise PixelArtError('rebuild: atlas cell names did not survive round-trip')
            if [c['name'] for c in layout_data['atlas']['cells']] != manifest.get('cell_names'):
                raise PixelArtError('rebuild: layout.json cell names mismatch')
            rebuilt_artifacts[out_dir / 'asset.png'] = encoded(rebuilt)
            rebuilt_artifacts[out_dir / 'layout.json'] = encoded(rebuilt_layout)
            verified_targets.append('asset.png')

        elif mode == 'assembly':
            project, sources, _ = load_project(source_dir / 'layers/project.json')
            rebuilt, _ = assemble(project, sources)
            delivered = _read_static_png(source_dir / 'asset.png').convert('RGBA')
            if rebuilt.tobytes() != delivered.tobytes():
                raise PixelArtError('rebuild: assembly asset.png mismatch')
            if [p['name'] for p in project['parts']] != manifest.get('part_names'):
                raise PixelArtError('rebuild: assembly part names did not survive round-trip')
            rebuilt_artifacts[out_dir / 'asset.png'] = encoded(rebuilt)
            verified_targets.append('asset.png')

        else:
            raise PixelArtError(f'rebuild: unknown manifest mode {mode!r}')

        summary = {
            'verified': True,
            'mode': mode,
            'crc_checked': crc_ok,
            'manifest_files_checked': len(manifest.get('files_sha256', {})),
            'rebuilt_targets': verified_targets,
            'preserved_cell_names': manifest.get('cell_names'),
            'preserved_part_names': manifest.get('part_names'),
            'preserved_layer_files': manifest.get('layer_files'),
        }
        rebuilt_artifacts[out_dir / 'rebuild-verification.json'] = encoded(summary)
        publish(rebuilt_artifacts, force=force, portable=portable)
        return summary
