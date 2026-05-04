import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import civitai_gallery_downloader as mod


class DownloaderCoreTests(unittest.TestCase):
    def test_default_media_type_is_image(self):
        cfg = mod.parse_args([
            "https://civitai.com/user/Lannfield/videos",
            "--output-dir",
            "out",
            "--page-delay",
            "0",
            "--download-delay",
            "0",
        ])
        self.assertEqual(cfg.username, "Lannfield")
        self.assertEqual(cfg.media_type, "image")

    def test_fallback_switches_to_author_id_query(self):
        cfg = mod.parse_args([
            "https://civitai.com/user/Lannfield/images",
            "--output-dir",
            "out",
            "--page-delay",
            "0",
            "--download-delay",
            "0",
        ])

        fallback_items = [{"id": 1, "url": "https://example/a.jpeg", "type": "image"}]

        with patch.object(mod, "collect_items_with_params", side_effect=[[], fallback_items]) as mock_collect:
            with patch.object(mod, "extract_author_id_from_page", return_value=12345):
                items, source_mode = mod.collect_images(cfg)

        self.assertEqual(source_mode, "author_id_query")
        self.assertEqual(items, fallback_items)
        self.assertEqual(mock_collect.call_count, 2)

    def test_max_downloads_generates_skipped_reason_and_media_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "out"
            cfg = mod.parse_args([
                "NexBlend",
                "--output-dir",
                str(out_dir),
                "--media-type",
                "all",
                "--max-downloads",
                "2",
                "--page-delay",
                "0",
                "--download-delay",
                "0",
                "--no-progress",
            ])

            items = [
                {"id": 1001, "url": "https://example/1.jpeg", "type": "image", "mimeType": "image/jpeg"},
                {"id": 1002, "url": "https://example/2.mp4", "type": "video", "mimeType": "video/mp4"},
                {"id": 1003, "url": "https://example/3.jpeg", "type": "image", "mimeType": "image/jpeg"},
            ]

            def fake_download(_url: str, destination: Path) -> int:
                destination.write_bytes(b"x")
                return 1

            with patch.object(mod, "http_download", side_effect=fake_download):
                downloaded, skipped, failed, report_file = mod.download_items(cfg, items, "username_query")

            self.assertEqual(downloaded, 2)
            self.assertEqual(skipped, 1)
            self.assertEqual(failed, 0)
            self.assertIsNotNone(report_file)

            report_data = json.loads(Path(report_file).read_text(encoding="utf-8"))
            skipped_items = [x for x in report_data["items"] if x["status"] == "skipped"]
            self.assertEqual(len(skipped_items), 1)
            self.assertEqual(skipped_items[0]["reason"], "max-downloads limit reached")

            user_dir = out_dir / "NexBlend"
            self.assertTrue((user_dir / "images").exists())
            self.assertTrue((user_dir / "video").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
