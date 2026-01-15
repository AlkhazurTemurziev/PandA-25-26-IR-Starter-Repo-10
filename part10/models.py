from __future__ import annotations
from typing import List, Dict, Any, Tuple


class LineMatch:
    def __init__(self, line_no: int, text: str, spans: List[Tuple[int, int]]):
        self.line_no = line_no
        self.text = text
        self.spans = spans

    def copy(self):
        return LineMatch(self.line_no, self.text, list(self.spans))


class SearchResult:
    def __init__(self, title: str, title_spans: List[Tuple[int, int]], line_matches: List[LineMatch],
                 matches: int) -> None:
        self.title = title
        self.title_spans = title_spans
        self.line_matches = line_matches
        self.matches = matches

    def copy(self):
        return SearchResult(self.title, self.title_spans, self.line_matches, self.matches)

    def combine_with(self, other: SearchResult) -> SearchResult:
        new_matches = self.matches + other.matches
        new_title_spans = sorted(self.title_spans + other.title_spans)

        lines_by_no = {}
        for lm in self.line_matches:
            lines_by_no[lm.line_no] = lm.copy()

        for lm in other.line_matches:
            ln = lm.line_no
            if ln in lines_by_no:
                lines_by_no[ln].spans = lines_by_no[ln].spans + lm.spans
            else:
                lines_by_no[ln] = lm.copy()

        merged_lines = sorted(lines_by_no.values(), key=lambda x: x.line_no)
        return SearchResult(self.title, new_title_spans, merged_lines, new_matches)

    @staticmethod
    def ansi_highlight(text: str, spans, hl_mode: str = "DEFAULT"):
        if not spans:
            return text

        spans = sorted(spans)
        merged = []

        current_start, current_end = spans[0]
        for s, e in spans[1:]:
            if s <= current_end:
                current_end = max(current_end, e)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = s, e
        merged.append((current_start, current_end))

        out = []
        i = 0
        for s, e in merged:
            out.append(text[i:s])
            if hl_mode == "GREEN":
                out.append("\033[1;92m")
            else:
                out.append("\033[30m\033[43m")
            out.append(text[s:e])
            out.append("\033[0m")
            i = e
        out.append(text[i:])
        return "".join(out)

    def print(self, idx: int, highlight: bool, total_docs: int, hl_mode: str = "DEFAULT"):
        if highlight:
            title_line = SearchResult.ansi_highlight(self.title, self.title_spans, hl_mode)
        else:
            title_line = self.title

        print(f"\n[{idx}/{total_docs}] {title_line}")
        for lm in self.line_matches:
            if highlight:
                line_out = SearchResult.ansi_highlight(lm.text, lm.spans, hl_mode)
            else:
                line_out = lm.text
            print(f"  [{lm.line_no:2}] {line_out}")


class Sonnet:
    def __init__(self, sonnet_data: Dict[str, Any]):
        self.title = sonnet_data["title"]
        self.lines = sonnet_data["lines"]

    @staticmethod
    def find_spans(text: str, pattern: str):
        spans = []
        if not pattern:
            return spans

        for i in range(len(text) - len(pattern) + 1):
            if text[i:i + len(pattern)] == pattern:
                spans.append((i, i + len(pattern)))
        return spans

    def search_for(self, query: str) -> SearchResult:
        title_raw = str(self.title)
        lines_raw = self.lines

        q = query.lower()
        title_spans = Sonnet.find_spans(title_raw.lower(), q)

        line_matches = []
        for idx, line_raw in enumerate(lines_raw, start=1):
            spans = Sonnet.find_spans(line_raw.lower(), q)
            if spans:
                line_matches.append(LineMatch(idx, line_raw, spans))

        total = len(title_spans) + sum(len(lm.spans) for lm in line_matches)
        return SearchResult(title_raw, title_spans, line_matches, total)


# ToDo 1: new class for search - I called it SearchEngine
# it holds the sonnets and does the search
class SearchEngine:
    def __init__(self, sonnets: List[Sonnet]):
        self.sonnets = sonnets

    def search(self, query: str, search_mode: str) -> List[SearchResult]:
        words = query.split()
        combined_results = []

        for word in words:
            results = [s.search_for(word) for s in self.sonnets]

            if not combined_results:
                combined_results = results
            else:
                for i in range(len(combined_results)):
                    combined_result = combined_results[i]
                    result = results[i]

                    if search_mode == "AND":
                        if combined_result.matches > 0 and result.matches > 0:
                            combined_results[i] = combined_result.combine_with(result)
                        else:
                            combined_result.matches = 0
                    elif search_mode == "OR":
                        combined_results[i] = combined_result.combine_with(result)

        return combined_results


# ToDo 2: class for settings - this was confusing to figure out
# each setting has: command name, valid values, attribute name on config
class Setting:
    def __init__(self, command: str, values: List[str], attr_name: str, display_name: str):
        self.command = command  # like ":highlight"
        self.values = values  # like ["on", "off"]
        self.attr_name = attr_name  # like "highlight"
        self.display_name = display_name  # for printing

    def try_handle(self, raw: str, config) -> bool:
        # returns True if we handled the command, False if not our command
        if not raw.startswith(self.command):
            return False

        parts = raw.split()
        if len(parts) == 2:
            value = parts[1]
            # check if value is valid (need to handle case)
            value_upper = value.upper()
            value_lower = value.lower()

            # find matching value
            matched_value = None
            for v in self.values:
                if v.upper() == value_upper or v.lower() == value_lower:
                    matched_value = v
                    break

            if matched_value is not None:
                # special case for highlight which uses True/False
                if self.attr_name == "highlight":
                    setattr(config, self.attr_name, matched_value.lower() == "on")
                    print(f"Highlighting", "ON" if getattr(config, self.attr_name) else "OFF")
                else:
                    setattr(config, self.attr_name, matched_value.upper())
                    print(f"{self.display_name} set to", getattr(config, self.attr_name))
                config.save()
                return True

        # invalid usage
        print(f"Usage: {self.command} {'|'.join(self.values)}")
        return True  # still handled, just with error