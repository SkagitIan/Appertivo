import datetime
import json
import os

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - library missing in tests
    OpenAI = None


def enhance_special_content(special):
    """Use OpenAI to enhance textual content for a Special.

    Sends the current title, description, price, start_date, and end_date
    to the OpenAI API and updates the instance with any returned values.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return special
    client = OpenAI(api_key=api_key)
    prompt = (
        "Enhance the following restaurant special. "
        "Return JSON with keys: title, description, price, start_date, end_date.\n"
        f"Title: {special.title}\n"
        f"Description: {special.description}\n"
        f"Price: {special.price}\n"
        f"Start Date: {special.start_date}\n"
        f"End Date: {special.end_date}"
    )
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        response_format={"type": "json_object"},
    )
    try:
        content = response.output[0].content[0].text
        data = json.loads(content)
    except Exception:
        return special
    for field in ["title", "description", "price", "start_date", "end_date"]:
        value = data.get(field)
        if not value:
            continue
        if field in {"start_date", "end_date"}:
            try:
                value = datetime.date.fromisoformat(value)
            except Exception:
                continue
        setattr(special, field, value)
    special.save()
    return special
