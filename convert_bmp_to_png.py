#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_bmp_to_png.py — 將 BMP 圖片檔案無損轉換為 PNG。

用法:
    python convert_bmp_to_png.py <BMP 檔案或目錄>

說明:
    - 參數為檔案時: 只轉換該檔案。
    - 參數為目錄時: 遞迴轉換目錄下所有 .bmp 檔案,
      輸出的 .png 放在同一位置(同名、副檔名改為 .png)。
    - PNG 本身為無損格式; 腳本會以 BMP 原始的像素模式直接存檔
      (1-bit 二值 / 8-bit 灰階 / 8-bit 調色盤 / 24-bit RGB / 32-bit RGBA),
      不做任何重新取樣或壓縮損耗, 畫質完全不會下降。
    - 轉換後會自動逐像素比對原圖與 PNG, 若有差異會報錯。
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("未偵測到 Pillow, 請先執行: pip install Pillow")

# PIL 可讀取的 BMP 模式, 以及 PNG 能直接保存的模式
PNG_OK_MODES = {"1", "L", "I", "P", "RGB", "RGBA"}


def _normalize(img: Image.Image):
    """轉成可逐像素比較的格式, 供驗證使用。"""
    if img.mode in ("1", "L", "P", "RGB", "RGBA"):
        return img.convert("RGB" if img.mode in ("1", "L", "P", "RGB") else "RGBA")
    return img.convert("RGB")


def convert(src: Path, dst: Path) -> None:
    with Image.open(src) as img:
        img.load()
        to_save = img
        if img.mode not in PNG_OK_MODES:
            # 理論上 BMP 不會落到這裡; 保險起見轉成 RGB/RGBA
            to_save = img.convert("RGBA" if "A" in img.mode else "RGB")
        to_save.save(dst, format="PNG")

    # 驗證: 重新讀取 PNG 並逐像素比對, 確保畫質未下降
    with Image.open(dst) as out, Image.open(src) as ref:
        a, b = _normalize(out), _normalize(ref)
        if a.size != b.size:
            raise RuntimeError(f"尺寸不一致: {a.size} vs {b.size}")
        if a.tobytes() != b.tobytes():
            raise RuntimeError("像素數據不一致, 轉換可能損耗!")

    print(f"OK: {src} -> {dst}")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    target = Path(sys.argv[1])

    if target.is_file():
        if target.suffix.lower() != ".bmp":
            print(f"錯誤: {target} 不是 .bmp 檔案", file=sys.stderr)
            return 1
        try:
            convert(target, target.with_suffix(".png"))
        except Exception as e:
            print(f"失敗: {target}: {e}", file=sys.stderr)
            return 1
        return 0

    if not target.is_dir():
        print(f"錯誤: {target} 不存在", file=sys.stderr)
        return 1

    bmps = sorted(p for p in target.rglob("*")
                  if p.is_file() and p.suffix.lower() == ".bmp")
    if not bmps:
        print(f"在 {target} 下找不到 .bmp 檔案")
        return 0

    failures = 0
    for p in bmps:
        try:
            convert(p, p.with_suffix(".png"))
        except Exception as e:
            failures += 1
            print(f"失敗: {p}: {e}", file=sys.stderr)

    print(f"\n完成: 成功 {len(bmps) - failures} / {len(bmps)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
