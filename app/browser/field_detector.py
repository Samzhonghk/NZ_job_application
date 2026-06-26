from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser


@dataclass(frozen=True)
class FormField:
    selector: str
    field_type: str
    label: str = ""
    name: str = ""
    placeholder: str = ""
    aria_label: str = ""
    value: str = ""

    @property
    def search_text(self) -> str:
        return " ".join(
            part
            for part in [self.label, self.name, self.placeholder, self.aria_label]
            if part
        )


class StaticFormParser(HTMLParser):
    """Small fixture parser used by tests and local file dry-runs."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.fields: list[FormField] = []
        self._labels_by_for: dict[str, str] = {}
        self._current_label_for: str | None = None
        self._current_label_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        lower = tag.lower()
        if lower == "label":
            self._current_label_for = attrs_dict.get("for", "")
            self._current_label_text = []
            return

        if lower in {"input", "textarea", "select"}:
            field_id = attrs_dict.get("id", "")
            name = attrs_dict.get("name", "")
            selector = _selector_for(lower, field_id, name, len(self.fields))
            field_type = attrs_dict.get("type", lower) if lower == "input" else lower
            label = self._labels_by_for.get(field_id, "")
            self.fields.append(
                FormField(
                    selector=selector,
                    field_type=field_type,
                    label=label,
                    name=name,
                    placeholder=attrs_dict.get("placeholder", ""),
                    aria_label=attrs_dict.get("aria-label", ""),
                )
            )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "label" and self._current_label_for is not None:
            self._labels_by_for[self._current_label_for] = " ".join(self._current_label_text).strip()
            self._current_label_for = None
            self._current_label_text = []

    def handle_data(self, data: str) -> None:
        if self._current_label_for is not None:
            self._current_label_text.append(data.strip())


def parse_static_form(html: str) -> list[FormField]:
    parser = StaticFormParser()
    parser.feed(html)
    return _apply_labels(parser.fields, parser._labels_by_for)


def _apply_labels(fields: list[FormField], labels_by_for: dict[str, str]) -> list[FormField]:
    updated: list[FormField] = []
    for field in fields:
        label = field.label
        if not label and field.selector.startswith("#"):
            label = labels_by_for.get(field.selector[1:], "")
        updated.append(
            FormField(
                selector=field.selector,
                field_type=field.field_type,
                label=label,
                name=field.name,
                placeholder=field.placeholder,
                aria_label=field.aria_label,
                value=field.value,
            )
        )
    return updated


def _selector_for(tag: str, field_id: str, name: str, index: int) -> str:
    if field_id:
        return f"#{field_id}"
    if name:
        return f'{tag}[name="{name}"]'
    return f"{tag}:nth-of-type({index + 1})"

