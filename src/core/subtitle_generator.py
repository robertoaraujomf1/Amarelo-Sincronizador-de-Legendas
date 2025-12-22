from datetime import timedelta


class SubtitleGenerator:
    def __init__(self):
        pass

    def _format_time(self, seconds: float) -> str:
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        millis = int((seconds - total_seconds) * 1000)

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def generate_from_segments(self, segments: list[dict]) -> str:
        """
        segments: [{start, end, text}]
        """
        lines = []

        for idx, seg in enumerate(segments, start=1):
            start = self._format_time(seg["start"])
            end = self._format_time(seg["end"])
            text = seg["text"]

            lines.append(str(idx))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")

        return "\n".join(lines).strip() + "\n"
