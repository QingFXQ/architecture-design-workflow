"""Read-only delivery preflight. Checks file/version/print evidence, not architectural or aesthetic quality."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

DRAWINGS = {'plan', 'elevation', 'section', 'site'}


def validate(data, root):
    root = Path(root)
    issues, assets, stale = [], {}, set()

    def issue(level, code, target, message):
        issues.append({'level': level, 'code': code, 'target': target, 'message': message})

    def positive(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0

    def inspect_pdf(path, target, expected_size=None, required_font=None):
        try:
            import fitz
        except ImportError:
            issue('warning', 'PDF_INSPECTION_UNAVAILABLE', target, 'PyMuPDF未安装；未核实PDF纸幅／字体，需其他实际检查。')
            return
        try:
            with fitz.open(path) as pdf:
                if expected_size and len(pdf) != 1:
                    issue('error', 'BOARD_PAGE_COUNT', target, f'应为单张PDF，实际{len(pdf)}页')
                font_names, text_spans = set(), []
                for page in pdf:
                    if expected_size:
                        actual = (page.rect.width * 25.4 / 72, page.rect.height * 25.4 / 72)
                        if any(abs(a-b) > .5 for a, b in zip(actual, expected_size)):
                            issue('error', 'PAPER_SIZE', target, f'实测{actual[0]:.2f}×{actual[1]:.2f}mm，与清单不符')
                    for block in page.get_text('dict')['blocks']:
                        for line in block.get('lines', []):
                            text_spans.extend(span for span in line['spans'] if span.get('text', '').strip())
                    for font in page.get_fonts(full=True):
                        xref, _, _, name, *_ = font
                        font_names.add(name.casefold().replace(' ', ''))
                        if xref and not pdf.extract_font(xref)[3]:
                            issue('warning', 'FONT_NOT_EMBEDDED', target, f'字体{name}未提取到嵌入数据，需核打印替换')
                if required_font and text_spans:
                    aliases = ['fangsong', 'simfang', '仿宋'] if required_font.casefold() in {'fangsong', '仿宋'} else [required_font.casefold().replace(' ', '')]
                    # Mixed heading fonts are allowed on boards; this applies only to a drawing asset.
                    unmatched = [name for name in font_names if not any(alias in name for alias in aliases)]
                    if unmatched:
                        issue('warning', 'DRAWING_FONT', target, '存在不匹配的图纸字体：' + ', '.join(sorted(unmatched)))
                if expected_size and text_spans:
                    minimum = data.get('print_profile', {}).get('min_text_height_mm')
                    if positive(minimum):
                        small = sum(span['size'] * 25.4 / 72 < minimum - .05 for span in text_spans)
                        if small:
                            issue('warning', 'SMALL_PDF_TEXT', target, f'{small}处文字名义字高小于{minimum}mm；需看局部，不能只改图名')
                elif not text_spans:
                    issue('warning', 'NO_EXTRACTABLE_TEXT', target, '没有可提取文字，可能是整页光栅／转曲；需人工视觉检查清晰度')
        except Exception as exc:
            issue('error', 'INVALID_PDF', target, f'无法读取PDF：{type(exc).__name__}: {exc}')

    current = data.get('project', {}).get('current_revisions', {})
    for asset in data.get('assets', []):
        key = asset.get('id')
        if not key or key in assets:
            issue('error', 'ASSET_ID', str(key), '成果ID为空或重复')
            continue
        assets[key] = asset
        for scope, revision in asset.get('source_revisions', {}).items():
            if current.get(scope) != revision:
                stale.add(key)
                issue('error', 'STALE_SOURCE', key, f'{scope}来源{revision}与当前{current.get(scope)}不符')
        file = asset.get('file')
        path = root / file if file else None
        if not path or not path.is_file():
            issue('error', 'MISSING_ASSET', key, f'找不到实际图件：{file}')
        elif path.stat().st_size == 0:
            issue('error', 'EMPTY_ASSET', key, '图件为空文件')
        elif path.suffix.lower() == '.pdf':
            inspect_pdf(path, key, required_font=asset.get('required_font_family'))
        if asset.get('kind') in DRAWINGS:
            if not positive(asset.get('scale')):
                issue('error', 'SCALE', key, '需填写实际最终比例分母，且大于0')
            if not asset.get('title', '').endswith('图'):
                issue('warning', 'DRAWING_TITLE', key, '正式图名应清楚写xxx图，比例另列')
        if not asset.get('visual_reviewed'):
            issue('warning', 'VISUAL_REVIEW', key, '尚未记录实际看完整图面；本工具不能替代')

    # Propagate stale source status through downstream dependencies.
    for key, asset in assets.items():
        for dep in asset.get('depends_on', []):
            if dep not in assets:
                issue('error', 'MISSING_DEPENDENCY', key, f'未登记依赖{dep}')
    for _ in range(len(assets)):
        changed = False
        for key, asset in assets.items():
            if key not in stale and any(dep in stale for dep in asset.get('depends_on', [])):
                stale.add(key); changed = True
                issue('error', 'STALE_DEPENDENCY', key, '使用了过期的上游图件')
        if not changed:
            break

    boards = data.get('boards', [])
    brief = data.get('brief', {})
    expected_count = brief.get('board_count')
    if expected_count is not None and len(boards) != expected_count:
        issue('error', 'BOARD_COUNT', 'boards', f'要求{expected_count}张，登记{len(boards)}张')
    placed, board_ids = set(), set()
    for board in boards:
        key = board.get('id', '')
        if not key or key in board_ids:
            issue('error', 'BOARD_ID', str(key), '图板ID为空或重复')
        board_ids.add(key)
        width, height = board.get('width_mm'), board.get('height_mm')
        if not positive(width) or not positive(height):
            issue('error', 'BOARD_SIZE', key, '纸幅宽高需为有效毫米值')
            continue
        requested = brief.get('paper_mm')
        if requested and [width, height] != requested:
            issue('error', 'BRIEF_PAPER_SIZE', key, '登记纸幅／方向与任务书不符')
        path = root / board.get('file', '')
        if not path.is_file():
            issue('error', 'MISSING_BOARD', key, '最终PDF文件不存在')
        elif path.suffix.lower() != '.pdf':
            issue('error', 'BOARD_FORMAT', key, '最终图板需为PDF')
        else:
            inspect_pdf(path, key, expected_size=(width, height))
        for placement in board.get('placements', []):
            aid = placement.get('asset')
            if aid not in assets:
                issue('error', 'UNKNOWN_PLACEMENT', key, f'未知成果{aid}')
                continue
            placed.add(aid)
            x, y = placement.get('x_mm', 0), placement.get('y_mm', 0)
            w, h = placement.get('width_mm'), placement.get('height_mm')
            if not all(isinstance(n, (int, float)) and math.isfinite(n) for n in [x, y]) or not positive(w) or not positive(h):
                issue('error', 'PLACEMENT_SIZE', aid, '版面位置／宽高无效')
                continue
            if x < 0 or y < 0 or x+w > width+.5 or y+h > height+.5:
                issue('error', 'OUTSIDE_BOARD', aid, '图件超出纸面；有意出血需另按打印方案处理')
            a = assets[aid]
            model_w, scale = a.get('model_width_m'), a.get('scale')
            if positive(model_w) and positive(scale):
                expected = model_w * 1000 / scale
                if abs(expected-w) > max(.5, expected*.01):
                    issue('error', 'PLACED_SCALE', aid, f'该几何跨度按比例应宽{expected:.2f}mm，实际登记{w:.2f}mm；宽度必须指净几何而非整张带边图')
            min_height = data.get('print_profile', {}).get('min_text_height_mm')
            final_height = placement.get('final_annotation_height_mm')
            if positive(min_height) and positive(final_height) and final_height < min_height:
                issue('warning', 'SMALL_DRAWING_TEXT', aid, '最终图内字高偏小，需要调整图内注记')
            pixels = a.get('pixels')
            if pixels and positive(pixels[0]):
                ppi = pixels[0] / (w/25.4)
                minimum = data.get('print_profile', {}).get('min_raster_ppi')
                if positive(minimum) and ppi < minimum:
                    issue('warning', 'RASTER_PPI', aid, f'按登记像素计算有效{ppi:.0f}PPI，低于本项目{minimum}')
        if not all(board.get('visual_review', {}).get(view) for view in ['overview', 'details']):
            issue('warning', 'BOARD_VISUAL_REVIEW', key, '未记录整版＋100%局部实际检查')
    for aid in brief.get('required_assets', []):
        if aid not in assets:
            issue('error', 'REQUIRED_ASSET', aid, '必交图未登记')
        elif aid not in placed:
            issue('error', 'REQUIRED_NOT_PLACED', aid, '必交图未放入最终图板')
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--strict', action='store_true', help='also fail on warnings; not an additional mandatory Gate')
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding='utf-8-sig'))
        issues = validate(data, args.manifest.resolve().parent)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 2
    errors = sum(i['level'] == 'error' for i in issues)
    warnings = len(issues)-errors
    result = {'errors': errors, 'warnings': warnings, 'issues': issues, 'scope': 'Read-only preflight; not proof of design, visual quality or building compliance.'}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'错误 {errors}；提示 {warnings}。不能代替看图和建筑判断。')
        for i in issues:
            print(f"[{i['level']}] {i['target']} / {i['code']}: {i['message']}")
    return int(errors > 0 or (args.strict and warnings > 0))


if __name__ == '__main__':
    raise SystemExit(main())
